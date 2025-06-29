# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libavif-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file from the current directory (which is Loopline)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project code from the current directory
COPY . .

# Run collectstatic
RUN python manage.py collectstatic --noinput

# The CMD instruction will now run migrations first, then start the server.
CMD python manage.py migrate && gunicorn config.wsgi:application --bind 0.0.0.0:10000