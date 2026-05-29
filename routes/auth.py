import uuid
import bcrypt
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from extensions import db_sql, limiter
from models import User, UserAddress, Order

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if "user" in session:
        return redirect(url_for("public.index"))
    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not email or not password:
            flash("Email and password are required.", "error")
            return render_template("login.html")
        try:
            user = User.query.filter_by(email=email).first()
        except Exception as e:
            flash(f"Database error: {e}", "error")
            return render_template("login.html")
        if not user or not bcrypt.checkpw(
            password[:72].encode("utf-8"),
            user.password_hash.encode("utf-8")
        ):
            flash("Invalid email or password.", "error")
            return render_template("login.html")
        full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        session["user"] = {
            "id":    str(user.id),
            "name":  full_name,
            "email": user.email,
            "role":  user.role or "customer",
        }
        flash(f"Welcome back, {full_name}!", "success")
        next_url = request.args.get("next") or request.form.get("next")
        if next_url:
            return redirect(next_url)
        if user.role in ("admin", "manager"):
            try:
                return redirect(url_for("admin_dashboard"))
            except Exception:
                return redirect("/admin")
        return redirect(url_for("public.index"))
    return render_template("login.html")


@bp.route("/register", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def register():
    if "user" in session:
        return redirect(url_for("public.index"))
    if request.method == "POST":
        fname    = request.form.get("first_name", "").strip()
        lname    = request.form.get("last_name", "").strip()
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm_password", "")
        name     = f"{fname} {lname}".strip()
        if not all([fname, email, password]):
            flash("All fields are required.", "error")
            return render_template("register.html")
        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template("register.html")
        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("register.html")
        try:
            if User.query.filter_by(email=email).first():
                flash("An account with that email already exists.", "error")
                return render_template("register.html")
            hashed   = bcrypt.hashpw(password[:72].encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            
            new_user = User(
                id=str(uuid.uuid4()),
                first_name=fname,
                last_name=lname,
                email=email,
                password_hash=hashed,
                role="customer"
            )
            db_sql.session.add(new_user)
            db_sql.session.commit()
            
            session["user"] = {
                "id":    str(new_user.id),
                "name":  f"{new_user.first_name} {new_user.last_name or ''}".strip(),
                "email": new_user.email,
                "role":  "customer",
            }
            flash(f"Welcome to Khushi Decors, {name}!", "success")
            return redirect(url_for("public.index"))
        except Exception as e:
            db_sql.session.rollback()
            flash(f"Registration failed: {e}", "error")
    return render_template("register.html")


@bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("public.index"))


@bp.route("/account", methods=["GET", "POST"])
def account():
    if "user" not in session:
        flash("Please log in to continue.", "error")
        return redirect(url_for("auth.login", next=request.url))
    uid = session["user"]["id"]
    if request.method == "POST":
        action = request.form.get("action", "")
        if action == "update_profile":
            fname = request.form.get("first_name", "").strip()
            lname = request.form.get("last_name", "").strip()
            if not fname:
                flash("First name is required.", "error")
            else:
                try:
                    user = User.query.get(uid)
                    if user:
                        user.first_name = fname
                        user.last_name = lname
                        db_sql.session.commit()
                        session["user"]["name"] = f"{fname} {lname}".strip()
                        flash("Profile updated successfully.", "success")
                except Exception as e:
                    db_sql.session.rollback()
                    flash(f"Error updating profile: {e}", "error")
        elif action == "add_address":
            try:
                is_default = request.form.get("is_default") == "on"
                if is_default:
                    UserAddress.query.filter_by(user_id=uid).update({"is_default": 0})
                
                addr = UserAddress(
                    id=str(uuid.uuid4()),
                    user_id=uid,
                    label=request.form.get("label", "Home"),
                    first_name=request.form.get("first_name", ""),
                    last_name=request.form.get("last_name", ""),
                    phone=request.form.get("phone", ""),
                    address_line1=request.form.get("address_line1", ""),
                    address_line2=request.form.get("address_line2", ""),
                    city=request.form.get("city", ""),
                    state=request.form.get("state", ""),
                    pincode=request.form.get("pincode", ""),
                    country=request.form.get("country", "India"),
                    is_default=1 if is_default else 0
                )
                db_sql.session.add(addr)
                db_sql.session.commit()
                flash("Address added successfully.", "success")
            except Exception as e:
                db_sql.session.rollback()
                flash(f"Error saving address: {e}", "error")
        return redirect(url_for("auth.account"))
    try:
        user = User.query.get(uid)
        addresses = UserAddress.query.filter_by(user_id=uid).order_by(UserAddress.is_default.desc(), UserAddress.created_at.desc()).all()
        orders = Order.query.filter_by(user_id=uid).order_by(Order.created_at.desc()).all()
    except Exception as e:
        user = None
        addresses = []
        orders = []
        flash(f"Error loading account data: {e}", "error")
    return render_template("account.html", user=user, addresses=addresses, orders=orders)


@bp.route("/account/address/<addr_id>/delete", methods=["POST"])
def account_address_delete(addr_id):
    if "user" not in session:
        return redirect(url_for("auth.login"))
    try:
        addr = UserAddress.query.filter_by(id=addr_id, user_id=session["user"]["id"]).first()
        if addr:
            db_sql.session.delete(addr)
            db_sql.session.commit()
            flash("Address removed.", "success")
    except Exception as e:
        db_sql.session.rollback()
        flash(f"Error deleting address: {e}", "error")
    return redirect(url_for("auth.account"))


@bp.route("/account/address/<addr_id>/default", methods=["POST"])
def account_address_default(addr_id):
    if "user" not in session:
        return redirect(url_for("auth.login"))
    uid = session["user"]["id"]
    try:
        UserAddress.query.filter_by(user_id=uid).update({"is_default": 0})
        addr = UserAddress.query.filter_by(id=addr_id, user_id=uid).first()
        if addr:
            addr.is_default = 1
            db_sql.session.commit()
            flash("Default address updated.", "success")
    except Exception as e:
        db_sql.session.rollback()
        flash(f"Error updating default address: {e}", "error")
    return redirect(url_for("auth.account"))
