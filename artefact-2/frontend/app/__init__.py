from datetime import date
from functools import wraps
import os
import random
import requests
from flask import Flask, g, redirect, render_template, request, session, url_for, flash
# Our forms
from .forms import RegistrationForm, LoginForm, ProfileForm, SearchForm, CollectiveForm

app = Flask(__name__)

# WARNING: CSRF protection is disabled for simplicity in this project
app.config['WTF_CSRF_ENABLED'] = False
# Secret key for session management and security features
app.config['SECRET_KEY'] = "change-me"

# API URLs to microservices
AUTH_API = os.getenv('AUTH_API_URL')
COLLECTIVES_API = os.getenv('COLLECTIVES_API_URL')
PROFILE_API = os.getenv('PROFILE_API_URL')
PICTURES_API = os.getenv('PICTURES_API_URL')
PICTURES_URL_FROM_HOST = "http://localhost:5004/pictures"



# DECORATORS ----------------------------------------------------------------------

@app.before_request
def load_auth_context():
  """
  Called before every request.
  Asks authentication service whether the current token matches an active session.
  Sets 'is_authenticated' and 'role' fields in g.user object based on the answer.
  """
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
  response = requests.get(f"{AUTH_API}/sessions/{token}")
  
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
  """
  Injects g.user as current_user so it is usable from all templates.
  Importantly, this means that referncing 'current_user' in templates 
  has nothing to do with the Flask-Login proxy of the same name.

  Returns:
      dict: current_user object with fields 'is_authenticated' and 'role'
  """
  return dict(current_user=g.user)


def login_required(f):
  """
  Decorator to require authentication.
  Just checks if g.user is authenticated since g.user 
  is always set before this decorator is called.
  """
  @wraps(f)
  def decorated_function(*args, **kwargs):
    if not g.user["is_authenticated"]:
      flash("Please log in", "warning")
      return redirect(url_for("login"))
    return f(*args, **kwargs)
  return decorated_function


def role_required(role_name):
  """
  Decorator to require specific role.
  Just checks if g.user has given role since g.user 
  is always set before this decorator is called.

  Args:
      role_name (str): name of the required role
  """
  def decorator(f):
    @wraps(f)
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
    # Select 3 random collectives from the database, or fewer if there are less than 3 available.
    entries = response.json()
    selected_entries = random.sample(entries, min(3, len(entries)))
  else:
    selected_entries = {}
  return render_template("landingpage.html", selected_entries=selected_entries, pictures_url = PICTURES_URL_FROM_HOST)


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


@app.route('/logout', methods=['GET'])
@login_required
def logout():
  """
  Log out user by asking auth to delete session entry.

  Returns:
      Response: Redirect to home
  """
  token = session.get('session_token')
  if token:
    response = requests.delete(f"{AUTH_API}/sessions/{token}")
    
    if response.ok:
      session.clear()
      flash("Session ended", "success")
      return redirect(url_for("landing"))
    
  flash("Logout failed", "error")
  return redirect(url_for("landing"))




# PROFILE ROUTES ------------------------------------------------------------------ 
@app.route("/profile", methods=['GET'])
@login_required
@role_required("seeker")
def profile():
  """
  The seeker's profile page.

  Returns:
      str: The profile page with seeker's profile info if any
  """
  user_id = session.get("user_id") # Safe because @login_required ensures user is authenticated
  
  response = requests.get(f"{PROFILE_API}/profiles/{user_id}")
  
  if response.ok:
    profile = response.json()
    # Convert birthdate string from JSON back to date object
    if profile.get("birthdate"):
      profile["birthdate"] = date.fromisoformat(profile["birthdate"])
  else:
    profile = {} # TODO: Pre-populate data here if any? (default data)
  
  form = ProfileForm(data=profile)
  return render_template("profiles/seeker.html", form=form, profile=profile, pictures_url = PICTURES_URL_FROM_HOST)
  
  
@app.route("/profile", methods=['POST'])
@login_required
@role_required("seeker")
def create_or_update_profile():
  """
  Send a PUT request to profile microservice to replace
  profile info with the newly submitted information.

  Returns:
      Response | str: The profile page
  """
  user_id = session.get("user_id") # Safe because @login_required ensures user is authenticated
  form = ProfileForm()
  
  # Fetch the existing profile for rendering in case of error and to get old image name
  profile = {}
  profile_response = requests.get(f"{PROFILE_API}/profiles/{user_id}")
  if profile_response.ok:
    profile = profile_response.json
  
  if form.validate():
    image_name = profile.get("image_name") # user's current profile picture
    
    if form.image.data:
      # Upload image
      file_storage = form.image.data
      files = {
        "file": (
          file_storage.filename,
          file_storage.stream
        )
      }
      
      # send data as multipart/formdata request to API
      picture_response = requests.post(f"{PICTURES_API}/pictures", files=files)
      # flash(f"Response code after uploading picture: {picture_response.status_code}") #TODO debug msg
      if picture_response.status_code == 201:
        # if success, update image_name
        data = picture_response.json()
        image_name = data["image_name"]
        flash("Image was uploaded! Name is" + image_name)
      else:
        # Picture upload failed. Abort profile update. #TODO Man kunne nok teknisk set godt kun opdatere med det andet information, hvis kun image fejler.
        flash("Image upload failed. Profile was not saved.", "error")
        return render_template("profiles/seeker.html", form=form, profile=profile, pictures_url=PICTURES_URL_FROM_HOST)

    profile_data = {
      "name": form.name.data,
      "description": form.description.data,
      "birthdate": (form.birthdate.data.isoformat() if form.birthdate.data else None),
      "gender": form.gender.data,
      "occupation": form.occupation.data,
      "image_name": image_name
    }

    # Create or update profile
    response = requests.put(f"{PROFILE_API}/profiles/{user_id}", json=profile_data)
  
    if response.ok:
      flash("Profile saved!", "success")
      return redirect(url_for("profile"))
    else:
      flash("Error saving profile", "error")
      # Reload site with profile data so user can just press save again without losing changes
      return render_template("profiles/seeker.html", form=form, profile=profile, pictures_url = PICTURES_URL_FROM_HOST)
  else:
    flash("Invalid input", "error")
    return render_template("profiles/seeker.html", form=form, profile=profile, pictures_url = PICTURES_URL_FROM_HOST)


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

  return render_template("collectives/index.html", collective_entries=data, form=filters, pictures_url=PICTURES_URL_FROM_HOST)


@app.route("/collectives/<int:id>", methods=["GET"])
def collectives_view(id):
  response = requests.get(f"{COLLECTIVES_API}/collectives/{id}")
  if response.status_code == 200:
    entry = response.json()

    return render_template("collectives/view.html", entry=entry, pictures_url=PICTURES_URL_FROM_HOST)
  else:
    flash("Couldn't get collective", "error")
    return redirect(url_for("collectives_index"))

@app.route("/provider/collectives", methods=["GET", "POST"])
@login_required
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
  
  return render_template("profiles/provider.html", collective_entries=collective_entries, pictures_url=PICTURES_URL_FROM_HOST)

@app.route("/collectives/create", methods=["GET", "POST"])
@login_required
@role_required("provider")
def collectives_create():
  form = CollectiveForm()

  if form.validate_on_submit():

    file_storage = form.image.data

    files = {
      "file": (
        file_storage.filename,
        file_storage.stream
      )
    }

    # send data as multipart/formdata request to API
    response = requests.post(f"{PICTURES_API}/pictures", files = files)
    if response.status_code == 201:
      data = response.json()
      image_name = data["image_name"]

      collective_data = {
        "submitter_id": session.get("user_id"), #TODO Lavet hurtigt af C-E, er det good to go?
        "city": form.city.data,
        "street": form.street.data,
        "roomsize": form.roomsize.data,
        "price": form.price.data,
        "description": form.description.data,
        "image_name": image_name
      }
      response = requests.post(f"{COLLECTIVES_API}/collectives", json=collective_data)
      if response.ok:
        flash("Collective created!", "success")
        return redirect(url_for("provider_collectives"))
      else:
        flash("Error creating collective. Removing previously uploaded image...", "error")  #TODO remove image
        response = requests.delete(f"{PICTURES_API}/pictures/{image_name}")
        if not response.ok:
          flash("The previously uploaded image could not be deleted.")  #TODO C-E måske bare fjern denne besked til useren? 
    else:
      flash("Image could not be uploaded.")
    
  return render_template("collectives/create.html", form=form)

@app.route("/collectives/delete/<int:id>", methods=["POST"])
@login_required
@role_required("provider")
def collectives_delete(id):
  """
  Deletes a collective entry. 
  Method is POST because forms cannot send DELETE requests. 

  Args:
      id (int): Id of the collective to delete

  Returns:
      Response: Redirect to provider's overview of their collectives
  """
  # Fetch collcetive so we can get the name of its image
  response = requests.get(f"{COLLECTIVES_API}/collectives/{id}")
  if response.ok:
    data = response.json()
    image_name = data["image_name"]
  else:
    flash("Sorry, we couldn't find the collective that you wanted to delete.", 'warning')
    redirect(url_for('provider_collectives'))
    
  
  # Delete image first
  response = requests.delete(f"{PICTURES_API}/pictures/{image_name}")
  if not response.ok:
    flash("Failed to delete image. Please try again.", "error")
    return redirect(url_for('provider_collectives'))
  
  # Then try to delete collective - can fail leaving collective with no image. 
  response = requests.delete(f"{COLLECTIVES_API}/collectives/{id}")
  if response.ok:
      flash("Collective deleted.","success")
  else:
    flash("Image was successfully deleted, but not the collective.", "error")
  
  return redirect(url_for('provider_collectives'))
  
