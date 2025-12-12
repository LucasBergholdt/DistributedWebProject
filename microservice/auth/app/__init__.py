import secrets
import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

app = Flask(__name__)

# Cofnigure SQLAlchemy ORM
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
# Secret key for session management and security features 
app.config['SECRET_KEY'] = "change-me" #TODO Needed?


# Data Model ------------------------------------------------------------------

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class User(db.Model):
  """
  User model representing a user in the application.
  Inherits from db.Model to integrate SQLAlchemy.
  """
  __tablename__ = 'users'

  id = db.Column(db.Integer, primary_key=True)
  # User's email, it is used as user identification during authentication so must be unique but it can be changed over time
  email = db.Column(db.String(60), unique=True, index=True)
  # User's password, stored as a hash
  password = db.Column(db.String(80))
  # User's role ('seeker' or 'provider')
  role = db.Column(db.String(20), nullable=False) #TODO: Could use seperate roles table for better scaling
  
  session = db.relationship("Session", back_populates="users")

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
    user = cls( email    = email.strip(),
                password = bcrypt.generate_password_hash(password).decode('utf-8'),
                role     = role)
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
  
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
  token = db.Column(db.String, unique=True, nullable=False) # should be unique
  created_at = db.Column(db.DateTime, default=db.func.now())
  expires_at = db.Column(db.DateTime, nullable=True)  # optional

  user = db.relationship("User", back_populates="sessions")

  @classmethod
  def create_session(cls, user_id, expiry_date=None):
    """
    Create a new session with the provided details.

    Args:
        user_id (str): The user's id
        expiry_date (DateTime, optional): The date the session should expire. Defaults to None.

    Returns:
        Session: The newly created session object.
    """
    # Generate the token. Repeat until we get one that does not exist in the database.
    token = secrets.token_urlsafe(16)
    while (cls.session_exists(token)):
      token = secrets.token_urlsafe(16)
      
    session = cls(user_id    = user_id,
                  token      = token,
                  expires_at = expiry_date)
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


# Clears the database and create tables within the application context
with app.app_context():
  # db.drop_all() #TODO
  db.create_all()



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
  
  # TODO: Bør man tjekke at email og password ikke er null. Vi laver jo altid en forms.validate inden, men kan kan vel teknisk set godt kalde uden det er gjort.
  # TODO: har gjort det for nu...
  if all([email, password, role]): # works because None = False
    return jsonify([{"error": "Missing required fields"}]), 400
  
  if (User.email_exists(email)):
    return jsonify({"error": "Email already exists"}), 400 #TODO: Security risk telling that email exists
  else:
    # Create user and a session
    user = User.create_user(
      email    = email,
      password = password,
      role     = role
    )
    
    session = Session.create_session(user.id)
    
    return jsonify({"message": "Authenticated (user created)", 
                    "user_id": user.id,
                    "role": role,
                    "session_token": session.token
                    }), 200
  
  
@app.route("/sessions", methods=['POST'])
def login_authentication():
  #TODO: Præciser rolle. Hvad er interfacet?
  """
  Login authentication;
  - Data modtages fra frontend, "/" route. 
  - Returnerer en respons, der afgør om brugere logges ind. 
  - En user login session repræsenteres derfor med post - vi laver en ny "session ressource".

  """
  # Get data from request
  data = request.get_json()
  token = data.get('session_token')
  email = data.get('email')
  password = data.get('password')
  user = User.get_by_email(email)

  # TODO: Vi sender aldrig en token med, men i guess det giver god defensive mening at lave dette tjek? Security risk uden?
  # If the token already exists, the user is already logged in.
  if token and Session.session_exists(token):
        session = Session.get_by_token(token)
        user = User.get_by_id(session.user_id)
        return jsonify({
            "message": "Token already exists",
            "user_id": session.user_id,
            "role": user.role,
            "session_token": session.token
        }), 200
  
  # Check credentials:
  if user and user.check_password(password):
    # Valid credentials: create session and return user id, role and session token.
    session = Session.create_session(user_id=user.id)
    return jsonify({"message": "Authenticated (new token)", 
                    "user_id": user.id, 
                    "role": user.role,
                    "session_token": session.token
                    }), 200
  else:
    # Invalid credentials:
    return jsonify({"error": "Invalid credentials"}), 401


@app.route("/sessions", methods=['GET'])
def current_session():
  #TODO: Burde man gøre det til /session/<token>? Vi prøver jo få en specifik session ud fra en token og ikke alle sessions
  """
  Fetches session information.
  
  Expectrs a JSON payload with 'session_token'.
  - If session with token exists return users id, role, session token and session creation date.
  - If no session with token exists return error.

  Returns:
      Response: JSON object with either an error or session details.
  """
  # Get the token from request params
  token = request.args.get("session_token")
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
      "session_token": session.token,
      "created_at": session.created_at.isoformat()  #TODO: Currently not used
    })


@app.route('/sessions', methods=['DELETE'])
def logout():
  """
  Deletes terminated session from the session table upon logout.

  Returns:
      Response: JSON object
  """

  token = request.args.get("session_token") # Request data fra frontend
  session = Session.get_by_token(token)
  if not session:
    return jsonify({"error": "Session not found"}), 404
  
  # Delete session from table
  db.session.delete(session)
  db.session.commit()

  return jsonify({"message": "Logged out"}), 200