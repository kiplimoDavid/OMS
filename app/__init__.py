import os
from flask import Flask
from config import Config, config
from app.utils.filters import chunk_list
from app.context_processors import inject_cart_item_count
from app.extensions import db, migrate, login_manager, csrf  # ← Centralized extensions

# ─── Custom Jinja2 Filters ─────────────────────────────────────────────────
import locale

# Function to format numbers as currency
def currency_format(value):
    try:
        # Set the locale to use the user's default currency formatting
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')  # or other locales
        return locale.currency(value, grouping=True)
    except Exception as e:
        return f"${value:.2f}"  # Fallback to simple format if the locale fails


def format_currency(value):
    """Format value as USD currency."""
    try:
        return f"${value:,.2f}"
    except (TypeError, ValueError):
        return value

# ─── Application Factory ──────────────────────────────────────────────────────
def create_app(config_class=Config):
    app = Flask(__name__)

    # Ensure instance folder exists (required for SQLite on Render)
    os.makedirs(os.path.join(app.root_path, 'instance'), exist_ok=True)


    env = os.getenv("FLASK_ENV", "development")
    app.config.from_object(config[env])

    # ─── Session Configuration ────────────────────────────────────────────────
    app.config.update(
        SESSION_COOKIE_SECURE=False,  # Set to True in production with HTTPS
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
    )

    # ─── Initialize Extensions ────────────────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # ─── Login Manager Configuration ──────────────────────────────────────────
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    login_manager.session_protection = "strong"

    # ─── Jinja2 Filters ───────────────────────────────────────────────────────
    app.jinja_env.filters['format_currency'] = format_currency
    app.jinja_env.filters['chunk'] = chunk_list

    # ─── Register Context Processor ───────────────────────────────────────────
    app.context_processor(inject_cart_item_count)

    # ─── Register Blueprints ──────────────────────────────────────────────────
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.customers import bp as customers_bp
    app.register_blueprint(customers_bp, url_prefix='/customers')

    from app.cart import bp as cart_bp
    app.register_blueprint(cart_bp, url_prefix='/view_cart')

    from app.products import bp as products_bp
    app.register_blueprint(products_bp, url_prefix='/products')

    from app.orders import bp as orders_bp
    app.register_blueprint(orders_bp, url_prefix='/orders')

    from app.reports import bp as reports_bp
    app.register_blueprint(reports_bp, url_prefix='/reports')

    from app.search import bp as search_bp
    app.register_blueprint(search_bp, url_prefix='/search')

    from app.account.routes import bp as account_bp
    app.register_blueprint(account_bp, url_prefix='/account')

    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from app.customer import bp as customer_bp
    app.register_blueprint(customer_bp, url_prefix='/customer')
    
    from app.support.routes import bp as support_bp
    app.register_blueprint(support_bp, url_prefix='/support')


    # ─── M-PESA Payments ─────────────────────────────────────────────────────
    from app.mpesa.routes import bp
    app.register_blueprint(bp)

    from app.mpesa.routes import bp
    app.register_blueprint(payments_bp)

    

    # ─── Import Models ────────────────────────────────────────────────────────
    from app import models  # Ensure models are discovered by Flask-Migrate

    return app


