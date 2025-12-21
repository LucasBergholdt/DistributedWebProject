import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask import Response 
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Cofnigure SQLAlchemy ORM
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')

def is_allowed_file_extension(filename):
  """
  Checks that the extension of provided filename is supported.

  Args:
      filename (str): the name of the file

  Returns:
      bool: true if extension is supported, otherwise false
  """
  return '.' in filename and \
          filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


# Data Model ------------------------------------------------------------------

db = SQLAlchemy(app)

class Pictures(db.Model):
  """
  Picture model representing an image.
  Inherits from db.Model to integrate SQLAlchemy.
  """
  __tablename__ = 'pictures'

  id = db.Column(db.Integer, primary_key=True)
  image_name = db.Column(db.String(500), unique=True)
  image_data = db.Column(db.LargeBinary, nullable=False)  # blob data


  @classmethod
  def create_picture(cls, image_name, image_data):
    """
    Creates a picture in the database
    
    Args:
        image_name (str): image name with random string
        image_data (byte): blob data fetched by file_storage.read()

    Returns:
        Pictures: The created Pictures object
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
  
  
# For populating the site with some default data for show:
def create_default_images():
  default_images = ["1.jpg", "2.jpg", "3.jpg"]
  
  for image_name in default_images:
    # Skip if the image already exists to avoid duplicates
    if Pictures.get_by_name(image_name):
      continue
    
    image_path = os.path.join("/service/default_images", image_name)
    
    # Opening in binary mode to get blob data ("rb")
    file = open(image_path, "rb")
    image_data = file.read()
    
    Pictures.create_picture(image_name, image_data)
    
# Create tables and default pictures
with app.app_context():
  db.create_all()
  create_default_images()


# ROUTES ----------------------------------------------------------------------

@app.route("/pictures", methods=['POST'])
def upload():
  """
  Uploads a new picture.
  Expects payload with blob data and filename.
  Makes a new filename and stores the blobdata with this filename.

  Returns:
    Response: JSON object with new filename.
  """
  # Ensuring all data is as expected
  if "file" not in request.files:
    return jsonify({"error": "Missing file"}), 400
  file_storage = request.files["file"]

  image_name = file_storage.filename
  blobdata = file_storage.read()

  if not all([image_name, blobdata]):
      return jsonify({"error": "Missing data"}), 400

  # Get secure version of provided filename
  filename = secure_filename(image_name)
  
  # Check that file has an allowed extension
  if not is_allowed_file_extension(filename):
      return jsonify({"error": "File extension not allowed"}), 405

  # Generate a random uuid to add infront of file name to ensure uniqueness
  random_str = uuid.uuid4().hex
  image_name = random_str + filename

  # Create the picture
  Pictures.create_picture(image_name, blobdata)
  
  return jsonify({"image_name": image_name}), 201


@app.route("/pictures/<string:image_name>", methods=['GET'])
def download(image_name):
  """
  Downloads a picture

  Args:
      image_name (str): The name of the image

  Returns:
      Response: Response with mimetype image/jpeg or JSON with error message.
  """
  entry = Pictures.get_by_name(image_name)
  if entry:
      return Response(
        entry.image_data,
        mimetype="image/jpeg",
        headers={
            "Content-Disposition": f'inline; filename="{entry.image_name}"'
      })
  else:
      return jsonify({"error": "Picture not found"}), 404
    
    
@app.route("/pictures/<string:image_name>", methods=["DELETE"])
def delete(image_name):
  """
  Deletes a picture entry. 

  Args:
      image_name (str): Name of image to delete

  Returns:
      Response: JSON with success or error message
  """
  entry = Pictures.get_by_name(image_name)
  if entry:
    db.session.delete(entry)
    db.session.commit()
    return jsonify({"success": "Picture successfully deleted"}), 200
  else:
    return jsonify({"error": "Picture not found."}), 404