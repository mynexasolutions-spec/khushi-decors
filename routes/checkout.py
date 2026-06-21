import uuid
import json
import razorpay
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, abort
from extensions import db_sql, csrf
from sqlalchemy import and_, func
from helpers import get_cached_store_settings, refresh_cart_prices, calc_shipping
from models import (
    Coupon, CouponUsage, UserAddress, Order, OrderItem,
    Product, ProductReview, ProductImage, Media
)

bp = Blueprint("checkout", __name__)

ALLOWED_PAYMENT_METHODS = {"cod", "razorpay"}


# ── Coupon validation ──────────────────────────────────────────────────────────

def _validate_coupon(code, user_id, subtotal):
    """Returns (coupon_dict, discount_amount, error_message)."""
    code = (code or "").strip().upper()
    if not code:
        return None, 0.0, "Please enter a coupon code."

    try:
        from sqlalchemy import func
        coupon = Coupon.query.filter(func.upper(Coupon.code) == code, Coupon.is_active == 1).first()
        if not coupon:
            return None, 0.0, "Invalid or inactive coupon code."

        if coupon.expires_at and coupon.expires_at < datetime.now():
            return None, 0.0, "This coupon has expired."

        min_order = float(coupon.min_order_amount or coupon.min_order or 0)
        if subtotal < min_order:
            return None, 0.0, f"Minimum order amount of ₹{min_order:.0f} required for this coupon."

        if coupon.usage_limit:
            count = CouponUsage.query.filter_by(coupon_id=coupon.id).count()
            if count >= coupon.usage_limit:
                return None, 0.0, "This coupon has reached its usage limit."

        if user_id and coupon.usage_limit_per_user:
            count = CouponUsage.query.filter_by(coupon_id=coupon.id, user_id=user_id).count()
            if count >= coupon.usage_limit_per_user:
                return None, 0.0, "You have already used this coupon."

        value = float(coupon.value or 0)
        if coupon.type == "percentage" or coupon.type == "percent":
            discount = subtotal * (value / 100)
            if coupon.max_discount:
                discount = min(discount, float(coupon.max_discount))
        else:
            discount = min(value, subtotal)

        # Convert ORM object to a dict for template/response compatibility
        coupon_dict = {
            "id": coupon.id,
            "code": coupon.code,
            "type": coupon.type,
            "value": coupon.value,
            "min_order_amount": coupon.min_order_amount,
            "usage_limit": coupon.usage_limit,
            "usage_limit_per_user": coupon.usage_limit_per_user
        }
        return coupon_dict, round(discount, 2), None
    except Exception as e:
        return None, 0.0, f"Error validating coupon: {e}"


# ── Apply-coupon AJAX endpoint ─────────────────────────────────────────────────

@csrf.exempt
@bp.route("/apply_coupon", methods=["POST"])
def apply_coupon():
    if "user" not in session:
        return jsonify({"valid": False, "error": "Login required."}), 401

    data     = request.get_json(silent=True) or {}
    code     = (data.get("coupon_code") or data.get("code") or "").strip()
    subtotal = float(data.get("subtotal") or 0)
    uid      = session["user"]["id"]

    coupon, discount, error = _validate_coupon(code, uid, subtotal)
    if error:
        return jsonify({"valid": False, "error": error})

    shipping  = calc_shipping(subtotal)
    new_total = round(max(0.0, subtotal + shipping - discount), 2)

    return jsonify({
        "valid":           True,
        "discount_amount": discount,
        "new_total":       new_total,
        "message":         f"Coupon applied! You save ₹{discount:.0f}.",
    })


# ── Razorpay order creation ────────────────────────────────────────────────────

@csrf.exempt
@bp.route("/razorpay/create_order", methods=["POST"])
def rzp_create_order():
    if "user" not in session:
        return jsonify({"success": False, "message": "Login required."}), 401

    settings   = get_cached_store_settings()
    key_id     = settings.get("razorpay_key_id", "").strip()
    key_secret = settings.get("razorpay_key_secret", "").strip()

    if settings.get("online_payment_enabled", "false") != "true":
        return jsonify({"success": False, "message": "Online payment is not enabled."}), 403
    if not key_id or not key_secret:
        return jsonify({"success": False, "message": "Razorpay is not configured."}), 400

    cart = session.get("cart", {})
    if not cart:
        return jsonify({"success": False, "message": "Cart is empty."}), 400

    try:
        data        = request.get_json(silent=True) or {}
        coupon_code = (data.get("coupon_code") or "").strip()

        cart, subtotal = refresh_cart_prices(cart)
        session["cart"] = cart

        discount = 0.0
        if coupon_code:
            uid = session["user"]["id"]
            _, discount, _ = _validate_coupon(coupon_code, uid, subtotal)

        shipping     = calc_shipping(subtotal, settings)
        amount_total = max(0.0, subtotal + shipping - discount)
        amount_paisa = int(round(amount_total * 100))

        client = razorpay.Client(auth=(key_id, key_secret))
        order  = client.order.create({
            "amount":          amount_paisa,
            "currency":        "INR",
            "payment_capture": 1,
        })
        return jsonify({"success": True, "order": order})
    except razorpay.errors.BadRequestError as e:
        return jsonify({"success": False, "message": f"Razorpay error: {e}"}), 400
    except Exception:
        return jsonify({"success": False, "message": "Could not create payment order. Please try again."}), 500


# ── Main checkout ──────────────────────────────────────────────────────────────

@bp.route("/checkout", methods=["GET", "POST"])
def checkout():
    if "user" not in session:
        flash("Please log in to continue.", "error")
        return redirect(url_for("auth.login", next=request.url))
    cart = session.get("cart", {})
    if not cart:
        flash("Your cart is empty.", "error")
        return redirect(url_for("cart.view_cart"))

    uid            = session["user"]["id"]
    cart, subtotal = refresh_cart_prices(cart)
    session["cart"] = cart

    settings       = get_cached_store_settings()
    shipping       = calc_shipping(subtotal, settings)
    cod_enabled    = settings.get("cod_enabled", "true") == "true"
    online_enabled = settings.get("online_payment_enabled", "false") == "true"

    try:
        addresses = UserAddress.query.filter_by(user_id=uid).order_by(UserAddress.is_default.desc(), UserAddress.created_at.desc()).all()
    except Exception:
        addresses = []

    if request.method == "POST":
        payment_method = request.form.get("payment_method", "").strip()
        coupon_code    = request.form.get("coupon_code", "").strip().upper()
        notes          = request.form.get("notes", "").strip()
        save_address   = request.form.get("save_address") == "on"
        saved_address_id = request.form.get("saved_address_id", "").strip()
        addr_first     = request.form.get("addr_first_name", "").strip()
        addr_last      = request.form.get("addr_last_name", "").strip()
        addr_phone     = request.form.get("addr_phone", "").strip()
        addr_line1     = request.form.get("addr_line1", "").strip()
        addr_line2     = request.form.get("addr_line2", "").strip()
        addr_city      = request.form.get("addr_city", "").strip()
        addr_state     = request.form.get("addr_state", "").strip()
        addr_pin       = request.form.get("addr_pincode", "").strip()
        addr_country   = request.form.get("addr_country", "India").strip()

        if payment_method not in ALLOWED_PAYMENT_METHODS:
            flash("Invalid payment method.", "error")
            return redirect(url_for("checkout.checkout"))

        razorpay_key_id     = settings.get("razorpay_key_id", "").strip()
        razorpay_key_secret = settings.get("razorpay_key_secret", "").strip()
        razorpay_ready      = online_enabled and bool(razorpay_key_id) and bool(razorpay_key_secret)

        if payment_method == "cod" and not cod_enabled:
            flash("Cash on Delivery is not available.", "error")
            return redirect(url_for("checkout.checkout"))
        if payment_method == "razorpay" and not razorpay_ready:
            flash("Online payment is not available at this time.", "error")
            return redirect(url_for("checkout.checkout"))

        shipping_addr = None
        if saved_address_id:
            addr_obj = UserAddress.query.filter_by(id=saved_address_id, user_id=uid).first()
            if not addr_obj:
                flash("Selected address could not be found. Please choose it again.", "error")
                return redirect(url_for("checkout.checkout"))
            shipping_addr = {
                "first_name": addr_obj.first_name,
                "last_name": addr_obj.last_name,
                "phone": addr_obj.phone,
                "address_line1": addr_obj.address_line1,
                "address_line2": addr_obj.address_line2,
                "city": addr_obj.city,
                "state": addr_obj.state,
                "pincode": addr_obj.pincode,
                "country": addr_obj.country
            }
            addr_first   = addr_obj.first_name
            addr_last    = addr_obj.last_name
            addr_phone   = addr_obj.phone
            addr_line1   = addr_obj.address_line1
            addr_line2   = addr_obj.address_line2
            addr_city    = addr_obj.city
            addr_state   = addr_obj.state
            addr_pin     = addr_obj.pincode
            addr_country = addr_obj.country

        if not addr_line1 or not addr_city or not addr_pin or not addr_phone:
            flash("Please fill in all required address fields.", "error")
            return render_template(
                "checkout.html",
                cart=cart, subtotal=subtotal, shipping=shipping, total=subtotal + shipping,
                settings=settings, cod_enabled=cod_enabled, online_enabled=online_enabled,
                addresses=addresses,
                free_shipping_threshold=float(settings.get("free_shipping_threshold") or 599),
                free_shipping_enabled=settings.get("free_shipping_enabled", "true") == "true",
                free_shipping_all=settings.get("free_shipping_all") == "true",
            )

        coupon          = None
        discount_amount = 0.0
        if coupon_code:
            coupon, discount_amount, coupon_error = _validate_coupon(coupon_code, uid, subtotal)
            if coupon_error:
                flash(f"Coupon: {coupon_error}", "error")
                coupon_code     = ""
                discount_amount = 0.0

        total = max(0.0, subtotal + shipping - discount_amount)

        payment_status = "pending"
        if payment_method == "razorpay":
            rzp_payment_id = request.form.get("razorpay_payment_id", "").strip()
            rzp_order_id   = request.form.get("razorpay_order_id", "").strip()
            rzp_signature  = request.form.get("razorpay_signature", "").strip()
            if not rzp_payment_id or not rzp_order_id or not rzp_signature:
                flash("Payment information is incomplete. Please try again.", "error")
                return redirect(url_for("checkout.checkout"))
            try:
                client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))
                client.utility.verify_payment_signature({
                    "razorpay_order_id":   rzp_order_id,
                    "razorpay_payment_id": rzp_payment_id,
                    "razorpay_signature":  rzp_signature,
                })
                payment_status = "paid"
            except razorpay.errors.SignatureVerificationError:
                flash("Payment signature verification failed. Please contact support if your money was deducted.", "error")
                return redirect(url_for("checkout.checkout"))
            except Exception:
                flash("Payment verification failed. Please contact support if your money was deducted.", "error")
                return redirect(url_for("checkout.checkout"))

        shipping_addr = shipping_addr or {
            "first_name": addr_first, "last_name": addr_last, "phone": addr_phone,
            "address_line1": addr_line1, "address_line2": addr_line2,
            "city": addr_city, "state": addr_state, "pincode": addr_pin, "country": addr_country,
        }
        customer_name  = session["user"].get("name", f"{addr_first} {addr_last}").strip()
        customer_email = session["user"].get("email", "")

        try:
            order_id     = str(uuid.uuid4())
            order_number = f"ORD-{uuid.uuid4().hex[:12].upper()}"
            
            new_order = Order(
                id=order_id,
                order_number=order_number,
                user_id=uid,
                subtotal=subtotal,
                shipping_amount=shipping,
                total_amount=total,
                status='pending',
                payment_method=payment_method,
                payment_status=payment_status,
                shipping_address_json=json.dumps(shipping_addr),
                customer_name=customer_name,
                customer_email=customer_email,
                customer_phone=addr_phone,
                notes=notes,
                coupon_code=coupon_code or "",
                discount_amount=discount_amount
            )
            db_sql.session.add(new_order)

            for item_key, item in cart.items():
                unit_price = float(item.get("price", 0))
                qty        = int(item.get("qty", 1))
                pid        = item.get("product_id")
                vid        = item.get("variation_id")

                # Update stock
                p = Product.query.get(pid)
                if p:
                    p.stock_quantity = max(0, (p.stock_quantity or 0) - qty)
                    if p.stock_quantity <= 0:
                        p.stock_status = 'out_of_stock'

                new_item = OrderItem(
                    id=str(uuid.uuid4()),
                    order_id=order_id,
                    product_id=pid,
                    variation_id=vid or None,
                    quantity=qty,
                    unit_price=unit_price,
                    total_price=unit_price * qty,
                    product_name_snapshot=item.get("name", "")
                )
                db_sql.session.add(new_item)

            if coupon:
                usage = CouponUsage(
                    id=str(uuid.uuid4()),
                    coupon_id=coupon["id"],
                    user_id=uid,
                    order_id=order_id
                )
                db_sql.session.add(usage)

            if save_address:
                try:
                    is_default = len(addresses) == 0
                    if is_default:
                        UserAddress.query.filter_by(user_id=uid).update({"is_default": 0})
                    
                    new_addr = UserAddress(
                        id=str(uuid.uuid4()),
                        user_id=uid,
                        label='Home',
                        first_name=addr_first,
                        last_name=addr_last,
                        phone=addr_phone,
                        address_line1=addr_line1,
                        address_line2=addr_line2,
                        city=addr_city,
                        state=addr_state,
                        pincode=addr_pin,
                        country=addr_country,
                        is_default=1 if is_default else 0
                    )
                    db_sql.session.add(new_addr)
                except Exception:
                    pass

            db_sql.session.commit()
            session.pop("cart", None)
            flash("Order placed successfully!", "success")
            return redirect(url_for("checkout.order_success", order_id=order_id))
        except Exception as e:
            db_sql.session.rollback()
            flash(f"Error placing order: {e}", "error")

    total = subtotal + shipping
    return render_template(
        "checkout.html",
        cart=cart, subtotal=subtotal, shipping=shipping, total=total,
        settings=settings, cod_enabled=cod_enabled, online_enabled=online_enabled,
        addresses=addresses,
        free_shipping_threshold=float(settings.get("free_shipping_threshold") or 599),
        free_shipping_enabled=settings.get("free_shipping_enabled", "true") == "true",
        free_shipping_all=settings.get("free_shipping_all") == "true",
    )


# ── Order success ──────────────────────────────────────────────────────────────

@bp.route("/order/<order_id>/success")
def order_success(order_id):
    if "user" not in session:
        return redirect(url_for("auth.login"))
    uid = session["user"]["id"]
    try:
        order = Order.query.filter_by(id=order_id, user_id=uid).first()
        if not order:
            abort(404)
            
        items_rows = (db_sql.session.query(OrderItem, Product.name.label("product_name"), Media.file_url.label("image_url"))
                      .outerjoin(Product, Product.id == OrderItem.product_id)
                      .outerjoin(ProductImage, and_(ProductImage.product_id == OrderItem.product_id, ProductImage.is_primary == 1))
                      .outerjoin(Media, Media.id == ProductImage.media_id)
                      .filter(OrderItem.order_id == order_id)
                      .all())
        
        items = []
        for oi, p_name, img_url in items_rows:
            items.append({
                "id": oi.id,
                "order_id": oi.order_id,
                "product_id": oi.product_id,
                "quantity": oi.quantity,
                "unit_price": oi.unit_price,
                "total_price": oi.total_price,
                "product_name": p_name or oi.product_name_snapshot,
                "image_url": img_url
            })
            
        shipping_address = {}
        if order.shipping_address_json:
            try:
                shipping_address = json.loads(order.shipping_address_json)
            except Exception:
                pass
    except Exception as e:
        flash(f"Error loading order: {e}", "error")
        return redirect(url_for("auth.account"))
    return render_template("order_success.html", order=order, items=items, shipping_address=shipping_address)


@bp.route("/order/<order_id>")
def order_detail(order_id):
    if "user" not in session:
        return redirect(url_for("auth.login"))
    uid = session["user"]["id"]
    try:
        order = Order.query.filter_by(id=order_id, user_id=uid).first()
        if not order:
            abort(404)
        items = OrderItem.query.filter_by(order_id=order_id).all()
    except Exception as e:
        flash(f"Error fetching order: {e}", "error")
        return redirect(url_for("auth.account"))
    return render_template("order_detail.html", order=order, items=items)


@bp.route("/order/<order_id>/cancel", methods=["POST"])
def order_cancel(order_id):
    if "user" not in session:
        return redirect(url_for("auth.login"))
    uid = session["user"]["id"]
    try:
        order = Order.query.filter_by(id=order_id, user_id=uid).first()
        if not order:
            abort(404)
        if order.status in ("shipped", "delivered", "cancelled", "refunded"):
            flash("This order can no longer be cancelled.", "error")
            return redirect(url_for("checkout.order_detail", order_id=order_id))

        cancel_reason       = (request.form.get("cancel_reason") or "").strip()
        cancel_reason_other = (request.form.get("cancel_reason_other") or "").strip()
        if not cancel_reason:
            flash("Please select a cancellation reason.", "error")
            return redirect(url_for("checkout.order_detail", order_id=order_id))
        if cancel_reason == "Other":
            if not cancel_reason_other:
                flash("Please enter the cancellation reason details.", "error")
                return redirect(url_for("checkout.order_detail", order_id=order_id))
            cancel_reason = f"Other: {cancel_reason_other}"

        items = OrderItem.query.filter_by(order_id=order_id).all()
        for item in items:
            p = Product.query.get(item.product_id)
            if p:
                p.stock_quantity = (p.stock_quantity or 0) + (item.quantity or 0)
                p.stock_status = 'in_stock'
                
        order.status = 'cancelled'
        order.payment_status = 'cancelled'
        order.cancelled_at = datetime.utcnow()
        order.cancel_reason = cancel_reason
        
        db_sql.session.commit()
        flash("Order cancelled successfully.", "success")
    except Exception as e:
        db_sql.session.rollback()
        flash(f"Error cancelling order: {e}", "error")
    return redirect(url_for("checkout.order_detail", order_id=order_id))


@bp.route("/product/<product_id>/review", methods=["POST"])
def submit_review(product_id):
    if "user" not in session:
        return redirect(url_for("auth.login"))
    uid = session["user"]["id"]
    try:
        rating_str = request.form.get("rating", "").strip()
        comment    = request.form.get("comment", "").strip()
        if not rating_str or not rating_str.isdigit():
            flash("Please select a star rating.", "error")
            return redirect(url_for("public.product_detail", product_id=product_id))
        rating = int(rating_str)
        if not (1 <= rating <= 5):
            flash("Rating must be between 1 and 5.", "error")
            return redirect(url_for("public.product_detail", product_id=product_id))
        if len(comment) < 10:
            flash("Review must be at least 10 characters long.", "error")
            return redirect(url_for("public.product_detail", product_id=product_id))
            
        existing_review = ProductReview.query.filter_by(product_id=product_id, user_id=uid).first()
        if existing_review:
            flash("You have already submitted a review for this product.", "info")
            return redirect(url_for("public.product_detail", product_id=product_id))
            
        review = ProductReview(
            id=str(uuid.uuid4()),
            product_id=product_id,
            user_id=uid,
            rating=rating,
            body=comment,
            is_approved=1
        )
        db_sql.session.add(review)
        db_sql.session.commit()
        flash("Thank you! Your review has been submitted.", "success")
    except Exception as e:
        db_sql.session.rollback()
        flash(f"Error submitting review: {e}", "error")
    return redirect(url_for("public.product_detail", product_id=product_id))
