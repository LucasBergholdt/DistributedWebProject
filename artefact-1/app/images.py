import uuid
from flask import Blueprint, current_app
from werkzeug.utils import secure_filename
import os

# ----------- PART OF SEEKER AND PROVIDER DB -------- #

bp = Blueprint('images', __name__)

def is_allowed_file_extension(filename):
    """
    Checks that the extension of provided filename is supported.

    Args:
        filename (str): the name of the file

    Returns:
        bool: true if extension is supported, otherwise false
    """
    allowed = current_app.config.get('ALLOWED_EXTENSIONS', set())
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed
           
           
def save_image(form_image):
    """
    Saves the uploaded image with a unique name in the upload folder.

    Args:
        form_image: The file object from a form (e.g. form.image.data)

    Returns:
        str | None: The unique filename if saved successfully, otherwise None
    """
    # Check if file was uploaded
    if not form_image or not form_image.filename:
        return None

    # Get secure version of provided filename
    filename = secure_filename(form_image.filename)
    
    # Check that file has an allowed extension
    if not is_allowed_file_extension(filename):
        return None
    
    # Generate a random uuid string and add it to the filename, to ensure unique filenames
    random_str = uuid.uuid4().hex
    stored_name = random_str + filename
    # Store the image in the upload folder
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], stored_name)
    form_image.save(filepath)
    
    return stored_name
  

def delete_picture(filename):
    """
    Deletes a file from the upload folder

    Args:
        filename (str): The name of the file
    """
    # Do nothing if filename is null or empty
    if not filename:
        return
    else:
        # Delete the file from the upload folder
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(filepath):
            os.remove(filepath)
