# # Use an official Python runtime as a parent image
# FROM python:slim

# # copy requirements and install them
# COPY requirements.txt requirements.txt
# RUN pip install --no-cache-dir -r requirements.txt

# # copy application
# COPY . app

# # Flask config
# ENV FLASK_APP=app
# ENV FLASK_ENV=development

# # expose Flask’s port
# EXPOSE 5000

# # run Flask App
# ENTRYPOINT ["flask", "run", "--host", "0.0.0.0"]

FROM python:3.11-slim

WORKDIR /app

# Copy everything in auth folder
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Flask environment variables
ENV FLASK_APP=app:app
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# Run Flask
CMD ["flask", "run"]