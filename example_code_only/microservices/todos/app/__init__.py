# ------------------------------------------------------------------------------
# A REST API for managing a shared To-Do List in Flask
#
# This example demonstrates how to define endpoints of a simple to-do list API
# using Flask.
# ------------------------------------------------------------------------------

import os
from flask import Flask, jsonify, request
# from flask_login import current_user, login_required, LoginManager
from flask_sqlalchemy import SQLAlchemy

# ---------------------------------------------------------------------------
# Application setup
# ---------------------------------------------------------------------------

app = Flask(__name__)

# Configure the database connection for SQLAlchemy.
# If the environment variable DATABASE_URL is set, use it.
# Otherwise, fall back to a local SQLite file named todos.db.
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')

# Create a SQLAlchemy instance, which handles ORM mapping and DB operations.
db = SQLAlchemy(app)

# ---------------------------------------------------------------------------
# Data Model
# ---------------------------------------------------------------------------

class ToDo(db.Model):
    """
    Represents a single to-do item in the database.
    Each instance of this class corresponds to one row in the 'todos' table.
    """

    # Define the table columns (fields) and their types.
    id = db.Column(db.Integer, primary_key=True)               # Unique ID for each to-do.
    # title = db.Column(db.String(100), nullable=False)          # Short description (required).
    text = db.Column(db.String(200), nullable=True)         # Optional extra information.
    # completed = db.Column(db.Boolean, nullable=False, default=False)  # Status flag, defaults to False.
    user_id = db.Column(db.Integer, primary_key=False)     

    def to_dict(self):
        """
        Convert the ToDo object into a plain Python dictionary,
        making it easy to convert into JSON for HTTP responses.
        """
        dict = {
            "id": self.id,
            "text": self.text,
            # "completed": self.completed,
            "user_id": self.user_id
        }
        # if self.details:
            # dict["details"] = self.details
        return dict
    
    @staticmethod
    def get_entries_by_user_id(user_id):
        """
        Retrieves all relevant todos

        Args:
            id (int): The user's ID.

        Returns:
            User: The user object if found, otherwise None.
        """
        return ToDo.query.filter_by(user_id=user_id).all()

# Create all database tables if they don’t exist yet.
# app.app_context() ensures the operation runs with the correct Flask context.
with app.app_context():
    db.create_all()

# ---------------------------------------------------------------------------
# REST API Endpoints
# ---------------------------------------------------------------------------
# Each route below corresponds to one of the CRUD operations:
#   - Create (POST)
#   - Read (GET)
#   - Update (PUT)
#   - Delete (DELETE)
# The resource is a "to-do item", represented as JSON objects in requests/responses.
# ---------------------------------------------------------------------------


@app.route("/todos", methods=["GET"])
def get_entries():
    """
    Retrieve all to-do items from the database.

    Method: GET
    URL: /todos
    Response: 200 OK with a list of all to-dos in JSON format.
    """

    user_id = request.args.get("user_id", type=int)    
    user_todos = ToDo.get_entries_by_user_id(user_id)

    # Query all items, sorted by ID.
    # todos = ToDo.query.order_by(ToDo.id).all() 
    # Convert each item to a dictionary and serve the list as JSON
    return jsonify([todo.to_dict() for todo in user_todos]) 


@app.route("/todos", methods=["POST"])
def create_entry():
    """
    Create a new to-do item.

    Method: POST
    URL: /todos
    Body (JSON): {"title": "...", "details": "...", "completed": false}
    Response: 201 Created with the new item in JSON format.
    """
    
    data = request.get_json()  # Parse JSON from the request body.
    
    if not data or 'text' not in data:
        # Return an error if no JSON was provided or title is missing.
        return jsonify({'error': 'text is required'}), 400
    # Create a new ToDo object using data from the request.
    todo = ToDo(
        # title=data['title'],
        # completed=data.get('completed', False),
        text=data['text'],
        user_id=data['user_id']
    )
    
    # Add the new item to the database and commit the transaction.
    db.session.add(todo)
    db.session.commit()
    # Return the newly created object and HTTP 201 Created.
    return jsonify(todo.to_dict()), 201

@app.route("/todos/<int:user_id>/<int:id>", methods=["GET"])
def get_entry(user_id, id):
    """
    Retrieve a single to-do item by ID.

    Method: GET
    URL: /todos/<id>
    Response:
      200 OK with the item in JSON format, or
      404 Not Found if no such item exists.
    """
    
    # find frem til alle relevante entries baseret på id. 

    # users_todos = ToDo.get_entries_by_user_id(user_id)
    # todo = users_todos.filter_by(id=id).first()

    todo = ToDo.query.filter_by(user_id=user_id, id=id).first()


    # user = Todo.
    if not todo:
        return jsonify({'error': 'not found'}), 404
    return jsonify(todo.to_dict()), 200


@app.route("/todos/<int:id>", methods=["PUT"])
def update_entry(user_id, id):
    """
    Update an existing to-do item.

    Method: PUT
    URL: /todos/<id>
    Body (JSON): can include any combination of 'title', 'details', 'completed'.
    Response:
      200 OK with the updated item, or
      404 Not Found if no such item exists.
    """
    todo = ToDo.query.filter_by(user_id=user_id, id=id).first()

    if not todo:
        return jsonify({'error': 'not found'}), 404
    data = request.get_json() or {} # defaults to {} if there is no JSON payload
    # Update only the provided fields (partial update).
    # if 'title' in data:
    #     todo.title = data['title']
    # if 'completed' in data:
    #     todo.completed = data['completed']
    if 'text' in data:
        todo.text = data['text']
    db.session.commit()  # Save the changes to the database.
    return jsonify(todo.to_dict()), 200


@app.route("/todos/<int:user_id>/<int:id>", methods=["DELETE"])
def delete_entry(user_id, id):
    """
    Delete a to-do item by ID.

    Method: DELETE
    URL: /todos/<id>
    Response:
      204 No Content if successful, or
      404 Not Found if the item does not exist.
    """

    todo = ToDo.query.filter_by(user_id=user_id, id=id).first()

   
    if not todo:
        return jsonify({'error': 'not found'}), 404

    db.session.delete(todo)
    db.session.commit()

    # 204 means success, but no response body.
    return '', 204
