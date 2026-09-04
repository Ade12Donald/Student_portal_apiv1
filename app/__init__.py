from flask import Flask, jsonify


def create_app():
    app = Flask(__name__)

    from .routes import bp as students_bp
    app.register_blueprint(students_bp)

    @app.route("/")
    def index():
        return jsonify({"status": "Student Portal API is running", "docs": "/api/students"})

    return app
