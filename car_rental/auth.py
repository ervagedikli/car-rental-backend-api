from functools import wraps

from flask import jsonify, request
from werkzeug.security import check_password_hash

from .models import User


def require_auth(role=None):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            auth = request.authorization
            if not auth or not auth.username or not auth.password:
                return jsonify({"message": "Authentication required"}), 401

            user = User.query.filter_by(username=auth.username).first()
            if not user or not check_password_hash(user.password, auth.password):
                return jsonify({"message": "Invalid credentials"}), 401

            if role and user.role != role:
                return jsonify({"message": "Unauthorized role"}), 403

            return view(user, *args, **kwargs)

        return wrapped

    return decorator
