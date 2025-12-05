import os
from flask import Flask, redirect, render_template, request, url_for, flash, jsonify

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt

# import requests
from wtforms import Form, SubmitField, StringField, EmailField, PasswordField, BooleanField, ValidationError
from wtforms.validators import DataRequired, Length, Email, EqualTo

app = Flask(__name__)

# SQLACADEMY ORM
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
# WARNING: CSRF protection is disabled for simplicity in this demo
# app.config['WTF_CSRF_ENABLED'] = False
# # Secret key for session management and security features
# app.config['SECRET_KEY'] = "change-me"

# # The business logic API URL
# LOGIC_API = os.getenv('LOGIC_API_URL')

# # Initialize SQLAlchemy and Bcrypt extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class User(UserMixin, db.Model):
  """
  User model representing a user in the application.
  Inherits from both UserMixin and db.Model to integrate Flask-Login and SQLAlchemy.

  UserMixin provides default implementations for the methods that Flask-Login
  expects user objects to have:
  - is_authenticated: Property that should return True if the user is authenticated.
  - is_active: Property that should return True if the user is active.
  - is_anonymous: Property that should return False for regular users.
  - get_id(): Method that returns a unique identifier for the user as a string.

  By inheriting from UserMixin, the User class automatically gets these methods,
  making it compatible with Flask-Login's user management system.
  """

  __tablename__ = 'users'

  # Primary key
  id = db.Column(db.Integer, primary_key=True)
  # User's email, it is used as user identification during authentication so must be unique but it can be changed over time
  email      = db.Column(db.String(60), unique=True, index=True)
  # User's password, stored as a hash
  password   = db.Column(db.String(80))
  # User's name, not used for identification (just an example of an extra field)
  name = db.Column(db.String(80), nullable=False)

  def check_password(self, password):
    """
    Check if the provided password matches the stored hash.

    Args:
        password (str): The password to check.

    Returns:
        bool: True if the password matches, False otherwise.
    """
    return bcrypt.check_password_hash(self.password, password)

  @classmethod
  def create_user(cls, name, email, password):
    """
    Create a new user with the provided details.

    Args:
        name (str): The user's name.
        email (str): The user's email.
        password (str): The user's password, which will be hashed before storage.

    Returns:
        User: The newly created user object.
    """
    user = cls( name     = name.strip(),
                email    = email.strip(),
                password = bcrypt.generate_password_hash(password).decode('utf-8') )
    db.session.add(user)
    db.session.commit()
    return user
  
  @staticmethod
  def get_by_id(id):
    """
    Retrieve a user by their ID.

    Args:
        id (int): The user's ID.

    Returns:
        User: The user object if found, otherwise None.
    """
    return User.query.filter_by(id=id).first()
  
  @staticmethod
  def get_by_email(email):
    """
    Retrieve a user by their email.

    Args:
        email (str): The user's email.

    Returns:
        User: The user object if found, otherwise None.
    """
    return User.query.filter_by(email=email.strip()).first()

  @staticmethod
  def email_exists(email):
    """
    Check if an email already exists in the database.

    Args:
        email (str): The email to check.

    Returns:
        bool: True if the email exists, False otherwise.
    """
    email = User.query.filter_by(email=email).first()
    return email is not None

# Clears the database and create tables within the application context
with app.app_context():
  # db.drop_all() THIS ALLOWS FOR PERSISTANCE?
  db.create_all()

# FORMS -----------------------------------------------------------------------

# Custom validator to check if an email already exists
def email_exists(form, field):
  if User.email_exists(field.data):
    raise ValidationError('Email already exists.')

# WTForms for user registration
class RegistrationForm(Form):
  name = StringField('Name', validators=[DataRequired(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  email = EmailField('Email', validators=[DataRequired(), email_exists, Email()])
  password = PasswordField('Password', validators=[DataRequired(), EqualTo('confirm', message='Password must match')])
  confirm = PasswordField('Confirm', validators=[DataRequired()])
  submit = SubmitField('Register')

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
  email = EmailField('Email', validators=[DataRequired(), Email()])
  password = PasswordField('Password', validators=[DataRequired()])
  remember = BooleanField('Remember Me')
  submit = SubmitField('Login')

# SESSIONS --------------------------------------------------------------------

# -- JEG UDNYTTER IKKE DENNE NOK --

# Initialize the LoginManager with the Flask application
login_manager = LoginManager(app)
# Set the view to redirect to for unauthorized users (e.g., when @login_required is used)
login_manager.login_view = 'home'
# Enable session protection to guard against session hijacking
# 'strong' mode ensures that the session is invalidated if the user's IP or browser changes
login_manager.session_protection = 'strong'
# Callback function for Flask-Login to reload the user object from the user ID 
# stored in the session.
# This function is required by Flask-Login to retrieve the user object whenever 
# the application needs to know the current user. It is called when the session 
# is accessed, and the user's ID is retrieved from the session. The function 
# then fetches the corresponding user from the database.
@login_manager.user_loader
def load_user_from_id(id):
    return User.get_by_id(id)

# This is only for demonstration ------------------------------------
# A custom session interface that *does not encrypt* session data
# from plain_sessions import PlainCookieSessionInterface
# app.session_interface = PlainCookieSessionInterface()
# Disable session protection against session token hijacking
# login_manager.session_protection = None
# -------------------------------------------------------------------


class Entry(db.Model):
    __tablename__ = 'entries'

    id   = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(100), nullable=False)
    # check = db.Column(db.Boolean, nullable=False)

with app.app_context():
  # empty the database
  # db.drop_all() THIS ALLOWS FOR PERSISTANCE?
  # ensure the schema includes this data model
  db.create_all()
  # add some dummy data
  count = Entry.query.count()
  for i in range(count,3  ):
    db.session.add(Entry(text = "Opgave " + str(i)))
  db.session.commit()

# Forms -----------------------------------------------------------------------

# class EntryForm(Form):
#   text = StringField( label='Description', validators=[DataRequired(), Length(min=1, max=100) ] )
#   submit = SubmitField('Add')

# Routes for todo ----------------------------------------------------------------------

##### OLD 

# @app.route("/todo",methods=["GET","POST"])
# def todo():
#   form = EntryForm(request.form)
#   if request.method == 'POST' and form.validate():
#     text = form.text.data
#     db.session.add(Entry(text = text))
#     db.session.commit()
#   entries = Entry.query.order_by(Entry.id).all()
#   return render_template("todo.html", entries=entries, form=form)

# @app.route("/todo",methods=["GET","POST"])
# def todo():
#   form = EntryForm(request.form)
#   if request.method == 'POST' and form.validate():
#     text = form.text.data
#     # POST to backend service, if we use the form!
#     requests.post(f"{LOGIC_API}/entries", json={"text": text})
#   # GET entries from the backend
#   response = requests.get(f"{LOGIC_API}/entries") # Request GET
#   entries = response.json() if response.ok else [] # place data in entries, for use below. 
#   return render_template("todo.html", entries=entries, form=form)


# @app.route("/delete/<int:id>")
# def delete(id):
#   entry = Entry.query.filter_by(id=id).first()
#   if entry:
#     db.session.delete(entry)
#     db.session.commit()
#     flash('Entry deleted.', 'info')
#   else:
#     flash("Sorry, we couldn't find the entry that you wanted to delete.", 'warning')
#   return redirect(url_for('todo'))

# @app.route("/delete/<int:id>")
# def delete(id):

#   response = response.delete(f"{LOGIC_API}/entries/{id}")
  
#   if response.status_code == 200:
#     flash('Entry deleted.', 'info')
#   else:
#     flash("Sorry, we couldn't find the entry that you wanted to delete.", 'warning')
#   return redirect(url_for('todo'))

# # ROUTES for login ----------------------------------------------------------------------

@app.route("/login", methods=('GET','POST'))
def login_authentication():
  """
  Login authentication;
  - Data modtages fra frontend, "/" route. 
  - Returnerer en respons, der afgør om brugere logges ind. 

  """

  # MANGLER SESSION HÅNDTERING

  data = request.get_json() # Request data fra frontend
  email = data.get('email')
  password = data.get('password')
  user = User.get_by_email(email)
  if user and user.check_password(password): # Laver authentication og send tilbage til frontend
      # If the user credentials are correct, start an authenticated session
      login_user(user) ## ---------USIKKER PÅ OM DENNE SKAL VÆRE HER
      return jsonify({"message": "Authenticated", "user_id": user.id}), 200
  return jsonify({"message": "Invalid credentials"}), 401
  
  #### OLD VERSION
    # form = LoginForm(request.form)
    # if request.method == 'POST' and form.validate(): # Logging in
    #   user = User.get_by_email(form.email.data.strip())
    #   if user and user.check_password(form.password.data.strip()):
    #       # If the user credentials are correct, start an authenticated session
    #       login_user(user, form.remember.data)
    #       # Redirect to the user todo page
    #       return redirect(url_for('todo'))
    #   else:
    #       # Otherwise, display an error message and display the login form again
    #       flash("Invalid credentials","error")
    # return render_template('login.html', form=form)

@app.route("/register", methods=('GET','POST'))
def register():
  """
  Registration page:
  - Modtager data fra frontend, bruger det til authentication. 
  - MANGLER IMPLEMENTATION AF ERROR HANDLING
  """
  data = request.get_json()
  name = data.get('name')
  email = data.get('email')
  password = data.get('password')

  user = User.create_user(
    name = name,
    email = email,
    password = password
    )

  # Should implement more error handling, e.g if email exist. 

  return jsonify({"message": "Authenticated", "user_id": user.id}), 200
  

### MANGLER AT IMPLEMENTERE LOGOUT.
# 
# HER SKAL SESSION COOKIE DELETES VIA LOG_OUT()  
#
# @app.route('/logout', methods=['GET'])
# @login_required
# def logout():
#     # Terminates the authenticated session, deletes any related cookies 
#     logout_user()
#     return redirect(url_for('home'))

#### Handling updating entries from the frontend  -------------------------------------------------

@app.route("/entries", methods=["GET"])
def get_entries():
    entries = Entry.query.order_by(Entry.id).all()
    return jsonify([{"id": e.id, "text": e.text} for e in entries])

@app.route("/entries", methods=["POST"])
def add_entry():
    data = request.get_json()
    text = data.get('text')
    if not text:
        return jsonify({"error": "Text is required"}), 400
    entry = Entry(text=text)
    db.session.add(entry)
    db.session.commit()
    return jsonify({"id": entry.id, "text": entry.text}), 201

@app.route("/entries/<int:id>", methods=["DELETE"])
def delete_entry(id):
    entry = Entry.query.get(id)
    if not entry:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(entry)
    db.session.commit()
    return jsonify({"message": "Deleted"}), 200

