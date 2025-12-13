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

    price = db.Column(db.Integer())

    roomsize = db.Column(db.Integer())

    image = db.Column(db.String(500))

    @staticmethod
    def get_all():
        """Get all Collectives"""
        return Collective.query.order_by(Collective.id).all()

    @staticmethod
    def get_by_submitter(user_id):
        """Get all Collectives submitted by a specific user"""
        return Collective.query.filter_by(submitter_id=user_id).all()
    
    @classmethod
    def create_collective(cls, submitter_id, city, street, price, roomsize, image):
      """
      Create a new collective with the provided details.

      Args:
          name (str): The collective's name.
          email (str): The collective's email.
          password (str): The collective's password, which will be hashed before storage.

      Returns:
          collective: The newly created collective object.
      """
      
      collective = cls(
          submitter_id = submitter_id,
          city = city.strip(),
          street = street.strip(),
          price = price,
          roomsize = roomsize,
          image = image.strip()
      )

      db.session.add(collective)
      db.session.commit()
      return collective

with app.app_context():
  db.create_all()


# ------------------------------------------ ROUTES ----------------------------------------------------------------------
# Fetches all collectives. TODO: Support a parameter to fetch only list of collectives.
    # - List of Seeker's Collectives (that he applied for)
    # - List of Provider's Collectives

@app.route("/collectives", methods=["GET"])
def get_collectives():
    submitter_id = request.args.get("submitter_id", type=int)
    if submitter_id is not None:
        collectives = Collective.get_by_submitter(submitter_id)
    else:
        collectives = Collective.get_all()
        return jsonify([{
        "id": e.id, 
        "submitter_id": e.submitter_id, 
        "city": e.city,
        "street": e.street,
        "price": e.price,
        "roomsize": e.roomsize,
        "image": e.image}
        for e in collectives])  # returns list of json objects

@app.route("/collectives", methods=["POST"])
def post_collectives():
    data = request.get_json()   #fetch json objekt med info

    submitter_id = data.get('submitter_id')
    city = data.get('city')
    street = data.get('street')
    price = data.get('price')
    roomsize = data.get('roomsize')
    image = data.get('image')

    if not submitter_id or not price or not city or not street or not roomsize or not image:
        return jsonify({"error": "Missing data"}), 400

    collective = Collective.create_collective(
        submitter_id,
        city,
        street,
        price,
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