Build instructions:
1. Navigate to the artefact-1 directory
2. Build the image: `docker build -t mono-app .`
3. Run the container: `docker run -p 5000:5000 mono-app`

Once running the application will be acessible at localhost:5000

The application is monolithic but is split into smaller seperate
files for comprehensibility. This is facilitated by the use of 
Flask Blueprints and an application factory in __init__.py

The templates folder is also divided further into subfolders
for better organization.