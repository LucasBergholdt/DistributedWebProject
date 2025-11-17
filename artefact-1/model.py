from flask_login import UserMixin
from . import db, bcrypt

class User(UserMixin, db.Model):
    """
    User model representing a user in the application.
    Inherits from both UserMixin and db.Model to integrate Flask-Login and SQLAlchemy.

    UserMixin provides default implementations for the methods that Flask-Login
    expects user objects to have:
    - is_authenticated: Property that should return True if the user is authenticated.
    - is_active: Property that should return True if the user is active.
    - is_anonymous: Property that should return False for regular users.
    - get_id(): Method that returns a unique identifier for the user as a string.

    By inheriting from UserMixin, the User class automatically gets these methods,
    making it compatible with Flask-Login's user management system.
    """

    __tablename__ = 'users'

    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    # User's email, it is used as user identification during authentication so must be unique but it can be changed over time
    email      = db.Column(db.String(60), unique=True, index=True)
    # User's password, stored as a hash
    password   = db.Column(db.String(80))
    # User's name, not used for identification (just an example of an extra field)
    name = db.Column(db.String(80), nullable=False)

    # User's role, used for role-based access control. "seeker", "provider"
    role = db.Column(db.String(80), nullable=False)

    # Attributes of user. Mostly relevant for a Seeker. These fields can be left NULL for a Provider.
    description = db.Column(db.String(500))

    birthdate = db.Column(db.String(80))

    gender = db.Column(db.String(80))

    occupation = db.Column(db.String(80))

    image = db.Column(db.String(500))

    def check_password(self, password):
        """
        Check if the provided password matches the stored hash.

        Args:
            password (str): The password to check.

        Returns:
            bool: True if the password matches, False otherwise.
        """
        return bcrypt.check_password_hash(self.password, password)

    # TODO: Skal description+birthdate etc også angives ved User Registration? Tag beslutning om dette.
    @classmethod  #Class Method: Static Method men som tager imod selve classen som første argument. Tillader os her at constructe en class user og returne den.
    def create_user(cls, role, name, email, password, description, birthdate, gender, occupation):
      """
      Create a new user with the provided details.

      Args:
          name (str): The user's name.
          email (str): The user's email.
          password (str): The user's password, which will be hashed before storage.

      Returns:
          User: The newly created user object.
      """
      
      user = cls( role     = role.strip(),
                  name     = name.strip(),
                  email    = email.strip(),
                  password = bcrypt.generate_password_hash(password).decode('utf-8'),
                  description = description.strip(),
                  birthdate = birthdate.strip(),
                  gender = gender.strip(),
                  occupation = occupation.strip()
                )
                  # evt også image.
      db.session.add(user)
      db.session.commit()
      return user

    @staticmethod #Static Method. Modtager ikke et implicit first argument.
    def get_by_id(id):
      """
      Retrieve a user by their ID.

      Args:
          id (int): The user's ID.

      Returns:
          User: The user object if found, otherwise None.
      """
      return User.query.filter_by(id=id).first()

    @staticmethod
    def get_by_email(email):
      """
      Retrieve a user by their email.

      Args:
          email (str): The user's email.

      Returns:
          User: The user object if found, otherwise None.
      """
      return User.query.filter_by(email=email.strip()).first()
    
    @staticmethod
    def email_exists(email):
      """
      Check if an email already exists in the database.

      Args:
          email (str): The email to check.

      Returns:
          bool: True if the email exists, False otherwise.
      """
      email = User.query.filter_by(email=email).first()
      return email is not None
      
class Collective(db.Model):
    __tablename__ = 'collectives'

    id = db.Column(db.Integer, primary_key=True)
    submitter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    description = db.Column(db.String(500))

    address = db.Column(db.String(500))
  
    space = db.Column(db.Integer())

    slotsTotal = db.Column(db.Integer())

    vacantSlots = db.Column(db.Integer())

    # images?

    # TODO: Skal nok være statitc methods eller have self som første parameter? Kan egentlig godt lide Application.get_all() f.eks. -> mere deskriptivt.

    @staticmethod
    def get_all():
        """Get all Collectives"""
        return Collective.query.order_by(Collective.id).all()

    @staticmethod
    def get_by_submitter(user_id):
        """Get all Collectives submitted by a specific user"""
        return Collective.query.filter_by(submitter_id=user_id).all()

class Application(db.Model):
    """Placeholder Application model """
    __tablename__ = 'applications'

    id = db.Column(db.Integer, primary_key=True)
    submitter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    collective_id = db.Column(db.Integer, db.ForeignKey('collectives.id'), nullable=False)

    time_of_submission = db.Column(db.DateTime, nullable=False)
    applicationtext = db.Column(db.String(500))

    # TODO: Skal nok være statitc methods eller have self som første parameter? Kan egentlig godt lide Application.get_all() f.eks. -> mere deskriptivt.
    @staticmethod
    def get_all():
        """Get all Applications"""
        return Application.query.order_by(Application.id).all()
    
    @staticmethod
    def get_by_submitter(user_id):
        """Get all Applications submitted by a specific user"""
        return Application.query.filter_by(submitter_id=user_id).all()
    
    @staticmethod
    def get_by_collective(collective_id):
        """Get all Applications submitted by a specific user"""
        return Application.query.filter_by(collective_id=collective_id).all()
    