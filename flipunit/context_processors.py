from django.conf import settings

def site_settings(request):
    """Make site settings available in all templates"""
    return {
        'SITE_NAME': getattr(settings, 'SITE_NAME', 'FlipUnit.eu'),
        'SITE_DESCRIPTION': getattr(settings, 'SITE_DESCRIPTION', 'Simple, fast, no-login online converter hub'),
    }

