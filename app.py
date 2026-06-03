"""
app.py — Application factory for Khushi Decors.
"""
import os
from flask import Flask, render_template, session
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from extensions import csrf, limiter, handle_csrf_error
from extensions import db_sql, migrate as db_migrate
from helpers import register_jinja
import db


def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY", "dev-key-change-in-production")
    
    # Payload limit: 16MB
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    
    # Production flag
    app.config['PRODUCTION'] = os.getenv("PRODUCTION", "False").lower() == "true"
    
    # SQLAlchemy
    db_url = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    engine_options = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
    if db_url and not db_url.startswith("sqlite"):
        engine_options["connect_args"] = {"connect_timeout": 15}
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = engine_options
    
    db_sql.init_app(app)
    db_migrate.init_app(app, db_sql)
    
    # Session configuration
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = os.getenv("SESSION_COOKIE_SECURE", "False").lower() == "true"
    app.config["PERMANENT_SESSION_LIFETIME"] = 86400
    
    # CSRF configuration
    app.config["WTF_CSRF_TIME_LIMIT"] = None
    app.config["WTF_CSRF_CHECK_DEFAULT"] = True
    
    # Initialize extensions
    csrf.init_app(app)
    limiter.init_app(app)
    
    # Register CSRF error handler
    app.register_error_handler(400, handle_csrf_error)
    
    # Register Jinja2 helpers and globals
    register_jinja(app)
    
    # Session initialization - ensure session exists for CSRF token
    @app.before_request
    def ensure_session():
        session.setdefault('_csrf_initialized', True)

    @app.context_processor
    def inject_globals():
        cart  = session.get("cart", {})
        count = sum(item.get("qty", 0) for item in cart.values())
        return {"cart_count": count, "current_user": session.get("user")}

    # Blueprints
    from routes.public   import bp as public_bp
    from routes.auth     import bp as auth_bp
    from routes.cart     import bp as cart_bp
    from routes.checkout import bp as checkout_bp
    from routes.blog     import bp as blog_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(checkout_bp)
    app.register_blueprint(blog_bp)

    # Admin routes (plain endpoint names — no blueprint prefix needed)
    from routes.admin import register as reg_admin
    reg_admin(app)

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    return app


app = create_app()

import os as _os
# Only run setup in the main process (not the watchdog reloader child).
if _os.environ.get("WERKZEUG_RUN_MAIN") != "true":
    with app.app_context():
        # Quick check: only migrate if the users table doesn't exist yet
        try:
            from sqlalchemy import inspect
            inspector = inspect(db_sql.engine)
            if not inspector.has_table("users"):
                db.migrate()
        except Exception:
            # If connection fails, try migrate anyway (fresh database)
            try:
                db.migrate()
            except Exception:
                pass

        # ── Auto-create default admin if none exists ──
        try:
            from models import User
            if not User.query.filter_by(role='admin').first():
                import uuid, bcrypt
                pw = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode()
                admin_user = User(
                    id=str(uuid.uuid4()),
                    first_name="Admin",
                    last_name="User",
                    email="admin@khushidecors.com",
                    password_hash=pw.decode() if isinstance(pw, bytes) else pw,
                    role="admin"
                )
                db_sql.session.add(admin_user)
                db_sql.session.commit()
        except Exception:
            pass

if __name__ == "__main__":
    port  = int(os.getenv("PORT", 5001))
    debug = os.getenv("FLASK_ENV", "development") != "production"
    app.run(debug=debug, port=port, host="0.0.0.0")
# Triggering auto-reload for template and CSS changes - v3.4
