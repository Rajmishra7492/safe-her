from datetime import datetime

import bcrypt
from flask import Blueprint, current_app, jsonify, request

from utils.auth import generate_jwt

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True)
    if data is None:
        # Fallback for incorrect/missing Content-Type where body is form-encoded.
        data = request.form.to_dict() if request.form else {}

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    role = data.get("role", "user").strip().lower()
    if role not in ["user", "admin"]:
        role = "user"
    is_admin = role == "admin"

    if not name or not email or not password:
        return jsonify({"error": "Name, email and password are required"}), 400

    db = current_app.config["db"]
    if db.users.find_one({"email": email}):
        return jsonify({"error": "Email already exists"}), 409

    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    result = db.users.insert_one(
        {
            "name": name,
            "email": email,
            "password": hashed,
            "is_admin": is_admin,
            "role": role,
            "created_at": datetime.utcnow(),
        }
    )

    token = generate_jwt(result.inserted_id, current_app.config["JWT_SECRET"], current_app.config["JWT_EXPIRES_HOURS"])

    return jsonify(
        {
            "message": "Registration successful",
            "token": token,
            "user": {"id": str(result.inserted_id), "name": name, "email": email, "is_admin": is_admin, "role": role},
        }
    ), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)
    if data is None:
        data = request.form.to_dict() if request.form else {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    db = current_app.config["db"]
    user = db.users.find_one({"email": email})

    if not user or not bcrypt.checkpw(password.encode("utf-8"), user["password"]):
        return jsonify({"error": "Invalid credentials"}), 401

    token = generate_jwt(user["_id"], current_app.config["JWT_SECRET"], current_app.config["JWT_EXPIRES_HOURS"])

    return jsonify(
        {
            "message": "Login successful",
            "token": token,
            "user": {
                "id": str(user["_id"]),
                "name": user.get("name"),
                "email": user.get("email"),
                "is_admin": user.get("is_admin", False),
                "role": user.get("role", "admin" if user.get("is_admin", False) else "user"),
            },
        }
    )
