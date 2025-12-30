import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'some-secret-key-here')

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f"sqlite:///{os.path.join(basedir, 'instance', 'order_management.db')}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SEED_DEFAULT_DATA = os.environ.get('SEED_DEFAULT_DATA', 'false').lower() == 'true'


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
