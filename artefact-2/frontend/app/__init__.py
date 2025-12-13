from datetime import date
from functools import wraps
import os
import requests
from wtforms import DateField, Form, SelectField, StringField, SubmitField, EmailField, PasswordField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Optional, Length
from flask import Flask, redirect, render_template, request, session, url_for, flash

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
  
class ProfileForm(Form): #TODO Afviger fra monolit form
  name = StringField('Name', validators=[Optional(), Length(max=80)])
  description = TextAreaField('About you', validators=[Optional(), Length(max=500)])
  birthdate = DateField('Birthdate', format="%Y-%m-%d", validators=[Optional()])
  gender = StringField('Gender', validators=[Optional(), Length(max=80)])
  occupation = StringField('Occupation', validators=[Optional(), Length(max=80)])
  image = StringField('Profile Picture', validators=[Optional(), Length(max=500)])
  submit = SubmitField('Save Profile')


# DECORATORS ----------------------------------------------------------------------

def login_required(f):
  @wraps(f)
  def decorated_function(*args, **kwargs):
    token = session.get("session_token")
    
    if not token:
      flash("Please log in", "warning")
      return redirect(url_for("login"))
    
    # Validate session with auth service
    response = requests.get(f"{AUTH_API}/sessions", params={"session_token": token})

    if not response.ok:
      session.clear() # Invalid session
      flash("Session expired, please log in again", "warning")
      return redirect(url_for("login"))
    
    # Token matches an active session - user is authenticated
    return f(*args, **kwargs)
  return decorated_function


def role_required(role_name):
  def decorator(f):
    @wraps(f)
    @login_required   # Also requires login
    def decorated_function(*args, **kwargs):
      # Get the users role from session (just checked user is authenticated with @login_required)
      user_role = session.get("role")
      
      if user_role != role_name:
        flash(f"Access denied.", "error")
        return redirect(url_for("home"))
      
      # User has required role
      return f(*args, **kwargs)
    return decorated_function
  return decorator


# ROUTES ----------------------------------------------------------------------

@app.route("/", methods=('GET','POST'))
def home():
  """
  Landing page.

  Returns:
      str: Homepage template
  """
  return render_template("homepage.html")


@app.route("/dashboard")
def dashboard(): #TODO: DON'T THINK THIS WILL EVER BE USED WITH NEW LANDING PAGE APPROACH
  """
  Redirects the user to appropriate site based on role

  Returns:
      Response: the redirect response
  """
  role = session.get("role")
  
  if role == "seeker":
    return redirect(url_for("collective_overview"))
  elif role == "provider":
    return redirect(url_for("my_collectives"))
  else:
    return redirect(url_for("home"))



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
  # Get the current session cookie from browser
  token = session.get('session_token')
  if token:
    # Check if token matches an active session
    response = requests.get(f"{AUTH_API}/sessions", params={"session_token": token})
    # If it does user is already logged in
    if response.status_code == 200:
      flash("already logged in")
      return redirect(url_for("home")) # TODO: Kan man lave noget nice hvor man redirectes tilbage til hvor man var inden man blev sendt til login
  
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
      return redirect(url_for("home")) # TODO: Kan man lave noget nice hvor man redirectes tilbage til hvor man var inden man blev sendt til login
    else:
      flash(response.json().get("error", "Login failed"), "error")
  
  # Render login site
  return render_template('login.html', form=form)
  


@app.route("/register", methods=['POST', 'GET'])
def register():
  """
  Registration page.
  Sends a request to auth to register the user based on the filled out RegistrationForm.

  Returns:
      Response | str: Redirect to dashboard or render regisration page
  """

  # TODO: Overvej at kontrollere hvorvidt en bruger allerede er logget ind
    # -> hvis ikke vi gør dette kan en bruger registrere en ny konto mens de er logget ind

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
      return redirect(url_for('home')) # TODO: Kan man lave noget nice hvor man redirectes tilbage til hvor man var inden man blev sendt til register
    else:
      flash("Registration failed", "error")
  
  # Render registration page
  return render_template('register.html', form=form)


@app.route('/logout', methods=['POST'])
@login_required
def logout_view():
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
      return redirect(url_for("home"))
    
  flash("Logout failed", "error")
  return redirect(url_for("home")) #TODO: Skal vi redirecte til home??




# PROFILE ROUTES ------------------------------------------------------------------ 
@app.route("/profile", methods=['GET'])
@role_required("seeker")  # Also ensures user is authenticated
def profile():
  """
  The seeker's profile page.

  Returns:
      str: The profile page with seeker's profile info if any
  """
  user_id = session.get("user_id")
  
  response = requests.get(f"{PROFILE_API}/profiles/{user_id}")
  
  if response.ok:
    profile = response.json()
    # Convert birthdate string from JSON back to date object
    if profile.get("birthdate"):
      profile["birthdate"] = date.fromisoformat(profile["birthdate"])
  else:
    profile = {} # TODO: Pre-populate data here if any? (default data)
  
  form = ProfileForm(data=profile)
  return render_template("profile.html", form=form)
  
  
@app.route("/profile", methods=['POST'])
@role_required("seeker")
def create_or_update_profile(): #TODO: Cleanup return statements
  """
  Send a PUT request to profile microservice to replace
  profile info with the newly submitted information.

  Returns:
      Response | str: The profile page #TODO: redirect er jo måske lidt ligegyldig?
  """
  user_id = session.get("user_id")  # Safe because we @role_required ensures user is authenticated
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
      return render_template("profile.html", form=form)
  else:
    flash("Invalid input", "error")
    return render_template("profile.html", form=form)

