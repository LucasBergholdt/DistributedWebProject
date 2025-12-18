
from datetime import date
import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)

# Cofnigure SQLAlchemy ORM
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
#TODO secret key?


# Data Model ------------------------------------------------------------------

db = SQLAlchemy(app)

class SeekerProfile(db.Model):
    
    __tablename__ = 'seekerprofiles'

    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, unique=True, nullable=False) # Users can only have 1 profile
    name = db.Column(db.String(80), nullable=True)
    description = db.Column(db.String(500), nullable=True)
    birthdate = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(80), nullable=True)
    occupation = db.Column(db.String(80), nullable=True)
    image_name = db.Column(db.String(500), nullable=True)    # TODO: how fully should we support this?
    
    @classmethod
    def create_seekerprofile(cls, user_id, name, description, birthdate, gender, occupation, image_name):
        """
        Create a new seeker profile with the provided details.

        Args:
            user_id (int): User's id
            name (str): User's name
            description (str): A description of the user
            birthdate (Date): User's date of birth
            gender (str): User's gender
            occupation (str): User's occupation
            image_name (str): User's profile picture

        Returns:
            SeekerProfile: The newly created profile object
        """
        print("DEBUG: Entered create_seekerprofile")
        if birthdate:
            birthdate = (date.fromisoformat(birthdate))
        #TODO Har fjernet .strip() fordi felterne godt kan være None. Men vi skal nok stadig have strip funktionalitet.
        seekerprofile = cls(
                            user_id = user_id,
                            name = name,
                            description = description,
                            birthdate = birthdate,
                            gender = gender,
                            occupation = occupation,
                            image_name = image_name
                            )
        db.session.add(seekerprofile)
        print("DEBUG: About to commit new profile")
        db.session.commit()
        print("DEBUG: Commit succesful")
        return seekerprofile
    
    @staticmethod
    def get_by_user_id(user_id):
        """
        Retrieve a SeekerProfile by user_id.

        Args:
            id (int): The user's ID.

        Returns:
            SeekerProfile: The profile object if found, otherwise None.
        """
        return SeekerProfile.query.filter_by(user_id=user_id).first()
    
    def to_dict(self):
        """
        Convert the SeekerProfile object into a plain Python dictionary,
        making it easy to convert into JSON for HTTP responses.

        Returns:
            dict: SeekerProfile details in dictionary
        """
        return {
            "name": self.name,
            "description": self.description,
            "birthdate": self.birthdate.isoformat() if self.birthdate else None,
            "gender": self.gender,
            "occupation": self.occupation,
            "image_name": self.image_name
        }
        
    def replace_all_fields(self, name, description, birthdate, gender, occupation, image_name):
        """
        Replace all profile fields (PUT)

        Args:
            name (str): User's name
            description (str): A description of the user
            birthdate (Date): User's date of birth
            gender (str): User's gender
            occupation (str): User's occupation
            image_name (str): User's profile picture
        """
        if birthdate:
            birthdate = (date.fromisoformat(birthdate))
        self.name = name
        self.description = description
        self.birthdate = birthdate
        self.gender = gender
        self.occupation = occupation
        self.image_name = image_name
        db.session.commit()
        
        
with app.app_context():
    db.create_all()

# ROUTES ----------------------------------------------------------------------

@app.route("/profiles/<int:user_id>", methods=["GET"])
def get_profile(user_id):
    """
    Get the profile for the specified user.

    Args:
        user_id (ind): User's id

    Returns:
        Response: JSON object with profile details or error message.
    """
    profile = SeekerProfile.get_by_user_id(user_id)
    
    if profile:
        return jsonify(profile.to_dict()), 200
    else:
        return jsonify({"error": "Profile not found"}), 404
    
    
@app.route("/profiles/<int:user_id>", methods=["PUT"])
def put_profile(user_id):
    """
    Create or replace a profile.
    
    Epxects a JSON body with all profile fields.
    - If user doesn't have a profile, create it
    - If user has a profile replace it

    Args:
        user_id (int): The id of the user

    Returns:
        Response: JSON object with the new profile
    """
    # Get all the profile data from the request
    data = request.get_json()
    name = data.get("name")
    description = data.get("description")
    birthdate = data.get("birthdate")
    gender = data.get("gender")
    occupation = data.get("occupation")
    image_name = data.get("image_name")
    
    # Find the user's profile if it exists
    profile = SeekerProfile.get_by_user_id(user_id)
    
    if profile:
        # Replace current profile with provided information
        profile.replace_all_fields(name, description, birthdate, gender, occupation, image_name)
        status_code = 200
    else:
        # Create profile with provided information
        profile = SeekerProfile.create_seekerprofile(user_id, name, description, birthdate, gender, occupation, image_name)
        status_code = 201
    
    return jsonify(profile.to_dict()), status_code


#TODO: Skal API understøtte dette?
@app.route("/profiles/<int:user_id>", methods=["DELETE"])
def delete_profile(user_id):
    """
    Delete the profile associated with the given user id if it exists

    Args:
        user_id (int): User's id

    Returns:
        Response: 204 on success, 404 if profile doesn't exist
    """
    profile = SeekerProfile.get_by_user_id(user_id)

    if not profile:
        return jsonify({"error": "Profile not found"}), 404
    else:
        db.session.delete(profile)
        db.session.commit()
        return "", 204