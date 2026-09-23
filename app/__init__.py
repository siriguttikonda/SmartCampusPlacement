from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # Connect database
    db.init_app(app)

    # Import and register routes
    from app.routes.auth import auth_bp
    from app.routes.student import student_bp
    from app.routes.admin import admin_bp
    from app.routes.company import company_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(company_bp)

    @app.route("/")
    def home():
        try:
            with db.engine.connect():
                return "Flask is successfully connected to MySQL!"
        except Exception as e:
            return f"Database connection failed: {str(e)}"

    return app