from flask.cli import with_appcontext
from flask_login import UserMixin
from . import db, bcrypt
from .images import delete_picture


# ------- COMMON MODELS FOR ALL USERS -------- #

class User(UserMixin, db.Model):
    """
    User model representing a user in the application.
    Inherits from both UserMixin and db.Model to integrate Flask-Login and SQLAlchemy.

    By inheriting from UserMixin, the User class is automatically compatible with
    Flask-Login's user management system.
    """
    
    __tablename__ = 'users'

    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    # User's email, it is used as user identification during authentication so must be unique but it can be changed over time
    email      = db.Column(db.String(60), unique=True, index=True)
    # User's password, stored as a hash
    password   = db.Column(db.String(80))
    # User's role, used for role-based access control. "seeker", "provider"
    role = db.Column(db.String(80), nullable=False)
    
    # One-Many relationship between User and Application
    applications = db.relationship("Application", back_populates="user")
    # One-Many relationship between User and Collective
    collectives = db.relationship("Collective", back_populates="user")
    

    def check_password(self, password):
        """
        Check if the provided password matches the stored hash.

        Args:
            password (str): The password to check.

        Returns:
            bool: True if the password matches, False otherwise.
        """
        return bcrypt.check_password_hash(self.password, password)

    @classmethod
    def create_user(cls, role, email, password):
      """
      Create a new user with the provided details.

      Args:
          role (str): The user's role.
          email (str): The user's email.
          password (str): The user's password, which will be hashed before storage.

      Returns:
          User: The newly created user object.
      """
      user = cls( role     = role.strip(),
                  email    = email.strip(),
                  password = bcrypt.generate_password_hash(password).decode('utf-8'),
                )
      db.session.add(user)
      db.session.commit()
      return user

    @staticmethod
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
   
    
    
# ------- SEEKER SPECIFIC MODELS -------- #
class SeekerProfile(db.Model):
    __tablename__ = 'seekerprofiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    name = db.Column(db.String(80), nullable=True)
    description = db.Column(db.String(500), nullable=True)
    birthdate = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(80), nullable=True)
    occupation = db.Column(db.String(80), nullable=True)
    image = db.Column(db.String(500), nullable=True) # image name

    @classmethod
    def create_seekerprofile(cls, user_id, name, description, birthdate, gender, occupation, image):
        """
        Create a new seeker profile with the provided details.

        Args:
            user_id (int): User's id
            name (str | None): User's name
            description (str | None): A description of the user
            birthdate (Date | None): User's date of birth
            gender (str | None): User's gender
            occupation (str | None): User's occupation
            image (str| None): User's profile picture

        Returns:
            SeekerProfile: The newly created profile object
        """
        seekerprofile = cls(
                            user_id     = user_id,
                            name        = name,
                            description = description,
                            birthdate   = birthdate,
                            gender      = gender,
                            occupation  = occupation,
                            image       = image
                            )
        db.session.add(seekerprofile)
        db.session.commit()
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
    

    def replace_all_fields(self, name, description, birthdate, gender, occupation, image):
        """
        Replace all profile fields (PUT)

        Args:
            name (str | None): User's name
            description (str | None): A description of the user
            birthdate (Date | None): User's date of birth
            gender (str | None): User's gender
            occupation (str | None): User's occupation
            image (str| None): User's profile picture
        """
        self.name = name
        self.description = description
        self.birthdate = birthdate
        self.gender = gender
        self.occupation = occupation
        
        # If a new image is provided delete the old image and store the new one
        if image:
            delete_picture(self.image)
            self.image = image
        # If given image is None, we don't change the current image.
        # User needs to explicitly delete profile picture (unsupported) if they want that.

        db.session.commit()



# ------- PROVIDER SPECIFIC MODELS -------- #
class Collective(db.Model):
    __tablename__ = 'collectives'

    id = db.Column(db.Integer, primary_key=True)
    submitter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    city = db.Column(db.String(80), nullable=False)
    street = db.Column(db.String(80), nullable=False)
    roomsize = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Double, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    image = db.Column(db.String(500), nullable=False) #image name.
  
    # Many-One relationship between Collective and User
    user = db.relationship("User", back_populates="collectives")
    # One-Many relationship between Collective and Application
    applications = db.relationship("Application", back_populates="collective")

    @staticmethod
    def get_all():
        """
        Retrieve all collectives

        Returns:
            List: A list of all the collectives in the database
        """
        return Collective.query.order_by(Collective.id).all()

    @staticmethod
    def get_by_id(id):
        """
        Retrieve a collective by its ID

        Args:
            id (int): The ID of the collective

        Returns:
            Collective: The collective object if found, otherwise None.
        """
        return Collective.query.filter_by(id=id).first()

    @staticmethod
    def get_by_submitter(user_id):
        """
        Retrieve all collectives submitted by a specific user (provider)

        Args:
            user_id (int): The ID of the user

        Returns:
            List: A list of all the user's collectives
        """
        return Collective.query.filter_by(submitter_id=user_id).all()
    
    @staticmethod
    def get_by_city(city):
        """
        Retrieve collectives by a specific city.
        Gets collectives in cities that have the given city argument as prefix.

        Args:
            city (str): The name of a city

        Returns:
            List: A list of all found collectives
        """
        return Collective.query.filter(Collective.city.startswith(city)).all()
    
    def get_by_filters(city=None, roomsize=None, price=None):
        """
        Filters collectives by multiple filters.

        Args:
            city (str, optional): The city the collective should be in. Defaults to None.
            roomsize (int, optional): The minimum size of the room. Defaults to None.
            price (float, optional): The maximum price. Defaults to None.

        Returns:
            List: A list of all collectives matching the provided filters
        """
        # Fetch all queries.
        query = Collective.query

        # Filter step-by-step
        if city:
            query = query.filter(Collective.city.startswith(city))
        if roomsize:
            query = query.filter(Collective.roomsize >= roomsize)
        if price:
            query = query.filter(Collective.price <= price)

        return query.all()


    @classmethod
    def create_collective(cls, submitter_id, city, street, roomsize, price, description, image):
        """
        Create a new collective with the provided details.

        Args:
            submitter_id (int): The ID of the provider
            city (str): The city the collective is located in
            street (str): The name of the street
            roomsize (int): The size of the room in m^2
            price (double): The price of the room
            description (int): A description of the collective
            image (str): The name of the image of the collective

        Returns:
            Collective: The newly created collective object
        """
        collective = cls(
            submitter_id = submitter_id,
            city = city.strip(),
            street = street.strip(),
            roomsize = roomsize,
            price = price,
            description = description.strip(),
            image = image.strip()
        )
                    
        db.session.add(collective)
        db.session.commit()
        return collective


# ---------------- Initializing default data ---------------- #
def create_default_userbase():
  existing_seeker = User.query.filter_by(role="seeker").first()
  if not existing_seeker:
     User.create_user("seeker", "seeker@gmail.com", "123")
  existing_provider = User.query.filter_by(role="provider").first()
  if not existing_provider:
     User.create_user("provider", "provider@gmail.com", "123")


descr = """
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Mauris a finibus libero, at elementum urna. Sed dictum dapibus ornare. Maecenas egestas molestie vulputate. Donec maximus, ipsum a rhoncus eleifend, urna turpis volutpat mauris, id faucibus tellus turpis convallis tellus. Suspendisse a augue aliquet, dapibus risus et, condimentum turpis. Morbi finibus ultricies cursus. Nullam commodo felis eu facilisis lacinia. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos.

Vestibulum vestibulum neque eu lobortis malesuada. Pellentesque euismod erat mauris, non tempor lectus vulputate sit amet. Suspendisse eget nulla sed est lobortis imperdiet eu ut dui. Integer in semper ipsum, sed blandit sem. Maecenas consectetur vitae enim eu feugiat. Etiam non consectetur lorem. Sed non elit molestie, semper nulla vitae, sagittis eros. Suspendisse ante arcu, placerat vel ligula at, bibendum tincidunt tellus. Nam semper arcu neque, sit amet vestibulum felis commodo non. Nam in aliquet justo. Nulla auctor odio semper, eleifend massa et, volutpat purus. Suspendisse sit amet eros vel justo vehicula pharetra. Aenean tristique at ipsum id malesuada.
"""

def create_default_collectives():
  Collective.create_collective(2, "Odense C", "Vindegade", 50, 2569, descr,"1.jpg") #submitterID = 2. provider@gmail.com.
  Collective.create_collective(2, "Odense M", "Bogense", 23, 5000, descr, "2.jpg") #submitterID = 2. provider@gmail.com.
  Collective.create_collective(2, "Odense M", "Stige", 35, 4000, descr, "3.jpg") #submitterID = 2. provider@gmail.com.


# Create tables within the application context
def init_db(app):
    with app.app_context():
        db.create_all()
        create_default_userbase()
        create_default_collectives()





# -------------- UNFINISHED AND UNUSED APPLICATION MODEL ------------- #

class Application(db.Model):
    """Placeholder Application model """
    __tablename__ = 'applications'

    id = db.Column(db.Integer, primary_key=True)
    submitter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    collective_id = db.Column(db.Integer, db.ForeignKey('collectives.id'), nullable=False)

    time_of_submission = db.Column(db.DateTime, nullable=True)
    description = db.Column(db.String(500))

    # Many-One relationship between Application and User
    user = db.relationship("User", back_populates="applications")

    # Many-One relationship between Application and Collective
    collective = db.relationship("Collective", back_populates="applications")

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
    
    @classmethod  #Class Method: Static Method men som tager imod selve classen som første argument. Tillader os her at constructe en class user og returne den.
    def create_application(cls, submitter_id, collective_id,description):
      """
      Create a new application with the provided details.

      Args:
          name (str): The application's name.
          email (str): The application's email.
          password (str): The application's password, which will be hashed before storage.

      Returns:
          application: The newly created application object.
      """
      
      application = cls(
          submitter_id        = submitter_id,
          collective_id       = collective_id,
          description     = description.strip(),
      )
                  
      db.session.add(application)
      db.session.commit()
      return application