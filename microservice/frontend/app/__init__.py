import os
import requests
from wtforms import Form, SelectField, SubmitField, EmailField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo
from flask import Flask, redirect, render_template, request, session, url_for, flash

app = Flask(__name__)

# WARNING: CSRF protection is disabled for simplicity in this project
app.config['WTF_CSRF_ENABLED'] = False
# Secret key for session management and security features
app.config['SECRET_KEY'] = "change-me" #TODO Få denne fra environment?

# API URLs to microservices
AUTH_API = os.getenv('AUTH_API_URL')
COLLECTIVES_API = os.getenv('COLLECTIVES_API_URL')

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


# ROUTES ----------------------------------------------------------------------

@app.route("/", methods=('GET','POST'))
def home():
  """
  Landing page.
  
  Checks if current session token matches an active session.
  - If it does, redirects user based on role
  - If not, render login form and sends requests to auth to log in user
  - On success sets the session cookie

  Returns:
      Response | str: Redirect to dashboard or render login template
  """
  # Get the current session cookie from browser
  token = session.get('session_token')
  if token:
    # Check if token matches an active session
    response = requests.get(f"{AUTH_API}/sessions", params={"api_token": token})
    # If it does user is already logged in
    if response.status_code == 200:
      #TODO: Should we save the data here aswell or is it fine to assume that it is already set?
      data = response.json()
      session["role"] = data["role"]
      flash("already logged in")
      return redirect(url_for("dashboard"))

  # If session doesn't exist, user needs to login 
  form = LoginForm(request.form)
  if request.method == 'POST' and form.validate():  # Logging in
    email = form.email.data
    password = form.password.data
    # Create session: POST /sessions 
    response = requests.post(f"{AUTH_API}/sessions", 
                             json={"email": email, "password": password}) 

    if response.status_code == 200:
      ## Get json from auth service
      data = response.json()
      # Set session coookie
      session["role"] = data["role"]
      session["session_token"] = data["session_token"]
      flash("Login successful!", "success")
      return redirect(url_for("dashboard"))
    else:
      flash(response.json().get("error", "Login failed"), "error")
  
  # Render login site
  return render_template('login.html', form=form)


@app.route("/dashboard")
def dashboard():
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


@app.route("/users", methods=['POST', 'GET'])
def register():
  """
  Registration page.
  Sends a request to auth to register the user based on the filled out RegistrationForm.

  Returns:
      Response | str: Redirect to dashboard or render regisration page
  """

  # TODO: Overvej at kontrollere hvorvidt en bruger allerede er logget ind -> tror ikke det er nødvendigt

  form = RegistrationForm(request.form)
  if request.method == 'POST' and form.validate():
    # Register: POST /users
    response = requests.post(f"{AUTH_API}/users", json={"email": form.email.data, 
                                                        "password": form.password.data, 
                                                        "role": form.role.data}) 
    if response.status_code == 200:
      flash("Registration successful", "success")
      return redirect(url_for('dashboard')) # redirect based on user's role
    else:
      flash("Registration failed", "error")
  
  # Render registration page
  return render_template('register.html', form=form)


@app.route('/logout', methods=['POST'])
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