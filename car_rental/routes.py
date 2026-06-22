from datetime import datetime, timezone
from decimal import Decimal

from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from .auth import require_auth
from .extensions import db
from .models import Car, Rental, User


api = Blueprint("api", __name__)

VALID_ROLES = {"merchant", "user"}
VALID_CAR_STATUSES = {"available", "rented"}


def parse_datetime(value, field_name):
    if not value:
        raise ValueError(f"{field_name} is required")

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field_name} must be ISO format, example: 2026-06-20T10:00:00Z") from exc


def utc_now():
    return datetime.now(timezone.utc)


def normalize_datetime(value):
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def calculate_fee(rental, returned_at):
    start_date = normalize_datetime(rental.start_date)
    returned_at = normalize_datetime(returned_at)
    seconds = max((returned_at - start_date).total_seconds(), 0)
    days = max(1, int((seconds + 86399) // 86400))
    return Decimal(days) * rental.car.daily_price


@api.get("/health")
def health():
    return jsonify({"status": "ok"}), 200


@api.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")
    role = data.get("role")

    if not username or not password or not role:
        return jsonify({"message": "username, password and role are required"}), 400

    if role not in VALID_ROLES:
        return jsonify({"message": "role must be merchant or user"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"message": "Username already exists"}), 409

    user = User(username=username, password=generate_password_hash(password), role=role)
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User created successfully", "user": user.to_dict()}), 201


@api.post("/login")
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return jsonify({"message": "Authentication required"}), 401

    user = User.query.filter_by(username=auth.username).first()
    if not user or not check_password_hash(user.password, auth.password):
        return jsonify({"message": "Invalid credentials"}), 401

    return jsonify({"message": "Login successful", "user": user.to_dict()}), 200


@api.post("/cars")
@require_auth(role="merchant")
def create_car(current_user):
    data = request.get_json(silent=True) or {}
    required_fields = ("brand", "model")
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return jsonify({"message": f"Missing fields: {', '.join(missing_fields)}"}), 400

    car = Car(
        merchant_id=current_user.id,
        brand=data["brand"],
        model=data["model"],
        year=data.get("year"),
        color=data.get("color"),
        daily_price=Decimal(str(data.get("daily_price", 0))),
    )
    db.session.add(car)
    db.session.commit()

    return jsonify({"message": "Car created successfully", "car": car.to_dict()}), 201


@api.get("/cars")
def list_cars():
    query = Car.query

    brand = request.args.get("brand")
    model = request.args.get("model")
    status = request.args.get("status")
    min_year = request.args.get("min_year", type=int)
    max_year = request.args.get("max_year", type=int)

    if brand:
        query = query.filter(Car.brand.ilike(f"%{brand}%"))
    if model:
        query = query.filter(Car.model.ilike(f"%{model}%"))
    if status:
        query = query.filter_by(status=status)
    if min_year:
        query = query.filter(Car.year >= min_year)
    if max_year:
        query = query.filter(Car.year <= max_year)

    cars = query.order_by(Car.id.desc()).all()
    return jsonify({"cars": [car.to_dict() for car in cars]}), 200


@api.get("/cars/<int:car_id>")
def get_car(car_id):
    car = Car.query.get_or_404(car_id)
    return jsonify({"car": car.to_dict()}), 200


@api.patch("/cars/<int:car_id>")
@require_auth(role="merchant")
def update_car(current_user, car_id):
    car = Car.query.get_or_404(car_id)
    if car.merchant_id != current_user.id:
        return jsonify({"message": "You can update only your own cars"}), 403

    data = request.get_json(silent=True) or {}
    for field in ("brand", "model", "year", "color"):
        if field in data:
            setattr(car, field, data[field])

    if "daily_price" in data:
        car.daily_price = Decimal(str(data["daily_price"]))

    if "status" in data:
        if data["status"] not in VALID_CAR_STATUSES:
            return jsonify({"message": "Invalid car status"}), 400
        car.status = data["status"]

    db.session.commit()
    return jsonify({"message": "Car updated successfully", "car": car.to_dict()}), 200


@api.delete("/cars/<int:car_id>")
@require_auth(role="merchant")
def delete_car(current_user, car_id):
    car = Car.query.get_or_404(car_id)
    if car.merchant_id != current_user.id:
        return jsonify({"message": "You can delete only your own cars"}), 403

    active_rental = Rental.query.filter_by(car_id=car.id, status="active").first()
    if active_rental:
        return jsonify({"message": "Car has an active rental and cannot be deleted"}), 400

    db.session.delete(car)
    db.session.commit()
    return jsonify({"message": "Car deleted successfully"}), 200


@api.post("/rentals")
@require_auth(role="user")
def create_rental(current_user):
    data = request.get_json(silent=True) or {}
    car_id = data.get("car_id")
    if not car_id:
        return jsonify({"message": "car_id is required"}), 400

    try:
        end_date = normalize_datetime(parse_datetime(data.get("end_date"), "end_date"))
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400

    if end_date <= utc_now():
        return jsonify({"message": "end_date must be in the future"}), 400

    car = Car.query.get_or_404(car_id)
    if car.status != "available":
        return jsonify({"message": "Car is not available"}), 400

    rental = Rental(user_id=current_user.id, car_id=car.id, end_date=end_date)
    car.status = "rented"
    db.session.add(rental)
    db.session.commit()

    return jsonify({"message": "Rental created successfully", "rental": rental.to_dict()}), 201


@api.patch("/rentals/<int:rental_id>/extend")
@require_auth(role="user")
def extend_rental(current_user, rental_id):
    rental = Rental.query.get_or_404(rental_id)
    if rental.user_id != current_user.id:
        return jsonify({"message": "You can extend only your own rentals"}), 403

    if rental.status != "active":
        return jsonify({"message": "Only active rentals can be extended"}), 400

    if normalize_datetime(rental.end_date) <= utc_now():
        return jsonify({"message": "Rental period already ended"}), 400

    data = request.get_json(silent=True) or {}
    try:
        new_end_date = normalize_datetime(parse_datetime(data.get("end_date"), "end_date"))
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400

    if new_end_date <= normalize_datetime(rental.end_date):
        return jsonify({"message": "New end_date must be after current end_date"}), 400

    rental.end_date = new_end_date
    db.session.commit()
    return jsonify({"message": "Rental extended successfully", "rental": rental.to_dict()}), 200


@api.patch("/rentals/<int:rental_id>/return")
@require_auth(role="user")
def return_rental(current_user, rental_id):
    rental = Rental.query.get_or_404(rental_id)
    if rental.user_id != current_user.id:
        return jsonify({"message": "You can return only your own rentals"}), 403

    if rental.status != "active":
        return jsonify({"message": "Rental is already completed"}), 400

    returned_at = utc_now()
    rental.returned_at = returned_at
    rental.total_fee = calculate_fee(rental, returned_at)
    rental.status = "completed"
    rental.car.status = "available"
    db.session.commit()

    return jsonify({"message": "Car returned successfully", "rental": rental.to_dict()}), 200


@api.get("/rentals/history")
@require_auth(role="user")
def rental_history(current_user):
    rentals = (
        Rental.query.filter_by(user_id=current_user.id)
        .order_by(Rental.start_date.desc())
        .all()
    )
    return jsonify({"rentals": [rental.to_dict() for rental in rentals]}), 200
