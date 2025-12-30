from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length

class CustomerForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[Length(max=20)])
    company = StringField('Company', validators=[DataRequired(), Length(min=2, max=100)])
    default_shipping_address = StringField('Default Shipping Address', validators=[Length(max=255)])
    default_billing_address = StringField('Default Billing Address', validators=[Length(max=255)])
    addresses = StringField('Addresses', validators=[Length(max=255)])
    tax_id = StringField('Tax ID', validators=[Length(max=255)])
    notes = StringField('Notes', validators=[Length(max=255)])
    
    submit = SubmitField('Save')
