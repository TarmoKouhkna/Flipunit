"""
Custom middleware for FlipUnit
"""


class RemoveSitemapSecurityHeadersMiddleware:
    """
    Middleware to remove security headers from sitemap.xml responses.
    These headers are added by SecurityMiddleware but can cause issues
    with Google Search Console when fetching sitemaps.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Only remove headers for sitemap.xml
        if request.path == '/sitemap.xml':
            headers_to_remove = [
                'X-Frame-Options',
                'X-Content-Type-Options',
                'Referrer-Policy',
                'Cross-Origin-Opener-Policy',
                'X-Robots-Tag',
            ]
            
            # Django HttpResponse stores headers in _headers dict with normalized keys
            # We need to remove them from the internal _headers dict
            for header in headers_to_remove:
                try:
                    # Try standard deletion first
                    if header in response:
                        del response[header]
                    
                    # Also remove from _headers dict directly (Django's internal storage)
                    if hasattr(response, '_headers'):
                        # Headers are stored as (key, value) tuples, normalized to lowercase
                        header_lower = header.lower().replace('_', '-')
                        # Remove all variations - iterate over keys() to avoid modification during iteration
                        keys_to_remove = []
                        for key in list(response._headers.keys()):
                            if key.lower() == header_lower:
                                keys_to_remove.append(key)
                        for key in keys_to_remove:
                            del response._headers[key]
                    
                    # Don't set to empty string - we want to completely remove the header
                except (KeyError, AttributeError, TypeError):
                    # Header doesn't exist or response doesn't support these operations
                    pass
        
        return response
