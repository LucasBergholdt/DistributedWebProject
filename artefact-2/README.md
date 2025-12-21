# Build instructions:
1. Navigate to the artefact-2 directory
2. Run: `docker-compose up --build`

This will start all the required services including the database.
One all services are running, the frontend will be accessible at localhost:5000


# Directory structure
The artefact-2 directory is organized with a folder for each distict microservice.
Each microservice folder follows the structure:
📂<service-name>
 ┣ 📂app
 ┃ ┗ 📜__init__.py
 ┣ 📜Dockerfile
 ┗ 📜requirements.txt

The frontend service additionally includes directories templates and static for rendering user interface.
The templates folder is once again divided further into subfolders for better organization.


# Default data  
The system is populated with 3 default collectives and 2 default users:
Seeker user:
- email = seeker@gmail.com
- password = 123

Provider user:
- email = provider@gmail.com
- password = 123

All three default collectives are owned by the provider user.