from flask import Flask, current_app, session, redirect, render_template, request, url_for, flash, jsonify

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_bcrypt import Bcrypt
from flask_principal import Principal, Permission, RoleNeed, UserNeed, Identity, AnonymousIdentity, identity_changed, identity_loaded
import os



app = Flask(__name__)

# configure SQL Alchemy ORM, 
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
# WARNING: CSRF protection is disabled for simplicity in this demo
app.config['WTF_CSRF_ENABLED'] = False
# Secret key for session management and security features
app.config['SECRET_KEY'] = "change-me"

# Initialize SQLAlchemy and Bcrypt extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)  #object used for encrypting and decrypting.


# Initialize Principal Extension and create Permissions
principals = Principal(app)
seeker_permission = Permission(RoleNeed("seeker"))
provider_permission = Permission(RoleNeed("provider"))


# ---------------------------------- DATA MODEL -------------------------------
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
    # User's role, used for role-based access control. "seeker", "provider"
    role = db.Column(db.String(80), nullable=False)

    # Attributes of user. Mostly relevant for a Seeker. These fields can be left NULL for a Provider.
    description = db.Column(db.String(500), nullable=True)

    birthdate = db.Column(db.String(80), nullable=True)

    gender = db.Column(db.String(80), nullable=True)

    occupation = db.Column(db.String(80), nullable=True)

    image = db.Column(db.String(500), nullable=True)

    # One-Many relationship between User and Application
    applications = db.relationship("Application", back_populates="user")

    # One-Many relationship between User and Collective
    collectives = db.relationship("Collective", back_populates="user")

    def check_password(self, password):
        """
        Check if the provided password matches the stored hash.

        Args:
            password (str): The password to check.

        Returns:
            bool: True if the password matches, False otherwise.
        """
        return bcrypt.check_password_hash(self.password, password)

    #TODO: Mange felter bliver efterladt null. Lav evt ny side/viewfunction hvor user kan udfylde sine informationer.
    @classmethod
    def create_user(cls, role, name, email, password):
      """
      Create a new user with the provided details.

      Args:
          name (str): The user's name.
          email (str): The user's email.
          password (str): The user's password, which will be hashed before storage.

      Returns:
          User: The newly created user object.
      """
      
      user = cls( role     = role.strip(),
                  name     = name.strip(),
                  email    = email.strip(),
                  password = bcrypt.generate_password_hash(password).decode('utf-8'),

                )
                  # evt også image.
      db.session.add(user)
      db.session.commit()
      return user

      """ Brug til senere
                        description = description.strip(),
                  birthdate = birthdate.strip(),
                  gender = gender.strip(),
                  occupation = occupation.strip()
      
      
      """

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
      
class Collective(db.Model):
    __tablename__ = 'collectives'

    id = db.Column(db.Integer, primary_key=True)
    submitter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    description = db.Column(db.String(500))

    address = db.Column(db.String(500))
  
    space = db.Column(db.Integer())

    slotsTotal = db.Column(db.Integer())

    vacantSlots = db.Column(db.Integer())
  
    # Many-One relationship between Collective and User
    user = db.relationship("User", back_populates="collectives")
    # One-Many relationship between Collective and Application
    applications = db.relationship("Application", back_populates="collective")

    @staticmethod
    def get_all():
        """Get all Collectives"""
        return Collective.query.order_by(Collective.id).all()

    @staticmethod
    def get_by_submitter(user_id):
        """Get all Collectives submitted by a specific user"""
        return Collective.query.filter_by(submitter_id=user_id).all()
    
    @classmethod
    def create_collective(cls, submitter_id, address, space, slotsTotal, vacantSlots, description):
      """
      Create a new collective with the provided details.

      Args:
          name (str): The collective's name.
          email (str): The collective's email.
          password (str): The collective's password, which will be hashed before storage.

      Returns:
          collective: The newly created collective object.
      """
      
      collective = cls(
          submitter_id = submitter_id,
          address = address.strip(),
          space = space,
          slotsTotal = slotsTotal,
          vacantSlots = vacantSlots,
          description = description.strip()
      )
                  
      db.session.add(collective)
      db.session.commit()
      return collective


class Application(db.Model):
    """Placeholder Application model """
    __tablename__ = 'applications'

    id = db.Column(db.Integer, primary_key=True)
    submitter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    collective_id = db.Column(db.Integer, db.ForeignKey('collectives.id'), nullable=False)

    time_of_submission = db.Column(db.DateTime, nullable=True)  #TODO: Lav automatisk.
    description = db.Column(db.String(500))

    # Many-One relationship between Application and User
    user = db.relationship("User", back_populates="applications")

    # Many-One relationship between Application and Collective
    collective = db.relationship("Collective", back_populates="applications")

    @staticmethod
    def get_all():
        """Get all Applications"""
        return Application.query.order_by(Application.id).all()
    
    @staticmethod
    def get_by_submitter(user_id):
        """Get all Applications submitted by a specific user"""
        return Application.query.filter_by(submitter_id=user_id).all()
    
    @staticmethod
    def get_by_collective(collective_id):
        """Get all Applications submitted by a specific user"""
        return Application.query.filter_by(collective_id=collective_id).all()
    
    @classmethod  #Class Method: Static Method men som tager imod selve classen som første argument. Tillader os her at constructe en class user og returne den.
    def create_application(cls, submitter_id, collective_id,description):
      """
      Create a new application with the provided details.

      Args:
          name (str): The application's name.
          email (str): The application's email.
          password (str): The application's password, which will be hashed before storage.

      Returns:
          application: The newly created application object.
      """
      
      application = cls(
          submitter_id        = submitter_id,
          collective_id       = collective_id,
          description         = description.strip(),
      )
                  
      db.session.add(application)
      db.session.commit()
      return application
    

# Debug Purposes
def create_default_userbase():
  existing_seeker = User.query.filter_by(role="seeker").first()
  if not existing_seeker:
     User.create_user("seeker", "Bob", "seeker@gmail.com", "123")
  existing_provider = User.query.filter_by(role="provider").first()
  if not existing_provider:
     User.create_user("provider", "Alice", "provider@gmail.com", "123")

# Debug Purposes
def create_default_collectives_applications():
  Collective.create_collective(2, "Skovbogade", 50, 5, 2, "Et dejligt kollektiv i Odense By") #submitterID = 2. provider@gmail.com.
  Application.create_application(1, 1, "Jeg hedder Alice og vil gerne søge ind på kollektivet på Skovbogade.")

# Clears the database and create tables within the application context
with app.app_context():
  db.drop_all()
  db.create_all()
  create_default_userbase()
  create_default_collectives_applications()



# SESSIONS --------------------------------------------------------------------

# Initialize the LoginManager with the Flask application
login_manager = LoginManager(app)
# Set the view to redirect to for unauthorized users (e.g., when @login_required is used)
login_manager.login_view = 'login'
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

# Flask Principal identity_loaded signal handler. Called when identity_loaded signal has been called.
@identity_loaded.connect_via(app) # DEBUG: Denne manglede.
def on_identity_loaded(sender, identity):
    #Set the identity user object
    identity.user = current_user

    # Add the UserNeed to the identity (Note. Needs should be understood as Access-Control priviledges)
    if hasattr(current_user, 'id'):
        identity.provides.add(UserNeed(current_user.id))
    
    # Add the Role to the identity.
    if hasattr(current_user, 'role'):
        identity.provides.add(RoleNeed(current_user.role))


# Routes ----------------------------------------------------------------------
# LOGIC skal bruge USER_id.

"""
LOGIC:
@app.route("/applications/<int:id>")
  methods: DELETE, POST, GET
  skal også understøtte en parameter.




@app.route("/collectives/<int:id>")
  methods: DELETE, POST, GET


"""
# Fetches all applications. TODO: Support a parameter to fetch only list of applications.
    # - List of Seeker's Applications
    # - List of Provider's Applications
@app.route("/applications", methods=["GET"])
def get_applications():
    applications = Application.get_all()
    return jsonify([{
       "id": e.id, 
       "submitter_id": e.submitter_id, 
       "collective_id": e.collective_id,
       "time_of_submission": e.time_of_submission,
       "description": e.description}
    for e in applications])  # Liste af json objekter.


@app.route("/applications", methods=["POST"])
def get_applications():
    data = request.get_json()
    description = data.get('description')
    if not description:
        return jsonify({"error": "description is required"}), 400
    user_id = data.get('user_id')


    application = Application.create_application(description=description)
    Application(description=description)
    db.session.add(application)
    db.session.commit()
    return jsonify({"id": application.id, "text": application.text}), 201


@app.route("/applications/<int:id>", methods=["DELETE"])
def get_applications(id):
    application = Application.query.get(id)
    if not application:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(application)
    db.session.commit()
    return jsonify({"message": "Deleted"}), 200


# Fetches all collectives. TODO: Support a parameter to fetch only list of collectives.
    # - List of Seeker's Collectives (that he applied for)
    # - List of Provider's Collectives
@app.route("/collectives", methods=["GET"])
def get_collectives():
    collectives = Collective.get_all()
    return jsonify([{
       "id": e.id, 
       "submitter_id": e.submitter_id, 
       "description": e.description,
       "address": e.address,
       "space": e.space,
       "slotsTotal": e.slotsTotal,
       "vacantSlots": e.vacantSLots}
    for e in collectives])  # Liste af json objekter.

@app.route("/collectives", methods=["POST"])
def get_collectives():
    data = request.get_json()
    text = data.get('text')
    if not text:
        return jsonify({"error": "Text is required"}), 400
    collective = Collective(text=text)
    db.session.add(collective)
    db.session.commit()
    return jsonify({"id": collective.id, "text": collective.text}), 201

@app.route("/collectives/<int:id>", methods=["DELETE"])
def get_collectives(id):
    collective = Collective.query.get(id)
    if not collective:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(collective)
    db.session.commit()
    return jsonify({"message": "Deleted"}), 200

@app.route("/collectives/<int:id>/applications", methods=["GET"])
def get_collectives(id):
    applications = Application.get_by_collective(id)
    return jsonify([{
       "id": e.id, 
       "submitter_id": e.submitter_id, 
       "collective_id": e.collective_id,
       "time_of_submission": e.time_of_submission,
       "description": e.description}
    for e in applications])  # Liste af json objekter.









# ------------ Users --------------------
@app.route("/applications", methods=["GET"])
def get_applications():
    applications = Application.get_all()
    return jsonify([{
       "id": e.id, 
       "submitter_id": e.submitter_id, 
       "collective_id": e.collective_id,
       "time_of_submission": e.time_of_submission,
       "description": e.description}
    for e in applications])  # Liste af json objekter.



@app.route("/applications", methods=["POST"])
def get_applications():
    data = request.get_json()
    text = data.get('text')
    if not text:
        return jsonify({"error": "Text is required"}), 400
    application = Application(text=text)
    db.session.add(application)
    db.session.commit()
    return jsonify({"id": application.id, "text": application.text}), 201


@app.route("/applications/<int:id>", methods=["DELETE"])
def get_applications(id):
    application = Application.query.get(id)
    if not application:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(application)
    db.session.commit()
    return jsonify({"message": "Deleted"}), 200