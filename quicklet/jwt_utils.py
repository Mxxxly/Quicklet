import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app


print("jwt_utils loaded")

def generate_jwt(user):
    payload = {
        "user_id": user.id,
        "email": user.email,
        "exp": datetime.utcnow() + timedelta(
            minutes=current_app.config["JWT_EXPIRES_MINUTES"]
        )
    }

    return jwt.encode(
        payload,
        current_app.config["JWT_SECRET"],
        algorithm=current_app.config["JWT_ALGORITHM"]
    )


def jwt_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization")

        if not auth or not auth.startswith("Bearer "):
            return jsonify({"error": "Token required"}), 401

        token = auth.split(" ")[1]

        try:
            payload = jwt.decode(
                token,
                current_app.config["JWT_SECRET"],
                algorithms=[current_app.config["JWT_ALGORITHM"]]
            )
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        request.current_user = payload
        return f(*args, **kwargs)

    return wrapper
