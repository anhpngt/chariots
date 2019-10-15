from bisect import bisect_left
from datetime import datetime
from functools import lru_cache
from typing import List

import numpy as np
from flask import current_app
from app.database import db


class Vehicle(db.Model):
    __tablename__ = 'vehicle'

    id = db.Column(db.Integer, primary_key=True)
    vehiclename = db.Column(db.String(10), index=True, unique=True)
    capacity = db.Column(db.Float)
    orders = db.relationship('Order', backref='vehicle', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return str({
            attr: self.__getattribute__(attr)
            for attr in {'id', 'vehiclename', 'capacity'}
        })


class Order(db.Model):
    __tablename__ = 'order'

    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(140))
    latlon = db.Column(db.String(140))
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    load = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow())
    computed = db.Column(db.Boolean, default=False)

    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'))

    def __repr__(self):
        return str({
            attr: self.__getattribute__(attr)
            for attr in {'id', 'address', 'lat', 'lng',
                         'load', 'timestamp', 'computed', 'vehicle_id'}
        })


class DistanceMatrix(db.Model):
    __tablename__ = 'distance_matrix'

    # By setting 2 primary keys in this model, sqlalchemy sets a composite
    # primary key in the table
    id1 = db.Column(db.Integer, primary_key=True, autoincrement=False)
    id2 = db.Column(db.Integer, primary_key=True, autoincrement=False)
    distance = db.Column(db.Integer)

    def __repr__(self):
        return str({
            attr: self.__getattribute__(attr)
            for attr in {'id1', 'id2', 'distance'}
        })

    @staticmethod
    def query_all_sorted():
        return DistanceMatrix.query.order_by(DistanceMatrix.id1, DistanceMatrix.id2).all()

    @staticmethod
    def update_table(order_id_sequence: List[int], distance_matrix: np.ndarray) -> None:
        # Note that distance_matrix includes distances from/to depot,
        # which is not included in order_id_sequence
        n = len(order_id_sequence)
        assert distance_matrix.shape == (n+1, n+1), \
            f'Invalid distance_matrix shape ({distance_matrix.shape}, should be {(n+1, n+1)})'

        for i in range(-1, n):
            for j in range(-1, n):
                # Note that first entry (id* = 0) is for depot in CVRP
                id1 = 0 if i == -1 else order_id_sequence[i]
                id2 = 0 if j == -1 else order_id_sequence[j]
                distance_entry = DistanceMatrix(id1=id1, id2=id2,
                                                distance=int(distance_matrix[i][j]))
                db.session.add(distance_entry)
        Order.query.update({'computed': True})
        db.session.commit()

    @staticmethod
    def isupdated():
        return all([order.computed for order in db.session.query(Order.computed).all()])

    @staticmethod
    def get_distance_matrix(order_id_sequence: List[int]) -> np.ndarray:
        # Number of addresses minus 1 (missing the depot)
        n = len(order_id_sequence)
        distance_matrix = np.zeros(shape=(n+1, n+1))
        dm_entry_list = DistanceMatrix.query_all_sorted()

        @lru_cache(maxsize=256)
        def lookup_matrix_index(order_id: int) -> int:
            # Note that entry zero is reserved for depot
            if order_id == 0:
                return 0
            i = bisect_left(order_id_sequence, order_id)
            if i != len(order_id_sequence) and order_id_sequence[i] == order_id:
                return i + 1

            current_app.logger.error(
                f'Failed to lookup matrix distance for order <{order_id}>')
            raise ValueError

        for dm_entry in dm_entry_list:
            i = lookup_matrix_index(dm_entry.id1)
            j = lookup_matrix_index(dm_entry.id2)
            distance_matrix[i][j] = dm_entry.distance

        current_app.logger.debug(f'Distance matrix retrieved:\n{distance_matrix}')
        return distance_matrix
