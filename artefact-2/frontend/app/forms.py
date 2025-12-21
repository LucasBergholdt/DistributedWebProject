from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import DateField, FloatField, Form, IntegerField, RadioField, SelectField, StringField, SubmitField, EmailField, PasswordField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Optional, Length

# Form for user registration
class RegistrationForm(Form):
  email = EmailField('Email', validators=[DataRequired(), Email()])
  password = PasswordField('Password', validators=[DataRequired(), EqualTo('confirm', message='Password must match')])
  confirm = PasswordField('Confirm', validators=[DataRequired()])
  role = SelectField("Role", choices=[('seeker', 'Seeker'), ('provider', 'Provider')], validators=[DataRequired()])
  submit = SubmitField('Register')

# Form for user login
class LoginForm(Form):
  email = EmailField('Email', validators=[DataRequired(), Email()])
  password = PasswordField('Password', validators=[DataRequired()])
  remember = BooleanField('Remember Me')
  submit = SubmitField('Login')

# Form for updating seeker profiles
class ProfileForm(FlaskForm):
  name = StringField('Name', validators=[Optional(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  description = TextAreaField('About you', validators=[Optional()])
  birthdate = DateField('Birthdate', format="%Y-%m-%d", validators=[Optional()])
  gender = RadioField('Gender', choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], validators=[Optional()])
  occupation = StringField('Occupation', validators=[Optional(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  image = FileField("Profile picture", validators=[Optional()])
  submit = SubmitField('Save Profile')

# Form for the collective filter
class SearchForm(FlaskForm):
  city = StringField('Filter by city', validators=[Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  roomsize = IntegerField('Size of room')
  price = IntegerField('Price in DKK')
  submit = SubmitField('Search')
  
# Form for creating collectives
class CollectiveForm(FlaskForm):
  city = StringField('Name of city', validators=[DataRequired(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  street = StringField('Name of street', validators=[DataRequired(), Length(min=1, max=100, message='You cannot have less than 1 or more than 80 characters')])
  roomsize = IntegerField('Size of the room available (square meters)', validators=[DataRequired()])
  price = FloatField('Price in DKK', validators=[DataRequired()])
  description = TextAreaField('Describe your collective', validators=[DataRequired()])
  image = FileField(validators=[FileRequired()])
  submit = SubmitField('Register your collective')