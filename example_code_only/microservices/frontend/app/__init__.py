from flask import Flask, Response, jsonify, make_response, redirect, render_template, request, session, url_for, flash
import os
# from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
# from flask_bcrypt import Bcrypt

import requests
from wtforms import Form, SubmitField, StringField, EmailField, PasswordField, BooleanField, ValidationError
from wtforms.validators import DataRequired, Length, Email, EqualTo

app = Flask(__name__)

# Configure SQLAlchemy ORM to use SQLite database file 'flask.db'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
# WARNING: CSRF protection is disabled for simplicity in this demo
app.config['WTF_CSRF_ENABLED'] = False
# Secret key for session management and security features
app.config['SECRET_KEY'] = "change-me"

# The business logic API URL
AUTH_API = os.getenv('AUTH_API_URL')
TODO_API = os.getenv('TODO_API_URL')
# AUTH_API = "http://localhost:5001"


# WTForms for user registration
class RegistrationForm(Form):
  name = StringField('Name', validators=[DataRequired(), Length(min=1, max=80, message='You cannot have less than 1 or more than 80 characters')])
  email = EmailField('Email', validators=[DataRequired(), Email()]) # formerly had check if email already existed.
  password = PasswordField('Password', validators=[DataRequired(), EqualTo('confirm', message='Password must match')])
  confirm = PasswordField('Confirm', validators=[DataRequired()])
  submit = SubmitField('Register')

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


# Forms -----------------------------------------------------------------------

class EntryForm(Form):
  text = StringField( label='Description', validators=[DataRequired(), Length(min=1, max=100) ] )
  submit = SubmitField('Add')

# Routes for todo ----------------------------------------------------------------------

# @app.route("/todo",methods=["GET","POST"])
# def todo():
#   form = EntryForm(request.form)
#   if request.method == 'POST' and form.validate():
#     text = form.text.data
#     db.session.add(Entry(text = text))
#     db.session.commit()
#   entries = Entry.query.order_by(Entry.id).all()
#   return render_template("todo.html", entries=entries, form=form)

#---------
# LOGIC API -> HTTP request to logic container inside of docker 
# Connecting front end to backend. 

# KOMMUNIKATION MED TO-DO

  @app.route("/todos",methods=["GET","POST"])
  def todos():
    
    ### Tjekke, om en bruger allerede er logget ind via browserens cookies. 
    token = request.cookies.get('api_token')

    user_id = None

    if token:
      response = requests.get(f"{AUTH_API}/sessions", params={"api_token":token})
      if response.ok:
        user_id = response.json().get("user_id")
    
    if user_id is None:
      return redirect(url_for("home"))

    if not TODO_API:
      raise ValueError("TODO_API_URL environment variable is not set!")

    # ovenstående muligvis unødvendigt. 

    ## ACTUAL FUNCTIONALITY HERE ##

    # Hvis en bruger vil tilføje nyt:
    form = EntryForm(request.form)
    if request.method == 'POST' and form.validate():
      text = form.text.data
      # form.completed.data

      # POST to BACKEND TO_DO:
      # mangler tjek om korrekt (201)
      requests.post(f"{TODO_API}/todos", json={"text": text, "user_id":user_id})
    
    # GET entries already existing from the backend (todos).
    response = requests.get(f"{TODO_API}/todos",params={"user_id":user_id}) # Request GET
    entries = response.json() if response.ok else [] # place data in entries, for use below. 
    
    return render_template("todo.html", entries=entries, form=form)


# @app.route("/delete/<int:id>")
# def delete(id):
#   entry = Entry.query.filter_by(id=id).first()
#   if entry:
#     db.session.delete(entry)
#     db.session.commit()
#     flash('Entry deleted.', 'info')
#   else:
#     flash("Sorry, we couldn't find the entry that you wanted to delete.", 'warning')
#   return redirect(url_for('todo'))

@app.route("/delete/<int:id>")
def delete(id):

  token = request.cookies.get('api_token')

  user_id = None

  if token:
    response = requests.get(f"{AUTH_API}/sessions", params={"api_token":token})
    if response.ok:
      user_id = response.json().get("user_id")
  
  response = requests.delete(f"{TODO_API}/todos/{user_id}/{id}")
  
  if response.status_code == 204:
    flash('Entry deleted.', 'info')
  else:
    flash("Sorry, we couldn't find the entry that you wanted to delete.", 'warning')
  return redirect(url_for('todos'))

# ROUTES for login ----------------------------------------------------------------------

@app.route("/", methods=('GET','POST'))
def home():
  """
  Main page:
  - Landing page. Handles cookies. 
  - Current session stored in browser.
  - Requests data from the backend and acts upon returned message.
  """

  # Få den nuværende cookie ud af vores browser med api token. 
  token = request.cookies.get("api_token")
  
  if token:

    # Tjekker om brugerens session eksisterer. 
    # /sessions GET
    response = requests.get(f"{AUTH_API}/sessions", params={"api_token": token})
  
    if response.status_code == 200: 
      flash("already logged in")
      return redirect(url_for('todos'))

  # Hvis session ikke eksisterer, foretag normal startside flow. 
  form = LoginForm(request.form)

  if request.method == 'POST'and form.validate():  # Logging in
    email = form.email.data
    password = form.password.data
 
    # /sessions POST
    response = requests.post(f"{AUTH_API}/sessions", json={
        "email": email,
        "password": password,
      }) 

    if response.status_code == 200:
      
      ## Get json from backend
      data = response.json() # modtag token fra backend, for at sætte den i cookie. 
      
      # Login og set den returnerede token i vores browser-cookie. 
      flask_response = make_response(redirect(url_for('todos')))
      flask_response.set_cookie("api_token", data["api_token"], httponly=True, samesite="Lax", path='/')

      # session['user_id'] = data['user_id']        # DENNE SKAL MAN BRUGE, HVIS MAN ØNSKRE DEN TRADITIONELLE SESSION-COOKIE, I STEDET FOR "API-TOKEN"
      
      flash("Login successful!", "success")
      
      return flask_response
    else:
      flash(response.json().get("message", "Login failed"), "error")
      return render_template("login.html", form=form)
    
  return render_template('login.html', form=form)


# Vi har brug for en GET til at render en page, selvom vi kun POSTer noget.
@app.route("/users", methods=['POST', 'GET'])
def register():
  """
  Registration page:
  """

  # Overvej at kontrollere hvorvidt en bruger allerede er logget ind. 

  form = RegistrationForm(request.form)
  if request.method == 'POST' and form.validate():

    name = request.form['name']
    email = request.form['email']
    password = request.form['password']

    # /users POST
    response = requests.post(f"{AUTH_API}/users", json={
        "name": name,
        "email": email,
        "password": password
      }) 
  
    if response.status_code == 200:
      flash("Registration Successful","success")
      return redirect(url_for('home')) # Redirect to "/". 
    else:
      flash("Registration not succesful", "fail")
      return render_template('register.html', form=form)
    
  return render_template('register.html', form=form)

@app.route('/logout', methods=['POST'])
def logout_view():
  """Deletes Session entry."""
  
  token = request.cookies.get("api_token")

  if token:
    
    response = requests.delete(f"{AUTH_API}/sessions", params={"api_token":token})

    if response.ok:
      flash("Session ended","success")
      resp = redirect(url_for('home'))
      resp.set_cookie("api_token", "", expires=0)
      return resp
  else:
    flash("Session did not end", "fail")
    return redirect(url_for('home'))


