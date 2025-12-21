import secrets
import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

app = Flask(__name__)

# Cofnigure SQLAlchemy ORM
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')


# Data Model ------------------------------------------------------------------

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class User(db.Model):
  """
  User model representing a user in the application.
  Inherits from db.Model to integrate SQLAlchemy.
  """
  __tablename__ = 'users'

  # Primary key
  id = db.Column(db.Integer, primary_key=True)
  # User's email, it is used as user identification during authentication so must be unique
  email = db.Column(db.String(60), unique=True, index=True)
  # User's password, stored as a hash
  password = db.Column(db.String(80))
  # User's role, used for role-based access control ("seeker" or "provider")
  role = db.Column(db.String(20), nullable=False)
  
  # One-Many relationship between User and Session
  sessions = db.relationship("Session", back_populates="user")


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
  def create_user(cls, email, password, role):
    """
    Create a new user with the provided details.

    Args:
        email (str): The user's email.
        password (str): The user's password, which will be hashed before storage.
        role (str): The user's role, either 'seeker' or 'provider'

    Returns:
        User: The newly created user object.
    """
    user = cls( role     = role.strip(),
                email    = email.strip(),
                password = bcrypt.generate_password_hash(password).decode('utf-8')
              )
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


class Session(db.Model):
  """Represents an authenticated session"""

  __tablename__ = 'sessions'
  
  # Primary key
  id = db.Column(db.Integer, primary_key=True)
  # ID of the authenticated user
  user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
  # Token associated with this session, should be unique
  token = db.Column(db.String, unique=True, nullable=False)

  # One-Many relationship between User and Session
  user = db.relationship("User", back_populates="sessions")


  @classmethod
  def create_session(cls, user_id):
    """
    Create a new session with the provided details.

    Args:
        user_id (str): The user's id

    Returns:
        Session: The newly created session object.
    """
    # Generate the token. Repeat until we get one that does not exist in the database.
    token = secrets.token_urlsafe(16)
    while (cls.session_exists(token)):
      token = secrets.token_urlsafe(16)
    
    # Create the session
    session = cls(user_id = user_id,
                  token   = token)
    db.session.add(session)
    db.session.commit()
    
    return session

  @staticmethod
  def session_exists(token):
    """
    Check if a session already exists.

    Args:
        token (str): the session token

    Returns:
        bool: True if session exists, False otherwise
    """
    token = Session.query.filter_by(token=token).first()
    return token is not None
  
  @staticmethod
  def get_by_token(token):
    """
    Retrieve a session by token

    Args:
        token (str): The token we are querying for

    Returns:
        Session: The session object if found, otherwise None.
    """
    return Session.query.filter_by(token=token).first()


# For populating the site with some default data for show:
def create_default_userbase():
  existing_seeker = User.get_by_email("seeker@gmail.com")
  if not existing_seeker:
     User.create_user("seeker@gmail.com", "123", "seeker")
  existing_provider = User.get_by_email("provider@gmail.com")
  if not existing_provider:
     User.create_user("provider@gmail.com", "123", "provider")

# Creates tables and default users
with app.app_context():
  db.create_all()
  create_default_userbase()



# ROUTES ----------------------------------------------------------------------

@app.route("/users", methods=['POST'])
def register():
  """
  Registers a new user.
  
  Expects a JSON payload with 'email' and 'password'.
  - If email doesn't already exist, creates a new user and an associated session
  - On success returns JSON with user id, role and session token.

  Returns:
      Response: JSON object with either an error or authentication details.
  """
  # Get data from the request
  data     = request.get_json()
  email    = data.get('email')
  password = data.get('password')
  role     = data.get('role')
  
  if not all([email, password, role]): # works because None = False
    return jsonify([{"error": "Missing required fields"}]), 400
  
  if (User.email_exists(email)):
    return jsonify({"error": "Email already exists"}), 400
  else:
    # Create user
    user = User.create_user(
      email    = email,
      password = password,
      role     = role
    )
    
    # Create an authenticated session for the user
    session = Session.create_session(user.id)
    
    return jsonify({"message": "Authenticated (user created)", 
                    "user_id": user.id,
                    "role": role,
                    "session_token": session.token
                    }), 201
  
  
@app.route("/sessions", methods=['POST'])
def login_authentication():
  """
  Validates the users credentials and logs them in by creating a new session.
  On sucess returns JSON with user id, role and the session token.

  Returns:
      Response: JSON object with either an error or authentication details.
  """
  # Get data from request and fetch User object from db
  data = request.get_json()
  email = data.get('email')
  password = data.get('password')
  user = User.get_by_email(email)

  # Check credentials:
  if user and user.check_password(password):
    # Valid credentials: create session and return user id, role and session token.
    session = Session.create_session(user_id=user.id)
    return jsonify({"message": "Authenticated (new token)", 
                    "user_id": user.id, 
                    "role": user.role,
                    "session_token": session.token
                    }), 201
  else:
    # Invalid credentials:
    return jsonify({"error": "Invalid credentials"}), 401


@app.route("/sessions/<string:token>", methods=['GET'])
def current_session(token):
  """
  Fetches session information for a given token.
  - If session with token exists return users id, role and session token.
  - If no session with token exists return error.

  Args:
      token (str): The session token

  Returns:
      Response: JSON object with either an error or session details.
  """
  # Find the session tied with the token (if any)
  session = Session.get_by_token(token)

  if not session:
    return jsonify({"error": "Invalid or expired token"}), 401
  else:
    # Session exists so we return relevant information
    user = User.get_by_id(session.user_id)
    return jsonify({
      "user_id": session.user_id,
      "role": user.role,
      "session_token": session.token
    }), 200


@app.route('/sessions/<string:token>', methods=['DELETE'])
def logout(token):
  """
    Deletes terminated session from the session table upon logout.

  Args:
      token (str): The token associated with the session to delete

  Returns:
      Response: JSON object with error or success message
  """
  session = Session.get_by_token(token)
  if not session:
    return jsonify({"error": "Session not found"}), 404
  
  # Delete session from table
  db.session.delete(session)
  db.session.commit()

  return jsonify({"message": "Logged out"}), 200