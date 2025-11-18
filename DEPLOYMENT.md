# Deployment Guide for FlipUnit.eu

This guide will help you deploy your Django application to production.

## Prerequisites

- Domain: flipunit.eu (already registered)
- GitHub repository: Your code is already on GitHub
- Deployment platform account (choose one below)

## Deployment Options

### Option 1: Railway.app (Recommended - Easiest)

1. **Sign up**: Go to https://railway.app and sign up with GitHub
2. **Create new project**: Click "New Project" → "Deploy from GitHub repo"
3. **Select repository**: Choose your Flipunit repository
4. **Add PostgreSQL**: Click "+ New" → "Database" → "PostgreSQL"
5. **Set environment variables**:
   - `SECRET_KEY`: Generate a new secret key (use: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
   - `DEBUG`: `False`
   - `ALLOWED_HOSTS`: `flipunit.eu,www.flipunit.eu`
   - `DB_NAME`: (from PostgreSQL service)
   - `DB_USER`: (from PostgreSQL service)
   - `DB_PASSWORD`: (from PostgreSQL service)
   - `DB_HOST`: (from PostgreSQL service)
   - `DB_PORT`: `5432`
6. **Add custom domain**: 
   - Go to Settings → Domains
   - Add `flipunit.eu` and `www.flipunit.eu`
   - Update DNS records as instructed by Railway
7. **Deploy**: Railway will automatically deploy when you push to GitHub

### Option 2: Render.com (Free tier available)

1. **Sign up**: Go to https://render.com and sign up with GitHub
2. **Create Web Service**: New → Web Service → Connect GitHub repo
3. **Settings**:
   - Build Command: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - Start Command: `gunicorn flipunit.wsgi:application`
4. **Add PostgreSQL**: Create a PostgreSQL database
5. **Set environment variables** (same as Railway)
6. **Add custom domain**: Settings → Custom Domains → Add your domain
7. **Update DNS**: Follow Render's DNS instructions

### Option 3: DigitalOcean App Platform

1. **Sign up**: Go to https://www.digitalocean.com
2. **Create App**: Apps → Create App → GitHub
3. **Configure**: Select your repo, add PostgreSQL database
4. **Set environment variables** (same as above)
5. **Add domain**: Settings → Domains → Add custom domain

## DNS Configuration

After deploying, you need to update your domain's DNS records:

### For Railway:
- Add CNAME record: `www` → `your-app.railway.app`
- Add A record: `@` → Railway's IP (check Railway dashboard)

### For Render:
- Add CNAME record: `www` → `your-app.onrender.com`
- Add CNAME record: `@` → `your-app.onrender.com`

### For DigitalOcean:
- Follow their specific DNS instructions

## Post-Deployment Steps

1. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

2. **Collect static files**:
   ```bash
   python manage.py collectstatic --noinput
   ```

3. **Create superuser** (if needed):
   ```bash
   python manage.py createsuperuser
   ```

## Important Notes

- **FFmpeg**: Your app requires FFmpeg for video conversion. Check if your hosting platform supports it:
  - Railway: May need to add buildpack or use Docker
  - Render: May need custom build script
  - DigitalOcean: Usually available, may need to install

- **File size limits**: Your app handles files up to 500MB. Ensure your hosting platform supports this.

- **Environment variables**: Never commit `.env` files. Always use platform's environment variable settings.

## Testing

After deployment:
1. Visit https://flipunit.eu
2. Test a few converters
3. Check that static files (CSS, JS, images) load correctly
4. Test file uploads and conversions

## Troubleshooting

- **Static files not loading**: Run `collectstatic` command
- **Database errors**: Check environment variables are set correctly
- **500 errors**: Check logs in your hosting platform's dashboard
- **FFmpeg not found**: May need to install via buildpack or Docker

