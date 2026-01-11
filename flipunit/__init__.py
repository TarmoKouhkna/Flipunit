# This file intentionally left empty
# XSL removal is handled in flipunit/urls.py sitemap() function
# which uses line-by-line filtering to remove XSL stylesheet references

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
# Make import optional for local development (e.g., running migrations without Docker)
try:
    from .celery import app as celery_app
    __all__ = ('celery_app',)
except ImportError:
    # Celery not installed (e.g., local development without Docker)
    # This allows running migrations and other Django commands without Celery
    __all__ = ()
