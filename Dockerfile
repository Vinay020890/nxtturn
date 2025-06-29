# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies, including libavif-dev
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libavif-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY ./Loopline/requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the Django project code into the container
COPY ./Loopline /app/

# Set the start command for the container
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:10000"]