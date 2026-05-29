import math
import datetime as _dt
import uuid
from sqlalchemy import or_, and_, func, desc, case
from sqlalchemy.orm import aliased
from extensions import db_sql
from helpers import ttl_cache
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
    where EVERY variation of a variable product becomes its own listing card.
    Each card has its own name, image, price, stock, SKU, and description.
    """
    variable_products = Product.query.filter_by(is_active=1, type="variable").all()
    if not variable_products:
        return {}

    product_ids = [str(p.id) for p in variable_products]
    product_names = {str(p.id): p.name for p in variable_products}

    # Subquery for var_image
    var_image_sub = (db_sql.session.query(Media.file_url)
                     .join(VariationImage, VariationImage.media_id == Media.id)
                     .filter(VariationImage.variation_id == ProductVariation.id, VariationImage.is_primary == 1)
                     .limit(1)
                     .scalar_subquery())
                     
    # Subquery for product_image
    product_image_sub = (db_sql.session.query(Media.file_url)
                         .join(ProductImage, ProductImage.media_id == Media.id)
                         .filter(ProductImage.product_id == ProductVariation.product_id, ProductImage.is_primary == 1)
                         .limit(1)
                         .scalar_subquery())

    # Query variations and concatenate attribute values (grouped by variation id)
    rows = (db_sql.session.query(
                ProductVariation.product_id,
                ProductVariation.id.label("var_id"),
                ProductVariation.sku,
                ProductVariation.price,
                ProductVariation.sale_price,
                ProductVariation.stock_quantity,
                ProductVariation.stock_status,
                ProductVariation.name.label("var_name"),
                ProductVariation.description.label("var_desc"),
                ProductVariation.short_description.label("var_short_desc"),
                func.string_agg(AttributeValue.value, ', ').label("label"),
                var_image_sub.label("var_image"),
                product_image_sub.label("product_image")
            )
            .outerjoin(VariationAttributeValue, VariationAttributeValue.variation_id == ProductVariation.id)
            .outerjoin(AttributeValue, AttributeValue.id == VariationAttributeValue.attribute_value_id)
            .filter(ProductVariation.product_id.in_(product_ids))
            .group_by(ProductVariation.id, ProductVariation.product_id, ProductVariation.sku, 
                      ProductVariation.price, ProductVariation.sale_price, ProductVariation.stock_quantity,
                      ProductVariation.stock_status, ProductVariation.name, ProductVariation.description,
                      ProductVariation.short_description)
            .order_by(ProductVariation.product_id, ProductVariation.price)
            .all())

    result = {}
    for r in rows:
        pid = str(r.product_id)
        if pid not in result:
            result[pid] = []

        label = r.label or ""
        base_name = product_names.get(pid, "")

        result[pid].append({
            "var_id":         r.var_id,
            "sku":            r.sku,
            "price":          float(r.sale_price or r.price or 0),
            "stock_quantity": int(r.stock_quantity or 0),
            "stock_status":   r.stock_status or "in_stock",
            "name_override":  r.var_name or (f"{base_name} – {label}" if label else base_name),
            "image_url":      r.var_image or r.product_image or "",
            "description":    r.var_desc or "",
            "short_description": r.var_short_desc or "",
            "label":          label,
            "_preselect_label": label
        })

    return result

def _expand_product_list(products):
    """Expand every variation into a separate listing card."""
    var_map = _get_variation_cards()
    expanded = []
    for p in (products or []):
        pid = str(p["id"])
        if pid in var_map:
            for r in var_map[pid]:
                row = dict(p)
                row["id"]             = pid
                row["name"]           = r["name_override"]
                row["price"]          = r["price"]
                row["sale_price"]     = None
                row["stock_quantity"] = r["stock_quantity"]
                row["stock_status"]   = r["stock_status"]
                row["sku"]            = r["sku"]
                row["image_url"]      = r["image_url"] or p.get("image_url") or ""
                row["description"]    = r.get("description") or row.get("description") or ""
                row["short_description"] = r.get("short_description") or row.get("short_description") or ""
                row["_preselect_label"] = r.get("label", "")
                expanded.append(row)
        else:
            expanded.append(p)
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
            if preselect_match and str(v["id"]) == str(preselect_match["id"]):
                pass
            else:
                v["price"]          = base_price
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
    child_cat = aliased(Category)
    sub_count = (db_sql.session.query(func.count(Product.id))
                 .filter(Product.is_active == 1)
                 .filter(
                     or_(
                         Product.category_id == Category.id,
                         Product.category_id.in_(
                             db_sql.session.query(child_cat.id).filter(child_cat.parent_id == Category.id).scalar_subquery()
                         )
                     )
                 )
                 .correlate(Category)
                 .scalar_subquery())
                 
    parent_alias = aliased(Category)
    rows = (db_sql.session.query(
                Category.id, Category.name, Category.slug, Category.parent_id,
                parent_alias.name.label("parent_name"), Category.image_url.label("img"),
                sub_count.label("product_count")
            )
            .outerjoin(parent_alias, parent_alias.id == Category.parent_id)
            .order_by(Category.name.asc())
            .all())
            
    return [_row_to_dict(r) for r in rows]

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
