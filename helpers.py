import re
import functools
import time
import markupsafe
import cloudinary
import cloudinary.uploader
import db
import uuid


def slugify(text):
    if not text:
        return ""
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def ttl_cache(ttl_seconds=60):
    def decorator(func):
        cache = {}

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            now = time.time()
            cached = cache.get(key)
            if cached and now - cached[0] < ttl_seconds:
                return cached[1]
            result = func(*args, **kwargs)
            cache[key] = (now, result)
            return result

        wrapper.cache_clear = cache.clear
        return wrapper
    return decorator


def get_unique_slug(table, base_slug, exclude_id=None):
    from extensions import db_sql
    import models
    
    # Map table string to SQLAlchemy model
    model = None
    for name, obj in vars(models).items():
        if isinstance(obj, type) and issubclass(obj, db_sql.Model) and getattr(obj, "__tablename__", None) == table:
            model = obj
            break
            
    slug = base_slug or "item"
    if not model:
        return f"{base_slug}-{uuid.uuid4().hex[:8]}"

    counter = 1
    for _ in range(50):
        q = db_sql.session.query(model.id).filter(model.slug == slug)
        if exclude_id:
            q = q.filter(model.id != exclude_id)
        if not q.first():
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1
    return f"{base_slug}-{uuid.uuid4().hex[:8]}"


def get_store_settings():
    from models import StoreSetting
    try:
        rows = StoreSetting.query.all()
        return {r.key: r.value for r in rows}
    except Exception:
        return {"cod_enabled": "true", "online_payment_enabled": "false"}


@ttl_cache(ttl_seconds=60)
def get_cached_store_settings():
    return get_store_settings()


def refresh_cart_prices(cart):
    from models import Product, ProductVariation
    refreshed = {}
    subtotal  = 0
    if not cart:
        return refreshed, subtotal

    product_ids = list({str(item.get("product_id", "")).strip()
                        for item in cart.values() if item.get("product_id")})
    if not product_ids:
        return refreshed, subtotal

    products = Product.query.filter(Product.id.in_(product_ids)).all()
    product_map = {str(p.id): p for p in products}

    # Load all variation IDs from cart items
    var_ids = [str(item["variation_id"]) for item in cart.values()
               if item.get("variation_id")]
    var_price_map = {}
    if var_ids:
        variations = ProductVariation.query.filter(ProductVariation.id.in_(var_ids)).all()
        for v in variations:
            var_price_map[str(v.id)] = float(v.sale_price or v.price or 0)

    for key, item in cart.items():
        product_id = str(item.get("product_id", "")).strip()
        product    = product_map.get(product_id)
        if not product:
            continue
        price = float(product.sale_price or product.price or 0)
        # Use variation price if available
        var_id = str(item.get("variation_id") or "")
        if var_id and var_id in var_price_map:
            price = var_price_map[var_id]
        new_item = dict(item)
        new_item["price"] = price
        if not new_item.get("sku"):
            new_item["sku"] = product.sku or ""
        refreshed[key] = new_item
        subtotal += price * int(new_item.get("qty", 0))

    return refreshed, subtotal


# ─── Jinja2 globals / filters ──────────────────────────────────────────────────

import os

# Cloudinary is configured from the CLOUDINARY_URL environment variable
# which is loaded via python-dotenv at app startup.
cloudinary.config(from_url=os.getenv("CLOUDINARY_URL"))


def handle_upload(file, folder="khushi-decors-gallery"):
    """Upload a file — tries Cloudinary, falls back to local storage."""
    if not file or not file.filename:
        return None
    # Try Cloudinary first
    try:
        result = cloudinary.uploader.upload(
            file,
            folder=folder,
            resource_type="image",
            overwrite=False,
        )
        return result["secure_url"]
    except Exception:
        pass  # fall through to local storage

    # Local fallback — save to static/uploads/
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "jpg"
    safe_name = f"{uuid.uuid4().hex[:12]}.{ext}"
    upload_dir = os.path.join(os.path.dirname(__file__), "static", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file.seek(0)
    file.save(os.path.join(upload_dir, safe_name))
    return f"/uploads/{safe_name}"


CLOUDINARY_MAPPING = {
  "placeholder.png": "https://res.cloudinary.com/dljlnkh6x/image/upload/v1777410770/talbeena-gallery/static/we9iq7o3zsg4axrtkwbi.png"
}

def resolve_image(image_url):
    from flask import url_for
    # Default Cloudinary Placeholder
    PLACEHOLDER = CLOUDINARY_MAPPING.get("placeholder.png", "https://res.cloudinary.com/dljlnkh6x/image/upload/v1777410770/talbeena-gallery/static/we9iq7o3zsg4axrtkwbi.png")
    
    if not image_url:
        return PLACEHOLDER
    
    if image_url.startswith("http"):
        return image_url
        
    # Check mapping first
    clean_url = image_url.lstrip("/")
    if clean_url.startswith("images/"):
        clean_url = clean_url.replace("images/", "", 1)
        
    if clean_url in CLOUDINARY_MAPPING:
        return CLOUDINARY_MAPPING[clean_url]
        
    # If it's a relative path, we check if it's meant to be a static asset
    if image_url.startswith("/uploads/") or image_url.startswith("uploads/"):
        return url_for("static", filename=image_url.lstrip("/"))
        
    # Already a valid static path (images/ or css/ etc.)
    if "/" in image_url.lstrip("/"):
        return url_for("static", filename=image_url.lstrip("/"))
        
    # Fallback to static images folder for bare filenames
    return url_for("static", filename=f"images/{image_url.lstrip('/')}")


def _strip_html(text):
    if not text:
        return ""
    clean = re.sub(r'<[^>]+>', ' ', text)
    clean = clean.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&gt;', '>').replace('&lt;', '<')
    clean = re.sub(r'\n+', '\n', clean)
    return re.sub(r' +', ' ', clean).strip()


def format_description(text):
    if not text:
        return ""
    text = _strip_html(text)
    text = text.replace("\\n", "\n").replace("\r\n", "\n").replace("\r", "\n")
    rows, paras = [], []
    for line in [l.strip() for l in text.split("\n")]:
        if not line:
            continue
        m = re.match(r"^[•*-]?\s*(.+?)\s*:-\s*(.+)$", line)
        if m:
            rows.append((m.group(1).strip(), m.group(2).strip()))
        else:
            paras.append(re.sub(r"^[•*-]\s*", "", line))
    parts = []
    if rows:
        trs = "".join(
            f'<tr><td class="desc-key">{markupsafe.escape(k)}</td>'
            f'<td class="desc-val">{markupsafe.escape(v)}</td></tr>'
            for k, v in rows
        )
        parts.append(f'<table class="desc-table"><tbody>{trs}</tbody></table>')
    parts += [f'<p class="desc-para">{markupsafe.escape(p)}</p>' for p in paras]
    return markupsafe.Markup("".join(parts))


def format_short_desc(text):
    if not text:
        return ""
    text = _strip_html(text)
    text = text.replace("\\n", "\n").replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"^[•*-]\s*", "", l.strip()) for l in text.split("\n") if l.strip()]
    return markupsafe.Markup(
        "".join(f'<p class="short-desc-line">{markupsafe.escape(l)}</p>' for l in lines)
    )


def register_jinja(app):
    app.jinja_env.globals["resolve_image"] = resolve_image
    app.jinja_env.filters["format_description"] = format_description
    app.jinja_env.filters["format_short_desc"] = format_short_desc

    # ── URL helpers for templates ──────────────────────────────────────────────
    def _remove_param(key, value):
        """Return a query string with the given key=value pair removed."""
        from flask import request as _req
        params = [(k, v) for k, v in _req.args.items(multi=True)
                  if not (k == key and (not value or str(v) == str(value)))]
        import urllib.parse
        return urllib.parse.urlencode(params, doseq=True)

    def _page_url(page_num):
        """Return the current query string with the page parameter updated."""
        from flask import request as _req
        params = [(k, v) for k, v in _req.args.items(multi=True) if k != "page"]
        params.append(("page", str(page_num)))
        import urllib.parse
        return urllib.parse.urlencode(params, doseq=True)

    app.jinja_env.globals["remove_param"] = _remove_param
    app.jinja_env.globals["page_url"]     = _page_url

    # ── Date formatting filter (handles both datetime objects and strings) ──
    def _format_date(value):
        """Format a date/datetime to YYYY-MM-DD string."""
        if value is None:
            return ""
        if hasattr(value, "strftime"):
            return value.strftime("%Y-%m-%d")
        s = str(value)
        return s[:10] if len(s) >= 10 else s

    app.jinja_env.filters["date_short"] = _format_date
