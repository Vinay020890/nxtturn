# Final Dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev libavif-dev && rm -rf /var/lib/apt/lists/*
COPY ./Loopline/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./Loopline .
RUN python manage.py collectstatic --noinput
# This CMD just starts the server. Migrations are handled by Render.
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:10000"]