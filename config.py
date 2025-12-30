import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


# ─────────────────────────────────────────────────────────────
# Database configuration (SQLite fallback + PostgreSQL support)
# ─────────────────────────────────────────────────────────────
database_url = os.environ.get("DATABASE_URL")

# Fix for Render / SQLAlchemy incompatibility
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'some-secret-key-here')

    SQLALCHEMY_DATABASE_URI = database_url or \
        f"sqlite:///{os.path.join(basedir, 'instance', 'order_management.db')}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SEED_DEFAULT_DATA = os.environ.get(
        'SEED_DEFAULT_DATA', 'false'
    ).strip().lower() == 'true'

    # ================= M-PESA (SANDBOX) =================
    MPESA_ENV = os.environ.get("MPESA_ENV", "sandbox")

    MPESA_CONSUMER_KEY = os.environ.get("MPESA_CONSUMER_KEY")
    MPESA_CONSUMER_SECRET = os.environ.get("MPESA_CONSUMER_SECRET")

    MPESA_SHORTCODE = os.environ.get("MPESA_SHORTCODE", "174379")
    MPESA_PASSKEY = os.environ.get(
        "MPESA_PASSKEY",
        "bfb279f9aa9bdbcf158e97dd71a467cd1e89..."
    )

    MPESA_CALLBACK_URL = os.environ.get("MPESA_CALLBACK_URL")
    MPESA_TEST_PHONE = os.environ.get("MPESA_TEST_PHONE", "254729177471")
    # ====================================================


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig
}
