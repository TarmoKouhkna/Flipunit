from django.shortcuts import render
from django.http import JsonResponse
import requests
import socket
import ssl
import time
import re
from urllib.parse import urlparse
from django.views.decorators.http import require_http_methods


def normalize_domain(url):
    """Normalize and validate domain from user input"""
    if not url:
        return None
    
    # Strip whitespace
    url = url.strip()
    
    # Remove protocol
    url = re.sub(r'^https?://', '', url, flags=re.IGNORECASE)
    
    # Remove www. prefix (optional, we'll keep it for now)
    # url = re.sub(r'^www\.', '', url, flags=re.IGNORECASE)
    
    # Remove trailing slashes and paths
    url = url.split('/')[0]
    url = url.split('?')[0]  # Remove query strings
    url = url.split('#')[0]  # Remove fragments
    
    # Basic domain validation
    if not url or len(url) > 255:
        return None
    
    # Check if it looks like a domain
    domain_pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    if not re.match(domain_pattern, url):
        return None
    
    return url.lower()


def check_ssl_certificate(domain):
    """Check SSL certificate validity for a domain"""
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                return "ok"
    except ssl.SSLError:
        return "invalid"
    except (socket.gaierror, socket.timeout, OSError):
        return "unknown"  # Can't check if can't connect
    except Exception:
        return "unknown"


def index(request):
    """Main page for website status checker"""
    return render(request, 'isdown/index.html')


@require_http_methods(["GET"])
def api_check(request):
    """API endpoint to check website status"""
    url = request.GET.get('url', '').strip()
    
    if not url:
        return JsonResponse({
            'status': 'error',
            'error': 'URL parameter is required'
        }, status=400)
    
    # Normalize domain
    domain = normalize_domain(url)
    if not domain:
        return JsonResponse({
            'status': 'error',
            'error': 'Invalid domain format'
        }, status=400)
    
    result = {
        'status': 'down',
        'response_time': None,
        'dns': 'unknown',
        'ssl': 'unknown',
        'ip': None,
        'error': None,
        'http_status': None
    }
    
    # Step 1: DNS Resolution
    try:
        ip = socket.gethostbyname(domain)
        result['ip'] = ip
        result['dns'] = 'ok'
    except socket.gaierror:
        result['dns'] = 'fail'
        result['error'] = 'DNS resolution failed'
        return JsonResponse(result)
    except Exception as e:
        result['dns'] = 'fail'
        result['error'] = f'DNS error: {str(e)}'
        return JsonResponse(result)
    
    # Step 2: HTTP Request
    start_time = time.time()
    try:
        # Try HTTPS first
        https_url = f'https://{domain}'
        response = requests.head(
            https_url,
            timeout=10,
            allow_redirects=True,
            headers={'User-Agent': 'Mozilla/5.0 (compatible; Flipunit/1.0)'}
        )
        
        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        result['response_time'] = round(response_time, 2)
        result['http_status'] = response.status_code
        result['status'] = 'up'
        
        # Check SSL (since we used HTTPS)
        result['ssl'] = check_ssl_certificate(domain)
        
    except requests.exceptions.SSLError:
        # SSL error, try HTTP
        try:
            http_url = f'http://{domain}'
            start_time = time.time()
            response = requests.head(
                http_url,
                timeout=10,
                allow_redirects=True,
                headers={'User-Agent': 'Mozilla/5.0 (compatible; Flipunit/1.0)'}
            )
            
            response_time = (time.time() - start_time) * 1000
            result['response_time'] = round(response_time, 2)
            result['http_status'] = response.status_code
            result['status'] = 'up'
            result['ssl'] = 'not_applicable'  # HTTP doesn't use SSL
            
        except requests.exceptions.Timeout:
            result['error'] = 'Connection timeout'
            result['response_time'] = None
        except requests.exceptions.ConnectionError:
            result['error'] = 'Connection failed'
        except Exception as e:
            result['error'] = f'HTTP error: {str(e)}'
            
    except requests.exceptions.Timeout:
        result['error'] = 'Connection timeout'
        result['response_time'] = None
    except requests.exceptions.ConnectionError:
        result['error'] = 'Connection failed'
    except requests.exceptions.RequestException as e:
        result['error'] = f'Request error: {str(e)}'
    except Exception as e:
        result['error'] = f'Unexpected error: {str(e)}'
    
    return JsonResponse(result)











