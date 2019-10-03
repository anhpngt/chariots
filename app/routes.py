from flask import Flask
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from app.database import db
from app.database.models import Order
from app.database.models import Vehicle
from app.forms import OrderForm
from app.forms import VehicleForm


def setup_routes(app: Flask):
    @app.route('/')
    @app.route('/index')
    def index():
        orders = Order.query.all()
        vehicles = Vehicle.query.all()
        return render_template('index.html',
                               title='Home page',
                               orders=orders,
                               vehicles=vehicles)

    @app.route('/delete_order', methods=['POST'])
    def delete_order():
        Order.query.filter_by(id=request.form.get('delete_order')).delete()
        db.session.commit()
        return redirect(url_for('index'))

    @app.route('/delete_vehicle', methods=['POST'])
    def delete_vehicle():
        Vehicle.query.filter_by(id=request.form.get('delete_vehicle')).delete()
        db.session.commit()
        return redirect(url_for('index'))

    @app.route('/compute', methods=['GET', 'POST'])
    def compute():
        pass

    @app.route('/result')
    def result():
        pass

    @app.route('/order', methods=['GET', 'POST'])
    def order():
        form = OrderForm()
        if form.validate_on_submit():
            new_order = Order(address=form.address.data,
                              latlon=','.join([form.lat.data, form.lng.data]),
                              lat=float(form.lat.data),
                              lng=float(form.lng.data),
                              load=form.load.data)
            db.session.add(new_order)
            db.session.commit()

            flash('Order added')
            return redirect(url_for('index'))

        return render_template('order.html',
                               title='Orders',
                               form=form)

    @app.route('/vehicle', methods=['GET', 'POST'])
    def vehicle():
        form = VehicleForm()
        if form.validate_on_submit():
            vehicle = Vehicle(vehiclename=form.vehiclename.data,
                              capacity=form.capacity.data)
            db.session.add(vehicle)
            db.session.commit()

            flash("Vehicle added")
            return redirect(url_for('index'))

        return render_template('vehicle.html',
                               title='Vehicles',
                               form=form)
