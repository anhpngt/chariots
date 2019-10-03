from datetime import datetime

from app.database import db


class Vehicle(db.Model):
    __tablename__ = 'vehicle'

    id = db.Column(db.Integer, primary_key=True)
    vehiclename = db.Column(db.String(10), index=True, unique=True)
    capacity = db.Column(db.Float)
    orders = db.relationship('Order', backref='vehicle', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return '<Vehicle {}>'.format(self.vehiclename)


class Order(db.Model):
    __tablename__ = 'order'

    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(140))
    latlon = db.Column(db.String(140))
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    load = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow())

    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'))

    def __repr(self):
        return '<Order {}>'.format(self.address)
