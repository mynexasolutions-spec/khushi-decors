from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from extensions import db_sql
from helpers import refresh_cart_prices
from models import Product, ProductVariation, AttributeValue, VariationAttributeValue

bp = Blueprint("cart", __name__)


@bp.route("/cart")
def view_cart():
    cart_items = session.get("cart", {})
    cart_items, subtotal = refresh_cart_prices(cart_items)
    session["cart"] = cart_items
    shipping = 0 if subtotal >= 999 else 99
    return render_template(
        "cart.html",
        cart_items=cart_items,
        subtotal=subtotal,
        shipping=shipping,
        total=subtotal + shipping,
    )


@bp.route("/cart/add", methods=["POST"])
def cart_add():
    product_id       = str(request.form.get("product_id", "")).strip()
    variation_id     = str(request.form.get("variation_id", "")).strip()
    selected_options = str(request.form.get("selected_options", "")).strip()
    qty              = max(1, int(request.form.get("qty", 1)))

    if not product_id:
        flash("Invalid product.", "error")
        return redirect(request.referrer or url_for("public.shop"))

    try:
        product = Product.query.get(product_id)
        if not product:
            flash("Product not found.", "error")
            return redirect(request.referrer or url_for("public.shop"))

        display_name = product.name
        price        = float(product.sale_price or product.price or 0)
        sku          = product.sku or ""
        
        # Get primary image url
        img = ""
        if product.images:
            primary_img = [pi for pi in product.images if pi.is_primary == 1]
            if primary_img and primary_img[0].media:
                img = primary_img[0].media.file_url

        if variation_id:
            # Variable product — look up the specific variation
            var = ProductVariation.query.get(variation_id)
            if var:
                price = float(var.sale_price or var.price or price)
                sku   = var.sku or sku
                
                # Fetch variation attributes
                opts = (db_sql.session.query(AttributeValue.value)
                        .join(VariationAttributeValue, VariationAttributeValue.attribute_value_id == AttributeValue.id)
                        .filter(VariationAttributeValue.variation_id == variation_id)
                        .all())
                if opts:
                    display_name += f" ({' / '.join(o.value for o in opts)})"
            item_key = variation_id
        else:
            item_key = product_id

        if selected_options:
            display_name += f" ({selected_options})"
            item_key = f"{product_id}|{selected_options}"

        cart = session.get("cart", {})
        if item_key in cart:
            cart[item_key]["qty"] += qty
        else:
            cart[item_key] = {
                "product_id": product_id,
                "variation_id": variation_id or None,
                "name": display_name,
                "price": price,
                "qty": qty,
                "image": img,
                "sku": sku,
            }
        session["cart"] = cart
        flash(f"'{display_name}' added to cart!", "success")
    except Exception as e:
        flash(f"Error adding to cart: {e}", "error")

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        count = sum(i["qty"] for i in session.get("cart", {}).values())
        return jsonify({"success": True, "cart_count": count})
    return redirect(request.referrer or url_for("public.shop"))


@bp.route("/cart/remove", methods=["POST"])
def cart_remove():
    cart = session.get("cart", {})
    item_key = str(request.form.get("product_id", "")).strip()
    if item_key in cart:
        cart.pop(item_key)
        session["cart"] = cart
        flash("Item removed from cart.", "info")
    elif item_key:
        fallback = [k for k in cart if k.strip() == item_key]
        if fallback:
            cart.pop(fallback[0])
            session["cart"] = cart
            flash("Item removed from cart.", "info")
        else:
            flash("Item not found in cart.", "error")
    else:
        flash("Item not found in cart.", "error")
    return redirect(url_for("cart.view_cart"))


@bp.route("/cart/update", methods=["POST"])
def cart_update():
    cart = session.get("cart", {})
    for key in list(cart.keys()):
        current_qty = int(cart[key].get("qty", 1) or 1)
        raw_qty = request.form.get(f"qty_{key}", current_qty)
        try:
            new_qty = int(raw_qty)
        except (TypeError, ValueError):
            new_qty = current_qty
        cart[key]["qty"] = max(1, new_qty)
    session["cart"] = cart
    
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": True})
        
    flash("Cart updated.", "success")
    return redirect(url_for("cart.view_cart"))


@bp.route("/cart/ajax_update", methods=["POST"])
def cart_ajax_update():
    """AJAX: update single item qty, return new subtotal/total."""
    cart = session.get("cart", {})
    item_key = request.form.get("key", "").strip()
    delta = request.form.get("delta", "0")
    try:
        delta = int(delta)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid delta"}), 400

    if item_key in cart:
        new_qty = int(cart[item_key].get("qty", 1)) + delta
        new_qty = max(1, min(20, new_qty))
        cart[item_key]["qty"] = new_qty
        session["cart"] = cart

        from helpers import refresh_cart_prices
        _, subtotal = refresh_cart_prices(cart)
        shipping = 0 if subtotal >= 999 else 99
        return jsonify({
            "success": True,
            "qty": new_qty,
            "item_total": cart[item_key]["price"] * new_qty,
            "subtotal": subtotal,
            "shipping": shipping,
            "total": subtotal + shipping,
        })
    return jsonify({"error": "Item not found"}), 404


@bp.route("/cart/ajax_remove", methods=["POST"])
def cart_ajax_remove():
    """AJAX: remove item, return new subtotal/total."""
    cart = session.get("cart", {})
    item_key = request.form.get("key", "").strip()
    if item_key in cart:
        cart.pop(item_key)
        session["cart"] = cart
        from helpers import refresh_cart_prices
        _, subtotal = refresh_cart_prices(cart)
        shipping = 0 if subtotal >= 999 else 99
        return jsonify({
            "success": True,
            "subtotal": subtotal,
            "shipping": shipping,
            "total": subtotal + shipping,
            "cart_empty": len(cart) == 0,
        })
    return jsonify({"error": "Item not found"}), 404
