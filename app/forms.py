from flask_wtf import FlaskForm
from wtforms import FloatField
from wtforms import StringField
from wtforms import SubmitField
from wtforms.validators import DataRequired


class OrderForm(FlaskForm):
    load = FloatField('Load', validators=[DataRequired()])
    submit = SubmitField('Submit')


class VehicleForm(FlaskForm):
    vehiclename = StringField('Plate Number', validators=[DataRequired()])
    capacity = FloatField('Capacity', validators=[DataRequired()])
    submit = SubmitField('Submit')
