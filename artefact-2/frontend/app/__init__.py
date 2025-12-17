from datetime import date
from functools import wraps
import os
import requests
from wtforms import DateField, Form, IntegerField, RadioField, SelectField, StringField, SubmitField, EmailField, PasswordField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Optional, Length
from flask import Flask, g, redirect, render_template, request, session, url_for, flash
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired

app = Flask(__name__)

# WARNING: CSRF protection is disabled for simplicity in this project
app.config['WTF_CSRF_ENABLED'] = False
# Secret key for session management and security features
app.config['SECRET_KEY'] = "change-me" #TODO Få denne fra environment?

# API URLs to microservices
AUTH_API = os.getenv('AUTH_API_URL')
COLLECTIVES_API = os.getenv('COLLECTIVES_API_URL')
PROFILE_API = os.getenv('PROFILE_API_URL')

# Forms -----------------------------------------------------------------------
#TODO: Smid over i anden fil og import?
#TODO: Tilføj length validators i overenstemmelse med database constraints

# WTForms for user registration
class RegistrationForm(Form):
  email = EmailField('Email', validators=[DataRequired(), Email()]) #i: formerly had check if email already existed.
  password = PasswordField('Password', validators=[DataRequired(), EqualTo('confirm', message='Password must match')])
  confirm = PasswordField('Confirm', validators=[DataRequired()])
  role = SelectField("Role", choices=[('seeker', 'Seeker'), ('provider', 'Provider')], validators=[DataRequired()])
  submit = SubmitField('Register')

# WTForms for user login
class LoginForm(Form):
  email = EmailField('Email', validators=[DataRequired(), Email()])
  password = PasswordField('Password', validators=[DataRequired()])
  remember = BooleanField('Remember Me')
  submit = SubmitField('Login')
  
class ProfileForm(FlaskForm):
  name = StringField('Name', validators=[Optional(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  description = TextAreaField('About you', validators=[Optional(), Length(max=500, message='You cannot have more than 500 characters')])
  birthdate = DateField('Birthdate', format="%Y-%m-%d", validators=[Optional()])
  gender = RadioField('Gender', choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], validators=[Optional()])
  occupation = StringField('Occupation', validators=[Optional(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  image = FileField("Profile picture", validators=[FileRequired()])
  submit = SubmitField('Save Profile')

# WTForms for the collective filter
class SearchForm(FlaskForm):
  city = StringField('Filter by city', validators=[Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  roomsize = IntegerField('Size of room')
  price = IntegerField('Price in DKK')
  submit = SubmitField('Search')
  
class CollectiveForm(FlaskForm):
  city = StringField('Name of city', validators=[DataRequired(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  street = StringField('Name of street', validators=[DataRequired(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  roomsize = IntegerField('Size of the room available (square meters)', validators=[DataRequired()])
  price = IntegerField('Price in DKK', validators=[DataRequired()])
  description = TextAreaField('Describe your collective', validators=[DataRequired(), Length(min=1, max=300, message='You cannot have less than 1 or more than 300 characters')])
  image = FileField(validators=[FileRequired()])
  submit = SubmitField('Register your collective')

# DECORATORS ----------------------------------------------------------------------

@app.before_request
def load_auth_context():  
  # Skip static files
  if request.endpoint == "static":
    return
  
  # Initialise current user as not authenticated with no role
  g.user = {
    "is_authenticated": False,
    "role": None
  }
  
  token = session.get("session_token")
  if not token:
    return # not authenticated
  
  # session_token is not empty:
  response = requests.get(f"{AUTH_API}/sessions", params={"session_token": token})
  
  if response.ok:
    data = response.json()
    # set current user to authenticated with correct role
    g.user = {
      "is_authenticated": True,
      "role": data["role"]
    }
  else:
    # invalid session
    session.clear()


@app.context_processor
def inject_user():
  #TODO: Test om dette crasher ved static calls
  return dict(current_user=g.user)


def login_required(f):
  """
  Decorator to require authentication.
  Just checks if g.user is authenticated since g.user is
  always set before this decorator is called.
  """
  @wraps(f)
  def decorated_function(*args, **kwargs):
    if not g.user["is_authenticated"]:
      flash("Please log in", "warning")
      return redirect(url_for("login"))
    return f(*args, **kwargs)
  return decorated_function


def role_required(role_name):
  def decorator(f):
    @wraps(f)
    @login_required   # Also requires login
    def decorated_function(*args, **kwargs):
      if g.user["role"] != role_name:
        flash(f"Access denied.", "error")
        return redirect(url_for("landing"))
      return f(*args, **kwargs)
    return decorated_function
  return decorator


# ROUTES ----------------------------------------------------------------------

@app.route("/", methods=('GET','POST'))
def landing():
  """
  Landing page.

  Returns:
      str: Homepage template
  """
  response = requests.get(f"{COLLECTIVES_API}/collectives")
  if response.ok:
    selected_entries = response.json()[0:3]
  else:
    selected_entries = {}
  return render_template("landingpage.html", selected_entries=selected_entries)


# AUTH ROUTES ------------------------------------------------------------------ 

@app.route("/login", methods=['POST', 'GET'])
def login():
  """
  Login page.
  
  Checks if current session token matches an active session.
  - If it does, redirects user to home page
  - If not, render login form and sends requests to auth to log in user
  - On success sets the session cookie

  Returns:
      Response | str: Redirect to home or render login template
  """
  # ---- Check if user already has an active session ----
  # We already checked with auth service when setting g object so we just check this.
  if g.user["is_authenticated"]:
      flash("Already logged in", "info")
      return redirect(url_for("landing")) # TODO: Kan man lave noget nice hvor man redirectes tilbage til hvor man var inden man blev sendt til login
  
  # ---- User does NOT have an active session, need to login ----
  form = LoginForm(request.form)
  if request.method == 'POST' and form.validate():  # Logging in
    email = form.email.data
    password = form.password.data
    # Create session: POST /sessions 
    response = requests.post(f"{AUTH_API}/sessions", 
                             json={"email": email, "password": password}) 

    if response.ok:
      ## Get json from auth service response
      data = response.json()
      # Set session coookie
      session["user_id"] = data["user_id"]
      session["role"] = data["role"]
      session["session_token"] = data["session_token"]
      flash("Login successful!", "success")
      return redirect(url_for("landing")) # TODO: Kan man lave noget nice hvor man redirectes tilbage til hvor man var inden man blev sendt til login
    else:
      flash(response.json().get("error", "Login failed"), "error")
  
  # Render login site
  return render_template('auth/login.html', form=form)
  


@app.route("/register", methods=['POST', 'GET'])
def register():
  """
  Registration page.
  Sends a request to auth to register the user based on the filled out RegistrationForm.

  Returns:
      Response | str: Redirect to dashboard or render regisration page
  """
  # Can't register while already logged in
  if g.user["is_authenticated"]:
    flash("Already logged in", "info")
    return redirect(url_for("landing")) # TODO: Kan man lave noget nice hvor man redirectes tilbage til hvor man var inden man blev sendt til login

  form = RegistrationForm(request.form)
  if request.method == 'POST' and form.validate():
    # Register: POST /users
    response = requests.post(f"{AUTH_API}/users", json={"email": form.email.data, 
                                                        "password": form.password.data, 
                                                        "role": form.role.data}) 
    if response.status_code == 201:
      # Set up session cookie to log user in. QOL so users don't have to login right after registering
      data = response.json()
      session["user_id"] = data["user_id"]
      session["role"] = data["role"]
      session["session_token"] = data["session_token"]
      flash("Registration successful", "success")
      return redirect(url_for('landing')) # TODO: Kan man lave noget nice hvor man redirectes tilbage til hvor man var inden man blev sendt til register
    else:
      flash("Registration failed", "error")
  
  # Render registration page
  return render_template('auth/register.html', form=form)


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
  """
  Log out user by asking auth to delete session entry.

  Returns:
      Response: Redirect to home
  """
  token = session.get('session_token')
  if token:
    response = requests.delete(f"{AUTH_API}/sessions", params={"session_token": token})
    
    if response.ok:
      session.clear()
      flash("Session ended", "success")
      return redirect(url_for("landing"))
    
  flash("Logout failed", "error")
  return redirect(url_for("landing")) #TODO: Skal vi redirecte til home??




# PROFILE ROUTES ------------------------------------------------------------------ 
@app.route("/profile", methods=['GET'])
@role_required("seeker")  # Also ensures user is authenticated
def profile():
  """
  The seeker's profile page.

  Returns:
      str: The profile page with seeker's profile info if any
  """
  user_id = session.get("user_id") # Safe because @role_required ensures user is authenticated
  
  response = requests.get(f"{PROFILE_API}/profiles/{user_id}")
  
  if response.ok:
    profile = response.json()
    # Convert birthdate string from JSON back to date object
    if profile.get("birthdate"):
      profile["birthdate"] = date.fromisoformat(profile["birthdate"])
  else:
    profile = {} # TODO: Pre-populate data here if any? (default data)
  
  form = ProfileForm(data=profile)
  return render_template("profiles/seeker.html", form=form, profile=profile)
  
  
@app.route("/profile", methods=['POST'])
@role_required("seeker")
def create_or_update_profile():
  """
  Send a PUT request to profile microservice to replace
  profile info with the newly submitted information.

  Returns:
      Response | str: The profile page
  """
  user_id = session.get("user_id") # Safe because @role_required ensures user is authenticated
  form = ProfileForm(request.form)
  
  if form.validate():
    profile_data = {
      "name": form.name.data,
      "description": form.description.data,
      "birthdate": (form.birthdate.data.isoformat() if form.birthdate.data else None),
      "gender": form.gender.data,
      "occupation": form.occupation.data,
      "image": form.image.data
    }
  
    response = requests.put(f"{PROFILE_API}/profiles/{user_id}", json=profile_data)
  
    if response.ok:
      flash("Profile saved!", "success")
      return redirect(url_for("profile"))
    else:
      flash("Error saving profile", "error")
      # Reload site with profile data so user can just press save again without losing changes
      return render_template("profiles/seeker.html", form=form)
  else:
    flash("Invalid input", "error")
    return render_template("profiles/seeker.html", form=form)


# COLLECTIVE ROUTES ------------------------------------------------------------------
@app.route("/collectives", methods=["GET"])
def collectives_index():
  """
  Overview of all collectives. 
  Can be accessed by all roles, even anonymous. 
  User can apply filter.
  """
  
  filters = SearchForm(request.args)

  # detect if filter has been applied
  params = {}
  if request.args:
    if filters.city.data:
      params['city'] = filters.city.data.capitalize() # todo: ingen capitalize i monolit?
    if filters.price.data:
      params['price'] = filters.price.data
    if filters.roomsize.data:
      params['roomsize'] = filters.roomsize.data
  
  # Apply filter by passing along the parameters with the request.
    response = requests.get(f"{COLLECTIVES_API}/collectives", params=params)
    if response.ok:
      data = response.json()
      if params: 
        flash(f"Filters: {filters.city.data}, {filters.price.data}, {filters.roomsize.data} applied", "success")  
  
  # Or get all. 
  else: 
    response = requests.get(f"{COLLECTIVES_API}/collectives")
    if response.ok:
      data = response.json()
    else:
      data={}

  return render_template("collectives/index.html", collective_entries=data, form=filters)
    
  
#TODO: Crasher når vi går til kollektiv der ikke eksisterer.
@app.route("/collectives/<int:id>", methods=["GET"])
def collectives_view(id):
  response = requests.get(f"{COLLECTIVES_API}/collectives/{id}")
  if response.status_code == 200:
    entry = response.json()
    return render_template("collectives/view.html", entry=entry)
  else:
    flash("Couldn't get collective", "error")
    return redirect(url_for("collectives_index"))


@app.route("/provider/collectives", methods=["GET", "POST"])
@role_required("provider")
def provider_collectives():
  # Get the user's id.
  user_id = session.get("user_id")
  # Get all collectives the user has created
  response = requests.get(f"{COLLECTIVES_API}/collectives", params={"submitter_id": user_id})
  
  if response.status_code == 200:
    collective_entries = response.json()
  else:
    flash("Couldn't load your collectives", "error")
    collective_entries = {}
  
  return render_template("profiles/provider.html", collective_entries=collective_entries)


#TODO: Ikke testet pga. manglende image implementering
@app.route("/collectives/create", methods=["GET", "POST"])
@role_required("provider")
def collectives_create():
  form = CollectiveForm()
  
  if request.method == 'POST':
    if form.validate():
      # Setup form data in dictionary to be sent with request
      collective_data = {
        "city": form.city.data,
        "street": form.street.data,
        "roomsize": form.roomsize.data,
        "price": form.price.data,
        "description": form.description.data,
        "image": form.image.data
      }
      
      # POST /collectives: Try to create collective
      response = requests.post(f"{COLLECTIVES_API}/collectives", json=collective_data)
      
      if response.ok:
        flash("Collective created!", "success")
        return redirect(url_for("provider_collectives"))
      else:
        flash("Error creating collective", "error")
    else:
      flash("Invalid input", "error")
    
  return render_template("collectives/create.html", form=form)