FROM python:3.12-slim

# Install system dependencies including FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create directories for media and static files
RUN mkdir -p /app/media /app/staticfiles

# Expose port
EXPOSE 8000

# Create entrypoint script for better error handling
RUN echo '#!/bin/bash\n\
set -e\n\
python manage.py migrate\n\
python manage.py collectstatic --noinput\n\
exec gunicorn flipunit.wsgi:application --bind 0.0.0.0:8000 --workers 3\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Use entrypoint script
CMD ["/app/entrypoint.sh"]








