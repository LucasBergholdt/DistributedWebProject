from flask import Blueprint, current_app, session, redirect, render_template, request, url_for, flash
from flask_login import current_user, login_required, login_user, logout_user
from flask_principal import Permission, RoleNeed, UserNeed, Identity, AnonymousIdentity, identity_changed
from .model import User
from .forms import LoginForm, RegistrationForm

bp = Blueprint('auth', __name__)

# Create permissions
seeker_permission = Permission(RoleNeed("seeker"))
provider_permission = Permission(RoleNeed("provider"))


# SESSIONS --------------------------------------------------------------------

# @login_manager.user_loader 
def load_user_from_id(id):
    return User.get_by_id(id)

# Flask Principal identity_loaded signal handler. Called when identity_loaded signal has been called.
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

@bp.route("/login", methods=('GET','POST'))
def login():
  """
  Login page:
  - If the user is already authenticated, redirects to the landing page.
  - If not, displays the login form and processes login attempts.
  - On successful login, redirects to landing page.
  - On failed login, flashes an error message and redisplays the login form.

  Returns:
      Response | str: The redirect response or login page.
  """
  if current_user.is_authenticated:
    flash('You are already logged in.', 'info')
    return redirect(url_for("logic.landing"))
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
              return redirect(url_for("logic.landing"))
          else:
              # Otherwise, display an error message and display the login form again
              flash("Invalid credentials", "error")
      return render_template('auth/login.html', form=form)


@bp.route("/register", methods=('GET','POST'))
def register():
  """
  Register page:
  - If the user is already logged in redirect to landing page.
  - Otherwise display register form
  - On successful registration user is created in the database an logged in

  Returns:
      Response | str: Redirect to landing page or registration page
  """
  if current_user.is_authenticated:
    flash('You are already logged in.', 'info')
    return redirect(url_for("logic.landing"))
  else:
    form = RegistrationForm(request.form)

    if request.method == 'POST' and form.validate():
      user = User.create_user(
                      role = form.role.data,
                      email = form.email.data,
                      password = form.password.data
                      )
      
      login_user(user)
      flash("User created.", "success")
      return redirect(url_for('logic.landing'))
    
    return render_template('auth/register.html', form=form)


@bp.route('/logout', methods=['GET'])
@login_required
def logout():
  """
  Logs out the user and redirects to the landing page.
  """
  # Remove the user information from the session
  logout_user()

  # Remove session keys set by Flask-Principal
  for key in ('identity.name', 'identity.auth_type'):
      session.pop(key, None)

  # Tell Flask-Principal the user is anonymous
  identity_changed.send(current_app._get_current_object(),
                        identity=AnonymousIdentity())
  
  return redirect(url_for('logic.landing'))