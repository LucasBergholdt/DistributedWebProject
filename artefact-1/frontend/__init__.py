import os

from flask import Flask, render_template, request, flash, redirect, url_for

from wtforms import IntegerField, DateTimeField, DecimalField, FileField, Form, SubmitField, SelectField, StringField, EmailField, PasswordField, BooleanField, ValidationError
from wtforms.validators import DataRequired, Length, Email, EqualTo, InputRequired


import os
import requests


app = Flask(__name__)

app.config['WTF_CSRF_ENABLED'] = False # warning!
app.config['SECRET_KEY'] = "change-me"

# The business logic API URL
LOGIC_API = os.getenv('LOGIC_API_URL')

# ------------------------------------------- FORMS ------------------------------------------------------
def email_exists(form, field): 
  if User.email_exists(field.data): #LOGIC. 
    raise ValidationError('Email already exists.')

# WTForms for user registration.

class RegistrationForm(Form):
  role = SelectField('Role', 
                         choices=[('seeker', 'Seeker'), ('provider', 'Provider')], 
                         validators=[DataRequired()])
  name = StringField('Name', validators=[DataRequired(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  email = EmailField('Email', validators=[DataRequired(), email_exists, Email()])
  password = PasswordField('Password', validators=[DataRequired(), EqualTo('confirm', message='Password must match')])
  confirm = PasswordField('Confirm', validators=[DataRequired()])
  submit = SubmitField('Register')
"""
for opdatering af profil:

 description = StringField('Describe yourself', validators=[DataRequired(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  birthdate = StringField('Birthdate', validators=[DataRequired(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  gender = StringField('Gender', validators=[DataRequired(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  occupation = StringField('Occupation', validators=[DataRequired(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  image = StringField('Image', validators=[DataRequired(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
"""

class CollectiveForm(Form):
  address = StringField('Address of collective', validators=[DataRequired(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  space = IntegerField('Amount of space (square meters)', validators=[DataRequired()])
  slotsTotal = IntegerField('Amount of residents that the collective can hold', validators=[DataRequired()])
  vacantSlots = IntegerField('Amount of available slots in the collective', validators=[DataRequired()])
  description = StringField('Description of the collective', validators=[DataRequired(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  submit = SubmitField('Register your collective')

class ApplicationForm(Form):
  description = StringField('Your application', validators=[DataRequired(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  submit = SubmitField('Apply for this collective')

class LoginForm(Form):
  email = EmailField('Email', validators=[DataRequired(), Email()])
  password = PasswordField('Password', validators=[DataRequired()])
  remember = BooleanField('Remember Me')
  submit = SubmitField('Login')


# ------------------------------------------- ROUTES ------------------------------------------------------
@app.route("/", methods=('GET','POST'))
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
          role = User.get_by_id(current_user.get_id()).role   
          return redirect(url_for(role))
    else:
        form = LoginForm(request.form)
        if request.method == 'POST' and form.validate():


            # TODO: ALT underfølgende er Logic. Skal returne om Login var successfuldt.
        
            user = User.get_by_email(form.email.data.strip())
            if user and user.check_password(form.password.data.strip()):
                # If the user credentials are correct, start an authenticated session
                login_user(user, form.remember.data)

                # Tell Flask-Principal the identity has changed
                identity_changed.send(current_app._get_current_object(), identity=Identity(user.id))

                # Redirect to proper role.
                return redirect(url_for(user.role))
            else:
                # Otherwise, display an error message and display the login form again
                flash("Invalid credentials","error")
        return render_template('login.html', form=form)

@app.route("/register", methods=('GET','POST'))
def register():

  if current_user.is_authenticated: #LOGIC. Interager med /logic/is_authenticated
    flash('You are already logged in.','info')
    role = User.get_by_id(current_user.get_id()).role   #LOGIC.
    return redirect(url_for(role))
  else:
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
      # POST to backend service
      requests.post(f"{LOGIC_API}/entries", json={
         "role": form.role.data,
         "name": form.name.data,
         "email": form.email.data,
         "password": form.password.data}
         )
      flash("User created.","success")
      return redirect(url_for('login'))
    elif request.method == 'POST':
      flash("post bracket entered but form not validated.","Debug:")  # Only for debug purposes.
    return render_template('register.html', form=form, error="Invalid input")

# logout. Hvis muligt, flyt til LOGIC.
@app.route('/logout', methods=['GET'])
@login_required
def logout():
     # Remove the user information from the session
    logout_user()

    # Remove session keys set by Flask-Principal. LOGIC.
    for key in ('identity.name', 'identity.auth_type'):
        session.pop(key, None)

    # Tell Flask-Principal the user is anonymous
    identity_changed.send(current_app._get_current_object(),
                          identity=AnonymousIdentity())
    return redirect(url_for('login'))

# ------------------------- Seeker Routes ---------------------------------
@app.route("/seeker",methods=["GET","POST"])  #TODO: Fjern POST? Bruges ikke.
@login_required
@seeker_permission.require()
def seeker():
    collective_entries = requests.get(f"{LOGIC_API}/collectives") # ALL collectives.

    
    your_applications = requests.get(f"{LOGIC_API}/applications") # Fetches applications with your userID. TODO: Lav en parameter.
    #your_applications = current_user.applications #LOGIC
    #Collective.get_by_submitter(current_user.id)
    return render_template("seeker.html", collective_entries=collective_entries, your_applications=your_applications)

@app.route("/apply/<int:id>", methods=["GET", "POST"])
@login_required
@seeker_permission.require()
def apply(id):
  """For applying to a collective.
  """
  form = ApplicationForm(request.form)
  if request.method == 'POST' and form.validate():
    requests.post(f"{LOGIC_API}/applications", json={"description": form.description.data})
    flash("User created.","success")
    return redirect(url_for('seeker'))
    #Application.create_application(current_user.id, id, form.description.data) #LOGIC
  return render_template("apply.html", form=form)

# ------------------------- Provider Routes ---------------------------------
@app.route("/provider",methods=["GET","POST"])
@login_required
@provider_permission.require()
def provider():
    # Get all collectives that Provider owns. Done directly by accessing foreign keys.
    # evt. anvend user.collectives (vha. db.relationship())

    collective_entries = requests.get(f"{LOGIC_API}/collectives/{current_user.id}") # Fetches all collectives for current Provider. 
    #collective_entries = Collective.get_by_submitter(current_user.id) #LOGIC

    collective_entries = requests.get(f"{LOGIC_API}/applications{current_user.id}") # Fetches all applications for the current Provider. Laver nedenstående queries.
    # Get all applications mapped to these collectives.

    """
    application_entries = [ #LOGIC
      application
      for collective in collective_entries
        for application in collective.applications  #relationship() anvendes.
    ]
    return render_template("provider.html", collective_entries=collective_entries, application_entries=application_entries)
    """
@app.route("/new_collective", methods=["GET", "POST"])
@login_required
@provider_permission.require()
def new_collective():
    form = CollectiveForm(request.form)
  
    if request.method == 'POST' and form.validate(): 
        requests.post(f"{LOGIC_API}/entries", json={
                "address": form.role.data,
                "space": form.name.data,
                "slotsTotal": form.email.data,
                "vacantSlots": form.password.data,
                "description": form.description.data}
                )
        flash("Collective created.","success")
        return redirect(url_for('provider'))

    """
    Collective.create_collective( #LOGIC
          current_user.id, 
          form.address.data,
          form.space.data,
          form.slotsTotal.data,
          form.vacantSlots.data,
          form.description.data)
      return redirect(url_for("provider"))
    """

    return render_template("new_collective.html", form=form)

# Only Providers can do this. Security Flaw: Providers can remove another provider's collective.
@login_required
@provider_permission.require()
@app.route("/delete_collective/<int:id>")   #methods GET. TODO
def delete_collective(id):
    response = requests.delete(f"{LOGIC_API}/collectives/{id}")
    if response.status_code == 200:
      flash('Entry deleted.', 'info')
    else:
      flash("Sorry, could not delete that entry.", 'warning')
    return redirect(url_for('provider'))

"""LOGIC

  collective = Collective.query.filter_by(id=id).first() #LOGIC
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
"""

# ------------ Routes for both roles ------------------

# Both seekers and providers can do this now. Security Flaw: Providers can remove another provider's application. Same goes for seekers.
@login_required
@app.route("/delete_application/<int:id>")
def delete_application(id): #LOGIC
    response = requests.delete(f"{LOGIC_API}/applications/{id}")
    if response.status_code == 200:
      flash('Entry deleted.', 'info')
    else:
      flash("Sorry, could not delete that entry.", 'warning')
    return redirect(url_for(current_user.role))

"""LOGIC
    application = Application.query.filter_by(id=id).first() 
    if application:
        db.session.delete(application)
        db.session.commit()
        flash("Application has been deleted.", 'info')
    else:
      flash("Sorry, we couldn't find the application that you wanted to delete.", 'warning')
    return redirect(url_for(current_user.role))
"""






"""
LOGIC:
@app.route("/applications/<int:id>")
  methods: DELETE, POST, GET
  skal også understøtte en parameter.




@app.route("/collectives/<int:id>")
  methods: DELETE, POST, GET


"""



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