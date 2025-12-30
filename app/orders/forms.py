from flask_wtf import FlaskForm
from wtforms import SelectField, IntegerField, FieldList, FormField
from wtforms.validators import DataRequired, NumberRange

class OrderItemForm(FlaskForm):
    product_id = SelectField('Product', coerce=int, validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1)])

class OrderForm(FlaskForm):
    customer_id = SelectField('Customer', coerce=int, validators=[DataRequired()])
    items = FieldList(FormField(OrderItemForm), min_entries=1)
    shipping_address = FieldList(FormField(OrderItemForm), min_entries=1)
    billing_address = FieldList(FormField (OrderItemForm), min_entries=1)
    payment_method = FieldList(FormField (OrderItemForm), min_entries=1)
    estimated_delivery = FieldList(FormField (OrderItemForm), min_entries=1)
    notes = FieldList(FormField (OrderItemForm), min_entries=1)
    format_currency = FieldList(FormField (OrderItemForm), min_entries=1)