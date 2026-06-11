import csv
import io
import uuid
import itertools
from functools import wraps
from flask import render_template, request, redirect, url_for, flash, abort, session, jsonify
from datetime import datetime, timedelta
from sqlalchemy import func, desc, or_, and_

from extensions import db_sql
from helpers import slugify, get_cached_store_settings, get_unique_slug, handle_upload
from queries import get_products, get_categories, get_brands, get_admin_stats, get_featured_categories

from models import (
    Product, Category, Brand, Attribute, AttributeValue, Media, ProductImage,
    ProductVariation, VariationAttributeValue, ProductAttribute, ProductAttributeValue,
    VariationImage, Order, OrderItem, Coupon, CouponUsage, BlogPost, StoreSetting,
    NewsletterSubscriber, ProductReview, User, ContactMessage
)


def _sanitize_sku_prefix(prefix, fallback):
    cleaned = "".join(ch for ch in (prefix or "").upper() if ch.isalnum() or ch in ("-", "_"))
    cleaned = cleaned.strip("-_")
    return cleaned or fallback


def generate_unique_product_sku(name=None):
    base = _sanitize_sku_prefix(slugify(name or ""), "PRD")
    for _ in range(8):
        candidate = f"{base}-{uuid.uuid4().hex[:8].upper()}"
        if not Product.query.filter_by(sku=candidate).first():
            return candidate
    return f"{base}-{uuid.uuid4().hex[:12].upper()}"


def generate_unique_variation_sku(base_sku=None, exclude_id=None):
    base = _sanitize_sku_prefix(base_sku, "VAR")
    for _ in range(8):
        candidate = f"{base}-{uuid.uuid4().hex[:6].upper()}"
        q = ProductVariation.query.filter_by(sku=candidate)
        if exclude_id:
            q = q.filter(ProductVariation.id != exclude_id)
        if not q.first():
            return candidate
    return f"{base}-{uuid.uuid4().hex[:10].upper()}"


def generate_variations(product_id):
    """
    Generate real variation rows for the cartesian product of primary + secondary
    attribute values. Optional attributes are excluded because they don't change
    price/stock/SKU — they're just toggles on the product page.
    """
    # 1. Find primary + secondary attributes assigned to this product
    attr_rows = (db_sql.session.query(ProductAttribute.attribute_id, Attribute.variation_type)
                 .join(Attribute, Attribute.id == ProductAttribute.attribute_id)
                 .filter(ProductAttribute.product_id == product_id)
                 .filter(Attribute.variation_type.in_(["primary", "secondary"]))
                 .order_by(Attribute.display_order)
                 .all())

    if not attr_rows:
        return

    # 2. Fetch values for each attribute
    value_groups = []
    for attr in attr_rows:
        vals = (db_sql.session.query(AttributeValue.id, AttributeValue.value)
                .join(ProductAttributeValue, ProductAttributeValue.attribute_value_id == AttributeValue.id)
                .filter(ProductAttributeValue.product_id == product_id)
                .filter(AttributeValue.attribute_id == attr.attribute_id)
                .order_by(AttributeValue.value)
                .all())
        if vals:
            value_groups.append([(attr.attribute_id, v.id, v.value) for v in vals])

    if not value_groups:
        return

    # 3. Get base product data
    product = db_sql.session.get(Product, product_id)
    if not product:
        return

    base_price = float(product.sale_price or product.price or 0)
    base_stock = int(product.stock_quantity or 0)
    base_sku   = product.sku or "VAR"

    # 4. Delete existing variations and their attribute links
    try:
        var_ids = [v.id for v in ProductVariation.query.filter_by(product_id=product_id).all()]
        if var_ids:
            VariationImage.query.filter(VariationImage.variation_id.in_(var_ids)).delete(synchronize_session=False)
            VariationAttributeValue.query.filter(VariationAttributeValue.variation_id.in_(var_ids)).delete(synchronize_session=False)
            ProductVariation.query.filter(ProductVariation.id.in_(var_ids)).delete(synchronize_session=False)

        # 5. Batch-insert all variations + attribute-value links
        created = 0
        for combo in itertools.product(*value_groups):
            var_id  = str(uuid.uuid4())
            var_sku = generate_unique_variation_sku(base_sku)

            new_var = ProductVariation(
                id=var_id,
                product_id=product_id,
                sku=var_sku,
                price=base_price,
                sale_price=product.sale_price,
                stock_quantity=base_stock
            )
            db_sql.session.add(new_var)

            for attr_id, val_id, _ in combo:
                link = VariationAttributeValue(
                    id=str(uuid.uuid4()),
                    variation_id=var_id,
                    attribute_value_id=val_id
                )
                db_sql.session.add(link)
            created += 1

        db_sql.session.commit()
    except Exception as e:
        db_sql.session.rollback()
        raise e

    print(f"DEBUG: Generated {created} variations for product {product_id}")


def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = session.get("user")
        if not user:
            flash("Please log in to continue.", "error")
            return redirect(url_for("auth.login", next=request.url))
        if user.get("role") not in ("admin", "manager"):
            flash("You do not have permission to access this page.", "error")
            return redirect(url_for("public.index"))
        return f(*args, **kwargs)
    return decorated


def register(app):

    # ── Dashboard ──────────────────────────────────────────────────────────────

    @app.route("/admin/")
    @app.route("/admin")
    @require_admin
    def admin_dashboard():
        _empty_stats = {
            "total_products": 0, "total_orders": 0, "total_revenue": 0.0,
            "total_customers": 0, "pending_orders": 0, "low_stock": 0,
        }
        try:
            stats = get_admin_stats()
        except Exception as e:
            stats = _empty_stats
            flash(f"Stats error: {e}", "error")
        # Ensure all keys exist even if get_admin_stats returns a partial dict
        for k, v in _empty_stats.items():
            stats.setdefault(k, v)

        try:
            recent_orders_rows = (db_sql.session.query(
                Order.id, Order.created_at, Order.total_amount, Order.status,
                User.first_name, User.last_name, User.email
            ).outerjoin(User, User.id == Order.user_id)
             .order_by(Order.created_at.desc())
             .limit(10).all())
            recent_orders = []
            for r in recent_orders_rows:
                recent_orders.append({
                    "id": r.id,
                    "created_at": r.created_at,
                    "total_amount": r.total_amount,
                    "status": r.status,
                    "customer_name": f"{r.first_name or ''} {r.last_name or ''}".strip() or "Guest",
                    "customer_email": r.email
                })
        except Exception:
            recent_orders = []

        try:
            primary_img_sub = (db_sql.session.query(Media.file_url)
                               .join(ProductImage, ProductImage.media_id == Media.id)
                               .filter(ProductImage.product_id == Product.id, ProductImage.is_primary == 1)
                               .limit(1)
                               .scalar_subquery())
            recent_prod_rows = (db_sql.session.query(
                Product.id, Product.name, Product.sku, Product.price, Product.sale_price,
                Product.stock_quantity, Product.is_active, Product.created_at,
                Category.name.label("category_name"),
                primary_img_sub.label("image_url")
            ).outerjoin(Category, Category.id == Product.category_id)
             .filter(Product.is_active == 1)
             .order_by(Product.created_at.desc())
             .limit(8).all())
            recent_products = [dict(r._mapping) for r in recent_prod_rows]
        except Exception:
            recent_products = []

        try:
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            orders = (db_sql.session.query(Order.created_at, Order.total_amount)
                      .filter(Order.created_at >= seven_days_ago)
                      .filter(Order.status != 'cancelled')
                      .all())
            
            from collections import defaultdict
            grouped = defaultdict(float)
            
            today = datetime.utcnow()
            days = [(today - timedelta(days=i)) for i in range(7)]
            days.reverse()
            day_labels = [d.strftime('%d %b') for d in days]
            
            for d_label in day_labels:
                grouped[d_label] = 0.0
                
            for o_created, o_amount in orders:
                if o_created:
                    d_label = o_created.strftime('%d %b')
                    if d_label in grouped:
                        grouped[d_label] += float(o_amount or 0)
            
            chart_data = {
                "labels": day_labels,
                "values": [grouped[lbl] for lbl in day_labels]
            }
        except Exception:
            chart_data = {"labels": [], "values": []}

        return render_template(
            "admin/dashboard.html",
            stats=stats, recent_orders=recent_orders,
            recent_products=recent_products, chart_data=chart_data,
        )

    # ── Products ───────────────────────────────────────────────────────────────

    @app.route("/admin/products")
    @require_admin
    def admin_products():
        search   = request.args.get("search", "").strip()
        category = request.args.get("category", "").strip()
        brand    = request.args.get("brand", "").strip()
        page     = max(1, int(request.args.get("page", 1)))
        try:
            products, total, total_pages = get_products(
                search=search, category=category, brand=brand, page=page, per_page=20, skip_expand=True
            )
            categories = get_categories()
            brands     = get_brands()
        except Exception as e:
            products, total, total_pages = [], 0, 1
            categories = brands = []
            flash(f"Error: {e}", "error")
        return render_template(
            "admin/products.html",
            products=products, total=total, total_pages=total_pages, page=page,
            categories=categories, brands=brands,
            search=search, selected_category=category, selected_brand=brand,
        )

    @app.route("/admin/products/new", methods=["GET", "POST"])
    @require_admin
    def admin_product_new():
        categories     = get_categories()
        brands         = get_brands()
        
        attrs = Attribute.query.order_by(Attribute.name.asc()).all()
        all_attributes = []
        for a in attrs:
            options = AttributeValue.query.filter_by(attribute_id=a.id).order_by(AttributeValue.value.asc()).all()
            all_attributes.append({
                "id": a.id,
                "name": a.name,
                "slug": a.slug,
                "variation_type": a.variation_type,
                "options": [{
                    "id": o.id,
                    "attribute_id": o.attribute_id,
                    "value": o.value,
                    "image_url": o.image_url
                } for o in options]
            })
        
        if request.method == "POST":
            f = request.form
            name = (f.get("name") or "").strip()
            if not name:
                flash("Product name is required.", "error")
                return render_template("admin/product_form.html", product=None, categories=categories,
                                       brands=brands, all_attributes=all_attributes, action="new")
            try:
                stock_qty = int(f.get("stock_quantity") or 0)
                stock_status = f.get("stock_status", "in_stock")
                slug = get_unique_slug("products", f.get("slug") or slugify(name))
                sku_input = f.get("sku", "").strip()
                sku = sku_input or generate_unique_product_sku(name)

                # Create Product
                product = Product(
                    id=str(uuid.uuid4()),
                    name=name,
                    slug=slug,
                    sku=sku,
                    type=f.get("type", "simple"),
                    description=f.get("description"),
                    short_description=f.get("short_description"),
                    price=float(f.get("price") or 0),
                    sale_price=float(f.get("sale_price") or 0) or None,
                    stock_quantity=stock_qty,
                    stock_status=stock_status,
                    category_id=f.get("category_id") or None,
                    brand_id=f.get("brand_id") or None,
                    is_featured=1 if f.get("is_featured") == "on" else 0,
                    is_active=1 if f.get("is_active", "on") == "on" else 0
                )
                db_sql.session.add(product)

                # Handle Primary Image
                primary_file = request.files.get("primary_image")
                if primary_file and primary_file.filename:
                    url = handle_upload(primary_file)
                    mid = str(uuid.uuid4())
                    media = Media(id=mid, file_url=url)
                    db_sql.session.add(media)
                    pimg = ProductImage(id=str(uuid.uuid4()), product_id=product.id, media_id=mid, is_primary=1, display_order=0)
                    db_sql.session.add(pimg)

                # Handle Gallery Images
                gallery_files = request.files.getlist("gallery_images")
                for i, gfile in enumerate(gallery_files):
                    if gfile and gfile.filename:
                        url = handle_upload(gfile)
                        mid = str(uuid.uuid4())
                        media = Media(id=mid, file_url=url)
                        db_sql.session.add(media)
                        pimg = ProductImage(id=str(uuid.uuid4()), product_id=product.id, media_id=mid, is_primary=0, display_order=i+1)
                        db_sql.session.add(pimg)

                # Save Attributes
                attr_ids = request.form.getlist("attribute_ids")
                for attr_id in attr_ids:
                    p_attr = ProductAttribute(id=str(uuid.uuid4()), product_id=product.id, attribute_id=attr_id)
                    db_sql.session.add(p_attr)

                # Save Attribute Values
                val_ids = request.form.getlist("attribute_value_ids")
                for val_id in val_ids:
                    p_val = ProductAttributeValue(id=str(uuid.uuid4()), product_id=product.id, attribute_value_id=val_id)
                    db_sql.session.add(p_val)

                # Generate variations if needed
                if f.get("type") == "variable":
                    db_sql.session.commit()
                    generate_variations(product.id)
                else:
                    db_sql.session.commit()

                getattr(get_products, "cache_clear")()
                flash("Product created successfully.", "success")
                return redirect(url_for("admin_products"))
            except Exception as e:
                db_sql.session.rollback()
                flash(f"Error creating product: {e}", "error")

        return render_template("admin/product_form.html", product=None, categories=categories, brands=brands, all_attributes=all_attributes, action="new")

    @app.route("/admin/products/<product_id>/edit", methods=["GET", "POST"])
    @require_admin
    def admin_product_edit(product_id):
        product = db_sql.session.get(Product, product_id)
        if not product:
            abort(404)
        
        categories = get_categories()
        brands = get_brands()
        
        attrs = Attribute.query.order_by(Attribute.name.asc()).all()
        all_attributes = []
        for a in attrs:
            options = AttributeValue.query.filter_by(attribute_id=a.id).order_by(AttributeValue.value.asc()).all()
            all_attributes.append({
                "id": a.id,
                "name": a.name,
                "slug": a.slug,
                "variation_type": a.variation_type,
                "options": [{
                    "id": o.id,
                    "attribute_id": o.attribute_id,
                    "value": o.value,
                    "image_url": o.image_url
                } for o in options]
            })
        
        if request.method == "POST":
            f = request.form
            try:
                name = f.get("name")
                slug = get_unique_slug("products", f.get("slug") or slugify(name), exclude_id=product_id)
                sku_input = (f.get("sku") or "").strip()
                updated_sku = sku_input or product.sku or generate_unique_product_sku(name)

                # Update product properties
                old_type = product.type
                product.name = name
                product.slug = slug
                product.sku = updated_sku
                product.type = f.get("type")
                product.description = f.get("description")
                product.short_description = f.get("short_description")
                product.price = float(f.get("price") or 0)
                product.sale_price = float(f.get("sale_price") or 0) or None
                product.stock_quantity = int(f.get("stock_quantity") or 0)
                product.stock_status = f.get("stock_status")
                product.category_id = f.get("category_id") or None
                product.brand_id = f.get("brand_id") or None
                product.is_featured = 1 if f.get("is_featured") == "on" else 0
                product.is_active = 1 if f.get("is_active") == "on" else 0

                # Handle Primary Image
                primary_file = request.files.get("primary_image")
                if primary_file and primary_file.filename:
                    url = handle_upload(primary_file)
                    mid = str(uuid.uuid4())
                    media = Media(id=mid, file_url=url)
                    db_sql.session.add(media)
                    # Delete existing primary image link
                    ProductImage.query.filter_by(product_id=product_id, is_primary=1).delete()
                    pimg = ProductImage(id=str(uuid.uuid4()), product_id=product_id, media_id=mid, is_primary=1, display_order=0)
                    db_sql.session.add(pimg)

                # Handle New Gallery Images
                gallery_files = request.files.getlist("gallery_images")
                for gfile in gallery_files:
                    if gfile and gfile.filename:
                        url = handle_upload(gfile)
                        mid = str(uuid.uuid4())
                        media = Media(id=mid, file_url=url)
                        db_sql.session.add(media)
                        pimg = ProductImage(id=str(uuid.uuid4()), product_id=product_id, media_id=mid, is_primary=0)
                        db_sql.session.add(pimg)

                # Handle Deletions of Gallery Images
                for key in request.form:
                    if key.startswith("delete_image_"):
                        img_id = key.replace("delete_image_", "")
                        ProductImage.query.filter_by(id=img_id).delete()

                # Update attributes
                ProductAttribute.query.filter_by(product_id=product_id).delete()
                for aid in request.form.getlist("attribute_ids"):
                    p_attr = ProductAttribute(id=str(uuid.uuid4()), product_id=product_id, attribute_id=aid)
                    db_sql.session.add(p_attr)

                # Update attribute values
                ProductAttributeValue.query.filter_by(product_id=product_id).delete()
                for vid in request.form.getlist("attribute_value_ids"):
                    p_val = ProductAttributeValue(id=str(uuid.uuid4()), product_id=product_id, attribute_value_id=vid)
                    db_sql.session.add(p_val)

                # Clean up variations if type changed
                new_type = f.get("type")
                if old_type == "variable" and new_type != "variable":
                    var_ids = [v.id for v in ProductVariation.query.filter_by(product_id=product_id).all()]
                    if var_ids:
                        VariationImage.query.filter(VariationImage.variation_id.in_(var_ids)).delete(synchronize_session=False)
                        VariationAttributeValue.query.filter(VariationAttributeValue.variation_id.in_(var_ids)).delete(synchronize_session=False)
                        ProductVariation.query.filter(ProductVariation.id.in_(var_ids)).delete(synchronize_session=False)
                elif new_type == "variable" and old_type != "variable":
                    db_sql.session.commit()
                    generate_variations(product_id)
                else:
                    db_sql.session.commit()

                getattr(get_products, "cache_clear")()
                flash("Product updated successfully.", "success")
                return redirect(url_for("admin_products"))
            except Exception as e:
                db_sql.session.rollback()
                flash(f"Error: {e}", "error")

        # Fetch images for display
        pimg_rows = (db_sql.session.query(ProductImage.id, ProductImage.is_primary, Media.file_url.label("image_url"))
                     .join(Media, Media.id == ProductImage.media_id)
                     .filter(ProductImage.product_id == product_id)
                     .order_by(ProductImage.is_primary.desc(), ProductImage.display_order.asc())
                     .all())
        product_images = [dict(r._mapping) for r in pimg_rows]

        product_attribute_ids = [r.attribute_id for r in ProductAttribute.query.filter_by(product_id=product_id).all()]
        product_value_ids = [r.attribute_value_id for r in ProductAttributeValue.query.filter_by(product_id=product_id).all()]

        return render_template(
            "admin/product_form.html",
            product=product, product_images=product_images,
            categories=categories, brands=brands, all_attributes=all_attributes,
            product_attribute_ids=product_attribute_ids, product_value_ids=product_value_ids,
            action="edit"
        )

    @app.route("/admin/products/<product_id>/delete", methods=["POST"])
    @require_admin
    def admin_product_delete(product_id):
        product = db_sql.session.get(Product, product_id)
        if product:
            try:
                product.is_active = 0
                db_sql.session.commit()
                getattr(get_products, "cache_clear")()
                flash("Product deleted (deactivated).", "success")
            except Exception as e:
                db_sql.session.rollback()
                flash(f"Error: {e}", "error")
        else:
            flash("Product not found.", "error")
        return redirect(url_for("admin_products"))

    # ── Categories ─────────────────────────────────────────────────────────────

    @app.route("/admin/categories")
    @require_admin
    def admin_categories():
        try:
            categories = get_categories()
        except Exception as e:
            categories = []
            flash(f"Error: {e}", "error")
        return render_template("admin/categories.html", categories=categories)

    @app.route("/admin/categories/new", methods=["GET", "POST"])
    @require_admin
    def admin_category_new():
        if request.method == "POST":
            name = (request.form.get("name") or "").strip()
            if not name:
                flash("Category name is required.", "error")
                return render_template("admin/category_form.html", category=None, categories=get_categories())
            slug       = request.form.get("slug") or slugify(name)
            parent_id  = request.form.get("parent_id") or None
            is_featured = 1 if request.form.get("is_featured") == "on" else 0
            image_url = handle_upload(request.files.get("image_file")) or request.form.get("image_url") or None
            
            try:
                new_cat = Category(
                    id=str(uuid.uuid4()),
                    name=name,
                    slug=slug,
                    parent_id=parent_id,
                    image_url=image_url,
                    is_featured=is_featured
                )
                db_sql.session.add(new_cat)
                db_sql.session.commit()
                getattr(get_categories, "cache_clear")()
                getattr(get_featured_categories, "cache_clear")()
                flash("Category created", "success")
                return redirect(url_for("admin_categories"))
            except Exception as e:
                db_sql.session.rollback()
                flash(f"Error: {e}", "error")
        return render_template("admin/category_form.html", category=None, categories=get_categories())

    @app.route("/admin/categories/<cat_id>/edit", methods=["GET", "POST"])
    @require_admin
    def admin_category_edit(cat_id):
        category = db_sql.session.get(Category, cat_id)
        if not category:
            abort(404)
        if request.method == "POST":
            image_url = handle_upload(request.files.get("image_file")) or category.image_url
            try:
                category.name = request.form.get("name")
                category.slug = request.form.get("slug")
                category.parent_id = request.form.get("parent_id") or None
                category.image_url = image_url
                category.is_featured = 1 if request.form.get("is_featured") == "on" else 0
                db_sql.session.commit()
                getattr(get_categories, "cache_clear")()
                getattr(get_featured_categories, "cache_clear")()
                flash("Category updated", "success")
                return redirect(url_for("admin_categories"))
            except Exception as e:
                db_sql.session.rollback()
                flash(f"Error: {e}", "error")
        return render_template("admin/category_form.html", category=category, categories=get_categories())

    @app.route("/admin/categories/<cat_id>/delete", methods=["POST"])
    @require_admin
    def admin_category_delete(cat_id):
        category = db_sql.session.get(Category, cat_id)
        if category:
            try:
                Product.query.filter_by(category_id=cat_id).update({Product.category_id: None})
                Category.query.filter_by(parent_id=cat_id).update({Category.parent_id: None})
                
                db_sql.session.delete(category)
                db_sql.session.commit()
                getattr(get_categories, "cache_clear")()
                getattr(get_featured_categories, "cache_clear")()
                flash("Category deleted.", "success")
            except Exception as e:
                db_sql.session.rollback()
                flash(f"Error: {e}", "error")
        else:
            flash("Category not found.", "error")
        return redirect(url_for("admin_categories"))

    # ── Brands ─────────────────────────────────────────────────────────────────

    @app.route("/admin/brands")
    @require_admin
    def admin_brands():
        try:
            brand_rows = (db_sql.session.query(
                Brand.id, Brand.name, Brand.slug, Brand.image_url, Brand.is_active, Brand.created_at,
                func.count(Product.id).label("product_count")
            ).outerjoin(Product, Product.brand_id == Brand.id)
             .group_by(Brand.id, Brand.name, Brand.slug, Brand.image_url, Brand.is_active, Brand.created_at)
             .order_by(Brand.name.asc())
             .all())
            brands = [dict(r._mapping) for r in brand_rows]
        except Exception as e:
            brands = []
            flash(f"Error: {e}", "error")
        return render_template("admin/brands.html", brands=brands)

    @app.route("/admin/brands/new", methods=["GET", "POST"])
    @require_admin
    def admin_brand_new():
        if request.method == "POST":
            name = (request.form.get("name") or "").strip()
            if not name:
                flash("Brand name is required.", "error")
                return render_template("admin/brand_form.html", brand=None)
            slug = request.form.get("slug") or slugify(name)
            image_url = handle_upload(request.files.get("image_file")) or None
            try:
                new_brand = Brand(
                    id=str(uuid.uuid4()),
                    name=name,
                    slug=slug,
                    image_url=image_url
                )
                db_sql.session.add(new_brand)
                db_sql.session.commit()
                getattr(get_brands, "cache_clear")()
                flash("Brand created.", "success")
                return redirect(url_for("admin_brands"))
            except Exception as e:
                db_sql.session.rollback()
                flash(f"Error: {e}", "error")
        return render_template("admin/brand_form.html", brand=None)

    @app.route("/admin/brands/<brand_id>/edit", methods=["GET", "POST"])
    @require_admin
    def admin_brand_edit(brand_id):
        brand = db_sql.session.get(Brand, brand_id)
        if not brand:
            abort(404)
        if request.method == "POST":
            name = request.form.get("name")
            slug = request.form.get("slug") or slugify(name)
            image_url = handle_upload(request.files.get("image_file")) or brand.image_url
            try:
                brand.name = name
                brand.slug = slug
                brand.image_url = image_url
                db_sql.session.commit()
                getattr(get_brands, "cache_clear")()
                flash("Brand updated.", "success")
                return redirect(url_for("admin_brands"))
            except Exception as e:
                db_sql.session.rollback()
                flash(f"Error: {e}", "error")
        return render_template("admin/brand_form.html", brand=brand)

    @app.route("/admin/brands/<brand_id>/delete", methods=["POST"])
    @require_admin
    def admin_brand_delete(brand_id):
        brand = db_sql.session.get(Brand, brand_id)
        if brand:
            try:
                Product.query.filter_by(brand_id=brand_id).update({Product.brand_id: None})
                db_sql.session.delete(brand)
                db_sql.session.commit()
                getattr(get_brands, "cache_clear")()
                flash("Brand deleted.", "success")
            except Exception as e:
                db_sql.session.rollback()
                flash(f"Error: {e}", "error")
        else:
            flash("Brand not found.", "error")
        return redirect(url_for("admin_brands"))

    # ── Orders ─────────────────────────────────────────────────────────────────

    @app.route("/admin/orders")
    @require_admin
    def admin_orders():
        import math
        page     = max(1, int(request.args.get("page", 1)))
        per_page = 20
        offset   = (page - 1) * per_page
        try:
            order_rows = (db_sql.session.query(
                Order.id, Order.created_at, Order.total_amount, Order.status,
                User.first_name, User.last_name, User.email,
                func.count(OrderItem.id).label("item_count")
            ).outerjoin(User, User.id == Order.user_id)
             .outerjoin(OrderItem, OrderItem.order_id == Order.id)
             .group_by(Order.id, Order.created_at, Order.total_amount, Order.status, User.first_name, User.last_name, User.email)
             .order_by(Order.created_at.desc())
             .limit(per_page).offset(offset).all())
             
            orders = []
            for r in order_rows:
                orders.append({
                    "id": r.id,
                    "created_at": r.created_at,
                    "total_amount": r.total_amount,
                    "status": r.status,
                    "customer_name": f"{r.first_name or ''} {r.last_name or ''}".strip() or "Guest",
                    "customer_email": r.email,
                    "item_count": r.item_count
                })
            
            total = Order.query.count()
            total_pages = max(1, math.ceil(total / per_page))
        except Exception as e:
            orders, total, total_pages = [], 0, 1
            flash(f"Error: {e}", "error")
        return render_template(
            "admin/orders.html", orders=orders, total=total, total_pages=total_pages, page=page
        )

    @app.route("/admin/orders/<order_id>")
    @require_admin
    def admin_order_detail(order_id):
        try:
            order_row = (db_sql.session.query(
                Order.id, Order.user_id, Order.status, Order.total_amount, Order.payment_method,
                Order.payment_status, Order.order_number, Order.coupon_code, Order.discount_amount,
                Order.subtotal, Order.shipping_amount, Order.shipping_address_json, Order.customer_name,
                Order.customer_email, Order.customer_phone, Order.notes, Order.cancelled_at,
                Order.cancel_reason, Order.created_at, Order.updated_at,
                User.first_name, User.last_name, User.email
            ).outerjoin(User, User.id == Order.user_id)
             .filter(Order.id == order_id).first())
             
            if not order_row:
                abort(404)
                
            order = dict(order_row._mapping)
            order["customer_name"] = order.get("customer_name") or f"{order_row.first_name or ''} {order_row.last_name or ''}".strip() or "Guest"
            order["customer_email"] = order.get("customer_email") or order_row.email

            item_rows = (db_sql.session.query(
                OrderItem.id, OrderItem.order_id, OrderItem.product_id, OrderItem.variation_id,
                OrderItem.quantity, OrderItem.unit_price, OrderItem.total_price, OrderItem.product_name_snapshot,
                OrderItem.created_at, Product.name.label("product_name"), Product.sku
            ).outerjoin(Product, Product.id == OrderItem.product_id)
             .filter(OrderItem.order_id == order_id).all())
            items = [dict(r._mapping) for r in item_rows]
        except Exception as e:
            flash(f"Error: {e}", "error")
            return redirect(url_for("admin_orders"))
        return render_template("admin/order_detail.html", order=order, items=items)

    @app.route("/admin/orders/<order_id>/status", methods=["POST"])
    @require_admin
    def admin_order_status(order_id):
        status = request.form.get("status")
        valid  = ("pending", "processing", "shipped", "delivered", "cancelled", "refunded")
        if status not in valid:
            flash("Invalid status.", "error")
            return redirect(url_for("admin_order_detail", order_id=order_id))
        order = db_sql.session.get(Order, order_id)
        if order:
            try:
                order.status = status
                order.updated_at = datetime.utcnow()
                db_sql.session.commit()
                flash(f"Order status updated to '{status}'.", "success")
            except Exception as e:
                db_sql.session.rollback()
                flash(f"Error: {e}", "error")
        else:
            flash("Order not found.", "error")
        return redirect(url_for("admin_order_detail", order_id=order_id))

    # ── Customers ──────────────────────────────────────────────────────────────

    @app.route("/admin/customers")
    @require_admin
    def admin_customers():
        try:
            customers = User.query.filter_by(role='customer').order_by(User.created_at.desc()).all()
        except Exception as e:
            customers = []
            flash(f"Error: {e}", "error")
        return render_template("admin/customers.html", customers=customers)

    @app.route("/admin/subscribers")
    @require_admin
    def admin_subscribers():
        try:
            subscribers = NewsletterSubscriber.query.order_by(NewsletterSubscriber.subscribed_at.desc()).all()
        except Exception as e:
            subscribers = []
            flash(f"Error loading subscribers: {e}", "error")
        return render_template("admin/subscribers.html", subscribers=subscribers)

    # ── Attributes ─────────────────────────────────────────────────────────────

    @app.route("/admin/attributes")
    @require_admin
    def admin_attributes():
        try:
            attr_rows = (db_sql.session.query(
                Attribute.id, Attribute.name, Attribute.slug, Attribute.variation_type,
                func.count(AttributeValue.id).label("value_count")
            ).outerjoin(AttributeValue, AttributeValue.attribute_id == Attribute.id)
             .group_by(Attribute.id, Attribute.name, Attribute.slug, Attribute.variation_type)
             .order_by(Attribute.name.asc())
             .all())
            attributes = [dict(r._mapping) for r in attr_rows]
        except Exception as e:
            attributes = []
            flash(f"Error: {e}", "error")
        return render_template("admin/attributes.html", attributes=attributes)

    @app.route("/admin/attributes/new", methods=["GET", "POST"])
    @require_admin
    def admin_attribute_new():
        if request.method == "POST":
            name       = request.form.get("name")
            slug       = request.form.get("slug") or slugify(name)
            var_type   = request.form.get("variation_type", "secondary")
            
            if not name:
                flash("Name is required", "error")
            else:
                try:
                    new_attr = Attribute(
                        id=str(uuid.uuid4()),
                        name=name,
                        slug=slug,
                        variation_type=var_type
                    )
                    db_sql.session.add(new_attr)
                    db_sql.session.commit()
                    flash("Attribute created", "success")
                    return redirect(url_for("admin_attributes"))
                except Exception as e:
                    db_sql.session.rollback()
                    flash(f"Error: {e}", "error")
        return render_template("admin/attribute_form.html", attribute=None)

    @app.route("/admin/attributes/<attr_id>/edit", methods=["GET", "POST"])
    @require_admin
    def admin_attribute_edit(attr_id):
        attribute = db_sql.session.get(Attribute, attr_id)
        if not attribute:
            abort(404)
        if request.method == "POST":
            var_type  = request.form.get("variation_type", "secondary")
            try:
                attribute.name = request.form.get("name")
                attribute.slug = request.form.get("slug")
                attribute.variation_type = var_type
                db_sql.session.commit()
                flash("Attribute updated", "success")
                return redirect(url_for("admin_attributes"))
            except Exception as e:
                db_sql.session.rollback()
                flash(f"Error: {e}", "error")
        return render_template("admin/attribute_form.html", attribute=attribute)

    @app.route("/admin/attributes/<attr_id>/delete", methods=["POST"])
    @require_admin
    def admin_attribute_delete(attr_id):
        attribute = db_sql.session.get(Attribute, attr_id)
        if attribute:
            try:
                ProductAttribute.query.filter_by(attribute_id=attr_id).delete()
                vals = AttributeValue.query.filter_by(attribute_id=attr_id).all()
                for val in vals:
                    ProductAttributeValue.query.filter_by(attribute_value_id=val.id).delete()
                    VariationAttributeValue.query.filter_by(attribute_value_id=val.id).delete()
                    db_sql.session.delete(val)
                db_sql.session.delete(attribute)
                db_sql.session.commit()
                flash("Attribute deleted", "success")
            except Exception as e:
                db_sql.session.rollback()
                flash(f"Error: {e}", "error")
        else:
            flash("Attribute not found.", "error")
        return redirect(url_for("admin_attributes"))

    @app.route("/admin/attributes/<attr_id>/values", methods=["GET", "POST"])
    @require_admin
    def admin_attribute_values(attr_id):
        attribute = db_sql.session.get(Attribute, attr_id)
        if not attribute:
            flash("Attribute not found", "error")
            return redirect(url_for("admin_attributes"))
        if request.method == "POST":
            value     = request.form.get("value")
            image_url = handle_upload(request.files.get("image_file")) or None
            if value:
                try:
                    new_val = AttributeValue(
                        id=str(uuid.uuid4()),
                        attribute_id=attr_id,
                        value=value,
                        image_url=image_url
                    )
                    db_sql.session.add(new_val)
                    db_sql.session.commit()
                    flash("Value added", "success")
                except Exception as e:
                    db_sql.session.rollback()
                    flash(f"Error: {e}", "error")
        values = AttributeValue.query.filter_by(attribute_id=attr_id).order_by(AttributeValue.value.asc()).all()
        return render_template("admin/attribute_values.html", attribute=attribute, values=values)

    @app.route("/admin/attributes/<attr_id>/values/bulk_update", methods=["POST"])
    @require_admin
    def admin_attribute_values_bulk_update(attr_id):
        f = request.form
        try:
            values = AttributeValue.query.filter_by(attribute_id=attr_id).all()
            for v in values:
                new_value = (f.get(f"value_{v.id}") or "").strip()
                if new_value:
                    v.value = new_value
            db_sql.session.commit()
            flash("Attribute values updated.", "success")
        except Exception as e:
            db_sql.session.rollback()
            flash(f"Error updating values: {e}", "error")
        return redirect(url_for("admin_attribute_values", attr_id=attr_id))

    @app.route("/admin/attributes/values/<val_id>/delete", methods=["POST"])
    @require_admin
    def admin_attribute_value_delete(val_id):
        attr_id = request.form.get("attribute_id")
        value = db_sql.session.get(AttributeValue, val_id)
        if value:
            try:
                ProductAttributeValue.query.filter_by(attribute_value_id=val_id).delete()
                VariationAttributeValue.query.filter_by(attribute_value_id=val_id).delete()
                db_sql.session.delete(value)
                db_sql.session.commit()
                getattr(get_products, "cache_clear")()
                flash("Value deleted", "success")
            except Exception as e:
                db_sql.session.rollback()
                flash(f"Error: {e}", "error")
        else:
            flash("Value not found.", "error")
        return redirect(url_for("admin_attribute_values", attr_id=attr_id))

    @app.route("/admin/attributes/values/<val_id>/edit", methods=["GET", "POST"])
    @require_admin
    def admin_attribute_value_edit(val_id):
        value = db_sql.session.get(AttributeValue, val_id)
        if not value:
            abort(404)
        attribute = db_sql.session.get(Attribute, value.attribute_id)
        if request.method == "POST":
            new_value = request.form.get("value")
            image_url = handle_upload(request.files.get("image_file")) or value.image_url
            try:
                value.value = new_value
                value.image_url = image_url
                db_sql.session.commit()
                flash("Value updated", "success")
                return redirect(url_for("admin_attribute_values", attr_id=value.attribute_id))
            except Exception as e:
                db_sql.session.rollback()
                flash(f"Error: {e}", "error")
        return render_template("admin/attribute_value_form.html", attribute=attribute, value=value)

    # ── Variations ─────────────────────────────────────────────────────────────

    @app.route("/admin/products/<product_id>/variations")
    @require_admin
    def admin_product_variations(product_id):
        product = db_sql.session.get(Product, product_id)
        if not product:
            abort(404)
            
        var_list = ProductVariation.query.filter_by(product_id=product_id).order_by(ProductVariation.sku.asc()).all()
        
        variations = []
        for v in var_list:
            opts = (db_sql.session.query(AttributeValue.value)
                    .join(VariationAttributeValue, VariationAttributeValue.attribute_value_id == AttributeValue.id)
                    .filter(VariationAttributeValue.variation_id == v.id)
                    .all())
            option_names = " / ".join(o.value for o in opts)
            
            variations.append({
                "id": v.id,
                "product_id": v.product_id,
                "sku": v.sku,
                "price": v.price,
                "sale_price": v.sale_price,
                "stock_quantity": v.stock_quantity,
                "stock_status": v.stock_status,
                "name": v.name,
                "short_description": v.short_description,
                "description": v.description,
                "option_names": option_names
            })

        linked_attr_rows = (db_sql.session.query(Attribute.id, Attribute.name)
                            .join(ProductAttribute, ProductAttribute.attribute_id == Attribute.id)
                            .filter(ProductAttribute.product_id == product_id)
                            .order_by(ProductAttribute.display_order.asc())
                            .all())
        linked_attributes = []
        for r in linked_attr_rows:
            options = (db_sql.session.query(AttributeValue.id, AttributeValue.value, AttributeValue.image_url)
                       .join(ProductAttributeValue, ProductAttributeValue.attribute_value_id == AttributeValue.id)
                       .filter(AttributeValue.attribute_id == r.id, ProductAttributeValue.product_id == product_id)
                       .order_by(AttributeValue.value.asc())
                       .all())
            if not options:
                options = AttributeValue.query.filter_by(attribute_id=r.id).order_by(AttributeValue.value.asc()).all()
                
            linked_attributes.append({
                "id": r.id,
                "name": r.name,
                "options": [dict(o._mapping) if hasattr(o, "_mapping") else {
                    "id": o.id,
                    "value": o.value,
                    "image_url": o.image_url
                } for o in options]
            })

        var_ids = [v["id"] for v in variations]
        variation_images = {}
        if var_ids:
            img_rows = (db_sql.session.query(VariationImage.variation_id, VariationImage.is_primary, Media.file_url)
                        .join(Media, Media.id == VariationImage.media_id)
                        .filter(VariationImage.variation_id.in_(var_ids))
                        .order_by(VariationImage.is_primary.desc(), VariationImage.display_order.asc())
                        .all())
            for r in img_rows:
                vid = str(r.variation_id)
                variation_images.setdefault(vid, []).append(dict(r._mapping))
                
        return render_template(
            "admin/variations.html", product=product, variations=variations,
            attributes=linked_attributes, variation_images=variation_images,
        )

    @app.route("/admin/products/<product_id>/variations/new", methods=["POST"])
    @require_admin
    def admin_variation_new(product_id):
        f = request.form
        product = db_sql.session.get(Product, product_id)
        if not product:
            abort(404)
        try:
            variation_sku = (f.get("sku") or "").strip() or generate_unique_variation_sku(product.sku)
            var_id = str(uuid.uuid4())
            new_var = ProductVariation(
                id=var_id,
                product_id=product_id,
                sku=variation_sku,
                price=float(product.sale_price or product.price or 0),
                sale_price=None,
                stock_quantity=int(product.stock_quantity or 0)
            )
            db_sql.session.add(new_var)
            
            for key, val_id in f.items():
                if key.startswith("attr_") and val_id:
                    link = VariationAttributeValue(
                        id=str(uuid.uuid4()),
                        variation_id=var_id,
                        attribute_value_id=val_id
                    )
                    db_sql.session.add(link)
            db_sql.session.commit()
            flash("Variation created", "success")
        except Exception as e:
            db_sql.session.rollback()
            flash(f"Error: {e}", "error")
        return redirect(url_for("admin_product_variations", product_id=product_id))

    @app.route("/admin/variations/<var_id>/delete", methods=["POST"])
    @require_admin
    def admin_variation_delete(var_id):
        product_id = request.form.get("product_id")
        variation = db_sql.session.get(ProductVariation, var_id)
        if variation:
            try:
                VariationImage.query.filter_by(variation_id=var_id).delete()
                VariationAttributeValue.query.filter_by(variation_id=var_id).delete()
                OrderItem.query.filter_by(variation_id=var_id).delete()
                
                db_sql.session.delete(variation)
                db_sql.session.commit()
                getattr(get_products, "cache_clear")()
                flash("Variation deleted", "success")
            except Exception as e:
                db_sql.session.rollback()
                flash(f"Error: {e}", "error")
        else:
            flash("Variation not found.", "error")
        return redirect(url_for("admin_product_variations", product_id=product_id))

    @app.route("/admin/products/<product_id>/variations/bulk_update", methods=["POST"])
    @require_admin
    def admin_variations_bulk_update(product_id):
        try:
            var_list = ProductVariation.query.filter_by(product_id=product_id).all()
            for v in var_list:
                sku     = (request.form.get(f"sku_{v.id}") or "").strip()
                price   = request.form.get(f"price_{v.id}", "").strip()
                stock   = request.form.get(f"stock_{v.id}", "").strip()
                var_name = (request.form.get(f"name_{v.id}") or "").strip()
                short_desc = (request.form.get(f"short_desc_{v.id}") or "").strip()
                desc    = (request.form.get(f"description_{v.id}") or "").strip()

                try:
                    p = float(price) if price else 0
                except (ValueError, TypeError):
                    p = 0
                try:
                    s = int(stock) if stock else 0
                except (ValueError, TypeError):
                    s = 0

                v.sku = sku or f"VAR-{v.id[:8].upper()}"
                v.price = p
                v.stock_quantity = s
                v.stock_status = "out_of_stock" if (s <= 0) else "in_stock"
                v.name = var_name
                v.short_description = short_desc
                v.description = desc

                img_files = request.files.getlist(f"image_{v.id}")
                img_files = [f for f in img_files if f and f.filename]
                if img_files:
                    VariationImage.query.filter_by(variation_id=v.id).update({VariationImage.is_primary: 0})
                    for idx, img_file in enumerate(img_files):
                        url = handle_upload(img_file, folder="khushi-decors-variations")
                        if url:
                            mid = str(uuid.uuid4())
                            media = Media(id=mid, file_url=url)
                            db_sql.session.add(media)
                            vimg = VariationImage(
                                id=str(uuid.uuid4()),
                                variation_id=v.id,
                                media_id=mid,
                                is_primary=(1 if idx == 0 else 0),
                                display_order=idx
                            )
                            db_sql.session.add(vimg)

            db_sql.session.commit()
            getattr(get_products, "cache_clear")()
            flash("All variations updated successfully.", "success")
        except Exception as e:
            db_sql.session.rollback()
            flash(f"Error during bulk update: {e}", "error")
        return redirect(url_for("admin_product_variations", product_id=product_id))

    # ── Reviews ────────────────────────────────────────────────────────────────

    @app.route("/admin/reviews")
    @require_admin
    def admin_reviews():
        try:
            review_rows = (db_sql.session.query(
                ProductReview.id, ProductReview.product_id, ProductReview.user_id, ProductReview.rating,
                ProductReview.title, ProductReview.body, ProductReview.is_approved, ProductReview.created_at,
                Product.name.label("product_name"),
                User.first_name, User.last_name
            ).outerjoin(Product, Product.id == ProductReview.product_id)
             .outerjoin(User, User.id == ProductReview.user_id)
             .order_by(ProductReview.created_at.desc())
             .all())
             
            reviews = []
            for r in review_rows:
                reviews.append({
                    "id": r.id,
                    "product_id": r.product_id,
                    "user_id": r.user_id,
                    "rating": r.rating,
                    "title": r.title,
                    "body": r.body,
                    "is_approved": r.is_approved,
                    "created_at": r.created_at,
                    "product_name": r.product_name,
                    "reviewer_name": f"{r.first_name or ''} {r.last_name or ''}".strip() or "Guest"
                })
        except Exception as e:
            reviews = []
            flash(f"Error loading reviews: {e}", "error")
        return render_template("admin/reviews.html", reviews=reviews)

    @app.route("/admin/reviews/<review_id>/approve", methods=["POST"])
    @require_admin
    def admin_review_approve(review_id):
        action = request.form.get("action", "approve")
        review = db_sql.session.get(ProductReview, review_id)
        if review:
            try:
                approved = (action == "approve")
                review.is_approved = 1 if approved else 0
                db_sql.session.commit()
                flash("Review " + ("approved." if approved else "rejected."), "success")
            except Exception as e:
                db_sql.session.rollback()
                flash(f"Error: {e}", "error")
        else:
            flash("Review not found.", "error")
        return redirect(url_for("admin_reviews"))

    @app.route("/admin/reviews/<review_id>/delete", methods=["POST"])
    @require_admin
    def admin_review_delete(review_id):
        review = db_sql.session.get(ProductReview, review_id)
        if review:
            try:
                db_sql.session.delete(review)
                db_sql.session.commit()
                flash("Review deleted.", "success")
            except Exception as e:
                db_sql.session.rollback()
                flash(f"Error: {e}", "error")
        else:
            flash("Review not found.", "error")
        return redirect(url_for("admin_reviews"))

    # ── Settings ───────────────────────────────────────────────────────────────

    @app.route("/admin/settings", methods=["GET", "POST"])
    @require_admin
    def admin_settings():
        if request.method == "POST":
            toggle_keys  = ["cod_enabled", "online_payment_enabled", "free_shipping_enabled", "free_shipping_all"]
            text_keys    = ["razorpay_key_id", "razorpay_key_secret"]
            numeric_keys = ["shipping_fee", "free_shipping_threshold"]
            try:
                for key in toggle_keys:
                    value = "true" if request.form.get(key) == "on" else "false"
                    setting = db_sql.session.get(StoreSetting, key)
                    if setting:
                        setting.value = value
                        setting.updated_at = datetime.utcnow()
                    else:
                        db_sql.session.add(StoreSetting(key=key, value=value, updated_at=datetime.utcnow()))
                        
                for key in text_keys:
                    value = request.form.get(key, "").strip()
                    setting = db_sql.session.get(StoreSetting, key)
                    if setting:
                        setting.value = value
                        setting.updated_at = datetime.utcnow()
                    else:
                        db_sql.session.add(StoreSetting(key=key, value=value, updated_at=datetime.utcnow()))
                        
                for key in numeric_keys:
                    raw = request.form.get(key, "").strip()
                    try:
                        value = str(max(0, float(raw))) if raw else ("99" if key == "shipping_fee" else "999")
                    except ValueError:
                        value = "99" if key == "shipping_fee" else "999"
                    setting = db_sql.session.get(StoreSetting, key)
                    if setting:
                        setting.value = value
                        setting.updated_at = datetime.utcnow()
                    else:
                        db_sql.session.add(StoreSetting(key=key, value=value, updated_at=datetime.utcnow()))
                        
                db_sql.session.commit()
                getattr(get_cached_store_settings, "cache_clear")()
                flash("Settings saved successfully.", "success")
            except Exception as e:
                db_sql.session.rollback()
                flash(f"Error saving settings: {e}", "error")
            return redirect(url_for("admin_settings"))
        return render_template("admin/settings.html", settings=get_cached_store_settings())

    # ── Coupons ────────────────────────────────────────────────────────────────
    @app.route("/admin/coupons")
    @require_admin
    def admin_coupons():
        try:
            coupon_list = Coupon.query.order_by(Coupon.created_at.desc()).all()
            coupons = []
            for c in coupon_list:
                used_count = CouponUsage.query.filter_by(coupon_id=c.id).count()
                coupons.append({
                    "id": c.id,
                    "code": c.code,
                    "type": c.type,
                    "value": c.value,
                    "min_order_amount": c.min_order_amount,
                    "min_order": c.min_order,
                    "usage_limit": c.usage_limit,
                    "usage_limit_per_user": c.usage_limit_per_user,
                    "max_discount": c.max_discount,
                    "is_active": c.is_active,
                    "expires_at": c.expires_at,
                    "created_at": c.created_at,
                    "used_count": used_count
                })
        except Exception:
            coupons = []
        return render_template("admin/coupons.html", coupons=coupons)

    @app.route("/admin/coupons/new", methods=["GET", "POST"])
    @require_admin
    def admin_coupon_new():
        if request.method == "POST":
            f = request.form
            code = (f.get("code") or "").strip().upper()
            ctype = (f.get("type") or "").strip()

            if not code:
                flash("Coupon code is required.", "error")
                return render_template("admin/coupon_form.html", coupon=None)
            if ctype not in ("percentage", "fixed"):
                flash("Coupon type must be 'percentage' or 'fixed'.", "error")
                return render_template("admin/coupon_form.html", coupon=None)
            if Coupon.query.filter(func.upper(Coupon.code) == code).first():
                flash(f"Coupon code '{code}' already exists.", "error")
                return render_template("admin/coupon_form.html", coupon=None)

            try:
                limit_raw = f.get("usage_limit")
                limit_per_user_raw = f.get("usage_limit_per_user")
                max_discount_raw = f.get("max_discount")
                expires_at_raw = f.get("expires_at")
                
                new_coupon = Coupon(
                    id=str(uuid.uuid4()),
                    code=code,
                    type=ctype,
                    value=float(f.get("value") or 0),
                    min_order_amount=float(f.get("min_order_amount") or 0),
                    usage_limit=int(limit_raw) if limit_raw else None,
                    usage_limit_per_user=int(limit_per_user_raw) if limit_per_user_raw else 1,
                    max_discount=float(max_discount_raw) if max_discount_raw else None,
                    expires_at=datetime.strptime(expires_at_raw, "%Y-%m-%d") if expires_at_raw else None,
                    is_active=1 if f.get("is_active") == "on" else 0
                )
                db_sql.session.add(new_coupon)
                db_sql.session.commit()
                flash("Coupon created successfully.", "success")
                return redirect(url_for("admin_coupons"))
            except Exception as e:
                db_sql.session.rollback()
                flash(f"Error creating coupon: {e}", "error")
        return render_template("admin/coupon_form.html", coupon=None)

    @app.route("/admin/coupons/<coupon_id>/delete", methods=["POST"])
    @require_admin
    def admin_coupon_delete(coupon_id):
        coupon = db_sql.session.get(Coupon, coupon_id)
        if coupon:
            try:
                db_sql.session.delete(coupon)
                db_sql.session.commit()
                flash("Coupon deleted successfully.", "success")
            except Exception as e:
                db_sql.session.rollback()
                flash(f"Error deleting coupon: {e}", "error")
        else:
            flash("Coupon not found.", "error")
        return redirect(url_for("admin_coupons"))

    # ── CSV Import ─────────────────────────────────────────────────────────────

    @app.route("/admin/import", methods=["GET", "POST"])
    @require_admin
    def admin_import():
        results = None
        if request.method == "POST":
            csv_file = request.files.get("csv_file")
            if not csv_file or csv_file.filename == "":
                flash("Please select a CSV file.", "error")
                return render_template("admin/import.html", results=None)
            try:
                content  = csv_file.read().decode("utf-8-sig")
                reader   = csv.DictReader(io.StringIO(content))
                imported = skipped = 0
                errors   = []
                for i, row in enumerate(reader, 1):
                    try:
                        name  = (row.get("post_title") or row.get("name") or "").strip()
                        sku   = (row.get("sku") or "").strip() or generate_unique_product_sku(name)
                        desc  = (row.get("description") or row.get("post_content") or "").strip()
                        short = (row.get("short_description") or row.get("post_excerpt") or "").strip()
                        img   = (row.get("images") or row.get("image") or "").strip().split("|")[0].strip()
                        slug  = (row.get("post_name") or row.get("slug") or name.lower().replace(" ", "-")).strip()

                        if not name:
                            skipped += 1
                            continue
                        if Product.query.filter((Product.sku == sku) | (Product.slug == slug)).first():
                            skipped += 1
                            continue

                        try:
                            price = float(row.get("regular_price") or row.get("price") or 0)
                        except (ValueError, TypeError):
                            price = 0
                        try:
                            sale = float(row.get("sale_price") or 0) or None
                        except (ValueError, TypeError):
                            sale = None
                        try:
                            stock = int(row.get("stock") or row.get("stock_quantity") or 0)
                        except (ValueError, TypeError):
                            stock = 0

                        product = Product(
                            id=str(uuid.uuid4()),
                            name=name,
                            slug=slug,
                            sku=sku,
                            price=price,
                            sale_price=sale,
                            stock_quantity=stock,
                            stock_status="in_stock" if stock > 0 else "out_of_stock",
                            description=desc,
                            short_description=short,
                            is_active=1
                        )
                        db_sql.session.add(product)
                        
                        if img:
                            mid = str(uuid.uuid4())
                            media = Media(id=mid, file_url=img)
                            db_sql.session.add(media)
                            pimg = ProductImage(
                                id=str(uuid.uuid4()),
                                product_id=product.id,
                                media_id=mid,
                                is_primary=1
                            )
                            db_sql.session.add(pimg)
                            
                        imported += 1
                    except Exception as row_err:
                        errors.append(f"Row {i}: {row_err}")
                db_sql.session.commit()
                getattr(get_products, "cache_clear")()
                results = {"imported": imported, "skipped": skipped, "errors": errors}
                flash(f"Import complete: {imported} imported, {skipped} skipped.", "success")
            except Exception as e:
                db_sql.session.rollback()
                flash(f"CSV parse error: {e}", "error")
        return render_template("admin/import.html", results=results)

    # ── Blog ───────────────────────────────────────────────────────────────────

    @app.route("/admin/blog")
    @require_admin
    def admin_blog():
        posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
        return render_template("admin/blog_list.html", posts=posts)

    @app.route("/admin/blog/new", methods=["GET", "POST"])
    @require_admin
    def admin_blog_new():
        if request.method == "POST":
            f = request.form
            title = (f.get("title") or "").strip()
            if not title:
                flash("Title is required.", "error")
                return render_template("admin/blog_form.html", post=None)
            slug = get_unique_slug("blog_posts", f.get("slug") or slugify(title))
            image_url = handle_upload(request.files.get("image_file")) or f.get("image_url") or ""
            try:
                new_post = BlogPost(
                    id=str(uuid.uuid4()),
                    title=title,
                    slug=slug,
                    excerpt=f.get("excerpt", ""),
                    content=f.get("content", ""),
                    image_url=image_url,
                    author=f.get("author", "Admin") or "Admin",
                    published=1 if f.get("published") == "on" else 0
                )
                db_sql.session.add(new_post)
                db_sql.session.commit()
                flash("Blog post created.", "success")
                return redirect(url_for("admin_blog"))
            except Exception as e:
                db_sql.session.rollback()
                flash(f"Error creating post: {e}", "error")
        return render_template("admin/blog_form.html", post=None)

    @app.route("/admin/blog/<post_id>/edit", methods=["GET", "POST"])
    @require_admin
    def admin_blog_edit(post_id):
        post = db_sql.session.get(BlogPost, post_id)
        if not post:
            abort(404)
        if request.method == "POST":
            f = request.form
            title = (f.get("title") or "").strip()
            if not title:
                flash("Title is required.", "error")
                return render_template("admin/blog_form.html", post=post)
            slug = get_unique_slug("blog_posts", f.get("slug") or slugify(title), exclude_id=post_id)
            image_url = handle_upload(request.files.get("image_file")) or f.get("image_url") or post.image_url
            try:
                post.title = title
                post.slug = slug
                post.excerpt = f.get("excerpt", "")
                post.content = f.get("content", "")
                post.image_url = image_url
                post.author = f.get("author", "Admin") or "Admin"
                post.published = 1 if f.get("published") == "on" else 0
                db_sql.session.commit()
                flash("Blog post updated.", "success")
                return redirect(url_for("admin_blog"))
            except Exception as e:
                db_sql.session.rollback()
                flash(f"Error updating post: {e}", "error")
        return render_template("admin/blog_form.html", post=post)

    @app.route("/admin/blog/<post_id>/delete", methods=["POST"])
    @require_admin
    def admin_blog_delete(post_id):
        post = db_sql.session.get(BlogPost, post_id)
        if post:
            try:
                db_sql.session.delete(post)
                db_sql.session.commit()
                flash("Blog post deleted.", "success")
            except Exception as e:
                db_sql.session.rollback()
                flash(f"Error: {e}", "error")
        else:
            flash("Blog post not found.", "error")
        return redirect(url_for("admin_blog"))

    # ── Inquiries / Messages ──────────────────────────────────────────────────

    @app.route("/admin/messages")
    @require_admin
    def admin_messages():
        messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
        return render_template("admin/messages.html", messages=messages)

    @app.route("/admin/messages/<msg_id>/delete", methods=["POST"])
    @require_admin
    def admin_message_delete(msg_id):
        msg = db_sql.session.get(ContactMessage, msg_id)
        if msg:
            try:
                db_sql.session.delete(msg)
                db_sql.session.commit()
                flash("Message deleted.", "success")
            except Exception as e:
                db_sql.session.rollback()
                flash(f"Error: {e}", "error")
        else:
            flash("Message not found.", "error")
        return redirect(url_for("admin_messages"))

    # ── Style Planner ──────────────────────────────────────────────────────────

    @app.route("/admin/planner")
    @require_admin
    def admin_planner():
        from models import PlannerCollection
        collections = PlannerCollection.query.order_by(PlannerCollection.display_order).all()
        collection_data = []
        for col in collections:
            featured = []
            for cp in col.col_products.all():
                p = cp.product
                if p:
                    img = ""
                    pi = p.images.filter_by(is_primary=1).first() or p.images.first()
                    if pi and pi.media:
                        img = pi.media.file_url
                    featured.append({"cp_id": cp.id, "product": p, "image": img})
            collection_data.append({"collection": col, "products": featured})
        return render_template("admin/planner.html", collection_data=collection_data)

    @app.route("/admin/planner/add", methods=["POST"])
    @require_admin
    def admin_planner_add():
        from models import PlannerCollection
        title = request.form.get("title", "").strip()
        if not title:
            flash("Title is required.", "error")
            return redirect(url_for("admin_planner"))
        order = PlannerCollection.query.count()
        col = PlannerCollection(
            title=title,
            tip=request.form.get("tip", "").strip(),
            image_url=request.form.get("image_url", "").strip(),
            page_slug=request.form.get("page_slug", "").strip(),
            display_order=order,
            is_active=1
        )
        db_sql.session.add(col)
        db_sql.session.commit()
        flash(f"Collection '{title}' added.", "success")
        return redirect(url_for("admin_planner"))

    @app.route("/admin/planner/<col_id>/edit", methods=["GET", "POST"])
    @require_admin
    def admin_planner_edit(col_id):
        from models import PlannerCollection, Product, PlannerCollectionProduct
        col = db_sql.session.get(PlannerCollection, col_id)
        if not col:
            flash("Collection not found.", "error")
            return redirect(url_for("admin_planner"))
        
        if request.method == "POST":
            col.title     = request.form.get("title", col.title).strip()
            col.tip       = request.form.get("tip", col.tip).strip()
            col.image_url = request.form.get("image_url", col.image_url).strip()
            col.page_slug = request.form.get("page_slug", col.page_slug).strip()
            
            # Update featured products checklist
            selected_pids = request.form.getlist("featured_products")
            if len(selected_pids) > 3:
                flash("You can select up to 3 featured products max.", "error")
                return redirect(url_for("admin_planner_edit", col_id=col_id))
            
            # Clear existing products and re-add new ones
            PlannerCollectionProduct.query.filter_by(collection_id=col.id).delete()
            for idx, pid in enumerate(selected_pids):
                cp = PlannerCollectionProduct(
                    collection_id=col.id,
                    product_id=pid,
                    display_order=idx
                )
                db_sql.session.add(cp)
            
            db_sql.session.commit()
            flash("Collection and featured products updated.", "success")
            return redirect(url_for("admin_planner"))
            
        products = Product.query.filter_by(is_active=1).order_by(Product.name).all()
        featured_ids = [cp.product_id for cp in col.col_products.all()]
        return render_template("admin/planner_edit.html", col=col, products=products, featured_ids=featured_ids)

    @app.route("/admin/planner/<col_id>/toggle", methods=["POST"])
    @require_admin
    def admin_planner_toggle(col_id):
        from models import PlannerCollection
        col = db_sql.session.get(PlannerCollection, col_id)
        if col:
            col.is_active = 0 if col.is_active else 1
            db_sql.session.commit()
            flash(f"Collection {'shown' if col.is_active else 'hidden'}.", "success")
        return redirect(url_for("admin_planner"))

    @app.route("/admin/planner/<col_id>/delete", methods=["POST"])
    @require_admin
    def admin_planner_delete(col_id):
        from models import PlannerCollection
        col = db_sql.session.get(PlannerCollection, col_id)
        if col:
            db_sql.session.delete(col)
            db_sql.session.commit()
            flash("Collection deleted.", "success")
        return redirect(url_for("admin_planner"))

    @app.route("/admin/planner/<col_id>/products/add", methods=["POST"])
    @require_admin
    def admin_planner_product_add(col_id):
        from models import PlannerCollection, PlannerCollectionProduct
        col = db_sql.session.get(PlannerCollection, col_id)
        if not col:
            flash("Collection not found.", "error")
            return redirect(url_for("admin_planner"))
        product_id = request.form.get("product_id", "").strip()
        if not product_id:
            flash("No product selected.", "error")
            return redirect(url_for("admin_planner"))
        if col.col_products.count() >= 3:
            flash("Maximum 3 products per collection.", "error")
            return redirect(url_for("admin_planner"))
        if PlannerCollectionProduct.query.filter_by(
                collection_id=col_id, product_id=product_id).first():
            flash("Product already in this collection.", "error")
            return redirect(url_for("admin_planner"))
        cp = PlannerCollectionProduct(
            collection_id=col_id,
            product_id=product_id,
            display_order=col.col_products.count()
        )
        db_sql.session.add(cp)
        db_sql.session.commit()
        flash("Product added to collection.", "success")
        return redirect(url_for("admin_planner"))

    @app.route("/admin/planner/<col_id>/products/<cp_id>/remove", methods=["POST"])
    @require_admin
    def admin_planner_product_remove(col_id, cp_id):
        from models import PlannerCollectionProduct
        cp = PlannerCollectionProduct.query.filter_by(id=cp_id, collection_id=col_id).first()
        if cp:
            db_sql.session.delete(cp)
            db_sql.session.commit()
            flash("Product removed.", "success")
        return redirect(url_for("admin_planner"))

    @app.route("/admin/planner/search_products")
    @require_admin
    def admin_planner_search_products():
        q = request.args.get("q", "").strip()
        if len(q) < 2:
            return jsonify([])
        results = (Product.query
                   .filter(Product.name.ilike(f"%{q}%"), Product.is_active == 1)
                   .limit(10).all())
        out = []
        for p in results:
            img = ""
            pi = p.images.filter_by(is_primary=1).first() or p.images.first()
            if pi and pi.media:
                img = pi.media.file_url
            out.append({
                "id": p.id,
                "name": p.name,
                "price": float(p.sale_price or p.price or 0),
                "image": img
            })
        return jsonify(out)



