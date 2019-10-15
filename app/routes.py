from app.cvrp import DataModel
from flask import Flask
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from app.constants import DEPOT

from app.database import db
from app.database.models import Order, DistanceMatrix
from app.database.models import Vehicle
from app.forms import OrderForm
from app.forms import VehicleForm

data_model = DataModel()


def setup_routes(app: Flask):
    @app.route('/test')
    def test():
        print(DistanceMatrix.query.order_by(DistanceMatrix.id2, DistanceMatrix.id1).all())
        return dict(
            # result=[dm for dm in DistanceMatrix.query.order_by(DistanceMatrix.id1, DistanceMatrix.id2).all()]
        )

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
        order_id = request.form.get('delete_order')
        Order.query.filter_by(id=order_id).delete()
        db.session.commit()
        app.logger.info(f'Order (id: {order_id}) is deleted.')
        return redirect(url_for('index'))

    @app.route('/delete_vehicle', methods=['POST'])
    def delete_vehicle():
        vehicle_id = request.form.get('delete_vehicle')
        Vehicle.query.filter_by(id=vehicle_id).delete()
        db.session.commit()
        app.logger.info(f'Vehicle (id: {vehicle_id}) is deleted.')
        return redirect(url_for('index'))

    @app.route('/compute', methods=['GET', 'POST'])
    def compute():
        data_model.prepare_model(distance_mode='real')
        routes = data_model.solve()

        if not data_model.is_solved:
            app.logger.error('Failed to solve problem')
            flash('Failed to compute routes for vehicles.')
            return redirect(url_for('index'))

        allpaths = [rt.path for rt in routes]
        return render_template('compute.html', title='Compute', paths=allpaths)

    @app.route('/result')
    def result():
        if not data_model.is_solved:
            app.logger.warn('Problem is not solved')
            flash('Problem is not yet solved')
            return redirect(url_for('index'))

        all_orders = Order.query.all()
        order_data = [DEPOT.split(',')]

        for order in all_orders:
            order_data.append([order.lat, order.lng])

        allpathdata = [rt.path_data for rt in data_model.result_routes]

        import json
        return render_template('res.html',
                               title='Map',
                               path_data=json.dumps(allpathdata),
                               orders_data=json.dumps(order_data))

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
