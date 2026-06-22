from datetime import datetime, timezone

from .extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    cars = db.relationship("Car", back_populates="merchant", cascade="all, delete-orphan")
    rentals = db.relationship("Rental", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self):
        return {"id": self.id, "username": self.username, "role": self.role}


class Car(db.Model):
    __tablename__ = "cars"

    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    brand = db.Column(db.String(100), nullable=False, index=True)
    model = db.Column(db.String(100), nullable=False, index=True)
    year = db.Column(db.Integer, nullable=True)
    color = db.Column(db.String(50), nullable=True)
    daily_price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False, default="available", index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    merchant = db.relationship("User", back_populates="cars")
    rentals = db.relationship("Rental", back_populates="car", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "merchant_id": self.merchant_id,
            "brand": self.brand,
            "model": self.model,
            "year": self.year,
            "color": self.color,
            "daily_price": float(self.daily_price),
            "status": self.status,
        }


class Rental(db.Model):
    __tablename__ = "rentals"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    car_id = db.Column(db.Integer, db.ForeignKey("cars.id"), nullable=False, index=True)
    start_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    end_date = db.Column(db.DateTime, nullable=False)
    returned_at = db.Column(db.DateTime, nullable=True)
    total_fee = db.Column(db.Numeric(10, 2), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="active", index=True)

    user = db.relationship("User", back_populates="rentals")
    car = db.relationship("Car", back_populates="rentals")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "car": self.car.to_dict() if self.car else None,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "returned_at": self.returned_at.isoformat() if self.returned_at else None,
            "total_fee": float(self.total_fee) if self.total_fee is not None else None,
            "status": self.status,
        }
