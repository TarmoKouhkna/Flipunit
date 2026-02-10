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

# Copy and use optimized entrypoint (skips collectstatic on restart to prevent 504)
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 8000

CMD ["/app/entrypoint.sh"]








