from django.shortcuts import render
from django.http import HttpResponse
from django.contrib import messages
import json
import csv
import io
import re
import hashlib
import urllib.parse
import base64

# Check for optional dependencies
try:
    import htmlmin
    HTMLMIN_AVAILABLE = True
except ImportError:
    HTMLMIN_AVAILABLE = False

try:
    import rcssmin
    CSSMIN_AVAILABLE = True
except ImportError:
    CSSMIN_AVAILABLE = False

try:
    import rjsmin
    JSMIN_AVAILABLE = True
except ImportError:
    JSMIN_AVAILABLE = False

try:
    import jsbeautifier
    JSBEAUTIFIER_AVAILABLE = True
except ImportError:
    JSBEAUTIFIER_AVAILABLE = False

try:
    import sqlparse
    SQLPARSE_AVAILABLE = True
except ImportError:
    SQLPARSE_AVAILABLE = False

try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False


def index(request):
    """Developer converters main page"""
    return render(request, 'developer_converter/index.html', {
        'htmlmin_available': HTMLMIN_AVAILABLE,
        'cssmin_available': CSSMIN_AVAILABLE,
        'jsmin_available': JSMIN_AVAILABLE,
        'jsbeautifier_available': JSBEAUTIFIER_AVAILABLE,
        'sqlparse_available': SQLPARSE_AVAILABLE,
        'jwt_available': JWT_AVAILABLE,
    })


def minify_code(request):
    """Minify HTML, CSS, or JavaScript"""
    if request.method != 'POST':
        return render(request, 'developer_converter/minify.html', {
            'htmlmin_available': HTMLMIN_AVAILABLE,
            'cssmin_available': CSSMIN_AVAILABLE,
            'jsmin_available': JSMIN_AVAILABLE,
        })
    
    code = request.POST.get('code', '').strip()
    code_type = request.POST.get('code_type', 'html')
    
    if not code:
        messages.error(request, 'Please enter code to minify.')
        return render(request, 'developer_converter/minify.html', {
            'htmlmin_available': HTMLMIN_AVAILABLE,
            'cssmin_available': CSSMIN_AVAILABLE,
            'jsmin_available': JSMIN_AVAILABLE,
        })
    
    try:
        if code_type == 'html':
            if not HTMLMIN_AVAILABLE:
                messages.error(request, 'HTML minification requires htmlmin library. Install with: pip install htmlmin')
                return render(request, 'developer_converter/minify.html', {
                    'htmlmin_available': HTMLMIN_AVAILABLE,
                    'cssmin_available': CSSMIN_AVAILABLE,
                    'jsmin_available': JSMIN_AVAILABLE,
                })
            result = htmlmin.minify(code, remove_comments=True, remove_empty_space=True)
        elif code_type == 'css':
            if not CSSMIN_AVAILABLE:
                messages.error(request, 'CSS minification requires rcssmin library. Install with: pip install rcssmin')
                return render(request, 'developer_converter/minify.html', {
                    'htmlmin_available': HTMLMIN_AVAILABLE,
                    'cssmin_available': CSSMIN_AVAILABLE,
                    'jsmin_available': JSMIN_AVAILABLE,
                })
            result = rcssmin.cssmin(code)
        elif code_type == 'js':
            if not JSMIN_AVAILABLE:
                messages.error(request, 'JavaScript minification requires rjsmin library. Install with: pip install rjsmin')
                return render(request, 'developer_converter/minify.html', {
                    'htmlmin_available': HTMLMIN_AVAILABLE,
                    'cssmin_available': CSSMIN_AVAILABLE,
                    'jsmin_available': JSMIN_AVAILABLE,
                })
            result = rjsmin.jsmin(code)
        else:
            result = code
    except Exception as e:
        messages.error(request, f'Error minifying code: {str(e)}')
        return render(request, 'developer_converter/minify.html', {
            'code': code,
            'code_type': code_type,
            'htmlmin_available': HTMLMIN_AVAILABLE,
            'cssmin_available': CSSMIN_AVAILABLE,
            'jsmin_available': JSMIN_AVAILABLE,
        })
    
    return render(request, 'developer_converter/minify.html', {
        'code': code,
        'result': result,
        'code_type': code_type,
        'htmlmin_available': HTMLMIN_AVAILABLE,
        'cssmin_available': CSSMIN_AVAILABLE,
        'jsmin_available': JSMIN_AVAILABLE,
    })


def unminify_code(request):
    """Unminify (beautify) HTML, CSS, or JavaScript"""
    if request.method != 'POST':
        return render(request, 'developer_converter/unminify.html', {
            'htmlmin_available': HTMLMIN_AVAILABLE,
            'jsbeautifier_available': JSBEAUTIFIER_AVAILABLE,
        })
    
    code = request.POST.get('code', '').strip()
    code_type = request.POST.get('code_type', 'html')
    
    if not code:
        messages.error(request, 'Please enter code to unminify.')
        return render(request, 'developer_converter/unminify.html', {
            'htmlmin_available': HTMLMIN_AVAILABLE,
            'jsbeautifier_available': JSBEAUTIFIER_AVAILABLE,
        })
    
    try:
        if code_type == 'html':
            # HTML unminification is basic - just add line breaks
            # htmlmin doesn't have unminify, so we'll do basic formatting
            result = code.replace('><', '>\n<')
            result = re.sub(r'(\s+)', ' ', result)  # Normalize whitespace
            result = re.sub(r'>\s+<', '>\n<', result)  # Add line breaks
        elif code_type == 'css':
            # Basic CSS formatting
            result = code.replace(';', ';\n').replace('{', ' {\n').replace('}', '\n}\n')
            result = re.sub(r'\s+', ' ', result)  # Normalize whitespace
            result = re.sub(r';\s*', ';\n', result)  # Format semicolons
        elif code_type == 'js':
            if not JSBEAUTIFIER_AVAILABLE:
                messages.error(request, 'JavaScript beautification requires jsbeautifier library. Install with: pip install jsbeautifier')
                return render(request, 'developer_converter/unminify.html', {
                    'code': code,
                    'code_type': code_type,
                    'htmlmin_available': HTMLMIN_AVAILABLE,
                    'jsbeautifier_available': JSBEAUTIFIER_AVAILABLE,
                })
            opts = jsbeautifier.default_options()
            opts.indent_size = 2
            opts.preserve_newlines = True
            result = jsbeautifier.beautify(code, opts)
        else:
            result = code
    except Exception as e:
        messages.error(request, f'Error unminifying code: {str(e)}')
        return render(request, 'developer_converter/unminify.html', {
            'code': code,
            'code_type': code_type,
            'htmlmin_available': HTMLMIN_AVAILABLE,
            'jsbeautifier_available': JSBEAUTIFIER_AVAILABLE,
        })
    
    return render(request, 'developer_converter/unminify.html', {
        'code': code,
        'result': result,
        'code_type': code_type,
        'htmlmin_available': HTMLMIN_AVAILABLE,
        'jsbeautifier_available': JSBEAUTIFIER_AVAILABLE,
    })


def csv_to_json(request):
    """Convert CSV to JSON"""
    if request.method != 'POST':
        return render(request, 'developer_converter/csv_json.html', {'conversion_type': 'csv_to_json'})
    
    csv_text = request.POST.get('csv_text', '').strip()
    has_headers = request.POST.get('has_headers', 'on') == 'on'
    
    if not csv_text:
        messages.error(request, 'Please enter CSV data.')
        return render(request, 'developer_converter/csv_json.html', {
            'conversion_type': 'csv_to_json',
            'csv_text': csv_text,
        })
    
    try:
        if has_headers:
            csv_reader = csv.DictReader(io.StringIO(csv_text))
            result = json.dumps(list(csv_reader), indent=2, ensure_ascii=False)
        else:
            csv_reader = csv.reader(io.StringIO(csv_text))
            rows = list(csv_reader)
            result = json.dumps(rows, indent=2, ensure_ascii=False)
    except Exception as e:
        messages.error(request, f'Error converting CSV to JSON: {str(e)}')
        return render(request, 'developer_converter/csv_json.html', {
            'conversion_type': 'csv_to_json',
            'csv_text': csv_text,
        })
    
    return render(request, 'developer_converter/csv_json.html', {
        'conversion_type': 'csv_to_json',
        'csv_text': csv_text,
        'result': result,
        'has_headers': has_headers,
    })


def json_to_csv(request):
    """Convert JSON to CSV"""
    if request.method != 'POST':
        return render(request, 'developer_converter/csv_json.html', {'conversion_type': 'json_to_csv'})
    
    json_text = request.POST.get('json_text', '').strip()
    
    if not json_text:
        messages.error(request, 'Please enter JSON data.')
        return render(request, 'developer_converter/csv_json.html', {
            'conversion_type': 'json_to_csv',
            'json_text': json_text,
        })
    
    try:
        data = json.loads(json_text)
        
        if not isinstance(data, list):
            data = [data]
        
        if not data:
            messages.error(request, 'JSON must contain at least one object.')
            return render(request, 'developer_converter/csv_json.html', {
                'conversion_type': 'json_to_csv',
                'json_text': json_text,
            })
        
        # Get all unique keys from all objects
        all_keys = set()
        for item in data:
            if isinstance(item, dict):
                all_keys.update(item.keys())
        
        if not all_keys:
            messages.error(request, 'JSON objects must have at least one key.')
            return render(request, 'developer_converter/csv_json.html', {
                'conversion_type': 'json_to_csv',
                'json_text': json_text,
            })
        
        fieldnames = sorted(all_keys)
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for item in data:
            if isinstance(item, dict):
                writer.writerow({k: str(item.get(k, '')) for k in fieldnames})
            else:
                writer.writerow({fieldnames[0]: str(item)})
        
        result = output.getvalue()
    except json.JSONDecodeError as e:
        messages.error(request, f'Invalid JSON: {str(e)}')
        return render(request, 'developer_converter/csv_json.html', {
            'conversion_type': 'json_to_csv',
            'json_text': json_text,
        })
    except Exception as e:
        messages.error(request, f'Error converting JSON to CSV: {str(e)}')
        return render(request, 'developer_converter/csv_json.html', {
            'conversion_type': 'json_to_csv',
            'json_text': json_text,
        })
    
    return render(request, 'developer_converter/csv_json.html', {
        'conversion_type': 'json_to_csv',
        'json_text': json_text,
        'result': result,
    })


def sql_formatter(request):
    """Format SQL queries"""
    if request.method != 'POST':
        return render(request, 'developer_converter/sql_formatter.html', {
            'sqlparse_available': SQLPARSE_AVAILABLE,
        })
    
    if not SQLPARSE_AVAILABLE:
        messages.error(request, 'SQL formatting requires sqlparse library. Install with: pip install sqlparse')
        return render(request, 'developer_converter/sql_formatter.html', {
            'sqlparse_available': SQLPARSE_AVAILABLE,
        })
    
    sql = request.POST.get('sql', '').strip()
    indent_size = int(request.POST.get('indent_size', '2'))
    
    if not sql:
        messages.error(request, 'Please enter SQL query.')
        return render(request, 'developer_converter/sql_formatter.html', {
            'sqlparse_available': SQLPARSE_AVAILABLE,
        })
    
    try:
        formatted = sqlparse.format(sql, reindent=True, indent_width=indent_size, keyword_case='upper')
        result = formatted
    except Exception as e:
        messages.error(request, f'Error formatting SQL: {str(e)}')
        return render(request, 'developer_converter/sql_formatter.html', {
            'sql': sql,
            'sqlparse_available': SQLPARSE_AVAILABLE,
        })
    
    return render(request, 'developer_converter/sql_formatter.html', {
        'sql': sql,
        'result': result,
        'indent_size': indent_size,
        'sqlparse_available': SQLPARSE_AVAILABLE,
    })


def css_scss(request):
    """Convert between CSS and SCSS (basic conversion)"""
    if request.method != 'POST':
        return render(request, 'developer_converter/css_scss.html')
    
    code = request.POST.get('code', '').strip()
    conversion_type = request.POST.get('conversion_type', 'css_to_scss')
    
    if not code:
        messages.error(request, 'Please enter CSS or SCSS code.')
        return render(request, 'developer_converter/css_scss.html')
    
    try:
        if conversion_type == 'css_to_scss':
            # Basic CSS to SCSS conversion (nested selectors)
            # This is a simplified conversion - full SCSS requires a proper parser
            lines = code.split('\n')
            result_lines = []
            indent_level = 0
            
            for line in lines:
                stripped = line.strip()
                if not stripped or stripped.startswith('/*'):
                    continue
                
                # Check for closing brace
                if '}' in stripped:
                    indent_level = max(0, indent_level - 1)
                
                # Add line with proper indentation
                result_lines.append('  ' * indent_level + stripped)
                
                # Check for opening brace
                if '{' in stripped:
                    indent_level += 1
            
            result = '\n'.join(result_lines)
        else:  # scss_to_css
            # Basic SCSS to CSS conversion (flatten nested selectors)
            # This is simplified - full conversion requires a SCSS compiler
            lines = code.split('\n')
            result_lines = []
            current_selector = []
            
            for line in lines:
                stripped = line.strip()
                if not stripped or stripped.startswith('//') or stripped.startswith('/*'):
                    continue
                
                # Detect selector
                if ':' in stripped and '{' not in stripped and '}' not in stripped:
                    # Property
                    result_lines.append('  ' + stripped)
                elif '{' in stripped:
                    # Opening brace - extract selector
                    selector = stripped.split('{')[0].strip()
                    current_selector.append(selector)
                    full_selector = ' '.join(current_selector)
                    result_lines.append(full_selector + ' {')
                elif '}' in stripped:
                    # Closing brace
                    result_lines.append('}')
                    if current_selector:
                        current_selector.pop()
            
            result = '\n'.join(result_lines)
    except Exception as e:
        messages.error(request, f'Error converting: {str(e)}. Note: This is a basic converter. For full SCSS support, use a proper SCSS compiler.')
        return render(request, 'developer_converter/css_scss.html', {
            'code': code,
            'conversion_type': conversion_type,
        })
    
    return render(request, 'developer_converter/css_scss.html', {
        'code': code,
        'result': result,
        'conversion_type': conversion_type,
    })


def regex_tester(request):
    """Test regular expressions"""
    if request.method != 'POST':
        return render(request, 'developer_converter/regex_tester.html')
    
    pattern = request.POST.get('pattern', '').strip()
    test_text = request.POST.get('test_text', '').strip()
    flags = request.POST.getlist('flags')
    
    if not pattern:
        messages.error(request, 'Please enter a regular expression pattern.')
        return render(request, 'developer_converter/regex_tester.html', {
            'test_text': test_text,
        })
    
    try:
        # Build flags
        re_flags = 0
        if 'ignorecase' in flags:
            re_flags |= re.IGNORECASE
        if 'multiline' in flags:
            re_flags |= re.MULTILINE
        if 'dotall' in flags:
            re_flags |= re.DOTALL
        
        # Compile pattern
        regex = re.compile(pattern, re_flags)
        
        # Find all matches
        matches = list(regex.finditer(test_text))
        
        # Get match details
        match_details = []
        for match in matches:
            match_details.append({
                'match': match.group(),
                'start': match.start(),
                'end': match.end(),
                'groups': match.groups() if match.groups() else None,
            })
        
        # Check if pattern matches entire string
        full_match = regex.fullmatch(test_text) is not None
        
        # Check if pattern matches at start
        match_start = regex.match(test_text) is not None
        
    except re.error as e:
        messages.error(request, f'Invalid regular expression: {str(e)}')
        return render(request, 'developer_converter/regex_tester.html', {
            'pattern': pattern,
            'test_text': test_text,
            'flags': flags,
        })
    except Exception as e:
        messages.error(request, f'Error testing regex: {str(e)}')
        return render(request, 'developer_converter/regex_tester.html', {
            'pattern': pattern,
            'test_text': test_text,
            'flags': flags,
        })
    
    return render(request, 'developer_converter/regex_tester.html', {
        'pattern': pattern,
        'test_text': test_text,
        'flags': flags,
        'matches': match_details,
        'match_count': len(match_details),
        'full_match': full_match,
        'match_start': match_start,
    })


def jwt_decoder(request):
    """Decode JWT tokens"""
    if request.method != 'POST':
        return render(request, 'developer_converter/jwt_decoder.html', {
            'jwt_available': JWT_AVAILABLE,
        })
    
    if not JWT_AVAILABLE:
        messages.error(request, 'JWT decoding requires PyJWT library. Install with: pip install PyJWT')
        return render(request, 'developer_converter/jwt_decoder.html', {
            'jwt_available': JWT_AVAILABLE,
        })
    
    token = request.POST.get('token', '').strip()
    
    if not token:
        messages.error(request, 'Please enter a JWT token.')
        return render(request, 'developer_converter/jwt_decoder.html', {
            'jwt_available': JWT_AVAILABLE,
        })
    
    try:
        # Decode without verification (for display purposes)
        decoded = jwt.decode(token, options={"verify_signature": False})
        header = jwt.get_unverified_header(token)
        
        # Format as JSON
        header_json = json.dumps(header, indent=2)
        payload_json = json.dumps(decoded, indent=2)
    except jwt.DecodeError as e:
        messages.error(request, f'Invalid JWT token: {str(e)}')
        return render(request, 'developer_converter/jwt_decoder.html', {
            'token': token,
            'jwt_available': JWT_AVAILABLE,
        })
    except Exception as e:
        messages.error(request, f'Error decoding JWT: {str(e)}')
        return render(request, 'developer_converter/jwt_decoder.html', {
            'token': token,
            'jwt_available': JWT_AVAILABLE,
        })
    
    return render(request, 'developer_converter/jwt_decoder.html', {
        'token': token,
        'header': header_json,
        'payload': payload_json,
        'jwt_available': JWT_AVAILABLE,
    })


def url_encoder(request):
    """Encode/Decode URLs"""
    if request.method != 'POST':
        return render(request, 'developer_converter/url_encoder.html')
    
    text = request.POST.get('text', '').strip()
    conversion_type = request.POST.get('conversion_type', 'encode')
    
    if not text:
        messages.error(request, 'Please enter text to encode or decode.')
        return render(request, 'developer_converter/url_encoder.html')
    
    try:
        if conversion_type == 'encode':
            result = urllib.parse.quote(text, safe='')
        elif conversion_type == 'decode':
            result = urllib.parse.unquote(text)
        else:
            result = text
    except Exception as e:
        messages.error(request, f'Error processing URL: {str(e)}')
        return render(request, 'developer_converter/url_encoder.html', {
            'text': text,
            'conversion_type': conversion_type,
        })
    
    return render(request, 'developer_converter/url_encoder.html', {
        'text': text,
        'result': result,
        'conversion_type': conversion_type,
    })


def hash_generator(request):
    """Generate hash values (MD5, SHA1, SHA256)"""
    if request.method != 'POST':
        return render(request, 'developer_converter/hash_generator.html')
    
    text = request.POST.get('text', '').strip()
    hash_type = request.POST.get('hash_type', 'md5')
    
    if not text:
        messages.error(request, 'Please enter text to hash.')
        return render(request, 'developer_converter/hash_generator.html')
    
    try:
        text_bytes = text.encode('utf-8')
        
        if hash_type == 'md5':
            hash_obj = hashlib.md5(text_bytes)
        elif hash_type == 'sha1':
            hash_obj = hashlib.sha1(text_bytes)
        elif hash_type == 'sha256':
            hash_obj = hashlib.sha256(text_bytes)
        else:
            messages.error(request, 'Invalid hash type.')
            return render(request, 'developer_converter/hash_generator.html', {
                'text': text,
            })
        
        result = hash_obj.hexdigest()
    except Exception as e:
        messages.error(request, f'Error generating hash: {str(e)}')
        return render(request, 'developer_converter/hash_generator.html', {
            'text': text,
            'hash_type': hash_type,
        })
    
    return render(request, 'developer_converter/hash_generator.html', {
        'text': text,
        'result': result,
        'hash_type': hash_type,
    })

