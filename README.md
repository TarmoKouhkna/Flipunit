# FlipUnit.eu - Online Converter Hub

A simple, fast, no-login required Django-based online converter website offering unit converters, image converters, media converters, and everyday utilities.

## Features

- **Unit Converters**: Length, Weight, Temperature, Volume, Area, Speed
- **Image Converters**: JPEG→PNG, PNG→JPG, WebP tools, SVG→PNG
- **Media Converters**: YouTube→MP3 (with usage notice)
- **Utilities**: PDF tools, calculators, text utilities

## Technology Stack

- Django 5.2.8
- PostgreSQL
- Pillow (for image processing)
- Responsive CSS with mobile-first design

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Flipunit
   ```

2. **Create and activate virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up PostgreSQL database**
   - Create a PostgreSQL database named `flipunit` (or your preferred name)
   - Update database settings in `flipunit/settings.py` or use environment variables

5. **Configure environment variables** (optional)
   Create a `.env` file in the project root:
   ```env
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   DB_NAME=flipunit
   DB_USER=postgres
   DB_PASSWORD=postgres
   DB_HOST=localhost
   DB_PORT=5432
   ALLOWED_HOSTS=localhost,127.0.0.1
   ```

6. **Run migrations**
   ```bash
   python manage.py migrate
   ```

7. **Create superuser** (optional, for admin access)
   ```bash
   python manage.py createsuperuser
   ```

8. **Run development server**
   ```bash
   python manage.py runserver
   ```

9. **Access the application**
   - Open your browser and navigate to `http://127.0.0.1:8000/`

## Project Structure

```
Flipunit/
├── converters/          # Unit converters app
├── image_converter/     # Image conversion app
├── media_converter/     # Media conversion app
├── utilities/           # Utilities app (PDF, calculator, text tools)
├── flipunit/            # Main project settings
├── templates/           # HTML templates
├── static/              # CSS, JavaScript, images
└── media/               # User-uploaded files (created automatically)
```

## Environment Variables

The following environment variables can be set (with defaults in settings.py):

- `SECRET_KEY`: Django secret key
- `DEBUG`: Debug mode (True/False)
- `DB_NAME`: PostgreSQL database name
- `DB_USER`: PostgreSQL username
- `DB_PASSWORD`: PostgreSQL password
- `DB_HOST`: PostgreSQL host
- `DB_PORT`: PostgreSQL port
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts

## Features in Detail

### Unit Converters
- Convert between various units of measurement
- Supports: Length, Weight, Temperature, Volume, Area, Speed
- Real-time conversion with instant results

### Image Converters
- Convert between image formats (JPEG, PNG, WebP)
- Drag-and-drop file upload
- High-quality conversion with Pillow

### Media Converters
- YouTube to MP3 conversion (requires additional setup)
- Usage notice for copyright compliance
- Note: Full functionality requires `yt-dlp` library

### Utilities
- Online calculator
- Text tools (word count, character count)
- PDF tools (placeholder - requires additional libraries)

## SEO Optimization

- Meta tags for search engines
- Open Graph tags for social media
- Twitter Card support
- Canonical URLs
- Mobile-responsive design
- Fast loading times

## Mobile Optimization

- Responsive design with mobile-first approach
- Touch-friendly interface
- Optimized for all screen sizes
- Mobile menu navigation

## Production Deployment

For production deployment:

1. Set `DEBUG=False` in settings or environment variable
2. Set a secure `SECRET_KEY`
3. Configure `ALLOWED_HOSTS` with your domain
4. Set up proper static file serving
5. Configure database connection
6. Set up SSL/HTTPS
7. Configure media file storage (consider using cloud storage)

## Additional Libraries (Optional)

For enhanced functionality, you may want to install:

- `yt-dlp`: For YouTube to MP3 conversion (already included in requirements.txt)
- `FFmpeg`: Required for YouTube to MP3 audio extraction. Install separately:
  - macOS: `brew install ffmpeg`
  - Ubuntu/Debian: `sudo apt-get install ffmpeg`
  - Windows: Download from https://ffmpeg.org/download.html
- `PyPDF2` or `pypdf`: For PDF manipulation
- `cairosvg`: For SVG to PNG conversion

## License

This project is open source and available for use.

## Support

For issues or questions, please open an issue in the repository.

