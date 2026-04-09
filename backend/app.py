import os

from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from models.db import MongoDB
from routes.auth_routes import auth_bp
from routes.main_routes import main_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["UPLOAD_DIR"] = os.path.join(os.path.dirname(__file__), "static", "uploads")
    os.makedirs(app.config["UPLOAD_DIR"], exist_ok=True)
    CORS(app)

    db = MongoDB(app.config["MONGO_URI"])
    app.config["db"] = db

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    @app.route("/", methods=["GET"])
    def home():
        return jsonify({"message": "Women Safety API is running"})

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(host="0.0.0.0", port=5000, debug=True)
