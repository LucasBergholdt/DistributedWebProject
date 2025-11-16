# Command-Line Execution: flask run --debug
from flask import Flask, current_app, session, redirect, render_template, request, url_for, flash

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from flask_principal import Principal, Permission, RoleNeed, UserNeed, Identity, AnonymousIdentity, identity_changed, identity_loaded

from wtforms import Form, SubmitField, SelectField, StringField, EmailField, PasswordField, BooleanField, ValidationError
from wtforms.validators import DataRequired, Length, Email, EqualTo

from .forms import RegistrationFormSeeker, RegistrationFormProvider, LoginForm



app = Flask("Flask Session")

# Configure SQLAlchemy ORM to use SQLite database file 'flask.db'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///flask.db"
# WARNING: CSRF protection is disabled for simplicity in this demo
app.config['WTF_CSRF_ENABLED'] = False
# Secret key for session management and security features
app.config['SECRET_KEY'] = "change-me"

# Initialize SQLAlchemy and Bcrypt extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)  #object used for encrypting and decrypting.


# Abstract User Class!
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

    # Description of user
  description = db.Column(db.String(500))



  def check_password(self, password):
    """
    Check if the provided password matches the stored hash.

    Args:
        password (str): The password to check.

    Returns:
        bool: True if the password matches, False otherwise.
    """
    return bcrypt.check_password_hash(self.password, password)

  @classmethod  #Class Method: Static Method men som tager imod selve classen som første argument. Tillader os her at constructe en class user og returne den.
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
                password = bcrypt.generate_password_hash(password).decode('utf-8') )
    db.session.add(user)
    db.session.commit()
    return user

  @staticmethod #Static Method. Modtager ikke et implicit first argument.
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
  
class Seeker(User):
    __tablename__ = 'seekers'

    birthdate = db.Column(db.String(80))

    gender = db.Column(db.String(80))

    occupation = db.Column(db.String(80))

    image = db.Column(db.String(500))


class Provider(User):
    __tablename__ = 'providers'

    address = db.Column(db.String(500))
  
    space = db.Column(db.Integer())

    slotsTotal = db.Column(db.Integer())

    vacantSlots = db.Column(db.Integer())

    # images?

class Application(db.Model):
    """Placeholder Application model """
    __tablename__ = 'applications'

    id = db.Column(db.Integer, primary_key=True)
    submitter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    time_of_submission = db.Column(db.DateTime, nullable=False)

    status = db.Column(db.Enum('unhandled', 'forwarded', 'approved', 'rejected', 'needs_info', name='Application_status'), default='unhandled')

    # Relationship: one Application has one user
    user = db.relationship('User', back_populates='Applications')

    # TODO: Skal nok være statitc methods eller have self som første parameter? Kan egentlig godt lide Application.get_all() f.eks. -> mere deskriptivt.
    def get_all():
        """Get all Applications"""
        return Application.query.all()

    def get_by_submitter(user_id):
        """Get all Applications submitted by a specific user"""
        return Application.query.filter_by(submitter_id=user_id).all()
    
    def get_managed_Applications(user):
        """Get all Applications from users managed by the given user"""
        managed_user_ids = [u.id for u in user.managed_users]
        return Application.query.filter(Application.submitter_id.in_(managed_user_ids)).all()
    
    def can_update(self, user):
        """Returns whether a user can change status and all the allowed statuses to choose from: (bool, allowed_statuses)"""
        role = user.role.name
        if role == "accountant" and self.status != "approved":
            return True, ["forwarded", "rejected"]
        elif role == "manager" and self.submitter_id != user.id and self.status == "forwarded":
            return True, ["approved", "rejected", "needs_info"]
        elif role == "admin":
            return True, ["unhandled", "forwarded", "approved", "rejected", "needs_info"]
        else:
            return False, []

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


# ROUTES -----------------------------------------------------------------------

########### CONTROLLER ###############

# Lasse: Jeg tænker jeg på, om den logik vi bruger i vores view (templates) med Jinja, også overlapper lidt med 
# Controller-ansvar. Måske ikke?

@login_manager.user_loader
def load_user_from_id(id):
    return User.get_by_id(id)

# Flask Principal identity_loaded signal handler. Called when identity_loaded signal has been called.
@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
  #Set the identity user object
    identity.user = current_user

  # Add the UserNeed to the identity (Note. Needs should be understood as Access-Control priviledges)
    if hasattr(current_user, 'id'):
        identity.provides.add(UserNeed(current_user.id))
    
    # Add the Role to the identity.
    if hasattr(current_user, 'role'):
        identity.provides.add(RoleNeed(current_user.role))

    # if User isinstance of Seeker, så lav identity.provides.add(RoleNeed("seeker"")). Ellers så det andet.
    if isinstance(current_user, Seeker):
       identity.provides.add(RoleNeed("seeker"))
    elif isinstance(current_user, Provider):
       identity.provides.add(RoleNeed("provider"))

@app.route("/", methods=('GET','POST'))
def login():
    """
    Main page:
    - If the user is already authenticated, redirects to the personal page.
    - If not, displays the login form and processes login attempts.
    - On successful login, redirects to the proper page (e.g. salesman).
    - On failed login, flashes an error message and redisplays the login form.
    """
    if current_user.is_authenticated:
        flash('You are already logged in.','info')

        if isinstance(current_user, Seeker):
            return redirect(url_for('seeker'))
        elif isinstance(current_user, Provider):
            return redirect(url_for('provider'))
        
    else:
        form = LoginForm(request.form)
        if request.method == 'POST' and form.validate():
            user # Instantiér og sæt i IF-clauses.
            if form.type.data == "Seeker":
                user = Seeker.get_by_email(form.email.data.strip())
            elif form.type.data == "Provider":
                user = Provider.get_by_email(form.email.data.strip())

            if user and user.check_password(form.password.data.strip()):
                # If the user credentials are correct, start an authenticated session
                login_user(user, form.remember.data)

                # Tell Flask-Principal the identity has changed
                identity_changed.send(current_app._get_current_object(), identity=Identity(user.id))

                # Redirect to proper role.
                if isinstance(user, Seeker):
                   redirect(url_for('seeker'))
                elif isinstance(user, Provider):
                   redirect(url_for('provider'))
            else:
                # Otherwise, display an error message and display the login form again
                flash("Invalid credentials","error")
        return render_template('login.html', form=form)
    
@app.route("/register", methods=('GET','POST'))
def register():  
  return render_template('register.html', error="Invalid input")

@app.route("/register/seeker", methods=('GET','POST'))
def registerseeker():
  form = RegistrationFormSeeker(request.form)

  if request.method == 'POST' and form.validate():
    Seeker.create_user(
                    name = form.name.data,
                    email = form.email.data,
                    password = form.password.data,
                    birthdate = form.birthdate.data,
                    gender = form.gender.data,
                    occupation = form.occupation.data,
                    image = form.image.data,
                    description = form.description.data
                    )
    flash("User created.","success")

    return redirect(url_for('seeker'))    
  
  return render_template('registerseeker.html', form=form, error="Invalid input")

@app.route("/register/provider", methods=('GET','POST'))
def registerprovider():
  form = RegistrationFormProvider(request.form)

  if request.method == 'POST' and form.validate():
    Provider.create_user(
                    name = form.name.data,
                    email = form.email.data,
                    password = form.password.data,
                    address = form.address.data,
                    space = form.space.data,
                    slotsTotal = form.slotsTotal.data,
                    vacantSlots =form.vacantSlots.data,
                    description = form.description.data
                    )
    flash("User created.","success")

    return redirect(url_for('provider'))    
  
  return render_template('registerprovider.html', form=form, error="Invalid input")

@app.route('/logout', methods=['GET'])
@login_required
def logout():
     # Remove the user information from the session
    logout_user()

    # Remove session keys set by Flask-Principal
    for key in ('identity.name', 'identity.auth_type'):
        session.pop(key, None)

    # Tell Flask-Principal the user is anonymous
    identity_changed.send(current_app._get_current_object(),
                          identity=AnonymousIdentity())
    return redirect(url_for('login'))






# --------- Routes for Receipts ----------------------------------------------------------------------
# Dette er placeholders, skal implementeres.

# Disse skal muligvis bare implementeres som ét view, der så betinget af logik, indeholder forskellige ting.
# Ellers bliver det meget gentagende? /Lasse

# Jeg synes vi skal tænke over, hvordan vi kan vi få så meget SOLID og OOP med - måske svært med vores framework.
# Men ellers må vi redegøre for "Code Smell" i rapporten? :) /Lasse

# seeker
@app.route("/seeker",methods=["GET","POST"])
@login_required
def seeker():
  form = ReceiptForm(request.form)
  if request.method == 'POST' and form.validate():
    text = form.text.data
    db.session.add(Receipts(text = text))
    db.session.commit()
  entries = Receipts.query.order_by(Receipts.id).all()
  return render_template("seeker.html", entries=entries, form=form)


# provider
@app.route("/provider",methods=["GET","POST"])
@login_required
@accountant_permission.require()
def accountant():
  form = ReceiptForm(request.form)
  if request.method == 'POST' and form.validate():
    text = form.text.data
    db.session.add(Receipts(text = text))
    db.session.commit()
  entries = Receipts.query.order_by(Receipts.id).all()
  return render_template("accountant.html", entries=entries, form=form)






# manager
@app.route("/manager",methods=["GET","POST"])
@login_required
@manager_permission.require()
def manager():
  form = ReceiptForm(request.form)
  if request.method == 'POST' and form.validate():
    text = form.text.data
    db.session.add(Receipts(text = text))
    db.session.commit()
  entries = Receipts.query.order_by(Receipts.id).all()
  return render_template("manager.html", entries=entries, form=form)

### Ved ikke om vi skal beholde lige præcis denne mulighed, men lader den bare være her.

@app.route("/delete/<int:id>")
def delete(id):
  """For deleting receipts.
  
  """
  entry = Receipts.query.filter_by(id=id).first()
  if entry:
    db.session.delete(entry)
    db.session.commit()
    flash('Entry deleted.', 'info')
  else:
    flash("Sorry, we couldn't find the entry that you wanted to delete.", 'warning')

  role = current_user.role
  return redirect(url_for(role))

# admin
@app.route('/admin')
@admin_permission.require()
def admin():
    users = User.query.order_by(User.id).all()
    return render_template('admin.html', users=users)

##### Routes for Admin capabilities ######
@app.route("/delete_user/<int:id>")
def delete_user(id):
  user = User.query.filter_by(id=id).first()
  if user:
       db.session.delete(user)
       db.session.commit()
       msg = user.name + " has been deleted."
       flash(msg, 'info')
  else:
    flash("Sorry, we couldn't find the user that you wanted to delete.", 'warning')
  return redirect(url_for('admin'))

@app.route("/upgrade_role/<int:id>")
def upgrade_role(id):
  user = User.query.filter_by(id=id).first()
  if user:
    user.role = 'manager'
    db.session.commit()
    msg = user.name + " has been changed to Manager"
    flash(msg, 'info')
  else:
    flash("Sorry, we couldn't find the user that you wanted to upgrade to admin.", 'warning')
  
  return redirect(url_for('admin'))

@app.route("/degrade_role/<int:id>")
def degrade_role(id):
  user = User.query.filter_by(id=id).first()
  if user:
      user.role = 'salesman'
      db.session.commit()
      msg = user.name + " has been changed to Salesman"
      flash(msg, 'info')
  else:
    flash("Sorry, we couldn't find the admin that you wanted to degrade to user.", 'warning')
  
  return redirect(url_for('admin'))




