FROM python:3.11-slim

WORKDIR /service

# Copy everything in auth folder
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Flask environment variables
ENV FLASK_APP=app:app
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

EXPOSE 5000

# Run Flask
CMD ["flask", "run"]