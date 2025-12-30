# FlipUnit.eu - Online Converter Hub

A comprehensive, fast, and user-friendly Django-based online converter website offering a wide range of conversion tools and utilities. No login required - just upload, convert, and download.

## 🎯 Project Purpose

FlipUnit.eu is a one-stop solution for all your conversion needs. Whether you need to convert units of measurement, transform image formats, extract audio from videos, or use everyday utilities, this platform provides a simple, fast, and secure way to get things done without requiring user registration.

## ✨ Features

### 📐 Unit Converters (16 Converters)
- **Length**: Convert between meters, kilometers, centimeters, millimeters, miles, feet, inches, and yards
- **Weight**: Convert between kilograms, grams, pounds, ounces, tons, and stone
- **Temperature**: Convert between Celsius, Fahrenheit, and Kelvin
- **Volume**: Convert between liters, milliliters, gallons (US/UK), quarts (US/UK), pints (US/UK), cups, and fluid ounces (US/UK)
- **Area**: Convert between square meters, square feet, acres, hectares, and more
- **Speed**: Convert between m/s, km/h, mph, ft/s, and knots
- **Time**: Convert between seconds, milliseconds, minutes, hours, days, weeks, months, and years
- **Data Storage**: Convert between bytes, KB, MB, GB, TB, PB, and binary units (KiB, MiB, GiB, TiB)
- **Energy**: Convert between joules, kilojoules, calories, kilocalories, watt-hours, kilowatt-hours, electronvolts, BTU, and foot-pounds
- **Power**: Convert between watts, kilowatts, megawatts, horsepower (mechanical & metric), BTU/hour, and foot-pounds/second
- **Pressure**: Convert between pascal, kilopascal, bar, atmosphere, PSI, torr, mmHg, and inHg
- **Force**: Convert between newtons, kilonewtons, pound-force, kilogram-force, dynes, and ounce-force
- **Angle**: Convert between degrees, radians, gradians, turns, arcminutes, and arcseconds
- **Fuel Consumption**: Convert between MPG, L/100km, km/L, and more
- **Frequency**: Convert between Hertz, kilohertz, megahertz, RPM, and more
- **Data Transfer Rate**: Convert between Mbps, MB/s, Gbps, and more

### 🖼️ Image Converters
- **Universal Image Converter**: Convert between JPEG, PNG, WebP, BMP, TIFF, GIF, and HEIC formats
- **Image Resize**: Resize images while maintaining aspect ratio
- **Rotate & Flip**: Rotate images by any angle and flip horizontally/vertically
- **Remove EXIF**: Remove metadata from images for privacy
- **Grayscale Conversion**: Convert images to grayscale
- **Image Merge**: Combine multiple images into one
- **Watermark**: Add text or image watermarks to images
- **SVG to PNG**: Convert SVG vector graphics to PNG raster images

### 🎬 Media Converters
- **MP4 to MP3**: Extract audio from MP4 video files
- **Audio Converter**: Convert between MP3, WAV, OGG, FLAC, AAC, AIFF, and M4A formats
- **Audio Splitter**: Split audio files into segments by time
- **Audio Merge**: Merge multiple audio files into one
- **Reduce Audio Noise**: Reduce background noise from audio files
- **Video to GIF**: Convert video files to animated GIFs
- **Video Converter**: Convert between MP4, AVI, MOV, MKV, WebM, and 3GP formats
- **Video Compressor**: Compress video files to reduce file size
- **Mute Video**: Remove audio track from video files
- **Video Merge**: Combine multiple video files into one
- **Video Preview**: Generate preview thumbnails from videos

### 📄 PDF Tools
- **Universal PDF Converter**: Convert PDFs to various formats (images, HTML, text, EPUB, etc.)
- **PDF Merge**: Merge multiple PDF files into one
- **PDF Split**: Split PDF files into separate pages
- **PDF to Images**: Convert PDF pages to images (PNG, JPEG)
- **PDF to HTML**: Convert PDF files to HTML format
- **HTML to PDF**: Convert HTML files to PDF
- **PDF to Text**: Extract text content from PDF files
- **PDF Compress**: Compress PDF files to reduce file size
- **PDF Rotate**: Rotate PDF pages
- **PDF OCR**: Extract text from scanned PDFs using OCR
- **Remove PDF Metadata**: Remove metadata from PDF files
- **PDF to Flipbook**: Convert PDFs to interactive flipbook format
- **PDF to EPUB**: Convert PDF files to EPUB e-book format

### 💱 Currency & Crypto Converter
- **Currency Converter**: Convert between 100+ currencies with real-time exchange rates
- **Cryptocurrency Converter**: Convert between Bitcoin, Ethereum, and other cryptocurrencies

### 🎨 Color Picker & Converter
- **Color Picker**: Pick colors from screen using eyedropper tool
- **Color from Image**: Extract color palette from uploaded images
- **Color Format Converter**: Convert between HEX, RGB, HSL, CMYK, and HSV formats

### 📦 Archive Converters
- **RAR to ZIP**: Convert RAR archives to ZIP format
- **ZIP to 7Z**: Convert ZIP archives to 7Z format
- **7Z to ZIP**: Convert 7Z archives to ZIP format
- **TAR.GZ to ZIP**: Convert TAR.GZ archives to ZIP format
- **ZIP to TAR.GZ**: Convert ZIP archives to TAR.GZ format
- **Extract ISO**: Extract files from ISO disk images
- **Create ZIP**: Create ZIP archives from multiple files

### 📝 Text & String Converters
- **Uppercase/Lowercase**: Convert text case
- **CamelCase/Snake_case**: Convert between naming conventions
- **Remove Special Characters**: Clean text by removing special characters
- **Remove Duplicate Lines**: Remove duplicate lines from text
- **Sort Lines**: Sort lines alphabetically or numerically
- **JSON ↔ XML**: Convert between JSON and XML formats
- **JSON ↔ YAML**: Convert between JSON and YAML formats
- **HTML ↔ Markdown**: Convert between HTML and Markdown
- **Text ↔ Base64**: Encode/decode text to/from Base64
- **Word Counter**: Count words, characters, sentences, and paragraphs
- **Text to Speech**: Convert text to speech audio files

### 💻 Developer Converters
- **Code Minify**: Minify HTML, CSS, and JavaScript code
- **Code Unminify**: Beautify and format minified code
- **CSV ↔ JSON**: Convert between CSV and JSON formats
- **SQL Formatter**: Format and beautify SQL queries
- **CSS ↔ SCSS**: Convert between CSS and SCSS
- **Regex Tester**: Test and validate regular expressions
- **JWT Decoder**: Decode and inspect JWT tokens
- **URL Encoder/Decoder**: Encode and decode URLs
- **Hash Generator**: Generate MD5, SHA1, SHA256, SHA512 hashes

### 🛠️ Utilities
- **Calculator**: Simple online calculator with basic operations
- **QR Code Generator**: Generate QR codes from text or URLs
- **Timezone Converter**: Convert time between different time zones
- **Roman Numeral Converter**: Convert between Roman and Arabic numerals
- **Favicon Generator**: Generate favicon.ico files from any image
- **Timestamp Converter**: Convert Unix timestamps to readable dates and vice versa
- **Random Number Generator**: Generate random numbers within a range
- **Lorem Ipsum Generator**: Generate placeholder text
- **Random Word Generator**: Generate random words
- **Random Name Generator**: Generate random names
- **Word Lottery**: Random word picker tool

### 🤖 AI Chat
- **AI Chat Assistant**: Chat with AI using Google Gemini API for help with conversions and general questions

### 🔍 Other Tools
- **YouTube Thumbnail Downloader**: Download thumbnails from YouTube videos
- **Is Down Checker**: Check if websites are down or accessible

## 🛠️ Technology Stack

- **Backend Framework**: Django 5.2.8
- **Database**: PostgreSQL
- **Python Version**: 3.12.0
- **Image Processing**: Pillow 12.0.0, pillow-heif 0.13.0
- **PDF Processing**: pypdf 6.3.0, pdf2image 1.17.0, pdfplumber 0.11.4, pymupdf 1.23.0+, weasyprint 62.3
- **SVG Processing**: CairoSVG 2.8.2
- **Video/Audio Processing**: FFmpeg (system dependency)
- **Archive Processing**: py7zr 0.21.0+, rarfile 4.1+, pycdlib 1.13.0+
- **Text Processing**: markdown 3.5.0+, html2text 2024.2.26+, pyyaml 6.0+
- **Code Minification**: htmlmin 0.1.12+, rcssmin 1.1.1+, rjsmin 1.2.2+, jsbeautifier 1.15.1+
- **QR Code Generation**: qrcode[pil] 8.0
- **Text-to-Speech**: gtts 2.5.0+
- **Static Files**: WhiteNoise 6.8.2
- **Web Server**: Gunicorn 23.0.0
- **AI Integration**: Google Gemini API (for AI chat feature)
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
- **Pandoc** (for PDF ↔ RTF conversion)
  - macOS: `brew install pandoc`
  - Ubuntu/Debian: `sudo apt-get install pandoc`
  - Windows: Download from [https://pandoc.org/installing.html](https://pandoc.org/installing.html)
- **Tesseract OCR** (for OCR PDF conversion)
  - macOS: `brew install tesseract`
  - Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
  - Windows: Download from [https://github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki)
- **unrar** (for RAR archive writing)
  - macOS: `brew install unrar`
  - Ubuntu/Debian: `sudo apt-get install unrar`

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

# AI Chat (optional - for AI chat feature)
GOOGLE_GEMINI_API_KEY=your-google-gemini-api-key-here
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
├── converters/              # Unit converters app (16 different converters)
│   ├── migrations/
│   ├── templates/
│   ├── urls.py
│   └── views.py
│
├── image_converter/        # Image conversion and editing app
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
├── pdf_tools/              # PDF tools app (merge, split, convert, etc.)
│   ├── migrations/
│   ├── templates/
│   ├── urls.py
│   └── views.py
│
├── currency_converter/     # Currency and cryptocurrency converter
│   ├── migrations/
│   ├── templates/
│   ├── urls.py
│   └── views.py
│
├── color_picker/           # Color picker and converter app
│   ├── migrations/
│   ├── templates/
│   ├── urls.py
│   └── views.py
│
├── archive_converter/      # Archive format converter (ZIP, RAR, 7Z, etc.)
│   ├── migrations/
│   ├── templates/
│   ├── urls.py
│   └── views.py
│
├── text_converter/         # Text and string conversion tools
│   ├── migrations/
│   ├── templates/
│   ├── urls.py
│   └── views.py
│
├── developer_converter/     # Developer tools (minify, format, etc.)
│   ├── migrations/
│   ├── templates/
│   ├── urls.py
│   └── views.py
│
├── utilities/              # General utilities (calculator, QR codes, etc.)
│   ├── migrations/
│   ├── templates/
│   ├── urls.py
│   └── views.py
│
├── ai_chat/                # AI chat assistant using Google Gemini
│   ├── migrations/
│   ├── templates/
│   ├── urls.py
│   └── views.py
│
├── youtube_thumbnail/      # YouTube thumbnail downloader
│   ├── migrations/
│   ├── templates/
│   ├── urls.py
│   └── views.py
│
├── isdown/                 # Website status checker
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
│   ├── sitemaps.py        # Sitemap configuration for SEO
│   └── management/        # Custom management commands
│
├── templates/              # Global HTML templates
│   ├── base.html          # Base template
│   ├── home.html          # Homepage
│   ├── converters/        # Converter-specific templates
│   ├── image_converter/   # Image converter templates
│   ├── media_converter/   # Media converter templates
│   ├── pdf_tools/         # PDF tool templates
│   ├── text_converter/    # Text converter templates
│   ├── developer_converter/ # Developer tool templates
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
| `GOOGLE_GEMINI_API_KEY` | Google Gemini API key for AI chat feature | None | No (optional) |

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
- **Pillow 12.0.0**: Image processing and format conversion
- **pypdf 6.3.0**: PDF manipulation
- **pdf2image 1.17.0**: PDF to image conversion
- **CairoSVG 2.8.2**: SVG to PNG conversion
- **qrcode[pil] 8.0**: QR code generation
- **whitenoise 6.8.2**: Static file serving
- **gunicorn 23.0.0**: Production WSGI server
- **python-dotenv 1.0.0**: Environment variable management
- **requests 2.32.5**: HTTP library for API calls

### PDF Processing

- **pypdf 6.3.0**: PDF manipulation and merging
- **pdf2image 1.17.0**: PDF to image conversion
- **pdfplumber 0.11.4**: PDF text extraction
- **pymupdf 1.23.0+**: PDF to SVG conversion
- **pypandoc 1.11+**: PDF ↔ RTF conversion
- **pytesseract 0.3.10+**: OCR for PDF text extraction
- **ebooklib 0.18+**: PDF to EPUB conversion
- **weasyprint 62.3**: HTML to PDF conversion
- **python-docx 1.1.2**: Word document processing
- **docx2pdf 0.1.8**: Word to PDF conversion

### Archive Processing

- **py7zr 0.21.0+**: 7Z archive support
- **rarfile 4.1+**: RAR archive reading
- **pycdlib 1.13.0+**: ISO file extraction

### Text & Format Conversion

- **pyyaml 6.0+**: JSON ↔ YAML conversion
- **markdown 3.5.0+**: HTML ↔ Markdown conversion
- **html2text 2024.2.26+**: HTML to Markdown conversion
- **htmlmin 0.1.12+**: HTML minification
- **rcssmin 1.1.1+**: CSS minification
- **rjsmin 1.2.2+**: JavaScript minification
- **jsbeautifier 1.15.1+**: JavaScript unminification
- **PyJWT 2.8.0+**: JWT token decoding

### Media Processing

- **gtts 2.5.0+**: Text-to-speech conversion
- **pillow-heif 0.13.0**: HEIC image format support

### System Dependencies

- **FFmpeg**: Required for video/audio conversion
  - macOS: `brew install ffmpeg`
  - Ubuntu/Debian: `sudo apt-get install ffmpeg`
  - Windows: Download from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
- **Poppler**: Required for PDF to image conversion (optional but recommended)
  - macOS: `brew install poppler`
  - Ubuntu/Debian: `sudo apt-get install poppler-utils`
  - Windows: Download from [https://poppler.freedesktop.org/](https://poppler.freedesktop.org/)
- **Pandoc**: Required for PDF ↔ RTF conversion (optional)
  - macOS: `brew install pandoc`
  - Ubuntu/Debian: `sudo apt-get install pandoc`
  - Windows: Download from [https://pandoc.org/installing.html](https://pandoc.org/installing.html)
- **Tesseract OCR**: Required for OCR PDF conversion (optional)
  - macOS: `brew install tesseract`
  - Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
  - Windows: Download from [https://github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki)
- **unrar**: Required for RAR archive writing (optional)
  - macOS: `brew install unrar`
  - Ubuntu/Debian: `sudo apt-get install unrar`

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
python manage.py test pdf_tools
python manage.py test currency_converter
python manage.py test color_picker
python manage.py test archive_converter
python manage.py test text_converter
python manage.py test developer_converter
python manage.py test utilities
python manage.py test ai_chat
python manage.py test youtube_thumbnail
python manage.py test isdown
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
