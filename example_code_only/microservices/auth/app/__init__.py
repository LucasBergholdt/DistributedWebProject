from flask import Flask, Response, jsonify, redirect, render_template, request, session, url_for, flash
import os
# from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
# from flask_bcrypt import Bcrypt


from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt

import requests
from wtforms import Form, SubmitField, StringField, EmailField, PasswordField, BooleanField, ValidationError
from wtforms.validators import DataRequired, Length, Email, EqualTo

import secrets



app = Flask(__name__)

# SQLACADEMY ORM
# app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')

# # Configure SQLAlchemy ORM to use SQLite database file 'flask.db'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///flask.db"
# # WARNING: CSRF protection is disabled for simplicity in this demo
app.config['WTF_CSRF_ENABLED'] = False
# # Secret key for session management and security features
app.config['SECRET_KEY'] = "change-me"

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

# Repræsenterer brugere logget ind.
class Session(db.Model):
    __tablename__ = 'sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=db.func.now())
    expires_at = db.Column(db.DateTime, nullable=True)  # optional

    user = db.relationship("User", backref="sessions")
  
    @staticmethod
    def session_exists(token):
      """
      Check if an email already exists in the database.

      Args:
          email (str): The email to check.

      Returns:
          bool: True if the email exists, False otherwise.
      """
      token = Session.query.filter_by(token=token).first()
      return token is not None
    
    @staticmethod
    def get_by_token(token):
      return Session.query.filter_by(token=token).first()


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
  email = EmailField('Email', validators=[DataRequired(), Email()]) # formerly had check if email already existed.
  password = PasswordField('Password', validators=[DataRequired(), EqualTo('confirm', message='Password must match')])
  confirm = PasswordField('Confirm', validators=[DataRequired()])
  submit = SubmitField('Register')


# Initialize the LoginManager with the Flask application
# login_manager = LoginManager(app)
# Set the view to redirect to for unauthorized users (e.g., when @login_required is used)
# login_manager.login_view = '/sessions'
# Enable session protection to guard against session hijacking
# 'strong' mode ensures that the session is invalidated if the user's IP or browser changes
# login_manager.session_protection = 'strong'
# Callback function for Flask-Login to reload the user object from the user ID 
# stored in the session.
# This function is required by Flask-Login to retrieve the user object whenever 
# the application needs to know the current user. It is called when the session 
# is accessed, and the user's ID is retrieved from the session. The function 
# then fetches the corresponding user from the database.


@app.route("/users", methods=['POST'])
def register():
  """
  Registration page:
  -
  """

  data = request.get_json()
  name = data.get('name')
  email = data.get('email')
  password = data.get('password')

  # Needs check if user already exists
  # Should implement more error handling, e.g if email exist. 

  user = User.create_user(
    name = name,
    email = email,
    password = password
    )


  return jsonify({"message": "Authenticated (User created)", "user_id": user.id}), 200
  

# REST API repræsenterer url som ressourcer - en login-session er en ressource. 
# LOGGING IN
@app.route("/sessions", methods=['POST'])
def login_authentication():
  """
  Login authentication;
  - Data modtages fra frontend, "/" route. 
  - Returnerer en respons, der afgør om brugere logges ind. 
  - En user login session repræsenteres derfor med post - vi laver en ny "session ressource".

  """
  # Modtag log in data.
  data = request.get_json()

  token = data.get("api_token")
  email = data.get('email')
  password = data.get('password')
  user = User.get_by_email(email)

  # Hvis token eksisterer, er brugeren logget ind. Returner derfor brugerens token.
  if token and Session.session_exists(token):
        session = Session.get_by_token(token)
        return jsonify({
            "message": "Token already exists",
            "user_id": session.user_id,
            "api_token": session.token
        }), 200
  
  # Check brugerens credentials. 
  if user is None:
    return jsonify({"error": "User does not exist"}), 404

  if not user.check_password(password):
    return jsonify({"error": "Invalid password"}), 401

  # Lav en ny session, hver gang en bruger logger ind.
  token = make_token()
  session_record = Session(user_id=user.id, token=token)
  db.session.add(session_record)
  db.session.commit()

  # Send api token med tilbage til frontend og set_cookie i frontend. 
  response = jsonify({"message": "Authenticated (new token)", "user_id": user.id, "api_token":token}), 200

  return response

@app.route("/sessions", methods=['GET'])
def current_session():
  """
  Fetching session info for the frontend. 
  """
  
  token = request.args.get("api_token") # Request data fra frontend
  session = Session.get_by_token(token)

  if not session:
    return jsonify({"valid": False}), 401
  
  ## Hvis sessionen er oprettes, skal vi returnere de relevante oplysninger.
  return jsonify({
  "user_id": session.user_id,
  "api_token": session.token,
  "created_at": session.created_at.isoformat()
  })

@app.route('/sessions', methods=['DELETE'])
def logout():
  """
  Deletes terminated session from the session table upon logout. 
  """ 

  token = request.args.get("api_token") # Request data fra frontend
  session = Session.get_by_token(token)
  if not session:
    return jsonify({"error": "Session not found"}), 404
  
  # Delete session from table
  db.session.delete(session)
  db.session.commit()


  return jsonify({"message": "Logged out", "session_id": session.id}), 200


def make_token():
    """
    Creates a cryptographically-secure, URL-safe string
    """
    return secrets.token_urlsafe(16)  