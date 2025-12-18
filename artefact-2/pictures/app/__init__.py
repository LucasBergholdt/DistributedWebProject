import secrets
import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

from flask import Response #TODO

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

class Pictures(db.Model):
  """
  User model representing a user in the application.
  Inherits from db.Model to integrate SQLAlchemy.
  """
  __tablename__ = 'pictures'

  id = db.Column(db.Integer, primary_key=True)

  image_name = db.Column(db.String(500))

  image_data = db.Column(db.LargeBinary, nullable=False)  # blob data


  @classmethod
  def create_picture(cls, image_name, image_data):
    """
    Creates a picture
    
    :param cls: Description
    :param image_name: name: image name with random string.
    :param image_data: blob data. file_storage.read()
    """




    picture = cls(
        image_name = image_name,
        image_data = image_data 
    )

    db.session.add(picture)
    db.session.commit()
    return picture

  @staticmethod
  def get_by_id(id):
    """
    Retrieve a Picture by their ID.

    Args:
        id (int): The Picture's ID.

    Returns:
        Picture: The Picture object if found, otherwise None.
    """
    return Pictures.query.filter_by(id=id).first()
  
  @staticmethod
  def get_by_name(image_name):
    """
    Retrieve a Picture by their name.

    Args:
        name (str): The Picture's name.

    Returns:
        Picture: The Picture object if found, otherwise None.
    """
    return Pictures.query.filter_by(image_name=image_name).first()

# Clears the database and create tables within the application context
with app.app_context():
  db.drop_all() #TODO
  db.create_all()





# ROUTES ----------------------------------------------------------------------
# TODO: Done.
@app.route("/pictures", methods=['POST'])
def upload():
  """
  Uploads a new picture.
  Expects payload with blob data and filename.
  Makes a new filename and stores the blobdata with this filename.

  Returns:
    str: New filename.

  """

  if "file" not in request.files:
    return jsonify({"error": "Missing file"}), 400
  file_storage = request.files["file"]

  image_name = file_storage.filename
  blobdata = file_storage.read()  #TODO: Måske read selve file_Storage.stream? Eller ved Python godt dette?

  if not all([image_name, blobdata]):
      return jsonify({"error": "Missing data"}), 400

  # Get secure version of provided filename
  filename = secure_filename(image_name)
  
  # Check that file has an allowed extension
  if not is_allowed_file_extension(filename):
      return jsonify({"error": "File extension not allowed"}), 405

  random_str = uuid.uuid4().hex
  image_name = random_str + filename

  # return jsonify({"debug": "I got so far!"}), 499 #DEBUG

  # store the picture
  Pictures.create_picture(image_name, blobdata) # FAILER HER!
  # return jsonify({"debug": "I got so far!"}), 498 #DEBUG
  return jsonify({"image_name": image_name}), 201


@app.route("/pictures/<string:image_name>", methods=['GET'])
def download(image_name):
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
    entry = Pictures.get_by_name(image_name)
    if entry:
        return Response(
          entry.image_data,
          mimetype="image/jpeg",  # or entry.content_type if you store it
          headers={
              "Content-Disposition": f'inline; filename="{entry.image_name}"'
        })
    #BLOB, 200  #TODO
    else:
        return jsonify({"error": "Picture not found"}), 404


# TODO
@app.route("/pictures", methods=['GET'])
def download_multiple():
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