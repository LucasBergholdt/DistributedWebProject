import secrets
import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

import uuid
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Cofnigure SQLAlchemy ORM
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
# Secret key for session management and security features 
app.config['SECRET_KEY'] = "change-me" #TODO Needed?


def is_allowed_file_extension(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


# Data Model ------------------------------------------------------------------

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class Picture(db.Model):
  """
  User model representing a user in the application.
  Inherits from db.Model to integrate SQLAlchemy.
  """
  __tablename__ = 'pictures'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(300))
  data = db.Column(db.LargeBinary, nullable=False)


  @classmethod
  def create_picture(cls, name, data):
    picture = cls(
      name = name,
      data = data
    )

    db.session.add(picture)
    db.session.commit()

  @staticmethod
  def get_by_id(id):
    """
    Retrieve a Picture by their ID.

    Args:
        id (int): The Picture's ID.

    Returns:
        Picture: The Picture object if found, otherwise None.
    """
    return Picture.query.filter_by(id=id).first()
  
  @staticmethod
  def get_by_name(name):
    """
    Retrieve a Picture by their name.

    Args:
        name (str): The Picture's name.

    Returns:
        Picture: The Picture object if found, otherwise None.
    """
    return Picture.query.filter_by(name=name.strip()).first()

# Clears the database and create tables within the application context
with app.app_context():
  # db.drop_all() #TODO
  db.create_all()


# ROUTES ----------------------------------------------------------------------
# TODO: Done.
@app.route("/pictures", methods=['POST'])
def upload():
  """
  Uploads a new picture.
  Expects a payload with BLOB data.
  - If success, ...
  - ...

  Args:
    - A "file" sent by multipart/form data (by specifying "files" in requests.post)

  Returns:
    str: Stored filename
  """

  if "file" not in request.files:
    return jsonify({"error": "Missing file"}), 400
  file_storage = request.files["file"]

  name = file_storage.filename
  blobdata = file_storage.read()  #TODO: Måske read selve file_Storage.stream? Eller ved Python godt dette?

  if not all([name, blobdata]):
      return jsonify({"error": "Missing data"}), 400

  # Get secure version of provided filename
  filename = secure_filename(name)
  
  # Check that file has an allowed extension
  if not is_allowed_file_extension(filename):
      return jsonify({"error": "File extension not allowed"}), 405

  random_str = uuid.uuid4().hex
  stored_name = random_str + filename

  # store the picture
  Picture.create_picture(stored_name, blobdata)
  return jsonify({"filename": stored_name}), 201

  
@app.route("/pictures", methods=['GET'])
def download():
   """
  Downloads a picture
  Expects a name
  - If success, ...
  - ...

  Args:
    - The name of the image

  Returns:
      Response: BLOB object
  """
