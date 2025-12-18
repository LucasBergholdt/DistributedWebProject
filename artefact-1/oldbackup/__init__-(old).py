# Command-Line Execution: flask run --debug
from datetime import date
import uuid
from flask import Flask, current_app, session, redirect, render_template, request, url_for, flash

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_bcrypt import Bcrypt
from flask_principal import Principal, Permission, RoleNeed, UserNeed, Identity, AnonymousIdentity, identity_changed, identity_loaded
from wtforms import DateField, IntegerField, DateTimeField, DecimalField, FileField, Form, RadioField, SubmitField, SelectField, StringField, EmailField, PasswordField, BooleanField, TextAreaField, ValidationError
from wtforms.validators import DataRequired, Length, Email, EqualTo, InputRequired, Optional
# from wtforms.widgets import TextArea
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

# # Configure app for images

# UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'images')
# ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# def is_allowed_file_extension(filename):
#     return '.' in filename and \
#            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
           
           
# def save_image(form_image):
#     """
#     Saves the uploaded image with a unique name in the upload folder.

#     Args:
#         form_image: The file object from a form (e.g. form.image.data)

#     Returns:
#         str | None: The unique filename if saved successfully, otherwise None
#     """
#     # Check if file was uploaded
#     if not form_image or not form_image.filename:
#         return None

#     # Get secure version of provided filename
#     filename = secure_filename(form_image.filename)
    
#     # Check that file has an allowed extension
#     if not is_allowed_file_extension(filename):
#         return None
    
#     # Generate a random uuid string and add it to the filename, to ensure unique filenames
#     random_str = uuid.uuid4().hex
#     stored_name = random_str + filename
#     # Store the image in the upload folder
#     filepath = os.path.join(app.config['UPLOAD_FOLDER'], stored_name)
#     form_image.save(filepath)
    
#     return stored_name
  

# def delete_picture(filename):
#     """
#     Deletes a file from the upload folder

#     Args:
#         filename (str): The name of the file
#     """
#     # Do nothing if filename is null or empty
#     if not filename:
#         return
#     else:
#         # Delete the file from the upload folder
#         filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#         if os.path.exists(filepath):
#             os.remove(filepath)
            

# Initialize SQLAlchemy and Bcrypt extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)  #object used for encrypting and decrypting.


# Initialize Principal Extension and create Permissions
principals = Principal(app)
seeker_permission = Permission(RoleNeed("seeker"))
provider_permission = Permission(RoleNeed("provider"))


# # -------------------- MODEL ----------------------- #


# class User(UserMixin, db.Model):
#     """
#     User model representing a user in the application.
#     Inherits from both UserMixin and db.Model to integrate Flask-Login and SQLAlchemy.

#     UserMixin provides default implementations for the methods that Flask-Login
#     expects user objects to have:
#     - is_authenticated: Property that should return True if the user is authenticated.
#     - is_active: Property that should return True if the user is active.
#     - is_anonymous: Property that should return False for regular users.
#     - get_id(): Method that returns a unique identifier for the user as a string.

#     By inheriting from UserMixin, the User class automatically gets these methods,
#     making it compatible with Flask-Login's user management system.
#     """

#     __tablename__ = 'users'

#     # Primary key
#     id = db.Column(db.Integer, primary_key=True)
#     # User's email, it is used as user identification during authentication so must be unique but it can be changed over time
#     email      = db.Column(db.String(60), unique=True, index=True)
#     # User's password, stored as a hash
#     password   = db.Column(db.String(80))
#     # User's name, not used for identification (just an example of an extra field)
#     # name = db.Column(db.String(80), nullable=False)
#     # User's role, used for role-based access control. "seeker", "provider"
#     role = db.Column(db.String(80), nullable=False)

#     # One-Many relationship between User and Application
#     applications = db.relationship("Application", back_populates="user")

#     # One-Many relationship between User and Collective
#     collectives = db.relationship("Collective", back_populates="user")

#     #seekerprofile = db.relationship("Seekerprofile", back_populates="user")

#     def check_password(self, password):
#         """
#         Check if the provided password matches the stored hash.

#         Args:
#             password (str): The password to check.

#         Returns:
#             bool: True if the password matches, False otherwise.
#         """
#         return bcrypt.check_password_hash(self.password, password)

#     #TODO: Mange felter bliver efterladt null. Lav evt ny side/viewfunction hvor user kan udfylde sine informationer.
#     @classmethod
#     def create_user(cls, role, email, password):
#       """
#       Create a new user with the provided details.

#       Args:
#           role (str): The user's role.
#           email (str): The user's email.
#           password (str): The user's password, which will be hashed before storage.

#       Returns:
#           User: The newly created user object.
#       """
      
#       user = cls( role     = role.strip(),
#                   email    = email.strip(),
#                   password = bcrypt.generate_password_hash(password).decode('utf-8'),
#                 )
#                   # evt også image.
#       db.session.add(user)
#       db.session.commit()
#       return user

#     @staticmethod
#     def get_by_id(id):
#       """
#       Retrieve a user by their ID.

#       Args:
#           id (int): The user's ID.

#       Returns:
#           User: The user object if found, otherwise None.
#       """
#       return User.query.filter_by(id=id).first()

#     @staticmethod
#     def get_by_email(email):
#       """
#       Retrieve a user by their email.

#       Args:
#           email (str): The user's email.

#       Returns:
#           User: The user object if found, otherwise None.
#       """
#       return User.query.filter_by(email=email.strip()).first()
    
#     @staticmethod
#     def email_exists(email):
#       """
#       Check if an email already exists in the database.

#       Args:
#           email (str): The email to check.

#       Returns:
#           bool: True if the email exists, False otherwise.
#       """
#       email = User.query.filter_by(email=email).first()
#       return email is not None
    

# class SeekerProfile(db.Model):
#     __tablename__ = 'seekerprofiles'

#     # Primary key
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
#     name = db.Column(db.String(80), nullable=True)
#     description = db.Column(db.String(500), nullable=True)
#     birthdate = db.Column(db.Date, nullable=True)
#     gender = db.Column(db.String(80), nullable=True)
#     occupation = db.Column(db.String(80), nullable=True)
#     image = db.Column(db.String(500), nullable=True)

#     @classmethod
#     def create_seekerprofile(cls, user_id, name, description, birthdate, gender, occupation, image):
#         """
#         Create a new seeker profile with the provided details.

#         Args:
#             user_id (int): User's id
#             name (str): User's name
#             description (str): A description of the user
#             birthdate (Date): User's date of birth
#             gender (str): User's gender
#             occupation (str): User's occupation
#             image (str): User's profile picture

#         Returns:
#             SeekerProfile: The newly created profile object
#         """
#         #TODO Har fjernet .strip() fordi felterne godt kan være None. Men vi skal nok stadig have strip funktionalitet.
#         seekerprofile = cls(
#                             user_id = user_id,
#                             name = name,
#                             description = description,
#                             birthdate = birthdate,
#                             gender = gender,
#                             occupation = occupation,
#                             image = image
#                             )
#         db.session.add(seekerprofile)
#         db.session.commit()
#         return seekerprofile
    
    
#     @staticmethod
#     def get_by_user_id(user_id):
#         """
#         Retrieve a SeekerProfile by user_id.

#         Args:
#             id (int): The user's ID.

#         Returns:
#             SeekerProfile: The profile object if found, otherwise None.
#         """
#         return SeekerProfile.query.filter_by(user_id=user_id).first()
    

#     def replace_all_fields(self, name, description, birthdate, gender, occupation, image):
#         """
#         Replace all profile fields (PUT)

#         Args:
#             name (str | None): User's name
#             description (str | None): A description of the user
#             birthdate (Date | None): User's date of birth
#             gender (str | None): User's gender
#             occupation (str | None): User's occupation
#             image (str| None): User's profile picture
#         """
#         self.name = name
#         self.description = description
#         self.birthdate = birthdate
#         self.gender = gender
#         self.occupation = occupation
        
#         # If a new image is provided delete the old image and store the new one
#         if image:
#             delete_picture(self.image)
#             self.image = image
#         # If given image is None, we don't change the current image.
#         # User needs to explicitly delete profile picture if they want that.

#         db.session.commit()

# class Collective(db.Model):
#     __tablename__ = 'collectives'

#     id = db.Column(db.Integer, primary_key=True)
#     submitter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

#     city = db.Column(db.String(80))
#     street = db.Column(db.String(80))

#     roomsize = db.Column(db.Integer())
#     price = db.Column(db.Integer())

#     description = db.Column(db.String(500))
#     image = db.Column(db.String(500))   #image name.
  
#     # Many-One relationship between Collective and User
#     user = db.relationship("User", back_populates="collectives")
#     # One-Many relationship between Collective and Application
#     applications = db.relationship("Application", back_populates="collective")

#     @staticmethod
#     def get_all():
#         """Get all Collectives"""
#         return Collective.query.order_by(Collective.id).all()

#     @staticmethod
#     def get_by_id(id):
#         """Get collective by their ID"""
#         return Collective.query.filter_by(id=id).first()

#     @staticmethod
#     def get_by_submitter(user_id):
#         """Get all Collectives submitted by a specific user"""
#         return Collective.query.filter_by(submitter_id=user_id).all()
    
#     @staticmethod
#     def get_by_city(city):
#         """Get all Collectives which cityname has given argument as prefix)"""
#         return Collective.query.filter(Collective.city.startswith(city)).all()
    
#     def get_by_filters(city=None, roomsize=None, price=None):
#         """Filters collectives by multiple filters."""
#         # Fetch all queries.
#         query = Collective.query

#         # Filter step-by-step
#         if city:
#             query = query.filter(Collective.city.startswith(city))
#         if roomsize:
#             query = query.filter(Collective.roomsize >= roomsize)
#         if price:
#             query = query.filter(Collective.price <= price)

#         return query.all()


#     @classmethod
#     def create_collective(cls, submitter_id, city, street, roomsize, price, description, image):
#       """
#       Create a new collective with the provided details.

#       Args:
#           name (str): The collective's name.
#           email (str): The collective's email.
#           password (str): The collective's password, which will be hashed before storage.

#       Returns:
#           collective: The newly created collective object.
#       """
      
#       collective = cls(
#           submitter_id = submitter_id,
#           city = city.strip(),
#           street = street.strip(),
#           roomsize = roomsize,
#           price = price,
#           description = description.strip(),
#           image = image.strip()
#       )
                  
#       db.session.add(collective)
#       db.session.commit()
#       return collective


# class Application(db.Model):
#     """Placeholder Application model """
#     __tablename__ = 'applications'

#     id = db.Column(db.Integer, primary_key=True)
#     submitter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
#     collective_id = db.Column(db.Integer, db.ForeignKey('collectives.id'), nullable=False)

#     time_of_submission = db.Column(db.DateTime, nullable=True)  #TODO: Lav automatisk.
#     description = db.Column(db.String(500))

#     # Many-One relationship between Application and User
#     user = db.relationship("User", back_populates="applications")

#     # Many-One relationship between Application and Collective
#     collective = db.relationship("Collective", back_populates="applications")

#     @staticmethod
#     def get_all():
#         """Get all Applications"""
#         return Application.query.order_by(Application.id).all()
    
#     @staticmethod
#     def get_by_submitter(user_id):
#         """Get all Applications submitted by a specific user"""
#         return Application.query.filter_by(submitter_id=user_id).all()
    
#     @staticmethod
#     def get_by_collective(collective_id):
#         """Get all Applications submitted by a specific user"""
#         return Application.query.filter_by(collective_id=collective_id).all()
    
#     @classmethod  #Class Method: Static Method men som tager imod selve classen som første argument. Tillader os her at constructe en class user og returne den.
#     def create_application(cls, submitter_id, collective_id,description):
#       """
#       Create a new application with the provided details.

#       Args:
#           name (str): The application's name.
#           email (str): The application's email.
#           password (str): The application's password, which will be hashed before storage.

#       Returns:
#           application: The newly created application object.
#       """
      
#       application = cls(
#           submitter_id        = submitter_id,
#           collective_id       = collective_id,
#           description     = description.strip(),
#       )
                  
#       db.session.add(application)
#       db.session.commit()
#       return application
    

# # Debug Purposes
# def create_default_userbase():
#   existing_seeker = User.query.filter_by(role="seeker").first()
#   if not existing_seeker:
#      User.create_user("seeker", "seeker@gmail.com", "123")
#   existing_provider = User.query.filter_by(role="provider").first()
#   if not existing_provider:
#      User.create_user("provider", "provider@gmail.com", "123")


# descr = """
# Lorem ipsum dolor sit amet, consectetur adipiscing elit. Mauris a finibus libero, at elementum urna. Sed dictum dapibus ornare. Maecenas egestas molestie vulputate. Donec maximus, ipsum a rhoncus eleifend, urna turpis volutpat mauris, id faucibus tellus turpis convallis tellus. Suspendisse a augue aliquet, dapibus risus et, condimentum turpis. Morbi finibus ultricies cursus. Nullam commodo felis eu facilisis lacinia. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos.

# Vestibulum vestibulum neque eu lobortis malesuada. Pellentesque euismod erat mauris, non tempor lectus vulputate sit amet. Suspendisse eget nulla sed est lobortis imperdiet eu ut dui. Integer in semper ipsum, sed blandit sem. Maecenas consectetur vitae enim eu feugiat. Etiam non consectetur lorem. Sed non elit molestie, semper nulla vitae, sagittis eros. Suspendisse ante arcu, placerat vel ligula at, bibendum tincidunt tellus. Nam semper arcu neque, sit amet vestibulum felis commodo non. Nam in aliquet justo. Nulla auctor odio semper, eleifend massa et, volutpat purus. Suspendisse sit amet eros vel justo vehicula pharetra. Aenean tristique at ipsum id malesuada.
# """



# # Debug Purposes
# def create_default_collectives_applications():
#   Collective.create_collective(2, "Odense C", "Vindegade", 50, 2569, descr,"1.jpg") #submitterID = 2. provider@gmail.com.
#   Collective.create_collective(2, "Odense M", "Bogense", 23, 5000, descr, "2.jpg") #submitterID = 2. provider@gmail.com.
#   Collective.create_collective(2, "Odense M", "Stige", 35, 4000, descr, "3.jpg") #submitterID = 2. provider@gmail.com.

#   # Application.create_application(1, 1, "Jeg hedder Alice og vil gerne søge ind på kollektivet på Skovbogade.")


# # Clears the database and create tables within the application context
# with app.app_context():
#   db.drop_all()
#   db.create_all()
#   create_default_userbase()
#   create_default_collectives_applications()


# # -------------------------------- FORMS ------------------------------------- #
# # Custom validator to check if an email already exists
# # In WTForms custom validators must accept parameters form and field. So it is specified here even though it is not used.
# def email_exists(form, field):
#   if User.email_exists(field.data):
#     raise ValidationError('Email already exists.')

# # WTForms for user registration.
# class RegistrationForm(Form):
#   role = SelectField('Role', 
#                          choices=[('seeker', 'Seeker'), ('provider', 'Provider')], 
#                          validators=[DataRequired()])
#   # name = StringField('Name', validators=[DataRequired(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
#   email = EmailField('Email', validators=[DataRequired(), email_exists, Email()])
#   password = PasswordField('Password', validators=[DataRequired(), EqualTo('confirm', message='Password must match')])
#   confirm = PasswordField('Confirm password', validators=[DataRequired()])
#   submit = SubmitField('Register')


# class ProfileForm(FlaskForm):
#   name = StringField('Name', validators=[Optional(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
#   description = TextAreaField('About you', validators=[Optional(), Length(max=500, message='You cannot have more than 500 characters')])
#   birthdate = DateField('Birthdate', format="%Y-%m-%d", validators=[Optional()])
#   gender = RadioField('Gender', choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], validators=[Optional()])
#   occupation = StringField('Occupation', validators=[Optional(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
#   image = FileField("Profile picture", validators=[FileRequired()])
#   submit = SubmitField('Save Profile')


# class CollectiveForm(FlaskForm):
#   #address = StringField('Address of collective', validators=[DataRequired(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
#   city = StringField('Name of city', validators=[DataRequired(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
#   street = StringField('Name of street', validators=[DataRequired(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])

#   roomsize = IntegerField('Size of the room available (square meters)', validators=[DataRequired()])

#   price = IntegerField('Price in DKK', validators=[DataRequired()])

#   description = TextAreaField('Describe your collective', validators=[DataRequired(), Length(min=1, max=300, message='You cannot have less than 1 or more than 300 characters')])

#   image = FileField(validators=[FileRequired()])

#   submit = SubmitField('Register your collective')

# class SearchForm(FlaskForm):
#   city = StringField('Filter by city', validators=[Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
#   roomsize = IntegerField('Size of room')
#   price = IntegerField('Price in DKK')
#   submit = SubmitField('Search')

# class ApplicationForm(Form):
#   description = StringField('Your application', validators=[DataRequired(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
#   submit = SubmitField('Apply for this collective')

# # WARNING --------------------------------------------------------------------
# # Checking if an email is already registered during form validation introduces 
# # a potential security risk. An attacker can use the registration form to check 
# # if an email is already registered, effectively allowing them to enumerate 
# # valid user emails. A more secure approach is to always return a success 
# # message (e.g., "A confirmation email has been sent") regardless of whether 
# # the email is already registered. This prevents attackers from determining 
# # which emails are registered in the system. This example uses this insecure 
# # solution for simplicity as this is purely a demonstration of the session 
# # handling infrastructure.
# # -----------------------------------------------------------------------------

# # WTForms for user login
# class LoginForm(Form):
#   email = EmailField('Email', validators=[DataRequired(), Email()])
#   password = PasswordField('Password', validators=[DataRequired()])
#   remember = BooleanField('Remember Me')
#   submit = SubmitField('Login')

# # SESSIONS --------------------------------------------------------------------

# # Initialize the LoginManager with the Flask application
# login_manager = LoginManager(app)
# # Set the view to redirect to for unauthorized users (e.g., when @login_required is used)
# login_manager.login_view = 'login'
# # Enable session protection to guard against session hijacking
# # 'strong' mode ensures that the session is invalidated if the user's IP or browser changes
# login_manager.session_protection = 'strong'
# # Callback function for Flask-Login to reload the user object from the user ID 
# # stored in the session.
# # This function is required by Flask-Login to retrieve the user object whenever 
# # the application needs to know the current user. It is called when the session 
# # is accessed, and the user's ID is retrieved from the session. The function 
# # then fetches the corresponding user from the database.

# @login_manager.user_loader
# def load_user_from_id(id):
#     return User.get_by_id(id)

# # Flask Principal identity_loaded signal handler. Called when identity_loaded signal has been called.
# @identity_loaded.connect_via(app) # DEBUG: Denne manglede.
# def on_identity_loaded(sender, identity):
#     #Set the identity user object
#     identity.user = current_user

#     # Add the UserNeed to the identity (Note. Needs should be understood as Access-Control priviledges)
#     if hasattr(current_user, 'id'):
#         identity.provides.add(UserNeed(current_user.id))
    
#     # Add the Role to the identity.
#     if hasattr(current_user, 'role'):
#         identity.provides.add(RoleNeed(current_user.role))

# #-------------------------- ROUTES -----------------------------------------------------------------------

# @app.route("/", methods=['GET'])
# def landing():
#   """
#   Landing page for all visitors. 

#   Shows selected collectives as advertisement. 
#   """

#   # Denne her kan godt gøres mere nice.
#   selected_entries = Collective.get_all()[0:3] # Hmm, dette burde være 4, men render 3.
#   return render_template("landingpage.html", selected_entries=selected_entries)

# @app.route("/login", methods=('GET','POST'))
# def login():
#     """
#     Main page:
#     - If the user is already authenticated, redirects to the personal page.
#     - If not, displays the login form and processes login attempts.
#     - On successful login, redirects to the proper page (e.g. seeker).
#     - On failed login, flashes an error message and redisplays the login form.
#     """
#     if current_user.is_authenticated:
#       flash('You are already logged in.','info')
#       return redirect(url_for("landing"))
#     else:
#         form = LoginForm(request.form)
#         if request.method == 'POST' and form.validate():
#             user = User.get_by_email(form.email.data.strip())
#             if user and user.check_password(form.password.data.strip()):
#                 # If the user credentials are correct, start an authenticated session
#                 login_user(user, form.remember.data)

#                 # Tell Flask-Principal the identity has changed
#                 identity_changed.send(current_app._get_current_object(), identity=Identity(user.id))

#                 # Redirect to landing
#                 return redirect(url_for("landing"))
#             else:
#                 # Otherwise, display an error message and display the login form again
#                 flash("Invalid credentials","error")
#         return render_template('auth/login.html', form=form)

# @app.route("/register", methods=('GET','POST'))
# def register():
#   if current_user.is_authenticated:
#     flash('You are already logged in.','info')

#     return redirect(url_for("landing"))
#   else:
#     form = RegistrationForm(request.form)

#     if request.method == 'POST' and form.validate():
#       user = User.create_user(
#                       role = form.role.data,
#                       email = form.email.data,
#                       password = form.password.data
#                       )
      
#       login_user(user)
#       flash("User created.","success") # Skal vi egentlig overveje at fjerne disse? Ikke så "pro"
#       return redirect(url_for('landing'))
#     # elif request.method == 'POST':
#     #     flash("post bracket entered but form not validated.","Debug:")  # Only for debug purposes.
#     return render_template('auth/register.html', form=form)

# @app.route('/logout', methods=['GET'])
# @login_required
# def logout():
#      # Remove the user information from the session
#     logout_user()

#     # Remove session keys set by Flask-Principal
#     for key in ('identity.name', 'identity.auth_type'):
#         session.pop(key, None)

#     # Tell Flask-Principal the user is anonymous
#     identity_changed.send(current_app._get_current_object(),
#                           identity=AnonymousIdentity())
    
#     return redirect(url_for('landing'))

# @app.route("/collectives", methods=["GET"])
# def collectives_index():
#     form = SearchForm(formdata=request.args)
       
#     # if any arguments is given to URL
#     if (request.args):
#        collective_entries = Collective.get_by_filters(
#            form.city.data,
#            form.roomsize.data,
#            form.price.data 
#         )
#     else:
#        collective_entries = Collective.get_all()
      
#     return render_template("collectives/index.html", collective_entries=collective_entries, form=form)


# @app.route("/collectives/<int:id>", methods=["GET"])
# def collectives_view(id):
#     entry = Collective.get_by_id(id)
#     return render_template("collectives/view.html", entry=entry)


# @app.route("/collectives/delete/<int:id>", methods=["POST"])
# def collectives_delete(id):
#     """ 
#     Deletes a collective entry. Method is POST because HTML cannot send DELETE requests. 
#     """
#     entry = Collective.get_by_id(id)
#     if entry:
#         db.session.delete(entry)
#         db.session.commit()
#         delete_picture(entry.image)

#         #TODO: Delete corresponding picture in database.
#         flash("Collective deleted.","success")
#     else:
#        flash("Sorry, we couldn't find the collective that you wanted to delete.", 'warning')
#     return redirect(url_for('provider_collectives'))

# @app.route("/profile",methods=["GET"])
# @login_required
# @seeker_permission.require()
# def profile():
#     profile = SeekerProfile.get_by_user_id(current_user.id)
    
#     form = ProfileForm(obj=profile)
    
#     return render_template("profiles/seeker.html", form=form, profile=profile)
  
# @app.route("/profile",methods=["POST"])
# @login_required
# @seeker_permission.require()
# def put_profile():
#     form = ProfileForm()
#     profile = SeekerProfile.get_by_user_id(current_user.id)

#     if form.validate():
#         # Get data from form
#         name = form.name.data
#         description = form.description.data
#         birthdate = form.birthdate.data
#         gender = form.gender.data
#         occupation = form.occupation.data
#         # Save image if it exists
#         filename = None
#         if form.image.data:
#             filename = save_image(form.image.data)

#         if profile:
#             # Replace current profile with provided information
#             profile.replace_all_fields(name, description, birthdate, gender, occupation, filename)
#         else:
#             # Create profile with provided information
#             profile = SeekerProfile.create_seekerprofile(current_user.id, name, description, birthdate, gender, occupation, filename)
      
#         flash("Profile saved!", "success")
#         return redirect(url_for("profile"))
#     else:
#         # Reload site with the form data so user doesn't have to start all over if they input something invalid
#         flash("Invalid input", "error")
#         return render_template("profiles/seeker.html", form=form, profile=profile)

# @app.route("/provider/collectives",methods=["GET","POST"])
# @login_required
# @provider_permission.require()
# def provider_collectives():
#     collective_entries = Collective.get_by_submitter(current_user.id)
  
#     # Get all applications mapped to these collectives.
#     #application_entries = [
#     #  application
#     #  for collective in collective_entries
#     #    for application in collective.applications  #relationship() anvendes.
#     #]
#     return render_template("profiles/provider.html", collective_entries=collective_entries)

# @app.route("/collectives/create", methods=["GET", "POST"])
# @login_required
# @provider_permission.require()
# def collectives_create():
#   form = CollectiveForm()

#   if form.validate_on_submit():
#       Collective.create_collective(
#           current_user.id, 
#           form.city.data,
#           form.street.data,
#           form.roomsize.data,
#           form.price.data,
#           form.description.data,
#           save_image(form.image.data)
#         )
#       return redirect(url_for("provider_collectives"))
#   return render_template("collectives/create.html", form=form)


# ------------ Old Routes ------------------

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



"""
Old Code that might be useful later







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
  return redirect(url_for('provider_collectives'))






"""