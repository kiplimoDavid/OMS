import os
from app import create_app, db
from app.default_data import create_default_records

# Create the Flask app instance
app = create_app()

def should_seed_data():
    """
    Determines whether to seed data based on environment variable.
    """
    return os.getenv("SEED_DEFAULT_DATA", "false").strip().lower() == "true"

def is_original_process():
    """
    Werkzeug reloader spawns a secondary process; only seed on original.
    """
    return os.environ.get('WERKZEUG_RUN_MAIN') is None

if __name__ == '__main__':
    # Ensure logic only runs in main process
    if is_original_process():
        print("📦 Initializing application context...")
        with app.app_context():
            print("🧱 Ensuring all database tables exist...")
            db.create_all()

            if should_seed_data():
                print("⚙️ Seeding default data...")
                create_default_records(app)
            else:
                print("⚠️ Skipping default data seeding (SEED_DEFAULT_DATA is false or missing)")

    # Start Flask server
    flask_env = os.getenv("FLASK_ENV", "development")
    is_debug = flask_env != "production"

    print(f"\n🚀 Starting Flask server [ENV: {flask_env}]...")

    # You can adjust host/port here if needed
    app.run(debug=is_debug, host="0.0.0.0", port=5000)
