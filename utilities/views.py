from django.shortcuts import render
from django.http import HttpResponse
from django.contrib import messages
import re
import io
from datetime import datetime
import pytz
from PIL import Image
try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False

def index(request):
    """Utilities index page"""
    context = {
        'utilities': [
            {'name': 'Calculator', 'url_name': 'calculator', 'description': 'Simple online calculator'},
            {'name': 'Text Tools', 'url_name': 'text_tools', 'description': 'Word count, character count, and text utilities'},
            {'name': 'Color Converter', 'url_name': 'color_converter', 'description': 'Convert between HEX, RGB, HSL, and CMYK'},
            {'name': 'QR Code Generator', 'url_name': 'qr_code_generator', 'description': 'Generate QR codes from text or URLs'},
            {'name': 'Time Zone Converter', 'url_name': 'timezone_converter', 'description': 'Convert time between different time zones'},
            {'name': 'Roman Numeral Converter', 'url_name': 'roman_numeral_converter', 'description': 'Convert between Roman and Arabic numerals'},
            {'name': 'Favicon Generator', 'url_name': 'favicon_generator', 'description': 'Generate favicon.ico from any image'},
        ]
    }
    return render(request, 'utilities/index.html', context)

def _safe_evaluate(expression):
    """
    Safely evaluate a mathematical expression without using eval().
    Only supports basic arithmetic operations: +, -, *, /, and parentheses.
    """
    import re
    import operator
    
    # Remove all whitespace
    expression = expression.replace(' ', '')
    
    # Validate: only allow numbers, operators, parentheses, and decimal points
    if not re.match(r'^[0-9+\-*/().]+$', expression):
        raise ValueError('Invalid characters in expression')
    
    # Use a simple stack-based evaluator
    # This is a basic implementation that handles +, -, *, /, and parentheses
    def evaluate_expression(tokens):
        """Evaluate expression using operator precedence"""
        if not tokens:
            raise ValueError('Empty expression')
        
        # Handle parentheses first
        i = 0
        while i < len(tokens):
            if tokens[i] == '(':
                # Find matching closing parenthesis
                depth = 1
                j = i + 1
                while j < len(tokens) and depth > 0:
                    if tokens[j] == '(':
                        depth += 1
                    elif tokens[j] == ')':
                        depth -= 1
                    j += 1
                
                if depth != 0:
                    raise ValueError('Mismatched parentheses')
                
                # Recursively evaluate expression inside parentheses
                inner_result = evaluate_expression(tokens[i+1:j-1])
                tokens = tokens[:i] + [str(inner_result)] + tokens[j:]
                i = 0
                continue
            i += 1
        
        # Remove any remaining parentheses (shouldn't happen, but safety check)
        tokens = [t for t in tokens if t not in ('(', ')')]
        
        # Handle multiplication and division
        i = 0
        while i < len(tokens):
            if tokens[i] == '*':
                if i == 0 or i == len(tokens) - 1:
                    raise ValueError('Invalid expression')
                result = float(tokens[i-1]) * float(tokens[i+1])
                tokens = tokens[:i-1] + [str(result)] + tokens[i+2:]
                i = 0
            elif tokens[i] == '/':
                if i == 0 or i == len(tokens) - 1:
                    raise ValueError('Invalid expression')
                divisor = float(tokens[i+1])
                if divisor == 0:
                    raise ValueError('Division by zero')
                result = float(tokens[i-1]) / divisor
                tokens = tokens[:i-1] + [str(result)] + tokens[i+2:]
                i = 0
            else:
                i += 1
        
        # Handle addition and subtraction
        result = float(tokens[0])
        i = 1
        while i < len(tokens):
            if tokens[i] == '+':
                if i == len(tokens) - 1:
                    raise ValueError('Invalid expression')
                result += float(tokens[i+1])
                i += 2
            elif tokens[i] == '-':
                if i == len(tokens) - 1:
                    raise ValueError('Invalid expression')
                result -= float(tokens[i+1])
                i += 2
            else:
                raise ValueError(f'Unexpected token: {tokens[i]}')
        
        return result
    
    # Tokenize the expression
    tokens = []
    current_number = ''
    
    for char in expression:
        if char.isdigit() or char == '.':
            current_number += char
        else:
            if current_number:
                tokens.append(current_number)
                current_number = ''
            if char in '+-*/()':
                tokens.append(char)
    
    if current_number:
        tokens.append(current_number)
    
    if not tokens:
        raise ValueError('Empty expression')
    
    return evaluate_expression(tokens)

def calculator(request):
    """Simple calculator"""
    result = None
    error = None
    
    if request.method == 'POST':
        try:
            expression = request.POST.get('expression', '').strip()
            if expression:
                # Use safe evaluation instead of eval()
                result = _safe_evaluate(expression)
            else:
                error = 'Please enter an expression'
        except ValueError as e:
            error = f'Error: {str(e)}'
        except Exception as e:
            error = f'Error: {str(e)}'
    
    context = {
        'result': result,
        'error': error,
    }
    return render(request, 'utilities/calculator.html', context)

def text_tools(request):
    """Text utilities"""
    word_count = None
    char_count = None
    char_count_no_spaces = None
    text = ''
    
    if request.method == 'POST':
        text = request.POST.get('text', '')
        if text:
            word_count = len(text.split())
            char_count = len(text)
            char_count_no_spaces = len(text.replace(' ', ''))
    
    context = {
        'text': text,
        'word_count': word_count,
        'char_count': char_count,
        'char_count_no_spaces': char_count_no_spaces,
    }
    return render(request, 'utilities/text_tools.html', context)

def color_converter(request):
    """Color converter - HEX, RGB, HSL, CMYK"""
    result = None
    error = None
    input_format = None
    output_format = None
    
    if request.method == 'POST':
        input_format = request.POST.get('input_format')
        output_format = request.POST.get('output_format')
        color_input = request.POST.get('color_input', '').strip()
        
        if not color_input:
            error = 'Please enter a color value'
        else:
            try:
                # Parse input color
                if input_format == 'hex':
                    hex_color = color_input.lstrip('#')
                    if len(hex_color) == 3:
                        hex_color = ''.join([c*2 for c in hex_color])
                    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                elif input_format == 'rgb':
                    rgb_match = re.match(r'(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', color_input)
                    if not rgb_match:
                        raise ValueError('Invalid RGB format. Use: r, g, b')
                    r, g, b = map(int, rgb_match.groups())
                    if not all(0 <= x <= 255 for x in [r, g, b]):
                        raise ValueError('RGB values must be between 0 and 255')
                elif input_format == 'hsl':
                    hsl_match = re.match(r'(\d+)\s*,\s*(\d+)%\s*,\s*(\d+)%', color_input)
                    if not hsl_match:
                        raise ValueError('Invalid HSL format. Use: h, s%, l%')
                    h, s, l = map(float, hsl_match.groups())
                    if not (0 <= h <= 360 and 0 <= s <= 100 and 0 <= l <= 100):
                        raise ValueError('HSL values out of range')
                    r, g, b = hsl_to_rgb(h, s, l)
                elif input_format == 'cmyk':
                    cmyk_match = re.match(r'(\d+(?:\.\d+)?)%\s*,\s*(\d+(?:\.\d+)?)%\s*,\s*(\d+(?:\.\d+)?)%\s*,\s*(\d+(?:\.\d+)?)%', color_input)
                    if not cmyk_match:
                        raise ValueError('Invalid CMYK format. Use: c%, m%, y%, k%')
                    c, m, y, k = map(float, [x.rstrip('%') for x in cmyk_match.groups()])
                    if not all(0 <= x <= 100 for x in [c, m, y, k]):
                        raise ValueError('CMYK values must be between 0% and 100%')
                    r, g, b = cmyk_to_rgb(c, m, y, k)
                else:
                    raise ValueError('Invalid input format')
                
                # Convert to output format
                if output_format == 'hex':
                    result = f"#{r:02x}{g:02x}{b:02x}".upper()
                elif output_format == 'rgb':
                    result = f"rgb({r}, {g}, {b})"
                elif output_format == 'hsl':
                    h, s, l = rgb_to_hsl(r, g, b)
                    result = f"hsl({int(h)}, {int(s)}%, {int(l)}%)"
                elif output_format == 'cmyk':
                    c, m, y, k = rgb_to_cmyk(r, g, b)
                    result = f"cmyk({c:.1f}%, {m:.1f}%, {y:.1f}%, {k:.1f}%)"
                else:
                    raise ValueError('Invalid output format')
                    
            except Exception as e:
                error = str(e)
    
    context = {
        'result': result,
        'error': error,
        'input_format': input_format or 'hex',
        'output_format': output_format or 'rgb',
    }
    return render(request, 'utilities/color_converter.html', context)

def hsl_to_rgb(h, s, l):
    """Convert HSL to RGB"""
    h = h / 360.0
    s = s / 100.0
    l = l / 100.0
    
    if s == 0:
        r = g = b = l
    else:
        def hue_to_rgb(p, q, t):
            if t < 0: t += 1
            if t > 1: t -= 1
            if t < 1/6: return p + (q - p) * 6 * t
            if t < 1/2: return q
            if t < 2/3: return p + (q - p) * (2/3 - t) * 6
            return p
        
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r = hue_to_rgb(p, q, h + 1/3)
        g = hue_to_rgb(p, q, h)
        b = hue_to_rgb(p, q, h - 1/3)
    
    return int(round(r * 255)), int(round(g * 255)), int(round(b * 255))

def rgb_to_hsl(r, g, b):
    """Convert RGB to HSL"""
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    max_val = max(r, g, b)
    min_val = min(r, g, b)
    delta = max_val - min_val
    
    l = (max_val + min_val) / 2.0
    
    if delta == 0:
        h = s = 0
    else:
        s = delta / (2 - max_val - min_val) if l > 0.5 else delta / (max_val + min_val)
        
        if max_val == r:
            h = ((g - b) / delta + (6 if g < b else 0)) / 6.0
        elif max_val == g:
            h = ((b - r) / delta + 2) / 6.0
        else:
            h = ((r - g) / delta + 4) / 6.0
    
    return h * 360, s * 100, l * 100

def cmyk_to_rgb(c, m, y, k):
    """Convert CMYK to RGB"""
    c, m, y, k = c / 100.0, m / 100.0, y / 100.0, k / 100.0
    r = int(round(255 * (1 - c) * (1 - k)))
    g = int(round(255 * (1 - m) * (1 - k)))
    b = int(round(255 * (1 - y) * (1 - k)))
    return r, g, b

def rgb_to_cmyk(r, g, b):
    """Convert RGB to CMYK"""
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    k = 1 - max(r, g, b)
    if k == 1:
        return 0, 0, 0, 100
    c = (1 - r - k) / (1 - k) * 100
    m = (1 - g - k) / (1 - k) * 100
    y = (1 - b - k) / (1 - k) * 100
    return c, m, y, k * 100

def qr_code_generator(request):
    """Generate QR codes"""
    if not QRCODE_AVAILABLE:
        messages.error(request, 'QR code generation requires qrcode library. Install with: pip install qrcode[pil]')
        return render(request, 'utilities/qr_code_generator.html')
    
    if request.method != 'POST':
        return render(request, 'utilities/qr_code_generator.html')
    
    text = request.POST.get('text', '').strip()
    if not text:
        messages.error(request, 'Please enter text or URL to generate QR code.')
        return render(request, 'utilities/qr_code_generator.html')
    
    try:
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(text)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to bytes
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # Return image
        response = HttpResponse(img_buffer.read(), content_type='image/png')
        response['Content-Disposition'] = 'attachment; filename="qrcode.png"'
        return response
        
    except Exception as e:
        messages.error(request, f'Error generating QR code: {str(e)}')
        return render(request, 'utilities/qr_code_generator.html')

def timezone_converter(request):
    """Time zone converter"""
    result = None
    error = None
    
    if request.method == 'POST':
        try:
            from_tz = request.POST.get('from_timezone')
            to_tz = request.POST.get('to_timezone')
            date_str = request.POST.get('date', '').strip()
            time_str = request.POST.get('time', '').strip()
            
            if not from_tz or not to_tz:
                error = 'Please select both time zones'
            else:
                # Parse date and time
                if date_str and time_str:
                    datetime_str = f"{date_str} {time_str}"
                    try:
                        dt = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
                    except ValueError:
                        dt = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
                else:
                    dt = datetime.now()
                
                # Convert timezone
                from_timezone = pytz.timezone(from_tz)
                to_timezone = pytz.timezone(to_tz)
                
                # Localize and convert
                if dt.tzinfo is None:
                    dt = from_timezone.localize(dt)
                
                converted_dt = dt.astimezone(to_timezone)
                
                result = {
                    'original': dt.strftime('%Y-%m-%d %H:%M:%S %Z'),
                    'converted': converted_dt.strftime('%Y-%m-%d %H:%M:%S %Z'),
                    'from_tz': from_tz,
                    'to_tz': to_tz,
                }
        except Exception as e:
            error = str(e)
    
    # Get all world timezones organized by region
    all_timezones = [
        # UTC
        ('UTC', 'UTC (Coordinated Universal Time)'),
        
        # North America
        ('America/New_York', 'Eastern Time (US & Canada)'),
        ('America/Chicago', 'Central Time (US & Canada)'),
        ('America/Denver', 'Mountain Time (US & Canada)'),
        ('America/Los_Angeles', 'Pacific Time (US & Canada)'),
        ('America/Phoenix', 'Arizona (US)'),
        ('America/Anchorage', 'Alaska (US)'),
        ('America/Honolulu', 'Hawaii (US)'),
        ('America/Toronto', 'Toronto, Canada'),
        ('America/Vancouver', 'Vancouver, Canada'),
        ('America/Mexico_City', 'Mexico City'),
        ('America/Guatemala', 'Guatemala'),
        ('America/Havana', 'Havana, Cuba'),
        ('America/Jamaica', 'Jamaica'),
        ('America/Panama', 'Panama'),
        ('America/Bogota', 'Bogota, Colombia'),
        ('America/Lima', 'Lima, Peru'),
        ('America/Caracas', 'Caracas, Venezuela'),
        ('America/Santiago', 'Santiago, Chile'),
        ('America/Buenos_Aires', 'Buenos Aires, Argentina'),
        ('America/Sao_Paulo', 'Sao Paulo, Brazil'),
        ('America/Montevideo', 'Montevideo, Uruguay'),
        
        # Europe
        ('Europe/London', 'London, UK'),
        ('Europe/Dublin', 'Dublin, Ireland'),
        ('Europe/Lisbon', 'Lisbon, Portugal'),
        ('Europe/Madrid', 'Madrid, Spain'),
        ('Europe/Paris', 'Paris, France'),
        ('Europe/Brussels', 'Brussels, Belgium'),
        ('Europe/Amsterdam', 'Amsterdam, Netherlands'),
        ('Europe/Berlin', 'Berlin, Germany'),
        ('Europe/Rome', 'Rome, Italy'),
        ('Europe/Vienna', 'Vienna, Austria'),
        ('Europe/Zurich', 'Zurich, Switzerland'),
        ('Europe/Prague', 'Prague, Czech Republic'),
        ('Europe/Warsaw', 'Warsaw, Poland'),
        ('Europe/Budapest', 'Budapest, Hungary'),
        ('Europe/Bucharest', 'Bucharest, Romania'),
        ('Europe/Athens', 'Athens, Greece'),
        ('Europe/Helsinki', 'Helsinki, Finland'),
        ('Europe/Stockholm', 'Stockholm, Sweden'),
        ('Europe/Oslo', 'Oslo, Norway'),
        ('Europe/Copenhagen', 'Copenhagen, Denmark'),
        ('Europe/Moscow', 'Moscow, Russia'),
        ('Europe/Kiev', 'Kiev, Ukraine'),
        ('Europe/Istanbul', 'Istanbul, Turkey'),
        
        # Asia
        ('Asia/Dubai', 'Dubai, UAE'),
        ('Asia/Kuwait', 'Kuwait'),
        ('Asia/Riyadh', 'Riyadh, Saudi Arabia'),
        ('Asia/Baghdad', 'Baghdad, Iraq'),
        ('Asia/Tehran', 'Tehran, Iran'),
        ('Asia/Kabul', 'Kabul, Afghanistan'),
        ('Asia/Karachi', 'Karachi, Pakistan'),
        ('Asia/Dhaka', 'Dhaka, Bangladesh'),
        ('Asia/Kolkata', 'Kolkata, India'),
        ('Asia/Colombo', 'Colombo, Sri Lanka'),
        ('Asia/Kathmandu', 'Kathmandu, Nepal'),
        ('Asia/Yangon', 'Yangon, Myanmar'),
        ('Asia/Bangkok', 'Bangkok, Thailand'),
        ('Asia/Ho_Chi_Minh', 'Ho Chi Minh, Vietnam'),
        ('Asia/Manila', 'Manila, Philippines'),
        ('Asia/Singapore', 'Singapore'),
        ('Asia/Kuala_Lumpur', 'Kuala Lumpur, Malaysia'),
        ('Asia/Jakarta', 'Jakarta, Indonesia'),
        ('Asia/Hong_Kong', 'Hong Kong'),
        ('Asia/Shanghai', 'Shanghai, China'),
        ('Asia/Beijing', 'Beijing, China'),
        ('Asia/Taipei', 'Taipei, Taiwan'),
        ('Asia/Seoul', 'Seoul, South Korea'),
        ('Asia/Tokyo', 'Tokyo, Japan'),
        ('Asia/Ulaanbaatar', 'Ulaanbaatar, Mongolia'),
        ('Asia/Vladivostok', 'Vladivostok, Russia'),
        
        # Africa
        ('Africa/Cairo', 'Cairo, Egypt'),
        ('Africa/Johannesburg', 'Johannesburg, South Africa'),
        ('Africa/Lagos', 'Lagos, Nigeria'),
        ('Africa/Nairobi', 'Nairobi, Kenya'),
        ('Africa/Casablanca', 'Casablanca, Morocco'),
        ('Africa/Tunis', 'Tunis, Tunisia'),
        ('Africa/Algiers', 'Algiers, Algeria'),
        
        # Oceania
        ('Australia/Sydney', 'Sydney, Australia'),
        ('Australia/Melbourne', 'Melbourne, Australia'),
        ('Australia/Brisbane', 'Brisbane, Australia'),
        ('Australia/Perth', 'Perth, Australia'),
        ('Australia/Adelaide', 'Adelaide, Australia'),
        ('Australia/Darwin', 'Darwin, Australia'),
        ('Pacific/Auckland', 'Auckland, New Zealand'),
        ('Pacific/Fiji', 'Fiji'),
        ('Pacific/Honolulu', 'Honolulu, Hawaii'),
        ('Pacific/Guam', 'Guam'),
    ]
    
    context = {
        'result': result,
        'error': error,
        'timezones': all_timezones,
    }
    return render(request, 'utilities/timezone_converter.html', context)

def roman_numeral_converter(request):
    """Convert between Roman and Arabic numerals"""
    result = None
    error = None
    conversion_type = None
    
    if request.method == 'POST':
        conversion_type = request.POST.get('conversion_type', 'to_roman')
        input_value = request.POST.get('input_value', '').strip()
        
        if not input_value:
            error = 'Please enter a value'
        else:
            try:
                if conversion_type == 'to_roman':
                    # Convert Arabic to Roman
                    num = int(input_value)
                    if num < 1 or num > 3999:
                        error = 'Number must be between 1 and 3999'
                    else:
                        result = arabic_to_roman(num)
                else:
                    # Convert Roman to Arabic
                    result = roman_to_arabic(input_value.upper())
                    if result is None:
                        error = 'Invalid Roman numeral'
            except ValueError:
                error = 'Invalid input'
            except Exception as e:
                error = str(e)
    
    context = {
        'result': result,
        'error': error,
        'conversion_type': conversion_type or 'to_roman',
    }
    return render(request, 'utilities/roman_numeral_converter.html', context)

def arabic_to_roman(num):
    """Convert Arabic number to Roman numeral"""
    val = [
        1000, 900, 500, 400,
        100, 90, 50, 40,
        10, 9, 5, 4,
        1
    ]
    syb = [
        "M", "CM", "D", "CD",
        "C", "XC", "L", "XL",
        "X", "IX", "V", "IV",
        "I"
    ]
    roman_num = ''
    i = 0
    while num > 0:
        for _ in range(num // val[i]):
            roman_num += syb[i]
            num -= val[i]
        i += 1
    return roman_num

def roman_to_arabic(roman):
    """Convert Roman numeral to Arabic number"""
    roman_numerals = {
        'I': 1, 'V': 5, 'X': 10, 'L': 50,
        'C': 100, 'D': 500, 'M': 1000
    }
    
    result = 0
    prev_value = 0
    
    for char in reversed(roman):
        if char not in roman_numerals:
            return None
        value = roman_numerals[char]
        if value < prev_value:
            result -= value
        else:
            result += value
        prev_value = value
    
    return result

def favicon_generator(request):
    """Generate favicon from image"""
    if request.method != 'POST':
        return render(request, 'utilities/favicon_generator.html')
    
    if 'image_file' not in request.FILES:
        messages.error(request, 'Please upload an image file.')
        return render(request, 'utilities/favicon_generator.html')
    
    image_file = request.FILES['image_file']
    
    # Validate file size (max 10MB for favicon images)
    max_size = 10 * 1024 * 1024  # 10MB
    if image_file.size > max_size:
        messages.error(request, f'File size exceeds 10MB limit. Your file is {image_file.size / (1024 * 1024):.1f}MB.')
        return render(request, 'utilities/favicon_generator.html')
    
    # Check if it's an image
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    if not any(image_file.name.lower().endswith(ext) for ext in allowed_extensions):
        messages.error(request, 'Please upload a valid image file (JPG, PNG, GIF, BMP, or WebP).')
        return render(request, 'utilities/favicon_generator.html')
    
    try:
        # Open and process image
        img = Image.open(image_file)
        
        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Get original dimensions
        original_width, original_height = img.size
        
        # Calculate new dimensions maintaining aspect ratio
        target_size = 32
        if original_width > original_height:
            # Landscape or square
            new_width = target_size
            new_height = int(original_height * (target_size / original_width))
        else:
            # Portrait
            new_height = target_size
            new_width = int(original_width * (target_size / original_height))
        
        # Resize maintaining aspect ratio
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Create a square canvas with transparent/white background
        # Center the image on the canvas
        canvas = Image.new('RGB', (target_size, target_size), (255, 255, 255))
        
        # Calculate position to center the image
        x_offset = (target_size - new_width) // 2
        y_offset = (target_size - new_height) // 2
        
        # Paste the resized image onto the canvas
        canvas.paste(img, (x_offset, y_offset))
        
        # Save as ICO format
        ico_buffer = io.BytesIO()
        canvas.save(ico_buffer, format='ICO', sizes=[(32, 32)])
        ico_buffer.seek(0)
        
        # Return ICO file
        response = HttpResponse(ico_buffer.read(), content_type='image/x-icon')
        response['Content-Disposition'] = 'attachment; filename="favicon.ico"'
        return response
        
    except Exception as e:
        messages.error(request, f'Error generating favicon: {str(e)}')
        return render(request, 'utilities/favicon_generator.html')
