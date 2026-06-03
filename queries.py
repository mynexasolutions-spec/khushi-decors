import math
import datetime as _dt
import uuid
from sqlalchemy import or_, and_, func, desc, case
from sqlalchemy.orm import aliased
from extensions import db_sql
from helpers import ttl_cache, resolve_image
from models import (
    Product, Category, Brand, ProductImage, ProductVariation, 
    VariationAttributeValue, ProductAttribute, ProductAttributeValue,
    VariationImage, ProductReview, Order, User, Media, AttributeValue, Attribute
)

_EPOCH = _dt.datetime.min

def _row_to_dict(row):
    """Convert an SQLAlchemy Row object to a dictionary."""
    if hasattr(row, "_mapping"):
        return dict(row._mapping)
    return row

def _get_products_query(minimal=False):
    """Build the base select query for products, mimicking the raw SQL helpers."""
    # Subquery for min variation price
    min_var_price = (db_sql.session.query(func.min(ProductVariation.price))
                     .filter(ProductVariation.product_id == Product.id, ProductVariation.price > 0)
                     .scalar_subquery())
                     
    price_coalesce = func.coalesce(
        case(
            (Product.type == 'variable', min_var_price),
            else_=Product.price
        ),
        Product.price
    )
    
    # Subquery for primary image URL
    primary_img_sub = (db_sql.session.query(Media.file_url)
                       .join(ProductImage, ProductImage.media_id == Media.id)
                       .filter(ProductImage.product_id == Product.id, ProductImage.is_primary == 1)
                       .limit(1)
                       .scalar_subquery())
                       
    if minimal:
        q = db_sql.session.query(
            Product.id, Product.name, Product.slug, Product.sku, Product.type,
            Product.short_description, Product.description,
            price_coalesce.label("price"),
            Product.sale_price, Product.stock_status, Product.is_featured, Product.created_at,
            Category.name.label("category_name"), Category.slug.label("category_slug"),
            primary_img_sub.label("image_url")
        )
    else:
        q = db_sql.session.query(
            Product.id, Product.name, Product.slug, Product.sku, Product.type, 
            Product.short_description, Product.description,
            price_coalesce.label("price"),
            Product.sale_price, Product.stock_quantity, Product.stock_status,
            Product.is_featured, Product.is_active, Product.created_at,
            Category.name.label("category_name"), Category.slug.label("category_slug"),
            Brand.name.label("brand_name"), Brand.slug.label("brand_slug"),
            primary_img_sub.label("image_url")
        )
        
    q = q.outerjoin(Category, Category.id == Product.category_id)\
         .outerjoin(Brand, Brand.id == Product.brand_id)
         
    return q

@ttl_cache(ttl_seconds=120)
def _get_variation_cards():
    """
    Returns a lookup: { product_id: [ expanded_row_dict, ... ] }
    where variations are grouped by their primary attribute (e.g. Shape),
    displaying one clean catalog card per Shape instead of duplicate cards for sizes.
    """
    variable_products = Product.query.filter_by(is_active=1, type="variable").all()
    if not variable_products:
        return {}

    product_ids = [str(p.id) for p in variable_products]
    product_parents = {str(p.id): p for p in variable_products}

    # Fetch all variation attribute values in a single high-efficiency query
    vav_rows = (db_sql.session.query(
                    VariationAttributeValue.variation_id,
                    AttributeValue.value,
                    Attribute.variation_type
                )
                .join(AttributeValue, AttributeValue.id == VariationAttributeValue.attribute_value_id)
                .join(Attribute, Attribute.id == AttributeValue.attribute_id)
                .join(ProductVariation, ProductVariation.id == VariationAttributeValue.variation_id)
                .filter(ProductVariation.product_id.in_(product_ids))
                .all())
                
    vav_map = {}
    for r in vav_rows:
        vav_map.setdefault(str(r.variation_id), []).append({
            "value": r.value,
            "variation_type": r.variation_type
        })
        
    # Fetch primary variation image lookup map
    vi_rows = (db_sql.session.query(VariationImage.variation_id, Media.file_url)
               .join(Media, Media.id == VariationImage.media_id)
               .filter(VariationImage.is_primary == 1)
               .all())
    var_image_lookup = {str(r.variation_id): r.file_url for r in vi_rows}
    
    # Fetch parent product image lookup map
    pi_rows = (db_sql.session.query(ProductImage.product_id, Media.file_url)
               .join(Media, Media.id == ProductImage.media_id)
               .filter(ProductImage.is_primary == 1)
               .all())
    product_image_lookup = {str(r.product_id): r.file_url for r in pi_rows}

    result = {}
    for pid in product_ids:
        parent = product_parents.get(pid)
        if not parent:
            continue
            
        p_vars = ProductVariation.query.filter_by(product_id=parent.id).all()
        
        # Group variations of this product by primary values (e.g. Shape)
        groups = {}
        for v in p_vars:
            vid = str(v.id)
            vals = vav_map.get(vid, [])
            
            primary_vals = sorted([r["value"] for r in vals if r["variation_type"] == 'primary'])
            secondary_vals = sorted([r["value"] for r in vals if r["variation_type"] != 'primary'])
            
            if primary_vals:
                group_key = ", ".join(primary_vals)
            else:
                group_key = ", ".join(secondary_vals) if secondary_vals else ""
                
            groups.setdefault(group_key, []).append(v)
            
        result[pid] = []
        for group_key, vars_list in groups.items():
            # Pick lowest price variation to represent the group
            best_var = min(vars_list, key=lambda v: float(v.sale_price or v.price or 999999))
            
            # Resolve prices & stocks with parent fallbacks
            original_price = float(best_var.price or 0)
            sale_price = float(best_var.sale_price) if best_var.sale_price else None
            if original_price <= 0:
                original_price = float(parent.price or 0)
                sale_price = float(parent.sale_price) if parent.sale_price else None
                
            stock_val = int(best_var.stock_quantity or 0)
            if stock_val <= 0:
                stock_val = int(parent.stock_quantity or 0)
                
            stock_status_val = best_var.stock_status or parent.stock_status
            var_img = var_image_lookup.get(str(best_var.id)) or product_image_lookup.get(pid) or ""
            
            result[pid].append({
                "var_id":         str(best_var.id),
                "sku":            best_var.sku,
                "price":          original_price,
                "sale_price":     sale_price,
                "stock_quantity": stock_val,
                "stock_status":   stock_status_val,
                "name_override":  f"{parent.name} – {group_key}" if group_key else parent.name,
                "image_url":      resolve_image(var_img),
                "description":    best_var.description or "",
                "short_description": best_var.short_description or "",
                "label":          group_key,
                "_preselect_label": group_key
            })

    return result

def _expand_product_list(products):
    """Expand every variation into a separate listing card."""
    var_map = _get_variation_cards()
    expanded = []

    # Perform performant bulk fetches to load all images for slideshows
    prod_ids = [str(p["id"]) for p in (products or [])]

    # 1. Bulk Query all ProductImages for active products
    p_images_map = {}
    if prod_ids:
        from models import ProductImage
        p_img_rows = (db_sql.session.query(ProductImage.product_id, Media.file_url)
                      .join(Media, Media.id == ProductImage.media_id)
                      .filter(ProductImage.product_id.in_(prod_ids))
                      .order_by(ProductImage.display_order.asc())
                      .all())
        for p_id, f_url in p_img_rows:
            p_images_map.setdefault(str(p_id), []).append(resolve_image(f_url))

    # 2. Bulk Query all VariationImages in database
    v_images_map = {}
    v_img_rows = (db_sql.session.query(VariationImage.variation_id, Media.file_url)
                  .join(Media, Media.id == VariationImage.media_id)
                  .order_by(VariationImage.display_order.asc())
                  .all())
    for v_id, f_url in v_img_rows:
        v_images_map.setdefault(str(v_id), []).append(resolve_image(f_url))

    for p in (products or []):
        pid = str(p["id"])

        # Sourced product default images array
        default_images = p_images_map.get(pid, [])
        if not default_images:
            default_images = [resolve_image(p.get("image_url") or "")]

        if pid in var_map:
            for r in var_map[pid]:
                row = dict(p)
                row["id"]             = pid
                row["name"]           = r["name_override"]
                row["price"]          = r["price"]
                row["sale_price"]     = r["sale_price"]
                row["stock_quantity"] = r["stock_quantity"]
                row["stock_status"]   = r["stock_status"]
                row["sku"]            = r["sku"]
                row["image_url"]      = resolve_image(r["image_url"] or p.get("image_url") or "")
                row["description"]    = r.get("description") or row.get("description") or ""
                row["short_description"] = r.get("short_description") or row.get("short_description") or ""
                row["_preselect_label"] = r.get("label", "")

                # Assign slideshow images (variation images falling back to parent default images)
                var_imgs = v_images_map.get(str(r["var_id"]), [])
                row["images"]         = var_imgs if var_imgs else default_images
                expanded.append(row)
        else:
            p_copy = dict(p)
            p_copy.setdefault("description", "")
            p_copy.setdefault("short_description", "")
            p_copy["image_url"] = resolve_image(p_copy.get("image_url") or "")

            # Assign slideshow parent default images
            p_copy["images"]    = default_images
            expanded.append(p_copy)
    return expanded

@ttl_cache(ttl_seconds=60)
def get_products(search=None, categories=(), brands=(),
                 sort="created_at_desc", page=1, per_page=16,
                 featured=False, limit=None, on_sale=False,
                 min_price=None, max_price=None,
                 category=None, brand=None, skip_expand=False,
                 attribute_values=()):
    
    # Normalise inputs
    cats_list = list(c for c in (list(categories or []) + ([category] if category else [])) if c)
    if len(cats_list) > 1:
        all_cats = get_categories()
        sel_cats = [c for c in all_cats if c["slug"] in cats_list]
        parent_ids = {c["parent_id"] for c in sel_cats if c.get("parent_id")}
        cats = tuple(c["slug"] for c in sel_cats if c["id"] not in parent_ids)
    else:
        cats = tuple(cats_list)
        
    brnds = tuple(b for b in (list(brands or []) + ([brand] if brand else [])) if b)

    # Base query
    q = _get_products_query(minimal=(limit is not None))
    q = q.filter(Product.is_active == 1)

    # Search filter
    if search:
        search_like = f"%{search}%"
        var_search_sub = (db_sql.session.query(ProductVariation.product_id)
                          .join(VariationAttributeValue, VariationAttributeValue.variation_id == ProductVariation.id)
                          .join(AttributeValue, AttributeValue.id == VariationAttributeValue.attribute_value_id)
                          .filter(AttributeValue.value.like(search_like))
                          .scalar_subquery())
        q = q.filter(
            or_(
                Product.name.like(search_like),
                Product.sku.like(search_like),
                Product.description.like(search_like),
                Product.id.in_(var_search_sub)
            )
        )

    # Categories filter
    if cats:
        cat_slug_sub = (db_sql.session.query(Category.id)
                        .filter(
                            or_(
                                Category.slug.in_(cats),
                                Category.parent_id.in_(
                                    db_sql.session.query(Category.id).filter(Category.slug.in_(cats)).scalar_subquery()
                                )
                            )
                        )
                        .scalar_subquery())
        q = q.filter(Product.category_id.in_(cat_slug_sub))

    # Brands filter
    if brnds:
        q = q.filter(Brand.slug.in_(brnds))

    # Featured filter
    if featured:
        q = q.filter(Product.is_featured == 1)

    # On sale filter
    if on_sale:
        q = q.filter(Product.sale_price.isnot(None), Product.sale_price > 0, Product.sale_price < Product.price)

    # Attribute values filter
    if attribute_values:
        attr_vals_sub = (db_sql.session.query(ProductVariation.product_id)
                         .join(VariationAttributeValue, VariationAttributeValue.variation_id == ProductVariation.id)
                         .filter(VariationAttributeValue.attribute_value_id.in_(attribute_values))
                         .scalar_subquery())
        q = q.filter(Product.id.in_(attr_vals_sub))

    # Price filters
    min_var_price_sub = (db_sql.session.query(func.min(ProductVariation.price))
                         .filter(ProductVariation.product_id == Product.id, ProductVariation.price > 0)
                         .scalar_subquery())
    actual_price = func.coalesce(
        case(
            (Product.type == 'variable', min_var_price_sub),
            else_=Product.price
        ),
        Product.price
    )
    
    if min_price is not None:
        q = q.filter(func.coalesce(Product.sale_price, actual_price) >= min_price)
    if max_price is not None:
        q = q.filter(func.coalesce(Product.sale_price, actual_price) <= max_price)

    # Sorting
    order_map = {
        "created_at_desc": Product.created_at.desc(),
        "created_at_asc":  Product.created_at.asc(),
        "price_asc":       Product.price.asc(),
        "price_desc":      Product.price.desc(),
        "name_asc":        Product.name.asc(),
    }
    sort_order = order_map.get(sort, Product.created_at.desc())
    q = q.order_by(sort_order)

    if limit:
        rows = q.limit(limit).all()
        dict_rows = [_row_to_dict(r) for r in rows]
        return _expand_product_list(dict_rows)

    all_products = [_row_to_dict(r) for r in q.all()]

    if skip_expand:
        total       = len(all_products)
        total_pages = max(1, math.ceil(total / per_page))
        offset      = (page - 1) * per_page
        products    = all_products[offset:offset + per_page]
        return products, total, total_pages

    expanded = _expand_product_list(all_products)
    total       = len(expanded)
    total_pages = max(1, math.ceil(total / per_page))
    offset      = (page - 1) * per_page
    products    = expanded[offset:offset + per_page]
    return products, total, total_pages

@ttl_cache(ttl_seconds=120)
def get_homepage_products():
    """Single query for all homepage product sections; partitioned in Python."""
    q = _get_products_query(minimal=True).filter(Product.is_active == 1).order_by(Product.is_featured.desc(), Product.created_at.desc()).limit(100)
    rows = [_row_to_dict(r) for r in q.all()]
    
    featured   = [r for r in rows if r.get("is_featured")][:10]
    if not featured:
        featured = rows[:10]
    latest     = sorted(rows, key=lambda r: r.get("created_at") or _EPOCH, reverse=True)[:10]
    popular    = sorted(rows, key=lambda r: (r.get("name") or "").lower())[:10]
    
    price_asc  = sorted(rows, key=lambda r: float(r.get("price") or 0))
    promo1     = rows[:2]
    promo2     = price_asc[:2]

    # Expand primary variations in all sections
    featured = _expand_product_list(featured)
    latest   = _expand_product_list(latest)
    popular  = _expand_product_list(popular)
    promo1   = _expand_product_list(promo1)
    promo2   = _expand_product_list(promo2)
    
    return {
        "featured": featured, "latest": latest, "popular": popular,
        "promo1": promo1, "promo2": promo2
    }

@ttl_cache(ttl_seconds=600)
def get_featured_categories():
    rows = (db_sql.session.query(Category.name.label("label"), Category.image_url.label("img"), Category.slug)
            .filter(Category.parent_id.is_(None))
            .group_by(Category.name, Category.image_url, Category.slug)
            .order_by(Category.name.asc())
            .all())
    return [_row_to_dict(r) for r in rows]

@ttl_cache(ttl_seconds=120)
def get_product_detail(product_id, preselect=None):
    p_row = _get_products_query().filter(
        or_(
            Product.id == product_id,
            Product.slug == product_id,
            Product.name == product_id
        )
    ).first()
    if not p_row:
        return None, [], [], [], []
    product = _row_to_dict(p_row)

    images_rows = (db_sql.session.query(Media.file_url.label("image_url"), ProductImage.is_primary, func.coalesce(Media.alt_text, '').label("alt_text"))
                   .join(ProductImage, ProductImage.media_id == Media.id)
                   .filter(ProductImage.product_id == product_id)
                   .order_by(ProductImage.is_primary.desc(), ProductImage.display_order.asc())
                   .all())
    images = [_row_to_dict(r) for r in images_rows]

    variations_rows = ProductVariation.query.filter_by(product_id=product_id).all()
    variations = []
    for v in variations_rows:
        variations.append({
            "id": v.id, "product_id": v.product_id, "sku": v.sku,
            "price": float(v.price or 0), "sale_price": float(v.sale_price) if v.sale_price else None,
            "stock_quantity": int(v.stock_quantity or 0), "stock_status": v.stock_status,
            "name": v.name, "short_description": v.short_description, "description": v.description,
            "created_at": v.created_at
        })

    base_price = float(product.get("sale_price") or product.get("price") or 0)
    base_stock = int(product.get("stock_quantity") or 0)

    # Server-side pre-selection
    preselect_match = None
    if preselect and product.get("type") == "variable" and variations:
        preselect_parts = [p.strip() for p in preselect.split(",") if p.strip()]
        if preselect_parts:
            var_ids_tmp = [v["id"] for v in variations]
            vav_rows = (db_sql.session.query(VariationAttributeValue.variation_id, AttributeValue.value)
                        .join(AttributeValue, AttributeValue.id == VariationAttributeValue.attribute_value_id)
                        .filter(VariationAttributeValue.variation_id.in_(var_ids_tmp))
                        .all())
            var_val_map = {}
            for r in vav_rows:
                var_val_map.setdefault(str(r.variation_id), []).append(r.value)
            for v in variations:
                vals = var_val_map.get(str(v["id"]), [])
                if all(p in vals for p in preselect_parts):
                    preselect_match = v
                    break

    if variations:
        var_ids = [v["id"] for v in variations]
        all_vav = VariationAttributeValue.query.filter(VariationAttributeValue.variation_id.in_(var_ids)).all()
        vav_map = {}
        for row in all_vav:
            vav_map.setdefault(str(row.variation_id), []).append(row.attribute_value_id)
        for v in variations:
            if not v.get("price") or float(v["price"]) <= 0:
                v["price"] = base_price
            if not v.get("stock_quantity") or int(v["stock_quantity"]) <= 0:
                v["stock_quantity"] = base_stock
            v["attribute_value_ids"] = vav_map.get(str(v["id"]), [])
    else:
        for v in variations:
            v["price"]               = base_price
            v["stock_quantity"]      = base_stock
            v["attribute_value_ids"] = []

    if product.get("type") == "variable":
        product["price"] = base_price if base_price > 0 else float(product.get("price") or 0)

    # Apply preselect overrides
    if preselect_match:
        var_label = ", ".join(preselect_parts)
        var_display_name = (preselect_match.get("name") or f"{product['name']} – {var_label}") if var_label else product["name"]
        product["name"]             = var_display_name
        product["description"]      = preselect_match.get("description") or product.get("description", "")
        product["short_description"] = preselect_match.get("short_description") or product.get("short_description", "")
        product["price"]            = float(preselect_match.get("sale_price") or preselect_match.get("price") or product.get("price", 0))
        product["sale_price"]       = float(preselect_match["sale_price"]) if preselect_match.get("sale_price") else product.get("sale_price")
        product["sku"]              = preselect_match.get("sku") or product.get("sku", "")
        product["stock_quantity"]   = int(preselect_match.get("stock_quantity") or product.get("stock_quantity", 0))
        product["stock_status"]     = preselect_match.get("stock_status") or product.get("stock_status", "in_stock")

        var_images_rows = (db_sql.session.query(Media.file_url.label("image_url"), VariationImage.is_primary, func.coalesce(Media.alt_text, '').label("alt_text"))
                           .join(VariationImage, VariationImage.media_id == Media.id)
                           .filter(VariationImage.variation_id == preselect_match["id"])
                           .order_by(VariationImage.is_primary.desc(), VariationImage.display_order.asc())
                           .all())
        var_images = [_row_to_dict(r) for r in var_images_rows]
        if var_images:
            images = var_images
            product["image_url"] = var_images[0]["image_url"]

    reviews_rows = (db_sql.session.query(ProductReview)
                    .outerjoin(User, User.id == ProductReview.user_id)
                    .filter(ProductReview.product_id == product_id, ProductReview.is_approved == 1)
                    .order_by(ProductReview.created_at.desc())
                    .all())
    
    # Load user names manually
    reviews = []
    for r in reviews_rows:
        user_name = "Anonymous"
        if r.user_id:
            u = User.query.get(r.user_id)
            if u:
                user_name = f"{u.first_name} {u.last_name}".strip()
        reviews.append({
            "id": r.id, "product_id": r.product_id, "user_id": r.user_id,
            "rating": r.rating, "title": r.title, "body": r.body,
            "is_approved": r.is_approved, "created_at": r.created_at,
            "reviewer_name": user_name
        })

    # Fetch attributes
    attributes_rows = (db_sql.session.query(Attribute.id, Attribute.name, Attribute.slug)
                       .join(ProductAttribute, ProductAttribute.attribute_id == Attribute.id)
                       .filter(ProductAttribute.product_id == product_id)
                       .order_by(ProductAttribute.display_order.asc())
                       .all())
    attributes = [_row_to_dict(r) for r in attributes_rows]

    if not attributes:
        attributes_rows = (db_sql.session.query(Attribute.id, Attribute.name, Attribute.slug)
                           .distinct(Attribute.id)
                           .join(AttributeValue, AttributeValue.attribute_id == Attribute.id)
                           .join(VariationAttributeValue, VariationAttributeValue.attribute_value_id == AttributeValue.id)
                           .join(ProductVariation, ProductVariation.id == VariationAttributeValue.variation_id)
                           .filter(ProductVariation.product_id == product_id)
                           .all())
        attributes = [_row_to_dict(r) for r in attributes_rows]

    if attributes:
        attr_ids = [a["id"] for a in attributes]

        # Priority 1: values checked by admin
        pav_rows = (db_sql.session.query(AttributeValue.attribute_id, AttributeValue.id, AttributeValue.value)
                    .distinct(AttributeValue.id)
                    .join(ProductAttributeValue, ProductAttributeValue.attribute_value_id == AttributeValue.id)
                    .filter(AttributeValue.attribute_id.in_(attr_ids), ProductAttributeValue.product_id == product_id)
                    .order_by(AttributeValue.value.asc())
                    .all())
        pav_map = {}
        for row in pav_rows:
            pav_map.setdefault(str(row.attribute_id), []).append({"id": str(row.id), "value": row.value})

        # Priority 2: values linked through variations
        var_rows = (db_sql.session.query(AttributeValue.attribute_id, AttributeValue.id, AttributeValue.value)
                    .distinct(AttributeValue.id)
                    .join(VariationAttributeValue, VariationAttributeValue.attribute_value_id == AttributeValue.id)
                    .join(ProductVariation, ProductVariation.id == VariationAttributeValue.variation_id)
                    .filter(AttributeValue.attribute_id.in_(attr_ids), ProductVariation.product_id == product_id)
                    .order_by(AttributeValue.value.asc())
                    .all())
        var_map = {}
        for row in var_rows:
            var_map.setdefault(str(row.attribute_id), []).append({"id": str(row.id), "value": row.value})

        for attr in attributes:
            aid    = str(attr["id"])
            values = pav_map.get(aid) or var_map.get(aid)
            if not values:
                # Priority 3: fallback
                fallback = AttributeValue.query.filter_by(attribute_id=attr["id"]).order_by(AttributeValue.value.asc()).all()
                values = [{"id": str(r.id), "value": r.value} for r in fallback]
            attr["values"] = values

    return product, images, variations, reviews, attributes

@ttl_cache(ttl_seconds=120)
def get_related_products(category_slug, exclude_id, limit=4):
    q = _get_products_query(minimal=True).filter(Product.is_active == 1, Category.slug == category_slug, Product.id != exclude_id).order_by(Product.created_at.desc()).limit(limit)
    results = [_row_to_dict(r) for r in q.all()]
    if len(results) >= limit:
        return results

    existing_ids = [r["id"] for r in results] + [exclude_id]
    needed = limit - len(results)
    fallback_q = _get_products_query(minimal=True).filter(Product.is_active == 1, Product.id.notin_(existing_ids)).order_by(Product.created_at.desc()).limit(needed)
    fallback = [_row_to_dict(r) for r in fallback_q.all()]
    return results + fallback

@ttl_cache(ttl_seconds=120)
def get_categories():
    """Fetch all categories and calculate product counts, supporting parent inheritance."""
    # 1. Fetch all categories ordered by name
    cats = Category.query.order_by(Category.name.asc()).all()
    if not cats:
        return []

    # Create a parent name lookup map
    cat_map = {str(c.id): c for c in cats}
    
    # 2. Fetch active products' category IDs to compute counts
    products = db_sql.session.query(Product.category_id).filter(Product.is_active == 1).all()
    active_cat_ids = [str(p.category_id) for p in products if p.category_id]

    # 3. Compute direct and subcategory-inherited product counts
    results = []
    for c in cats:
        cid = str(c.id)
        # Find all direct child category IDs
        child_ids = [str(sub.id) for sub in cats if str(sub.parent_id) == cid]
        
        # Count active products directly in this category or in its subcategories
        direct_count = active_cat_ids.count(cid)
        child_count = sum(active_cat_ids.count(sub_id) for sub_id in child_ids)
        total_count = direct_count + child_count
        
        parent_name = None
        if c.parent_id:
            parent = cat_map.get(str(c.parent_id))
            if parent:
                parent_name = parent.name

        results.append({
            "id":            cid,
            "name":          c.name,
            "slug":          c.slug,
            "parent_id":     str(c.parent_id) if c.parent_id else None,
            "parent_name":   parent_name,
            "img":           c.image_url,
            "product_count": total_count
        })
        
    return results

@ttl_cache(ttl_seconds=120)
def get_brands():
    rows = (db_sql.session.query(
                Brand.id, Brand.name, Brand.slug,
                func.count(Product.id).label("product_count")
            )
            .outerjoin(Product, and_(Product.brand_id == Brand.id, Product.is_active == 1))
            .group_by(Brand.id, Brand.name, Brand.slug)
            .order_by(Brand.name.asc())
            .all())
    return [_row_to_dict(r) for r in rows]

@ttl_cache(ttl_seconds=120)
def get_admin_stats():
    """All dashboard stats using standard SQLAlchemy queries."""
    total_products  = Product.query.filter_by(is_active=1).count()
    total_orders    = Order.query.count()
    total_revenue   = db_sql.session.query(func.coalesce(func.sum(Order.total_amount), 0)).filter(Order.status != 'cancelled').scalar()
    total_customers = User.query.filter_by(role='customer').count()
    pending_orders  = Order.query.filter_by(status='pending').count()
    low_stock       = Product.query.filter(Product.stock_quantity <= 5, Product.is_active == 1).count()
    
    return {
        "total_products":  total_products,
        "total_orders":    total_orders,
        "total_revenue":   float(total_revenue or 0),
        "total_customers": total_customers,
        "pending_orders":  pending_orders,
        "low_stock":       low_stock
    }
