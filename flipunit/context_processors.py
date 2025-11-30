from django.conf import settings

def site_settings(request):
    """Make site settings available in all templates"""
    return {
        'SITE_NAME': getattr(settings, 'SITE_NAME', 'FlipUnit'),
        'SITE_DISPLAY_NAME': getattr(settings, 'SITE_DISPLAY_NAME', 'flipunit'),
        'SITE_DESCRIPTION': getattr(settings, 'SITE_DESCRIPTION', 'Simple, fast, no-login online converter hub'),
        'SITE_URL': getattr(settings, 'SITE_URL', 'https://flipunit.eu'),
    }

