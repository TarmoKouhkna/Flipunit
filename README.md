# FlipUnit.eu - Online Converter Hub

A comprehensive, fast, and user-friendly Django-based online converter website offering a wide range of conversion tools and utilities. No login required - just upload, convert, and download.

## 🎯 Project Purpose

FlipUnit.eu is a one-stop solution for all your conversion needs. Whether you need to convert units of measurement, transform image formats, extract audio from videos, or use everyday utilities, this platform provides a simple, fast, and secure way to get things done without requiring user registration.

## ✨ Features

### 📐 Unit Converters
- **Length Converter**: Convert between meters, kilometers, centimeters, millimeters, miles, feet, inches, and yards
- **Weight Converter**: Convert between kilograms, grams, pounds, ounces, tons, and stone
- **Temperature Converter**: Convert between Celsius, Fahrenheit, and Kelvin
- **Volume Converter**: Convert between liters, milliliters, gallons (US/UK), quarts (US/UK), pints (US/UK), cups, and fluid ounces (US/UK)
- **Area Converter**: Convert between various area units
- **Speed Converter**: Convert between different speed units

### 🖼️ Image Converters
- **JPEG to PNG**: Convert JPEG images to PNG format
- **PNG to JPG**: Convert PNG images to JPEG format
- **WebP Tools**: Convert to/from WebP format
- **SVG to PNG**: Convert SVG vector graphics to PNG raster images
- **Image Resize**: Resize images while maintaining aspect ratio

### 🎬 Media Converters
- **YouTube to MP3**: Extract audio from YouTube videos (with copyright usage notice)
- **MP4 to MP3**: Extract audio from MP4 video files
- **Audio Converter**: Convert between various audio formats
- **Video to GIF**: Convert video files to animated GIFs
- **Video Converter**: Convert between different video formats

### 🛠️ Utilities
- **PDF Tools**:
  - Merge multiple PDF files into one
  - Split PDF files into separate pages
  - Convert PDF pages to images
- **Calculator**: Simple online calculator with basic operations
- **Text Tools**: Word count, character count, and text analysis utilities
- **Color Converter**: Convert between HEX, RGB, HSL, and CMYK color formats
- **QR Code Generator**: Generate QR codes from text or URLs
- **Time Zone Converter**: Convert time between different time zones
- **Roman Numeral Converter**: Convert between Roman and Arabic numerals
- **Favicon Generator**: Generate favicon.ico files from any image

## 🛠️ Technology Stack

- **Backend Framework**: Django 5.2.8
- **Database**: PostgreSQL
- **Python Version**: 3.12.0
- **Image Processing**: Pillow 12.0.0
- **PDF Processing**: pypdf 6.3.0, pdf2image 1.17.0
- **SVG Processing**: CairoSVG 2.8.2
- **Video/Audio Processing**: FFmpeg (system dependency), yt-dlp 2025.11.12
- **QR Code Generation**: qrcode[pil] 8.0
- **Static Files**: WhiteNoise 6.8.2
- **Web Server**: Gunicorn 23.0.0
- **Frontend**: Responsive CSS with mobile-first design

## 📋 Prerequisites

Before you begin, ensure you have the following installed on your system:

### Required Software
- **Python 3.12.0** (or compatible version)
- **PostgreSQL** (version 12 or higher)
- **FFmpeg** (for media conversion features)
  - macOS: `brew install ffmpeg`
  - Ubuntu/Debian: `sudo apt-get install ffmpeg`
  - Windows: Download from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
- **Git** (for cloning the repository)

### Optional but Recommended
- **Poppler** (for PDF to image conversion)
  - macOS: `brew install poppler`
  - Ubuntu/Debian: `sudo apt-get install poppler-utils`
  - Windows: Download from [https://poppler.freedesktop.org/](https://poppler.freedesktop.org/)

## 🚀 Installation Guide

### Step 1: Clone the Repository

   ```bash
   git clone <repository-url>
   cd Flipunit
   ```

### Step 2: Create Virtual Environment

   ```bash
# Create virtual environment
   python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### Step 3: Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Set Up PostgreSQL Database

1. **Install PostgreSQL** (if not already installed)
   - macOS: `brew install postgresql`
   - Ubuntu/Debian: `sudo apt-get install postgresql postgresql-contrib`
   - Windows: Download from [https://www.postgresql.org/download/](https://www.postgresql.org/download/)

2. **Create Database and User**

   ```bash
   # Access PostgreSQL
   sudo -u postgres psql  # Linux
   # or
   psql postgres  # macOS/Windows (if configured)
   ```

   ```sql
   -- Create database
   CREATE DATABASE flipunit;

   -- Create user (optional, or use existing postgres user)
   CREATE USER flipunit_user WITH PASSWORD 'your_password_here';

   -- Grant privileges
   GRANT ALL PRIVILEGES ON DATABASE flipunit TO flipunit_user;

   -- Exit PostgreSQL
   \q
   ```

### Step 5: Configure Environment Variables

Create a `.env` file in the project root directory:

   ```env
# Django Settings
SECRET_KEY=your-secret-key-here-generate-a-long-random-string
   DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000

# Database Configuration
   DB_NAME=flipunit
DB_USER=flipunit_user
DB_PASSWORD=your_password_here
   DB_HOST=localhost
   DB_PORT=5432

# Site Configuration (optional)
SITE_URL=http://localhost:8000
```

**Important**: 
- Generate a secure `SECRET_KEY` using:
  ```python
  from django.core.management.utils import get_random_secret_key
  print(get_random_secret_key())
  ```
- For production, set `DEBUG=False` and use a strong `SECRET_KEY`

### Step 6: Run Database Migrations

   ```bash
   python manage.py migrate
   ```

This will create all necessary database tables.

### Step 7: Create Superuser (Optional)

Create an admin account to access Django admin panel:

   ```bash
   python manage.py createsuperuser
   ```

Follow the prompts to set up your admin credentials.

### Step 8: Collect Static Files

```bash
python manage.py collectstatic --noinput
```

This collects all static files (CSS, JavaScript, images) into the `staticfiles` directory.

### Step 9: Run Development Server

   ```bash
   python manage.py runserver
   ```

### Step 10: Access the Application

Open your web browser and navigate to:
- **Main site**: `http://127.0.0.1:8000/`
- **Admin panel**: `http://127.0.0.1:8000/admin/`

## 📁 Project Structure

```
Flipunit/
├── converters/              # Unit converters app (length, weight, temperature, etc.)
│   ├── migrations/         # Database migrations
│   ├── templates/          # HTML templates for converters
│   ├── urls.py            # URL routing for converters
│   └── views.py           # View functions for converters
│
├── image_converter/        # Image conversion app
│   ├── migrations/
│   ├── templates/
│   ├── urls.py
│   └── views.py
│
├── media_converter/        # Media conversion app (video, audio)
│   ├── migrations/
│   ├── templates/
│   ├── urls.py
│   └── views.py
│
├── utilities/              # Utilities app (PDF, calculator, text tools, etc.)
│   ├── migrations/
│   ├── templates/
│   ├── urls.py
│   └── views.py
│
├── flipunit/               # Main Django project settings
│   ├── settings.py        # Django settings and configuration
│   ├── urls.py            # Main URL configuration
│   ├── wsgi.py            # WSGI configuration for production
│   ├── asgi.py            # ASGI configuration
│   ├── context_processors.py  # Template context processors
│   └── sitemaps.py        # Sitemap configuration for SEO
│
├── templates/              # Global HTML templates
│   ├── base.html          # Base template
│   ├── home.html          # Homepage
│   ├── converters/        # Converter-specific templates
│   ├── image_converter/   # Image converter templates
│   ├── media_converter/   # Media converter templates
│   └── utilities/         # Utility tool templates
│
├── static/                 # Static files (CSS, JavaScript, images)
│   ├── css/
│   ├── js/
│   └── images/
│
├── staticfiles/            # Collected static files (generated)
│
├── media/                  # User-uploaded files (created automatically)
│
├── manage.py              # Django management script
├── requirements.txt       # Python dependencies
├── runtime.txt           # Python version specification
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose configuration
├── Procfile             # Heroku/Procfile configuration
└── README.md            # This file
```

## 🔧 Configuration Details

### Environment Variables

The application uses environment variables for configuration. All variables have defaults in `settings.py`, but you should set them explicitly for production:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SECRET_KEY` | Django secret key for cryptographic signing | Random key (dev only) | Yes (production) |
| `DEBUG` | Enable debug mode | `False` | No |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hostnames | `flipunit.eu,www.flipunit.eu` | Yes (production) |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated list of trusted origins for CSRF | Default origins | Yes (production) |
| `DB_NAME` | PostgreSQL database name | `flipunit` | No |
| `DB_USER` | PostgreSQL username | `postgres` | No |
| `DB_PASSWORD` | PostgreSQL password | `postgres` | No |
| `DB_HOST` | PostgreSQL host | `localhost` | No |
| `DB_PORT` | PostgreSQL port | `5432` | No |
| `SITE_URL` | Full URL of the site | `https://flipunit.eu` | No |

### File Upload Settings

- Maximum file size: 700MB (configurable in `settings.py`)
- Supported formats vary by tool (see individual tool pages)

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

1. **Build and run containers**:
   ```bash
   docker-compose up -d
   ```

2. **Run migrations**:
   ```bash
   docker-compose exec web python manage.py migrate
   ```

3. **Create superuser**:
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

4. **Collect static files**:
   ```bash
   docker-compose exec web python manage.py collectstatic --noinput
   ```

5. **Access the application**: `http://localhost:8000`

### Using Dockerfile Directly

1. **Build the image**:
   ```bash
   docker build -t flipunit .
   ```

2. **Run the container**:
   ```bash
   docker run -d \
     -p 8000:8000 \
     -e SECRET_KEY=your-secret-key \
     -e DEBUG=False \
     -e DB_NAME=flipunit \
     -e DB_USER=postgres \
     -e DB_PASSWORD=your-password \
     -e DB_HOST=host.docker.internal \
     flipunit
   ```

## 🚢 Production Deployment

### Pre-Deployment Checklist

1. ✅ Set `DEBUG=False` in environment variables
2. ✅ Set a secure `SECRET_KEY` (never commit to version control)
3. ✅ Configure `ALLOWED_HOSTS` with your domain
4. ✅ Set `CSRF_TRUSTED_ORIGINS` with your HTTPS URLs
5. ✅ Configure PostgreSQL database connection
6. ✅ Set up SSL/HTTPS certificate
7. ✅ Configure static file serving (WhiteNoise is included)
8. ✅ Set up media file storage (consider cloud storage for large files)
9. ✅ Configure reverse proxy (Nginx recommended)
10. ✅ Set up proper logging
11. ✅ Configure backup strategy for database

### Deployment Steps

1. **Set environment variables** on your production server
2. **Run migrations**: `python manage.py migrate`
3. **Collect static files**: `python manage.py collectstatic --noinput`
4. **Start Gunicorn**:
   ```bash
   gunicorn flipunit.wsgi:application --bind 0.0.0.0:8000 --workers 3
   ```

### Nginx Configuration Example

```nginx
server {
    listen 80;
    server_name flipunit.eu www.flipunit.eu;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name flipunit.eu www.flipunit.eu;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/Flipunit/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /path/to/Flipunit/media/;
        expires 7d;
    }
}
```

**Important**: After configuring Nginx with SSL, update `settings.py`:
- Set `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')`
- Set `SECURE_SSL_REDIRECT = True`
- Set `SESSION_COOKIE_SECURE = True`
- Set `CSRF_COOKIE_SECURE = True`

### Heroku Deployment

1. **Install Heroku CLI** and login
2. **Create Heroku app**:
   ```bash
   heroku create your-app-name
   ```
3. **Set environment variables**:
   ```bash
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set DEBUG=False
   heroku config:set ALLOWED_HOSTS=your-app-name.herokuapp.com
   ```
4. **Add PostgreSQL addon**:
   ```bash
   heroku addons:create heroku-postgresql:hobby-dev
   ```
5. **Deploy**:
   ```bash
   git push heroku main
   ```
6. **Run migrations**:
   ```bash
   heroku run python manage.py migrate
   ```

## 📦 Dependencies

### Core Dependencies

- **Django 5.2.8**: Web framework
- **psycopg2-binary 2.9.11**: PostgreSQL database adapter
- **Pillow 12.0.0**: Image processing
- **pypdf 6.3.0**: PDF manipulation
- **pdf2image 1.17.0**: PDF to image conversion
- **CairoSVG 2.8.2**: SVG to PNG conversion
- **yt-dlp 2025.11.12**: YouTube video downloading
- **qrcode[pil] 8.0**: QR code generation
- **whitenoise 6.8.2**: Static file serving
- **gunicorn 23.0.0**: Production WSGI server

### System Dependencies

- **FFmpeg**: Required for video/audio conversion
- **Poppler**: Required for PDF to image conversion (optional but recommended)

## 🔍 SEO Features

- Meta tags for search engines
- Open Graph tags for social media sharing
- Twitter Card support
- Canonical URLs
- XML Sitemap (`/sitemap.xml`)
- Robots.txt configuration
- Mobile-responsive design
- Fast loading times

## 📱 Mobile Optimization

- Responsive design with mobile-first approach
- Touch-friendly interface
- Optimized for all screen sizes
- Mobile menu navigation
- Fast performance on mobile devices

## 🧪 Testing

Run Django tests:

```bash
python manage.py test
```

Test individual apps:

```bash
python manage.py test converters
python manage.py test image_converter
python manage.py test media_converter
python manage.py test utilities
```

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Verify PostgreSQL is running: `sudo systemctl status postgresql` (Linux)
   - Check database credentials in `.env` file
   - Ensure database exists: `psql -l`

2. **FFmpeg Not Found**
   - Verify installation: `ffmpeg -version`
   - Ensure FFmpeg is in system PATH
   - For Docker, FFmpeg is included in the image

3. **Static Files Not Loading**
   - Run `python manage.py collectstatic`
   - Check `STATIC_ROOT` and `STATICFILES_DIRS` in settings
   - Verify WhiteNoise middleware is enabled

4. **Media Files Not Saving**
   - Ensure `media/` directory exists and is writable
   - Check `MEDIA_ROOT` and `MEDIA_URL` in settings
   - Verify file permissions: `chmod 755 media/`

5. **CSRF Token Errors**
   - Add your domain to `CSRF_TRUSTED_ORIGINS`
   - Ensure HTTPS is properly configured in production
   - Check that cookies are enabled in browser

6. **Import Errors**
   - Activate virtual environment: `source venv/bin/activate`
   - Reinstall dependencies: `pip install -r requirements.txt`
   - Check Python version: `python --version` (should be 3.12+)

## 📝 Development Guidelines

### Code Style
- Follow PEP 8 Python style guide
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Comment complex logic

### Adding New Features
1. Create feature branch: `git checkout -b feature/new-feature`
2. Implement changes
3. Test thoroughly
4. Update documentation
5. Submit pull request

### Database Migrations
- Always create migrations for model changes: `python manage.py makemigrations`
- Review migration files before applying
- Test migrations on development database first

## 📄 License

This project is open source and available for use.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 Support

For issues, questions, or feature requests:
- Open an issue in the repository
- Check existing documentation
- Review troubleshooting section above

## 🔗 Useful Links

- [Django Documentation](https://docs.djangoproject.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- [Pillow Documentation](https://pillow.readthedocs.io/)

---

**Built with ❤️ using Django**
