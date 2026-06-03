from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, Response, jsonify
import json
import uuid
from extensions import db_sql
from helpers import resolve_image, get_cached_store_settings
from queries import (
    get_products, get_categories, get_brands,
    get_product_detail, get_related_products,
    get_homepage_products, get_featured_categories,
)
from models import (
    Product, Category, Brand, AttributeValue, Attribute,
    ProductAttribute, ProductAttributeValue, ProductVariation,
    VariationAttributeValue, VariationImage, Media, ContactMessage,
    NewsletterSubscriber, BlogPost
)

bp = Blueprint("public", __name__)


@bp.route("/")
def index():
    try:
        data = get_homepage_products()
        featured            = data["featured"]
        latest              = data["latest"]
        popular             = data["popular"]
        promo1              = data["promo1"]
        promo2              = data["promo2"]
        
        featured_categories = get_featured_categories()
    except Exception as e:
        featured = latest = popular = promo1 = promo2 = []
        featured_categories = []
        flash(f"Data loading error: {e}", "error")

    # Fetch latest blog posts for homepage
    try:
        posts = BlogPost.query.filter_by(published=1).order_by(BlogPost.created_at.desc()).limit(3).all()
        blog_posts = []
        for p in posts:
            blog_posts.append({
                "title": p.title,
                "slug": p.slug,
                "excerpt": p.excerpt,
                "image_url": p.image_url,
                "author": p.author,
                "created_at": p.created_at
            })
    except Exception:
        blog_posts = []

    return render_template(
        "index.html",
        featured=featured, latest=latest, popular=popular,
        promo1=promo1, promo2=promo2,
        featured_categories=featured_categories,
        blog_posts=blog_posts,
    )


@bp.route("/shop")
def shop():
    search          = request.args.get("search", "").strip()
    selected_cats   = tuple(s for s in request.args.getlist("category") if s)
    selected_brands = tuple(s for s in request.args.getlist("brand")    if s)
    selected_attrs  = tuple(s for s in request.args.getlist("attr_value") if s)
    sort            = request.args.get("sort", "created_at_desc")
    page            = max(1, int(request.args.get("page", 1)))
    on_sale         = bool(request.args.get("on_sale", ""))
    featured        = bool(request.args.get("featured", ""))
    min_price       = request.args.get("min_price", "").strip()
    max_price       = request.args.get("max_price", "").strip()
    ajax            = request.args.get("ajax", "").strip() == "1" or request.headers.get("X-Requested-With") == "XMLHttpRequest"

    try:
        min_price_val = float(min_price) if min_price else None
        max_price_val = float(max_price) if max_price else None
    except ValueError:
        min_price_val = max_price_val = None

    try:
        # Dynamically query global pricing boundaries for the filter sliders
        prices_list = []
        p_prices = db_sql.session.query(Product.price, Product.sale_price).filter(Product.is_active == 1).all()
        for p_pr, s_pr in p_prices:
            if p_pr: prices_list.append(p_pr)
            if s_pr: prices_list.append(s_pr)
        var_prices = db_sql.session.query(ProductVariation.price, ProductVariation.sale_price).join(Product, Product.id == ProductVariation.product_id).filter(Product.is_active == 1).all()
        for v_pr, vs_pr in var_prices:
            if v_pr: prices_list.append(v_pr)
            if vs_pr: prices_list.append(vs_pr)

        global_min = int(min(prices_list)) if prices_list else 100
        global_max = int(max(prices_list)) if prices_list else 10000

        products, total, total_pages = get_products(
            search=search, categories=selected_cats, brands=selected_brands,
            sort=sort, page=page, per_page=16, on_sale=on_sale,
            featured=featured, min_price=min_price_val, max_price=max_price_val,
            attribute_values=selected_attrs,
        )
        all_categories = get_categories()
        all_brands     = get_brands()
        
        # Fetch primary attribute values (e.g. Flavors) for sidebar filter
        flavor_rows = (db_sql.session.query(AttributeValue.id, AttributeValue.value, AttributeValue.image_url)
                       .join(Attribute, Attribute.id == AttributeValue.attribute_id)
                       .filter(Attribute.variation_type == 'primary')
                       .order_by(AttributeValue.value)
                       .all())
        flavor_vals = []
        for r in flavor_rows:
            flavor_vals.append({
                "id": str(r.id),
                "value": r.value,
                "image_url": r.image_url
            })
    except Exception as e:
        products, total, total_pages = [], 0, 1
        all_categories = all_brands = []
        flavor_vals = []
        global_min, global_max = 100, 10000
        flash(f"Database error: {e}", "error")

    # Build parent → children tree for the sidebar accordion
    parent_cats  = [c for c in all_categories if not c.get("parent_id")]
    children_map = {}
    for c in all_categories:
        pid = c.get("parent_id")
        if pid:
            children_map.setdefault(str(pid), []).append(c)

    if ajax:
        return render_template(
            "partials/product_grid.html",
            products=products, total_count=total, total_pages=total_pages,
            current_page=page, categories=all_categories,
        )

    return render_template(
        "shop.html",
        products=products, total_count=total, total_pages=total_pages,
        current_page=page,
        categories=all_categories, brands=all_brands,
        parent_cats=parent_cats, children_map=children_map,
        search=search,
        current_categories=selected_cats,
        current_brands=selected_brands,
        current_attrs=selected_attrs,
        flavor_vals=flavor_vals,
        current_sort=sort,
        on_sale=on_sale,
        min_price=min_price, max_price=max_price,
        global_min=global_min, global_max=global_max,
    )


@bp.route("/product/<product_id>")
def product_detail(product_id):
    preselect = request.args.get("preselect", "").strip() or None
    try:
        product, images, variations, reviews, attributes = get_product_detail(product_id, preselect=preselect)
        # Embed variation attributes + variations in the page (avoids slow API calls)
        var_data = _get_variation_data(product_id)
        variation_json = json.dumps(var_data) if var_data else "null"
        # Also embed variations array for client-side matching
        vars_json = json.dumps(var_data["variations"]) if var_data and var_data.get("variations") else "[]"
    except Exception as e:
        flash(f"Error loading product: {e}", "error")
        return redirect(url_for("public.shop"))
    if not product:
        abort(404)
    
    # Resolve images list into simple URLs for storefront gallery
    gallery_images = [resolve_image(img["image_url"]) for img in images]
    if not gallery_images:
        gallery_images = ["/static/images/placeholder.png"]
        
    try:
        related = get_related_products(product.get("category_slug", ""), product_id)
    except Exception:
        related = []

    # Compute dynamic rating metrics
    num_reviews = len(reviews)
    avg_rating = round(sum(r["rating"] for r in reviews) / num_reviews, 1) if num_reviews > 0 else 0.0
    full_stars = int(avg_rating)
    half_star = 1 if (avg_rating - full_stars) >= 0.5 else 0
    empty_stars = 5 - full_stars - half_star

    settings = get_cached_store_settings()
    free_shipping_threshold = float(settings.get("free_shipping_threshold") or 999)

    return render_template(
        "product_detail.html",
        product=product, images=images, gallery_images=gallery_images, variations=variations,
        reviews=reviews, attributes=attributes, related=related, related_products=related,
        variation_json=variation_json, vars_json=vars_json,
        avg_rating=avg_rating, num_reviews=num_reviews,
        full_stars=full_stars, half_star=half_star, empty_stars=empty_stars,
        free_shipping_threshold=free_shipping_threshold
    )


@bp.route("/category/<slug>")
def category_page(slug):
    return redirect(url_for("public.shop", category=slug))


@bp.route("/brand/<slug>")
def brand_page(slug):
    return redirect(url_for("public.shop", brand=slug))


@bp.route("/about")
def about():
    return render_template("about.html")


@bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name    = request.form.get("name", "").strip()
        email   = request.form.get("email", "").strip().lower()
        message = request.form.get("message", "").strip()
        if not all([name, email, message]):
            flash("Please fill in all required fields.", "error")
        else:
            try:
                msg = ContactMessage(
                    id=str(uuid.uuid4()),
                    name=name,
                    email=email,
                    message=message
                )
                db_sql.session.add(msg)
                db_sql.session.commit()
                flash("Thank you for your message! We'll get back to you soon.", "success")
            except Exception as e:
                db_sql.session.rollback()
                flash("Something went wrong. Please try again later.", "error")
            return redirect(url_for("public.contact"))
    return render_template("contact.html")


@bp.route("/subscribe", methods=["POST"])
def subscribe():
    email = request.form.get("email", "").strip().lower()
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or "application/json" in (request.headers.get("Accept") or "")
    if email:
        try:
            existing = NewsletterSubscriber.query.filter_by(email=email).first()
            if not existing:
                sub = NewsletterSubscriber(
                    id=str(uuid.uuid4()),
                    email=email
                )
                db_sql.session.add(sub)
                db_sql.session.commit()
            message = "Thank you for subscribing to our newsletter!"
            if is_ajax:
                return jsonify({"success": True, "message": message})
            flash(message, "success")
        except Exception as e:
            db_sql.session.rollback()
            message = "An error occurred while subscribing."
            if is_ajax:
                return jsonify({"success": False, "message": message}), 500
            flash(message, "error")
    else:
        message = "Please enter a valid email address."
        if is_ajax:
            return jsonify({"success": False, "message": message}), 400
        flash(message, "error")
    return redirect(request.referrer or url_for("public.index"))


@bp.route("/sitemap.xml")
def sitemap():
    base = request.host_url.rstrip("/")

    static_pages = [
        ("",         "1.0", "daily"),
        ("/shop",    "0.9", "daily"),
        ("/about",   "0.7", "monthly"),
        ("/contact", "0.7", "monthly"),
    ]

    try:
        products = Product.query.filter_by(is_active=1).order_by(Product.updated_at.desc()).all()
    except Exception:
        products = []

    try:
        categories = Category.query.filter_by(is_active=1).all()
    except Exception:
        categories = []

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']

    for path, priority, freq in static_pages:
        lines.append(
            f"  <url><loc>{base}{path}</loc>"
            f"<changefreq>{freq}</changefreq>"
            f"<priority>{priority}</priority></url>"
        )

    for p in products:
        updated = p.updated_at
        lastmod = f"<lastmod>{updated.strftime('%Y-%m-%d')}</lastmod>" if updated else ""
        lines.append(
            f"  <url><loc>{base}/product/{p.id}</loc>"
            f"{lastmod}<changefreq>weekly</changefreq>"
            f"<priority>0.8</priority></url>"
        )

    for c in categories:
        lines.append(
            f"  <url><loc>{base}/shop?category={c.slug}</loc>"
            f"<changefreq>weekly</changefreq>"
            f"<priority>0.7</priority></url>"
        )

    lines.append("</urlset>")
    return Response("\n".join(lines), mimetype="application/xml")


@bp.route("/robots.txt")
def robots():
    base = request.host_url.rstrip("/")
    content = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /admin/\n"
        "Disallow: /cart\n"
        "Disallow: /checkout\n"
        "Disallow: /account\n"
        "Disallow: /login\n"
        "Disallow: /register\n"
        "\n"
        f"Sitemap: {base}/sitemap.xml\n"
    )
    return Response(content, mimetype="text/plain")


# ── Variation API ──────────────────────────────────────────────────────────────

@bp.route("/api/product/<product_id>/variation")
def api_product_variation(product_id):
    full = _get_variation_data(product_id)
    if full is None:
        return jsonify({"error": "Product not found"}), 404

    # If ?selected= is provided, find the matching variation
    selected_raw = request.args.get("selected", "")
    if selected_raw:
        selected_ids = set(s.strip() for s in selected_raw.split(",") if s.strip())
        match = None
        for vd in full["variations"]:
            v_val_ids = set(str(r["value_id"]) for r in vd["values"])
            if v_val_ids == selected_ids:
                match = vd
                break
        if match:
            return jsonify({
                "found": True,
                "price":          match["price"],
                "stock_quantity": match["stock_quantity"],
                "stock_status":   match["stock_status"],
                "sku":            match["sku"],
                "variation_id":   match["id"],
                "images":         match["images"],
                "name":           match.get("name", ""),
                "short_description": match.get("short_description", ""),
                "description":    match.get("description", ""),
            })
        else:
            return jsonify({"found": False, "message": "No matching variation"}), 404

    # Full data mode (no ?selected=)
    return jsonify(full)


def _get_variation_data(product_id):
    """Return the full variation attributes + variations dict for embedding / API."""
    product = Product.query.filter_by(id=product_id, is_active=1).first()
    if not product:
        return None

    attrs = (db_sql.session.query(Attribute.id, Attribute.name, Attribute.slug, Attribute.variation_type)
             .join(ProductAttribute, ProductAttribute.attribute_id == Attribute.id)
             .filter(ProductAttribute.product_id == product_id)
             .order_by(ProductAttribute.display_order)
             .all())

    if not attrs:
        return {
            "product": {
                "price":        float(product.sale_price or product.price or 0),
                "stock":        int(product.stock_quantity or 0),
                "stock_status": product.stock_status,
                "sku":          product.sku,
            },
            "attributes": [],
            "variations": [],
        }

    attr_ids = [a.id for a in attrs]
    
    pav_rows = (db_sql.session.query(AttributeValue.attribute_id, AttributeValue.id, AttributeValue.value, AttributeValue.image_url)
                .join(ProductAttributeValue, ProductAttributeValue.attribute_value_id == AttributeValue.id)
                .filter(ProductAttributeValue.product_id == product_id, AttributeValue.attribute_id.in_(attr_ids))
                .order_by(AttributeValue.value)
                .all())
                
    all_vals = (db_sql.session.query(AttributeValue.attribute_id, AttributeValue.id, AttributeValue.value, AttributeValue.image_url)
                .filter(AttributeValue.attribute_id.in_(attr_ids))
                .order_by(AttributeValue.value)
                .all())

    val_map = {}
    for row in pav_rows:
        val_map.setdefault(str(row.attribute_id), []).append(row)
    for row in all_vals:
        aid = str(row.attribute_id)
        if aid not in val_map:
            val_map.setdefault(aid, []).append(row)

    attr_groups = []
    for a in attrs:
        vals = val_map.get(str(a.id), [])
        attr_groups.append({
            "id":              str(a.id),
            "name":            a.name,
            "slug":            a.slug,
            "variation_type":  a.variation_type,
            "values": [{
                "id":        str(v.id),
                "value":     v.value,
                "image_url": resolve_image(v.image_url or ""),
            } for v in vals],
        })

    variations = ProductVariation.query.filter_by(product_id=product_id).all()
    var_data = []
    if variations:
        var_ids = [v.id for v in variations]
        vav_rows = (db_sql.session.query(VariationAttributeValue.variation_id, VariationAttributeValue.attribute_value_id, AttributeValue.value, AttributeValue.attribute_id)
                    .join(AttributeValue, AttributeValue.id == VariationAttributeValue.attribute_value_id)
                    .filter(VariationAttributeValue.variation_id.in_(var_ids))
                    .all())
        vav_map = {}
        for r in vav_rows:
            vav_map.setdefault(str(r.variation_id), []).append(r)

        vi_rows = (db_sql.session.query(VariationImage.variation_id, Media.file_url, VariationImage.is_primary)
                   .join(Media, Media.id == VariationImage.media_id)
                   .filter(VariationImage.variation_id.in_(var_ids))
                   .order_by(VariationImage.is_primary.desc(), VariationImage.display_order)
                   .all())
        var_image_map = {}
        for r in vi_rows:
            var_image_map.setdefault(str(r.variation_id), []).append(
                resolve_image(r.file_url or "")
            )

        for v in variations:
            vid = str(v.id)
            var_data.append({
                "id":             vid,
                "sku":            v.sku,
                "price":          float(v.sale_price or v.price or 0),
                "stock_quantity": int(v.stock_quantity or 0),
                "stock_status":   v.stock_status,
                "images":         var_image_map.get(vid, []),
                "values": [{
                    "attribute_id": str(r.attribute_id),
                    "value_id":     str(r.attribute_value_id),
                    "value":        r.value,
                } for r in vav_map.get(vid, [])],
                "name":             v.name or "",
                "short_description": v.short_description or "",
                "description":      v.description or "",
            })

    return {
        "product": {
            "price":        float(product.sale_price or product.price or 0),
            "stock":        int(product.stock_quantity or 0),
            "stock_status": product.stock_status,
            "sku":          product.sku,
        },
        "attributes": attr_groups,
        "variations": var_data,
    }
