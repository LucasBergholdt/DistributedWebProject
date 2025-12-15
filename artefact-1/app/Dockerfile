# Use an official Python runtime as a parent image
FROM python:3.12-slim AS builder

# copy requirements and install them
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# copy application. Makes new "mini-image". 
COPY . /app 

# Flask config
ENV FLASK_APP=app
ENV FLASK_ENV=development

# Expose Flask port
EXPOSE 5000

CMD flask run --host=0.0.0.0

