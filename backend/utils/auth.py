import datetime
import functools

import jwt
from flask import current_app, jsonify, request


def generate_jwt(user_id, secret, expires_hours=24):
    payload = {
        "user_id": str(user_id),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=expires_hours),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def token_required(secret=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return jsonify({"error": "Missing or invalid token header"}), 401

            token = auth_header.split(" ", 1)[1].strip()
            try:
                jwt_secret = secret or current_app.config.get("JWT_SECRET")
                data = jwt.decode(token, jwt_secret, algorithms=["HS256"])
                request.user_id = data.get("user_id")
            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Token expired"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"error": "Invalid token"}), 401

            return func(*args, **kwargs)

        return wrapper

    return decorator
