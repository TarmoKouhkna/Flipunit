FROM python:3.12-slim

# Install system dependencies including FFmpeg, pandoc, poppler, tesseract, and yt-dlp
RUN apt-get update && apt-get install -y \
    ffmpeg \
    postgresql-client \
    pandoc \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-eng \
    curl \
    wget \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install unrar from source (non-free package not in default repos)
# Download and build unrar from RARLab source
RUN wget -q https://www.rarlab.com/rar/unrarsrc-6.2.12.tar.gz -O /tmp/unrar.tar.gz && \
    cd /tmp && \
    tar -xzf unrar.tar.gz && \
    cd unrar && \
    make -j$(nproc) && \
    cp unrar /usr/local/bin/ && \
    chmod +x /usr/local/bin/unrar && \
    rm -rf /tmp/unrar* /tmp/unrar.tar.gz

# Install yt-dlp
RUN curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp \
    && chmod a+rx /usr/local/bin/yt-dlp

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Explicitly ensure __init__.py is copied (fix for Docker build issue)
COPY flipunit/__init__.py /app/flipunit/__init__.py
# Explicitly ensure urls.py is copied (fix for Docker build issue)
COPY flipunit/urls.py /app/flipunit/urls.py

# Create directories for media and static files
RUN mkdir -p /app/media /app/staticfiles

# Expose port
EXPOSE 8000

# Create entrypoint script for better error handling
# Calculate workers: (2 * CPU cores) + 1, default to 9 for 8-core system
RUN echo '#!/bin/bash\n\
set -e\n\
python manage.py migrate\n\
python manage.py collectstatic --noinput\n\
# Calculate workers based on CPU cores (default to 9 for 8-core)\n\
CPU_COUNT=$(nproc 2>/dev/null || echo 8)\n\
WORKERS=$((2 * CPU_COUNT + 1))\n\
# Cap at reasonable maximum\n\
if [ $WORKERS -gt 17 ]; then\n\
    WORKERS=17\n\
fi\n\
# Start with 9 workers for 8-core system, adjust as needed\n\
WORKERS=9\n\
exec gunicorn flipunit.wsgi:application --bind 0.0.0.0:8000 --workers $WORKERS --threads 2 --timeout 600 --max-requests 1000 --max-requests-jitter 100 --access-logfile - --error-logfile -\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Use entrypoint script
CMD ["/app/entrypoint.sh"]








