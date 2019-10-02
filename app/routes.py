from flask import Flask
from flask import render_template

from app.database.models import Order
from app.database.models import Vehicle


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
        return ''

    @app.route('/delete_vehicle', methods=['POST'])
    def delete_vehicle():
        pass

    @app.route('/compute', methods=['GET', 'POST'])
    def compute():
        pass

    @app.route('/result')
    def result():
        pass

    @app.route('/order', methods=['GET', 'POST'])
    def order():
        pass

    @app.route('/vehicle', methods=['GET', 'POST'])
    def vehicle():
        pass
