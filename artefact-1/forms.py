from wtforms import DateTimeField, DecimalField, FileField, Form, SubmitField, SelectField, StringField, EmailField, PasswordField, BooleanField, ValidationError
from wtforms.validators import DataRequired, Length, Email, EqualTo, InputRequired
from .model import User

# Custom validator to check if an email already exists
# In WTForms custom validators must accept parameters form and field. So it is specified here even though it is not used.
def email_exists(form, field):
  if User.email_exists(field.data):
    raise ValidationError('Email already exists.')

# WTForms for user registration.

# Abstract Base Form. Not to be used directly.
class RegistrationBaseForm(Form):
  name = StringField('Name', validators=[DataRequired(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  email = EmailField('Email', validators=[DataRequired(), email_exists, Email()])
  password = PasswordField('Password', validators=[DataRequired(), EqualTo('confirm', message='Password must match')])
  confirm = PasswordField('Confirm', validators=[DataRequired()])
  submit = SubmitField('Register')

class RegistrationFormSeeker(RegistrationBaseForm):
  birthdate = StringField('Birthdate', validators=[DataRequired(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  gender = StringField('Gender', validators=[DataRequired(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  occupation = StringField('Occupation', validators=[DataRequired(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  image = StringField('Image', validators=[DataRequired(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  description = StringField('Describe yourself', validators=[DataRequired(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])


class RegistrationFormProvider(RegistrationBaseForm):
  address = StringField('Name', validators=[DataRequired(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  space = StringField('How much space is there', validators=[DataRequired(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  slotsTotal = StringField('Name', validators=[DataRequired(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  vacantSlots = StringField('Name', validators=[DataRequired(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  description = StringField('Describe your collective', validators=[DataRequired(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])

# WARNING --------------------------------------------------------------------
# Checking if an email is already registered during form validation introduces 
# a potential security risk. An attacker can use the registration form to check 
# if an email is already registered, effectively allowing them to enumerate 
# valid user emails. A more secure approach is to always return a success 
# message (e.g., "A confirmation email has been sent") regardless of whether 
# the email is already registered. This prevents attackers from determining 
# which emails are registered in the system. This example uses this insecure 
# solution for simplicity as this is purely a demonstration of the session 
# handling infrastructure.
# -----------------------------------------------------------------------------

# WTForms for user login
class LoginForm(Form):
  type = SelectField("Usertype", choices=["Seeker", "Provider"], validators=[DataRequired()])
  email = EmailField('Email', validators=[DataRequired(), Email()])
  password = PasswordField('Password', validators=[DataRequired()])
  remember = BooleanField('Remember Me')
  submit = SubmitField('Login')


# Forms for adding receipts. Placeholder
class ReceiptForm(Form):
  """Form for entering data in receipts. Placeholder.
  """
  amount = DecimalField('Amount', validators=[DataRequired()])
  time_of_purchase = DateTimeField('Time of purchase', validators=[DataRequired()], format=['%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S'])
  bank_statement = StringField('Bank statement', validators=[DataRequired(), Length(min=1, max=100, message="You cannot have less than 1 or more than 100 characters")])
  file = FileField('Image of receipt', validators=[InputRequired()])
  submit = SubmitField('Create Receipt')


class StatusChangeForm(Form):
  new_status = SelectField("Status", choices=[], validators=[DataRequired()])
  submit = SubmitField('Change Status')