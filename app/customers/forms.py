from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Email

class CustomerForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[Email()])
    phone = StringField('Phone')
    address = TextAreaField('Address')
    company = StringField('company')
    default_shipping_address = StringField('default_shipping_address')
    default_billing_address = StringField('default_billing_address')
    tax_id = StringField('tax_id')
    notes = StringField('notes')