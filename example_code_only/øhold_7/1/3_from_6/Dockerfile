# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Install PostgreSQL and dependencies
RUN apt-get update && \
    apt-get install -y postgresql-17 && \
    rm -rf /var/lib/apt/lists/*

# copy requirements and install them
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# copy application. Laver ny "mini-image". HOLD ØJE MED CACHES, DET ER MEGET INTERESSANT
COPY app app 

# PostgreSQL configuration
ENV POSTGRES_USER=flaskuser
ENV POSTGRES_PASSWORD=flaskpass
ENV POSTGRES_DB=flaskdb

# Flask config
ENV FLASK_APP=app
ENV FLASK_ENV=development
ENV DATABASE_URL=postgresql://flaskuser:flaskpass@localhost:5432/flaskdb

# Expose Flask port
EXPOSE 5000

# Start PostgreSQL and Flask
# This uses bash to start PostgreSQL in the background, wait for it to start,
# create the database if necessary, and then start Flask.
CMD service postgresql start && \
    su - postgres -c "psql -c \"CREATE USER ${POSTGRES_USER} WITH PASSWORD '${POSTGRES_PASSWORD}'\" || true" && \
    su - postgres -c "psql -c \"CREATE DATABASE ${POSTGRES_DB} OWNER ${POSTGRES_USER}\" || true" && \
    flask run --host=0.0.0.0
