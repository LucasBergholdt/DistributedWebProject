from wtforms import DateField, DecimalField, IntegerField, FileField, Form, RadioField, SubmitField, SelectField, StringField, EmailField, PasswordField, BooleanField, TextAreaField, ValidationError
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional
from .model import User
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired


# -------------------------------- FORMS ------------------------------------- #

# Custom validator to check if an email already exists.
# In WTForms custom validators must accept parameters form and field. So it is specified here even though it is not used.
# Informing that email already exists imposes a security risk.
def email_exists(form, field):
  if User.email_exists(field.data):
    raise ValidationError('Email already exists.')


class RegistrationForm(Form):
  role = SelectField('Role', 
                         choices=[('seeker', 'Seeker'), ('provider', 'Provider')], 
                         validators=[DataRequired()])
  email = EmailField('Email', validators=[DataRequired(), email_exists, Email()])
  password = PasswordField('Password', validators=[DataRequired(), EqualTo('confirm', message='Password must match')])
  confirm = PasswordField('Confirm password', validators=[DataRequired()])
  submit = SubmitField('Register')

class SearchForm(FlaskForm):
  city = StringField('Filter by city', validators=[Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  roomsize = IntegerField('Size of room')
  price = IntegerField('Price in DKK')
  submit = SubmitField('Search')

class LoginForm(Form):
  email = EmailField('Email', validators=[DataRequired(), Email()])
  password = PasswordField('Password', validators=[DataRequired()])
  remember = BooleanField('Remember Me')
  submit = SubmitField('Login')

# --------- PROVIDERS --------- #
class CollectiveForm(FlaskForm):
  city = StringField('Name of city', validators=[DataRequired(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  street = StringField('Name of street', validators=[DataRequired(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  roomsize = IntegerField('Size of the room available (square meters)', validators=[DataRequired()])
  price = DecimalField('Price in DKK', validators=[DataRequired()])
  description = TextAreaField('Describe your collective', validators=[DataRequired(), Length(min=1, max=500, message='You cannot have less than 1 or more than 300 characters')])
  image = FileField(validators=[FileRequired()])
  submit = SubmitField('Register your collective')

# ------------ SEEKERS --------- #
class ProfileForm(FlaskForm):
  name = StringField('Name', validators=[Optional(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  description = TextAreaField('About you', validators=[Optional(), Length(max=500, message='You cannot have more than 500 characters')])
  birthdate = DateField('Birthdate', format="%Y-%m-%d", validators=[Optional()])
  gender = RadioField('Gender', choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], validators=[Optional()])
  occupation = StringField('Occupation', validators=[Optional(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  image = FileField("Profile picture", validators=[Optional()])
  submit = SubmitField('Save Profile')

# -------- NOT USED ----------- #
class ApplicationForm(Form):
  description = StringField('Your application', validators=[DataRequired(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  submit = SubmitField('Apply for this collective')
