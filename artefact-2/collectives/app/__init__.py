import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# configure SQL Alchemy ORM, 
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')

# Data Model ------------------------------------------------------------------

db = SQLAlchemy(app)

class Collective(db.Model):
    __tablename__ = 'collectives'

    id = db.Column(db.Integer, primary_key=True)
    submitter_id = db.Column(db.Integer, nullable=False)
    city = db.Column(db.String(80), nullable=False)
    street = db.Column(db.String(100), nullable=False)
    roomsize = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Double, nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_name = db.Column(db.String(500), nullable=False)

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
    
    @staticmethod
    def get_by_filters(city=None, roomsize=None, price=None, submitter_id=None):
        """
        Filters collectives by multiple filters.
        Returns all collectives if no filters are specified.

        Args:
            city (str, optional): The city the collective should be in. Defaults to None.
            roomsize (int, optional): The minimum size of the room. Defaults to None.
            price (float, optional): The maximum price. Defaults to None.
            submitter_id (int, optional): The id of owner of the collective. Defaults to None.

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
        if submitter_id:
            query = query.filter_by(submitter_id=submitter_id)
            
        return query.all()

    @classmethod
    def create_collective(cls, submitter_id, city, street, roomsize, price, description, image_name):
        """
        Create a new collective with the provided details.

        Args:
            submitter_id (int): The ID of the provider
            city (str): The city the collective is located in
            street (str): The name of the street
            roomsize (int): The size of the room in m^2
            price (double): The price of the room
            description (int): A description of the collective
            image_name (str): The name of the image of the collective

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
            image_name = image_name.strip()
        )

        db.session.add(collective)
        db.session.commit()
        return collective
  
    
    def to_dict(self):
        """
        Convert the Collective object into a plain Python dictionary,
        making it easy to convert into JSON for HTTP responses.

        Returns:
            dict: Collective details in dictionary
        """
        return {
            "id": self.id,
            "city": self.city,
            "street": self.street,
            "roomsize": self.roomsize,
            "price": self.price,
            "description": self.description,
            "image_name": self.image_name
        }


# ---------------- Initializing default data ---------------- #

# Description for default collectives
descr = """
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Mauris a finibus libero, at elementum urna. Sed dictum dapibus ornare. Maecenas egestas molestie vulputate. Donec maximus, ipsum a rhoncus eleifend, urna turpis volutpat mauris, id faucibus tellus turpis convallis tellus. Suspendisse a augue aliquet, dapibus risus et, condimentum turpis. Morbi finibus ultricies cursus. Nullam commodo felis eu facilisis lacinia. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos.

Vestibulum vestibulum neque eu lobortis malesuada. Pellentesque euismod erat mauris, non tempor lectus vulputate sit amet. Suspendisse eget nulla sed est lobortis imperdiet eu ut dui. Integer in semper ipsum, sed blandit sem. Maecenas consectetur vitae enim eu feugiat. Etiam non consectetur lorem. Sed non elit molestie, semper nulla vitae, sagittis eros. Suspendisse ante arcu, placerat vel ligula at, bibendum tincidunt tellus. Nam semper arcu neque, sit amet vestibulum felis commodo non. Nam in aliquet justo. Nulla auctor odio semper, eleifend massa et, volutpat purus. Suspendisse sit amet eros vel justo vehicula pharetra. Aenean tristique at ipsum id malesuada.
"""

# For populating the site with some default data for show:
def create_default_collectives():
  Collective.create_collective(2, "Aarhus C", "Vindegade", 50, 2569, descr,"1.jpg") #submitterID = 2. provider@gmail.com.
  Collective.create_collective(2, "Odense M", "Bogense", 23, 5000, descr, "2.jpg") #submitterID = 2. provider@gmail.com.
  Collective.create_collective(2, "Svendborg", "Strandvej", 35, 4000, descr, "3.jpg") #submitterID = 2. provider@gmail.com.

# Only creates the default collectives if db is empty
def seed_if_empty():
    if Collective.query.count() == 0:
        create_default_collectives()

# Creates tables and default collectives
with app.app_context():
  db.create_all()
  seed_if_empty()



# ------------------------------------------ ROUTES ----------------------------------------------------------------------

@app.route("/collectives", methods=["GET"])
def get_collectives():
    """
    Fetch all collectives filtering by any given filter params.

    Returns:
        Response: List of JSON objects with collective information
    """
    city = request.args.get("city")
    price = request.args.get("price", type=int)
    roomsize = request.args.get("roomsize", type=int)
    submitter_id = request.args.get("submitter_id", type=int)

    # Get collectives by applying filters.
    collectives = Collective.get_by_filters(city, roomsize, price, submitter_id)
    
    return jsonify([e.to_dict() for e in collectives]), 200  # returns list of json objects


@app.route("/collectives", methods=["POST"])
def post_collectives():
    """
    Creates a collective with the given information

    Returns:
        Response: Information about the created collective or error message.
    """
    # Get data from request
    data = request.get_json()
    submitter_id = data.get('submitter_id')
    city = data.get('city')
    street = data.get('street')
    price = data.get('price')
    description = data.get('description')
    roomsize = data.get('roomsize')
    image_name = data.get('image_name')

    # Ensure all required fields are present
    if not all([submitter_id, price, city, street, description, roomsize, image_name]): # works because None = False
        return jsonify({"error": "Missing data"}), 400

    # Create the collective
    collective = Collective.create_collective(
        submitter_id,
        city,
        street,
        roomsize,
        price,
        description,
        image_name
    )
    return jsonify(collective.to_dict()), 201


@app.route("/collectives/<int:id>", methods=["GET"])
def view_collective(id):
    """
    Fetches information about a collective with the given id.

    Args:
        id (int): ID of the collective

    Returns:
        Response: JSON object with collective information or error message.
    """
    entry = Collective.get_by_id(id)
    if entry:
        return jsonify(entry.to_dict()), 200
    else:
        return jsonify({"error": "Collective not found"}), 404


@app.route("/collectives/<int:id>", methods=["DELETE"])
def collectives_delete(id):
    """
    Deletes the collective entry with the given id.
    
    Args:
        id (int): ID of the collective
        
    Returns:
        Response: JSON object with success or error message
    """
    entry = Collective.get_by_id(id)
    if entry:
        db.session.delete(entry)
        db.session.commit()
        return jsonify({"success": "Collective successfully deleted"}), 200
    else:
        return jsonify({"error": "Collective not found."}), 404
