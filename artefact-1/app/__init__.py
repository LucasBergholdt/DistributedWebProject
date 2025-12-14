# Command-Line Execution: flask run --debug
from datetime import date
from flask import Flask, current_app, session, redirect, render_template, request, url_for, flash

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_bcrypt import Bcrypt
from flask_principal import Principal, Permission, RoleNeed, UserNeed, Identity, AnonymousIdentity, identity_changed, identity_loaded
from wtforms import DateField, IntegerField, DateTimeField, DecimalField, FileField, Form, RadioField, SubmitField, SelectField, StringField, EmailField, PasswordField, BooleanField, TextAreaField, ValidationError
from wtforms.validators import DataRequired, Length, Email, EqualTo, InputRequired, Optional
from werkzeug.utils import secure_filename
import os

#flask_wtf
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True # FOR DEBUGGING PURPOSE

# Configure SQLAlchemy ORM to use SQLite database file 'flask.db'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///flask.db"
# WARNING: CSRF protection is disabled for simplicity in this demo
app.config['WTF_CSRF_ENABLED'] = False
# Secret key for session management and security features
app.config['SECRET_KEY'] = "change-me"

# Configure app for images

UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize SQLAlchemy and Bcrypt extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)  #object used for encrypting and decrypting.


# Initialize Principal Extension and create Permissions
principals = Principal(app)
seeker_permission = Permission(RoleNeed("seeker"))
provider_permission = Permission(RoleNeed("provider"))


# -------------------- MODEL ----------------------- #


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
    # name = db.Column(db.String(80), nullable=False)
    # User's role, used for role-based access control. "seeker", "provider"
    role = db.Column(db.String(80), nullable=False)

    # One-Many relationship between User and Application
    applications = db.relationship("Application", back_populates="user")

    # One-Many relationship between User and Collective
    collectives = db.relationship("Collective", back_populates="user")

    #seekerprofile = db.relationship("Seekerprofile", back_populates="user")

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
    def create_user(cls, role, email, password):
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
                  email    = email.strip(),
                  password = bcrypt.generate_password_hash(password).decode('utf-8'),
                )
                  # evt også image.
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
    

class SeekerProfile(db.Model):

    __tablename__ = 'seekerprofiles'

    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    name = db.Column(db.String(80), nullable=True)
    description = db.Column(db.String(500), nullable=True)
    birthdate = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(80), nullable=True)
    occupation = db.Column(db.String(80), nullable=True)
    image = db.Column(db.String(500), nullable=True)    # TODO: fully support this


    #user = db.relationship("User", back_populates="seekerprofile")

    #TODO: Mange felter bliver efterladt null. Lav evt ny side/viewfunction hvor user kan udfylde sine informationer.
    @classmethod
    def create_seekerprofile(cls, user_id, name, description, birthdate, gender, occupation, image):
        """
        Create a new seeker profile with the provided details.

        Args:
            user_id (int): User's id
            name (str): User's name
            description (str): A description of the user
            birthdate (Date): User's date of birth
            gender (str): User's gender
            occupation (str): User's occupation
            image (str): User's profile picture

        Returns:
            SeekerProfile: The newly created profile object
        """
        print("DEBUG: Entered create_seekerprofile")
        if birthdate:
            birthdate = (date.fromisoformat(birthdate))
        #TODO Har fjernet .strip() fordi felterne godt kan være None. Men vi skal nok stadig have strip funktionalitet.
        seekerprofile = cls(
                            user_id = user_id,
                            name = name,
                            description = description,
                            birthdate = birthdate,
                            gender = gender,
                            occupation = occupation,
                            image = image
                            )
        db.session.add(seekerprofile)
        print("DEBUG: About to commit new profile")
        db.session.commit()
        print("DEBUG: Commit succesful")
        return seekerprofile
      
      
class Collective(db.Model):
    __tablename__ = 'collectives'

    id = db.Column(db.Integer, primary_key=True)
    submitter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # description = db.Column(db.String(500))

    city = db.Column(db.String(500))
    street = db.Column(db.String(500))

    price = db.Column(db.Integer())

    # address = db.Column(db.String(500))

    roomsize = db.Column(db.Integer())
    image = db.Column(db.String(500))
  
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
    
    def get_by_city(city):
        """Get all Collectives which cityname has given argument as prefix)"""
        return Collective.query.filter(Collective.city.startswith(city)).all()
    
    @classmethod
    def create_collective(cls, submitter_id, city, street, roomsize, price, image):
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
          price = price,
          city = city.strip(),
          street = street.strip(),
          roomsize = roomsize,
          image = image.strip()
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
          description     =description.strip(),
      )
                  
      db.session.add(application)
      db.session.commit()
      return application
    

# Debug Purposes
def create_default_userbase():
  existing_seeker = User.query.filter_by(role="seeker").first()
  if not existing_seeker:
     User.create_user("seeker", "seeker@gmail.com", "123")
  existing_provider = User.query.filter_by(role="provider").first()
  if not existing_provider:
     User.create_user("provider", "provider@gmail.com", "123")

# Debug Purposes
def create_default_collectives_applications():
  Collective.create_collective(2, "Odense C", "Vindegade", 50, 2569, "1.jpg") #submitterID = 2. provider@gmail.com.
  Collective.create_collective(2, "Odense M", "Bogense", 23, 5000, "2.jpg") #submitterID = 2. provider@gmail.com.
  Collective.create_collective(2, "Odense M", "Stige", 35, 4000, "3.jpg") #submitterID = 2. provider@gmail.com.

  # Application.create_application(1, 1, "Jeg hedder Alice og vil gerne søge ind på kollektivet på Skovbogade.")



# Clears the database and create tables within the application context
with app.app_context():
  db.drop_all()
  db.create_all()
  create_default_userbase()
  create_default_collectives_applications()




# -------------------------------- FORMS ------------------------------------- #
# Custom validator to check if an email already exists
# In WTForms custom validators must accept parameters form and field. So it is specified here even though it is not used.
def email_exists(form, field):
  if User.email_exists(field.data):
    raise ValidationError('Email already exists.')

# WTForms for user registration.
class RegistrationForm(Form):
  role = SelectField('Role', 
                         choices=[('seeker', 'Seeker'), ('provider', 'Provider')], 
                         validators=[DataRequired()])
  # name = StringField('Name', validators=[DataRequired(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  email = EmailField('Email', validators=[DataRequired(), email_exists, Email()])
  password = PasswordField('Password', validators=[DataRequired(), EqualTo('confirm', message='Password must match')])
  confirm = PasswordField('Confirm', validators=[DataRequired()])
  submit = SubmitField('Register')


class ProfileForm(FlaskForm):
  name = StringField('Name', validators=[Optional(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  description = TextAreaField('About you', validators=[Optional(), Length(max=500, message='You cannot have more than 500 characters')])
  birthdate = DateField('Birthdate', format="%Y-%m-%d", validators=[Optional()])
  gender = RadioField('Gender', choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], validators=[Optional()])
  occupation = StringField('Occupation', validators=[Optional(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  image = FileField(validators=[FileRequired()])
  submit = SubmitField('Save Profile')


class CollectiveForm(FlaskForm):
  #address = StringField('Address of collective', validators=[DataRequired(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  city = StringField('Name of city', validators=[DataRequired(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  street = StringField('Name of street', validators=[DataRequired(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])

  roomsize = IntegerField('Size of the room available (square meters)', validators=[DataRequired()])

  price = IntegerField('Price in DKK', validators=[DataRequired()])

  image = FileField(validators=[FileRequired()])

  submit = SubmitField('Register your collective')

class ApplicationForm(Form):
  description = StringField('Your application', validators=[DataRequired(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  submit = SubmitField('Apply for this collective')

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

#-------------------------- ROUTES -----------------------------------------------------------------------

@app.route("/", methods=('GET', 'POST'))
def landing():
  """
  TO MULIGE DESIGN:
  1. ALLE, ANONYME OG BRUGERE, FØRES HERTIL
  2. KUN ANONYME BRUGERE FØRES HERTIL
  HVAD SYNES I?

  Landing page for  visitorS.
  """

  ## Løsning 1: LOgget ind brugere kan ikke tilgå landing? 
  # if current_user.is_authenticated:
  #   # flash('You are already logged in.','info')
  #   role = User.get_by_id(current_user.get_id()).role   
  #   if role == "provider":
  #      return redirect(url_for("provider"))
  #   else: 
  #     return redirect(url_for("overview"))

# løsning 2: alle brugere kan altid komme til landing. (LIGE NU)

  return render_template("landingpage.html")

@app.route("/login", methods=('GET','POST'))
def login():
    """
    Main page:
    - If the user is already authenticated, redirects to the personal page.
    - If not, displays the login form and processes login attempts.
    - On successful login, redirects to the proper page (e.g. seeker).
    - On failed login, flashes an error message and redisplays the login form.
    """
    if current_user.is_authenticated:
      flash('You are already logged in.','info')
          # role = User.get_by_id(current_user.get_id()).role
      return redirect(url_for("overview"))
    else:
        form = LoginForm(request.form)
        if request.method == 'POST' and form.validate():
            user = User.get_by_email(form.email.data.strip())
            if user and user.check_password(form.password.data.strip()):
                # If the user credentials are correct, start an authenticated session
                login_user(user, form.remember.data)

                # Tell Flask-Principal the identity has changed
                identity_changed.send(current_app._get_current_object(), identity=Identity(user.id))

                # Redirect to proper role.
                return redirect(url_for("landing"))
            else:
                # Otherwise, display an error message and display the login form again
                flash("Invalid credentials","error")
        return render_template('login.html', form=form)

@app.route("/register", methods=('GET','POST'))
def register():
  if current_user.is_authenticated:
    flash('You are already logged in.','info')
    role = User.get_by_id(current_user.get_id()).role
    return redirect(url_for(role))
  else:
    form = RegistrationForm(request.form)

    if request.method == 'POST' and form.validate():
      User.create_user(
                      role = form.role.data,
                      email = form.email.data,
                      password = form.password.data
                      )
      flash("User created.","success")

      return redirect(url_for('login'))
    elif request.method == 'POST':
      flash("post bracket entered but form not validated.","Debug:")  # Only for debug purposes.
    return render_template('register.html', form=form, error="Invalid input")

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

""" LAYOUT OF WEBPAGE:


Seekers:
  GET: /seeker. 
    - Displays all Collectives by their address (and PrimaryID?). Has a "apply" next to them.
    - Displays all your Applications (by ApplicationID and CollectiveAddress)
  GET: /apply/<int:id>: Applies for a specific collective. Displays application form.
  POST: /apply/<int:id>: Sends application form and redirects to seeker URL.

Providers:
  GET: /provider. 
      - Displays all Applications assigned to your collectives (collectives with your ID on).
      - Displays all your collectives.
      - Offers you to construct new collective. /newCollective

  GET: /newCollective.
      - Displays CollectiveForm.
  POST: /newCollective.
      - Uploads database and redirects to /provider.
"""

## GAMMMEL "SEEKER" TILGANG
# @app.route("/seeker",methods=["GET","POST"])  #TODO: Fjern POST? Bruges ikke.
# @login_required
# @seeker_permission.require()
# @app.route("/home",methods=["GET"])
# def home():
#   if not (current_user.is_authenticated):
#      return redirect(url_for("login"))
#   elif (current_user.role == "seeker"): 
#      return redirect(url_for("seeker"))
#   else:
#      return redirect(url_for("provider"))


# ------------------------- Seeker Routes ---------------------------------
@app.route("/overview", methods=["GET","POST"])
def overview():
    city = request.args.get("city", type=str)
    if city is not None:
        collective_entries = Collective.get_by_city(city) # returner alle som starter med dette city-navn.
    else:
       collective_entries = Collective.get_all()

    # TODO: HVIS LOGGET IND --- implementer yderligere!!
    # E.G ABILITY TO APPLY BASED ON ROLE

     #  your_applications = current_user.applications
      # Collective.get_by_submitter(current_user.id)
      # som argument: your_applications=your_applications
      
    return render_template("overview.html", collective_entries=collective_entries)


#! TODO: NEEDS OVERHAUL.
@app.route("/seekerprofile",methods=["GET","POST"])
@login_required
@seeker_permission.require()
def seekerprofile():
    form = ProfileForm(request.form)

    if form.validate_on_submit():
      f = form.image.data
      filename = secure_filename(f.filename)
      filepath = os.path.join(
          app.config['UPLOAD_FOLDER'], filename
      )
      f.save(filepath)

      SeekerProfile.create_seekerprofile(
          current_user.id, 
          form.name.data,
          form.description.data,
          form.birthdate.data,
          form.gender.data,
          form.occupation.data,
          filename
          )
      return redirect(url_for("seeker"))
    return render_template("seekerprofile.html", form=form)

# ------------------------- Provider Routes ---------------------------------
@app.route("/provider",methods=["GET","POST"])
@login_required
@provider_permission.require()
def provider():
    # Get all collectives that Provider owns. Done directly by accessing foreign keys.
    # evt. anvend user.collectives (vha. db.relationship())
    collective_entries = Collective.get_by_submitter(current_user.id)
  
    # Get all applications mapped to these collectives.
    #application_entries = [
    #  application
    #  for collective in collective_entries
    #    for application in collective.applications  #relationship() anvendes.
    #]
    return render_template("provider.html", collective_entries=collective_entries)

@app.route("/new_collective", methods=["GET", "POST"])
@login_required
@provider_permission.require()
def new_collective():
  form = CollectiveForm()

  if form.validate_on_submit():
      f = form.image.data
      filename = secure_filename(f.filename)
      filepath = os.path.join(
          app.config['UPLOAD_FOLDER'], filename
      )
      f.save(filepath)

      Collective.create_collective(
          current_user.id, 
          form.city.data,
          form.street.data,
          form.roomsize.data,
          form.price.data,
          filename
          )
      return redirect(url_for("provider"))
  return render_template("new_collective.html", form=form)

# Only Providers can do this. Security Flaw: Providers can remove another provider's collective.
@login_required
@provider_permission.require()
@app.route("/delete_collective/<int:id>")
def delete_collective(id):
  collective = Collective.query.filter_by(id=id).first()
  if collective:
      # Delete all applications directed to this collective and the collective itself.
      for app in collective.applications:
        db.session.delete(app)
      db.session.delete(collective)
      db.session.commit()
      msg = collective.address + " and all corresponding applications has been deleted."
      flash(msg, 'info')

  else:
    flash("Sorry, we couldn't find the collective that you wanted to delete.", 'warning')
  return redirect(url_for('provider'))


# ------------ Routes for both roles ------------------

# Both seekers and providers can do this now. Security Flaw: Providers can remove another provider's application. Same goes for seekers.
@login_required
@app.route("/delete_application/<int:id>")
def delete_application(id):
    application = Application.query.filter_by(id=id).first()
    if application:
        db.session.delete(application)
        db.session.commit()
        flash("Application has been deleted.", 'info')
    else:
      flash("Sorry, we couldn't find the application that you wanted to delete.", 'warning')
    return redirect(url_for(current_user.role))


# Not used:
@app.route("/apply/<int:id>", methods=["GET", "POST"])
@login_required
@seeker_permission.require()
def apply(id):
  """For applying to a collective.
  """
  form = ApplicationForm(request.form)
  if request.method == 'POST' and form.validate():
      Application.create_application(current_user.id, id, form.description.data)
      return redirect(url_for("seeker"))
  return render_template("apply.html", form=form)
