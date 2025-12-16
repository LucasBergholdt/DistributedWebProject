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
    submitter_id = db.Column(db.Integer, nullable=False)    # had a foreign key before

    city = db.Column(db.String(500))
    street = db.Column(db.String(500))

    roomsize = db.Column(db.Integer())
    price = db.Column(db.Integer())
    
    description = db.Column(db.String(5000)) # todo: ændret til 5000, da debug strengen er for lang til 500. Hvorofr virker det så i monolith?
    image = db.Column(db.String(500))

    # Overvej konsekvens af manglende "relationships?"
    # Mere kompleks?

    @staticmethod
    def get_all():
        """Get all Collectives"""
        return Collective.query.order_by(Collective.id).all()

    @staticmethod
    def get_by_submitter(user_id):
        """Get all Collectives submitted by a specific user"""
        return Collective.query.filter_by(submitter_id=user_id).all()
    
    @staticmethod
    def get_by_submitter(user_id):
        """Get all Collectives submitted by a specific user"""
        return Collective.query.filter_by(submitter_id=user_id).all()
    
    @staticmethod
    def get_by_city(city):
        """Get all Collectives which cityname has given argument as prefix)"""
        return Collective.query.filter(Collective.city.startswith(city)).all()
    
    def get_by_filters(city, roomsize, price):
        """Filters collectives by multiple filters."""
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
    def create_collective(cls, submitter_id, city, street, roomsize, price, description,image):
      """
      Create a new collective with the provided details.

      Args:


      Returns:
          collective: The newly created collective object.
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
    


# Debug Purposes ------------------
descr = """
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Mauris a finibus libero, at elementum urna. Sed dictum dapibus ornare. Maecenas egestas molestie vulputate. Donec maximus, ipsum a rhoncus eleifend, urna turpis volutpat mauris, id faucibus tellus turpis convallis tellus. Suspendisse a augue aliquet, dapibus risus et, condimentum turpis. Morbi finibus ultricies cursus. Nullam commodo felis eu facilisis lacinia. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos.

Vestibulum vestibulum neque eu lobortis malesuada. Pellentesque euismod erat mauris, non tempor lectus vulputate sit amet. Suspendisse eget nulla sed est lobortis imperdiet eu ut dui. Integer in semper ipsum, sed blandit sem. Maecenas consectetur vitae enim eu feugiat. Etiam non consectetur lorem. Sed non elit molestie, semper nulla vitae, sagittis eros. Suspendisse ante arcu, placerat vel ligula at, bibendum tincidunt tellus. Nam semper arcu neque, sit amet vestibulum felis commodo non. Nam in aliquet justo. Nulla auctor odio semper, eleifend massa et, volutpat purus. Suspendisse sit amet eros vel justo vehicula pharetra. Aenean tristique at ipsum id malesuada.
"""

def create_default_collectives():
  Collective.create_collective(2, "Odense C", "Vindegade", 50, 2569, descr,"1.jpg") #submitterID = 2. provider@gmail.com.
  Collective.create_collective(2, "Odense M", "Bogense", 23, 5000, descr, "2.jpg") #submitterID = 2. provider@gmail.com.
  Collective.create_collective(2, "Odense M", "Stige", 35, 4000, descr, "3.jpg") #submitterID = 2. provider@gmail.com.
  Collective.create_collective(2, "København", "Nørrebro", 10, 10000, descr, "5.jpg") #submitterID = 2. provider@gmail.com.
# def seed_if_empty():
    # if Collective.query.count() == 0:
        # create_default_collectives()

with app.app_context():
  db.drop_all()
  db.create_all()
#   seed_if_empty()
  create_default_collectives()

  


# ------------------------------------------ ROUTES ----------------------------------------------------------------------
# Fetches all collectives. TODO: Support a parameter to fetch only list of collectives.
    # - List of Seeker's Collectives (that he applied for)
    # - List of Provider's Collectives

@app.route("/collectives", methods=["GET"])
def get_collectives():
    city = request.args.get("city")
    price = request.args.get("price", type=int)
    roomsize = request.args.get("roomsize", type=int)
    # submitter_id = filter.submitter_id

    # if submitter_id is not None:
    #     collectives = Collective.get_by_submitter(submitter_id)
    # city = filters.get("city")
    # price = filters.get("price")
    # roomsize = filters.get("roomsize")

    if city or price or roomsize:
        collectives = Collective.get_by_filters(city, roomsize, price)

    else:
        collectives = Collective.get_all()
    
    return jsonify([{
    "id": e.id, 
    "submitter_id": e.submitter_id, 
    "city": e.city,
    "street": e.street,
    "price": e.price,
    "description": e.description,
    "roomsize": e.roomsize,
    "image": e.image}
    for e in collectives]), 200  # returns list of json objects

@app.route("/collectives", methods=["POST"])
def post_collectives():
    data = request.get_json()   #fetch json objekt med info

    submitter_id = data.get('submitter_id')
    city = data.get('city')
    street = data.get('street')
    price = data.get('price')
    description = data.get('description')
    roomsize = data.get('roomsize')
    image = data.get('image')

    if not submitter_id or not price or not city or not street or not roomsize or not image:
        return jsonify({"error": "Missing data"}), 400

    collective = Collective.create_collective(
        submitter_id,
        city,
        street,
        price,
        description,
        roomsize,
        image
    )
    db.session.add(collective)
    db.session.commit()
    return jsonify({"id": collective.id}), 201  #TODO return whole collective object like in ToDo example?






















""" Old code




@app.route("/collectives/<int:id>", methods=["DELETE"])
def get_collectives(id):
    collective = Collective.query.get(id)
    if not collective:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(collective)
    db.session.commit()
    return jsonify({"message": "Deleted"}), 200


@app.route("/collectives/<int:id>/applications", methods=["GET"])
def get_collectives(id):
    applications = Application.get_by_collective(id)
    return jsonify([{
       "id": e.id, 
       "submitter_id": e.submitter_id, 
       "collective_id": e.collective_id,
       "time_of_submission": e.time_of_submission,
       "description": e.description}
    for e in applications])  # Liste af json objekter.
"""