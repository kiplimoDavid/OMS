from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, SelectField, TelField
from wtforms.validators import DataRequired, Length, ValidationError, Email
from wtforms.fields import EmailField

class PaymentMethodForm(FlaskForm):
    method_type = SelectField(
        'Payment Method',
        choices=[
            ('MPESA', 'M-Pesa'),
            ('PAYPAL', 'PayPal'),
            ('CARD', 'Credit/Debit Card'),
            ('BANK', 'Bank Deposit')
        ],
        validators=[DataRequired()]
    )

    # Card fields
    card_type = StringField('Card Type')
    card_number = StringField('Card Number')
    expiration_date = StringField('Expiration Date')  # MM/YYYY
    cardholder_name = StringField('Cardholder Name')

    # PayPal fields
    paypal_email = EmailField('PayPal Email')

    # M-Pesa fields
    mpesa_number = TelField('M-Pesa Phone Number')

    # Bank fields
    bank_account = StringField('Bank Account Number')

    is_default = BooleanField('Set as Default')
    submit = SubmitField('Add Payment Method')

    def validate(self, extra_validators=None):
        """Custom conditional validation depending on method_type """
        initial_validation = super().validate(extra_validators)
        if not initial_validation:
            return False

        if self.method_type.data == 'CARD':
            if not self.card_type.data or len(self.card_type.data) < 2:
                self.card_type.errors.append('Card type is required.')
                return False
            if not self.card_number.data or not self._is_valid_card_number(self.card_number.data):
                self.card_number.errors.append('Invalid card number.')
                return False
            if not self.expiration_date.data or len(self.expiration_date.data) not in [5, 7]:
                self.expiration_date.errors.append('Expiration date must be MM/YYYY.')
                return False
            if not self.cardholder_name.data or len(self.cardholder_name.data) < 3:
                self.cardholder_name.errors.append('Cardholder name is required.')
                return False

        elif self.method_type.data == 'PAYPAL':
            if not self.paypal_email.data:
                self.paypal_email.errors.append('PayPal email is required.')
                return False

        elif self.method_type.data == 'MPESA':
            if not self.mpesa_number.data or not (10 <= len(self.mpesa_number.data) <= 15):
                self.mpesa_number.errors.append('Valid M-Pesa number is required.')
                return False

        elif self.method_type.data == 'BANK':
            if not self.bank_account.data:
                self.bank_account.errors.append('Bank account number is required.')
                return False

        return True

    def _is_valid_card_number(self, card_number):
        """Basic numeric length check; replace with Luhn for production"""
        return card_number.isdigit() and 13 <= len(card_number) <= 19
