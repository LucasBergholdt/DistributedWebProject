# Command-Line Execution: flask run --debug
from datetime import date
import uuid
from flask import Blueprint, Flask, current_app, session, redirect, render_template, request, url_for, flash

from flask_login import current_user, login_required, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
# from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
# from flask_bcrypt import Bcrypt
from flask_principal import Principal, Permission, RoleNeed, UserNeed, Identity, AnonymousIdentity, identity_changed, identity_loaded
# from wtforms.widgets import TextArea
from werkzeug.utils import secure_filename
# import os
 
from .model import Collective, User
from .forms import LoginForm, RegistrationForm

bp = Blueprint('auth', __name__)

# Create permissions
seeker_permission = Permission(RoleNeed("seeker"))
provider_permission = Permission(RoleNeed("provider"))


# SESSIONS --------------------------------------------------------------------

# Initialize the LoginManager with the Flask application
# login_manager = LoginManager(app)
# Set the view to redirect to for unauthorized users (e.g., when @login_required is used)
# login_manager.login_view = 'login'
# Enable session protection to guard against session hijacking
# 'strong' mode ensures that the session is invalidated if the user's IP or browser changes
# login_manager.session_protection = 'strong'
# Callback function for Flask-Login to reload the user object from the user ID 
# stored in the session.
# This function is required by Flask-Login to retrieve the user object whenever 
# the application needs to know the current user. It is called when the session 
# is accessed, and the user's ID is retrieved from the session. The function 
# then fetches the corresponding user from the database.

# @login_manager.user_loader 
def load_user_from_id(id):
    return User.get_by_id(id)

# Flask Principal identity_loaded signal handler. Called when identity_loaded signal has been called.
# @identity_loaded.connect_via(app) # DEBUG: Denne manglede.
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


@bp.route("/", methods=['GET'])
def landing():
  """
  Landing page for all visitors. 

  Shows selected collectives as advertisement. 
  """

  # Denne her kan godt gøres mere nice.
  selected_entries = Collective.get_all()[0:3] # Hmm, dette burde være 4, men render 3.
  return render_template("landingpage.html", selected_entries=selected_entries)

@bp.route("/login", methods=('GET','POST'))
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
      return redirect(url_for("landing"))
    else:
        form = LoginForm(request.form)
        if request.method == 'POST' and form.validate():
            user = User.get_by_email(form.email.data.strip())
            if user and user.check_password(form.password.data.strip()):
                # If the user credentials are correct, start an authenticated session
                login_user(user, form.remember.data)

                # Tell Flask-Principal the identity has changed
                identity_changed.send(current_app._get_current_object(), identity=Identity(user.id))

                # Redirect to landing
                return redirect(url_for("landing"))
            else:
                # Otherwise, display an error message and display the login form again
                flash("Invalid credentials","error")
        return render_template('auth/login.html', form=form)

@bp.route("/register", methods=('GET','POST'))
def register():
  if current_user.is_authenticated:
    flash('You are already logged in.','info')

    return redirect(url_for("landing"))
  else:
    form = RegistrationForm(request.form)

    if request.method == 'POST' and form.validate():
      user = User.create_user(
                      role = form.role.data,
                      email = form.email.data,
                      password = form.password.data
                      )
      
      login_user(user)
      flash("User created.","success") # Skal vi egentlig overveje at fjerne disse? Ikke så "pro"
      return redirect(url_for('landing'))
    # elif request.method == 'POST':
    #     flash("post bracket entered but form not validated.","Debug:")  # Only for debug purposes.
    return render_template('auth/register.html', form=form)

@bp.route('/logout', methods=['GET'])
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
    
    return redirect(url_for('landing'))