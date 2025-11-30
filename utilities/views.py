from django.shortcuts import render
from django.http import HttpResponse
from django.contrib import messages
import re
import io
import random
from datetime import datetime
import pytz
from PIL import Image
try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

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
            {'name': 'Timestamp Converter', 'url_name': 'timestamp_converter', 'description': 'Convert between timestamps and dates'},
            {'name': 'Text-to-Speech', 'url_name': 'text_to_speech', 'description': 'Convert text to speech audio'},
            {'name': 'Random Number Generator', 'url_name': 'random_number_generator', 'description': 'Generate random numbers'},
            {'name': 'Lorem Ipsum Generator', 'url_name': 'lorem_ipsum_generator', 'description': 'Generate Lorem Ipsum placeholder text'},
            {'name': 'Random Word Generator', 'url_name': 'random_word_generator', 'description': 'Generate random words from a dictionary'},
            {'name': 'Random Name Generator', 'url_name': 'random_name_generator', 'description': 'Generate random names from different regions'},
            {'name': 'Word Lottery', 'url_name': 'word_lottery', 'description': 'Pick a random word or name from your list'},
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

def timestamp_converter(request):
    """Convert between timestamps and dates"""
    result = None
    error = None
    conversion_type = None
    
    if request.method == 'POST':
        conversion_type = request.POST.get('conversion_type', 'timestamp_to_date')
        input_value = request.POST.get('input_value', '').strip()
        
        if not input_value:
            error = 'Please enter a value'
        else:
            try:
                if conversion_type == 'timestamp_to_date':
                    # Convert timestamp to date
                    try:
                        # Try as seconds (Unix timestamp)
                        timestamp = float(input_value)
                        if timestamp > 1e12:
                            # Milliseconds timestamp
                            timestamp = timestamp / 1000
                        dt = datetime.fromtimestamp(timestamp, tz=pytz.UTC)
                        result = {
                            'type': 'date',
                            'utc': dt.strftime('%Y-%m-%d %H:%M:%S UTC'),
                            'local': dt.astimezone().strftime('%Y-%m-%d %H:%M:%S %Z'),
                            'iso': dt.isoformat(),
                        }
                    except (ValueError, OSError) as e:
                        error = f'Invalid timestamp: {str(e)}'
                else:
                    # Convert date to timestamp
                    try:
                        # Try different date formats
                        date_formats = [
                            '%Y-%m-%d %H:%M:%S',
                            '%Y-%m-%d %H:%M',
                            '%Y-%m-%d',
                            '%d/%m/%Y %H:%M:%S',
                            '%d/%m/%Y %H:%M',
                            '%d/%m/%Y',
                            '%m/%d/%Y %H:%M:%S',
                            '%m/%d/%Y %H:%M',
                            '%m/%d/%Y',
                        ]
                        dt = None
                        for fmt in date_formats:
                            try:
                                dt = datetime.strptime(input_value, fmt)
                                break
                            except ValueError:
                                continue
                        
                        if dt is None:
                            error = 'Invalid date format. Try: YYYY-MM-DD HH:MM:SS'
                        else:
                            # Make timezone-aware (assume UTC if not specified)
                            if dt.tzinfo is None:
                                dt = pytz.UTC.localize(dt)
                            
                            timestamp_seconds = dt.timestamp()
                            timestamp_milliseconds = int(timestamp_seconds * 1000)
                            
                            result = {
                                'type': 'timestamp',
                                'seconds': int(timestamp_seconds),
                                'milliseconds': timestamp_milliseconds,
                            }
                    except Exception as e:
                        error = f'Error converting date: {str(e)}'
            except Exception as e:
                error = str(e)
    
    context = {
        'result': result,
        'error': error,
        'conversion_type': conversion_type or 'timestamp_to_date',
    }
    return render(request, 'utilities/timestamp_converter.html', context)

def text_to_speech(request):
    """Convert text to speech"""
    if request.method != 'POST':
        return render(request, 'utilities/text_to_speech.html', {'gtts_available': GTTS_AVAILABLE})
    
    if not GTTS_AVAILABLE:
        messages.error(request, 'Text-to-speech requires gTTS library. Install with: pip install gtts')
        return render(request, 'utilities/text_to_speech.html', {'gtts_available': False})
    
    text = request.POST.get('text', '').strip()
    language = request.POST.get('language', 'en')
    
    if not text:
        messages.error(request, 'Please enter text to convert to speech.')
        return render(request, 'utilities/text_to_speech.html', {'gtts_available': GTTS_AVAILABLE})
    
    if len(text) > 5000:
        messages.error(request, 'Text is too long. Maximum 5000 characters allowed.')
        return render(request, 'utilities/text_to_speech.html', {'gtts_available': GTTS_AVAILABLE})
    
    try:
        # Create text-to-speech
        tts = gTTS(text=text, lang=language, slow=False)
        
        # Save to bytes
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        # Return audio file
        response = HttpResponse(audio_buffer.read(), content_type='audio/mpeg')
        response['Content-Disposition'] = 'attachment; filename="speech.mp3"'
        return response
        
    except Exception as e:
        messages.error(request, f'Error generating speech: {str(e)}')
        return render(request, 'utilities/text_to_speech.html', {'gtts_available': GTTS_AVAILABLE})

def random_number_generator(request):
    """Generate random numbers"""
    result = None
    error = None
    
    if request.method == 'POST':
        try:
            min_val = int(request.POST.get('min_value', '1'))
            max_val = int(request.POST.get('max_value', '100'))
            count = int(request.POST.get('count', '1'))
            allow_duplicates = request.POST.get('allow_duplicates', 'off') == 'on'
            
            if min_val > max_val:
                error = 'Minimum value must be less than or equal to maximum value'
            elif count < 1:
                error = 'Count must be at least 1'
            elif count > 1000:
                error = 'Count cannot exceed 1000'
            elif not allow_duplicates and count > (max_val - min_val + 1):
                error = f'Cannot generate {count} unique numbers in range {min_val}-{max_val}'
            else:
                if allow_duplicates:
                    # Allow duplicates
                    numbers = [random.randint(min_val, max_val) for _ in range(count)]
                else:
                    # No duplicates
                    numbers = random.sample(range(min_val, max_val + 1), min(count, max_val - min_val + 1))
                
                result = {
                    'numbers': numbers,
                    'count': len(numbers),
                    'min': min_val,
                    'max': max_val,
                    'sum': sum(numbers),
                    'average': sum(numbers) / len(numbers) if numbers else 0,
                }
        except ValueError:
            error = 'Please enter valid numbers'
        except Exception as e:
            error = str(e)
    
    context = {
        'result': result,
        'error': error,
    }
    return render(request, 'utilities/random_number_generator.html', context)

def lorem_ipsum_generator(request):
    """Generate Lorem Ipsum text"""
    result = None
    error = None
    
    if request.method == 'POST':
        try:
            text_type = request.POST.get('text_type', 'paragraphs')
            count = int(request.POST.get('count', '3'))
            
            if count < 1:
                error = 'Count must be at least 1'
            elif count > 100:
                error = 'Count cannot exceed 100'
            else:
                lorem_words = [
                    'lorem', 'ipsum', 'dolor', 'sit', 'amet', 'consectetur', 'adipiscing', 'elit',
                    'sed', 'do', 'eiusmod', 'tempor', 'incididunt', 'ut', 'labore', 'et', 'dolore',
                    'magna', 'aliqua', 'enim', 'ad', 'minim', 'veniam', 'quis', 'nostrud',
                    'exercitation', 'ullamco', 'laboris', 'nisi', 'aliquip', 'ex', 'ea', 'commodo',
                    'consequat', 'duis', 'aute', 'irure', 'in', 'reprehenderit', 'voluptate',
                    'velit', 'esse', 'cillum', 'fugiat', 'nulla', 'pariatur', 'excepteur', 'sint',
                    'occaecat', 'cupidatat', 'non', 'proident', 'sunt', 'culpa', 'qui', 'officia',
                    'deserunt', 'mollit', 'anim', 'id', 'est', 'laborum'
                ]
                
                if text_type == 'paragraphs':
                    paragraphs = []
                    for _ in range(count):
                        # Generate 3-5 sentences per paragraph
                        sentences = []
                        for _ in range(random.randint(3, 5)):
                            # Generate 8-15 words per sentence
                            words = random.sample(lorem_words, random.randint(8, min(15, len(lorem_words))))
                            sentence = ' '.join(words).capitalize() + '.'
                            sentences.append(sentence)
                        paragraphs.append(' '.join(sentences))
                    result = '\n\n'.join(paragraphs)
                elif text_type == 'words':
                    words = random.choices(lorem_words, k=count)
                    result = ' '.join(words)
                elif text_type == 'sentences':
                    sentences = []
                    for _ in range(count):
                        words = random.sample(lorem_words, random.randint(8, min(15, len(lorem_words))))
                        sentence = ' '.join(words).capitalize() + '.'
                        sentences.append(sentence)
                    result = ' '.join(sentences)
                else:
                    error = 'Invalid text type'
        except ValueError:
            error = 'Please enter a valid number'
        except Exception as e:
            error = str(e)
    
    context = {
        'result': result,
        'error': error,
    }
    return render(request, 'utilities/lorem_ipsum_generator.html', context)

def random_word_generator(request):
    """Generate random words"""
    result = None
    error = None
    
    # Common English words dictionary
    word_list = [
        'apple', 'banana', 'car', 'dog', 'elephant', 'flower', 'guitar', 'house', 'island', 'jungle',
        'kite', 'lion', 'mountain', 'ocean', 'piano', 'queen', 'river', 'sun', 'tree', 'umbrella',
        'violin', 'water', 'xylophone', 'yacht', 'zebra', 'adventure', 'beautiful', 'courage', 'dream',
        'energy', 'freedom', 'garden', 'happiness', 'imagine', 'journey', 'kindness', 'laughter', 'magic',
        'nature', 'ocean', 'peace', 'quiet', 'rainbow', 'sunshine', 'travel', 'universe', 'victory',
        'wisdom', 'youth', 'zeal', 'art', 'book', 'cloud', 'dance', 'earth', 'fire', 'grace',
        'hope', 'ice', 'joy', 'kiss', 'light', 'music', 'night', 'ocean', 'peace', 'quest',
        'rain', 'star', 'time', 'unity', 'voice', 'wind', 'xenon', 'year', 'zenith', 'action',
        'brave', 'calm', 'daring', 'eager', 'faith', 'gentle', 'honest', 'ideal', 'jolly', 'keen',
        'loyal', 'mighty', 'noble', 'optimistic', 'proud', 'quick', 'radiant', 'strong', 'true', 'unique',
        'vital', 'wise', 'young', 'zealous', 'amazing', 'brilliant', 'creative', 'dynamic', 'excellent',
        'fantastic', 'glorious', 'heroic', 'incredible', 'joyful', 'kind', 'lovely', 'magnificent', 'noble',
        'outstanding', 'perfect', 'remarkable', 'splendid', 'terrific', 'unbelievable', 'wonderful', 'extraordinary',
        'zestful', 'achieve', 'believe', 'create', 'discover', 'explore', 'flourish', 'grow', 'inspire',
        'journey', 'kindle', 'learn', 'master', 'nurture', 'overcome', 'progress', 'quest', 'reach',
        'succeed', 'thrive', 'unite', 'venture', 'wonder', 'excel', 'yearn', 'zoom', 'abundant', 'bright',
        'colorful', 'diverse', 'elegant', 'fragrant', 'glowing', 'harmonious', 'inspiring', 'jubilant',
        'kaleidoscopic', 'luminous', 'majestic', 'nostalgic', 'optimistic', 'peaceful', 'quaint', 'radiant',
        'serene', 'tranquil', 'uplifting', 'vibrant', 'whimsical', 'exquisite', 'youthful', 'zestful'
    ]
    
    if request.method == 'POST':
        try:
            count = int(request.POST.get('count', '5'))
            min_length = request.POST.get('min_length', '').strip()
            max_length = request.POST.get('max_length', '').strip()
            starts_with = request.POST.get('starts_with', '').strip().lower()
            
            if count < 1:
                error = 'Count must be at least 1'
            elif count > 100:
                error = 'Count cannot exceed 100'
            else:
                # Filter words based on criteria
                filtered_words = word_list.copy()
                
                # Filter by minimum length
                if min_length:
                    min_len = int(min_length)
                    if min_len < 1:
                        error = 'Minimum length must be at least 1'
                    else:
                        filtered_words = [w for w in filtered_words if len(w) >= min_len]
                
                # Filter by maximum length
                if max_length and not error:
                    max_len = int(max_length)
                    if max_len < 1:
                        error = 'Maximum length must be at least 1'
                    elif min_length and max_len < int(min_length):
                        error = 'Maximum length must be greater than or equal to minimum length'
                    else:
                        filtered_words = [w for w in filtered_words if len(w) <= max_len]
                
                # Filter by starting letter
                if starts_with and not error:
                    if len(starts_with) != 1 or not starts_with.isalpha():
                        error = 'Starting letter must be a single alphabet character'
                    else:
                        filtered_words = [w for w in filtered_words if w.startswith(starts_with)]
                
                if not error:
                    if not filtered_words:
                        error = 'No words match the specified criteria. Try adjusting your filters.'
                    elif count > len(filtered_words):
                        # If requesting more words than available, use all available
                        words = random.sample(filtered_words, len(filtered_words))
                        result = {
                            'words': words,
                            'count': len(words),
                            'requested': count,
                            'note': f'Only {len(words)} words available matching your criteria'
                        }
                    else:
                        words = random.sample(filtered_words, count)
                        result = {
                            'words': words,
                            'count': len(words),
                            'requested': count,
                        }
        except ValueError:
            error = 'Please enter valid numbers'
        except Exception as e:
            error = str(e)
    
    context = {
        'result': result,
        'error': error,
    }
    return render(request, 'utilities/random_word_generator.html', context)

def random_name_generator(request):
    """Generate random names from different regions"""
    result = None
    error = None
    
    # Name databases organized by region and gender
    name_databases = {
        'european': {
            'male_first': [
                'Alexander', 'Andreas', 'Anton', 'Bjorn', 'Christoph', 'Dimitri', 'Erik', 'Felix',
                'Franz', 'Georg', 'Hans', 'Henrik', 'Ivan', 'Jakob', 'Klaus', 'Lars', 'Magnus',
                'Matthias', 'Nikolai', 'Oliver', 'Pavel', 'Rafael', 'Sebastian', 'Stefan',
                'Thomas', 'Ulrich', 'Viktor', 'Wolfgang', 'Yannick', 'Zoran', 'Adrian', 'Boris',
                'Christian', 'Daniel', 'Emil', 'Fabian', 'Gabriel', 'Hugo', 'Igor', 'Jan',
                'Konstantin', 'Leon', 'Marcel', 'Nicolas', 'Oscar', 'Patrick', 'Quentin', 'Roman',
                'Simon', 'Tobias', 'Uwe', 'Valentin', 'Werner', 'Xavier', 'Yves', 'Zachary'
            ],
            'female_first': [
                'Anna', 'Beatrice', 'Catherine', 'Diana', 'Elena', 'Franziska', 'Gabriela', 'Helena',
                'Isabella', 'Julia', 'Katarina', 'Laura', 'Maria', 'Natalia', 'Olivia', 'Petra',
                'Rosa', 'Sofia', 'Tatiana', 'Ulrike', 'Valentina', 'Wendy', 'Xenia', 'Yvonne',
                'Zara', 'Adriana', 'Bianca', 'Clara', 'Daria', 'Elisabeth', 'Fiona', 'Greta',
                'Hannah', 'Irina', 'Jana', 'Klara', 'Lena', 'Marta', 'Nina', 'Oksana',
                'Patricia', 'Renata', 'Sara', 'Teresa', 'Ursula', 'Vera', 'Wanda', 'Yara', 'Zoe'
            ],
            'last': [
                'Andersen', 'Berg', 'Berger', 'Bjork', 'Borg', 'Braun', 'Christensen', 'Eriksson',
                'Fischer', 'Garcia', 'Hansen', 'Hoffmann', 'Jensen', 'Klein', 'Kovac', 'Larsen',
                'Muller', 'Nielsen', 'Olsen', 'Petrov', 'Rasmussen', 'Schmidt', 'Svensson',
                'Wagner', 'Weber', 'Andersson', 'Bergmann', 'Carlsson', 'Dahl', 'Eriksen',
                'Forsberg', 'Gustafsson', 'Holm', 'Johansson', 'Karlsson', 'Lindberg', 'Martinez',
                'Nilsson', 'Petersen', 'Sandberg', 'Viktor', 'Zimmermann', 'Albrecht', 'Bauer',
                'Carter', 'Dvorak', 'Engel', 'Friedrich', 'Gruber', 'Hartmann', 'Ivanov',
                'Jankovic', 'Keller', 'Lehmann', 'Meyer', 'Novak', 'Peters', 'Richter', 'Stein'
            ]
        },
        'english': {
            'male_first': [
                'James', 'William', 'John', 'George', 'Charles', 'Thomas', 'Henry', 'Edward',
                'Robert', 'Richard', 'David', 'Michael', 'Christopher', 'Daniel', 'Matthew',
                'Andrew', 'Joseph', 'Mark', 'Peter', 'Paul', 'Steven', 'Anthony', 'Kenneth',
                'Brian', 'Kevin', 'Stephen', 'Gary', 'Eric', 'Jonathan', 'Ryan', 'Jacob',
                'Nicholas', 'Benjamin', 'Samuel', 'Adam', 'Nathan', 'Luke', 'Oliver', 'Jack',
                'Harry', 'Oscar', 'Arthur', 'Noah', 'Leo', 'Theo', 'Freddie', 'Archie', 'Joshua'
            ],
            'female_first': [
                'Mary', 'Elizabeth', 'Sarah', 'Margaret', 'Anne', 'Jane', 'Catherine', 'Emma',
                'Olivia', 'Sophia', 'Isabella', 'Charlotte', 'Amelia', 'Mia', 'Harper', 'Evelyn',
                'Abigail', 'Emily', 'Ella', 'Scarlett', 'Grace', 'Chloe', 'Victoria', 'Rebecca',
                'Lucy', 'Anna', 'Alice', 'Lily', 'Freya', 'Ivy', 'Florence', 'Rosie', 'Matilda',
                'Phoebe', 'Isla', 'Poppy', 'Elsie', 'Lottie', 'Maya', 'Sienna', 'Willow', 'Ava'
            ],
            'last': [
                'Smith', 'Jones', 'Taylor', 'Williams', 'Brown', 'Davies', 'Evans', 'Wilson',
                'Thomas', 'Roberts', 'Johnson', 'Lewis', 'Walker', 'Robinson', 'Wood', 'Thompson',
                'White', 'Watson', 'Jackson', 'Wright', 'Green', 'Harris', 'Cooper', 'King',
                'Lee', 'Martin', 'Clarke', 'James', 'Morgan', 'Hughes', 'Edwards', 'Hill',
                'Moore', 'Clark', 'Harrison', 'Scott', 'Young', 'Morris', 'Hall', 'Ward',
                'Turner', 'Carter', 'Phillips', 'Mitchell', 'Patel', 'Adams', 'Campbell', 'Anderson'
            ]
        },
        'usa': {
            'male_first': [
                'Michael', 'James', 'Robert', 'John', 'William', 'David', 'Richard', 'Joseph',
                'Thomas', 'Charles', 'Christopher', 'Daniel', 'Matthew', 'Anthony', 'Mark',
                'Donald', 'Steven', 'Paul', 'Andrew', 'Joshua', 'Kenneth', 'Kevin', 'Brian',
                'George', 'Timothy', 'Ronald', 'Jason', 'Edward', 'Jeffrey', 'Ryan', 'Jacob',
                'Gary', 'Nicholas', 'Eric', 'Jonathan', 'Stephen', 'Larry', 'Justin', 'Scott',
                'Brandon', 'Benjamin', 'Samuel', 'Frank', 'Gregory', 'Raymond', 'Alexander',
                'Patrick', 'Jack', 'Dennis', 'Jerry', 'Tyler', 'Aaron', 'Jose', 'Adam', 'Nathan'
            ],
            'female_first': [
                'Mary', 'Patricia', 'Jennifer', 'Linda', 'Elizabeth', 'Barbara', 'Susan', 'Jessica',
                'Sarah', 'Karen', 'Nancy', 'Lisa', 'Betty', 'Margaret', 'Sandra', 'Ashley',
                'Kimberly', 'Emily', 'Donna', 'Michelle', 'Dorothy', 'Carol', 'Amanda', 'Melissa',
                'Deborah', 'Stephanie', 'Rebecca', 'Sharon', 'Laura', 'Cynthia', 'Kathleen',
                'Amy', 'Angela', 'Shirley', 'Anna', 'Brenda', 'Pamela', 'Emma', 'Nicole',
                'Helen', 'Samantha', 'Olivia', 'Catherine', 'Christine', 'Samantha', 'Debra',
                'Rachel', 'Carolyn', 'Janet', 'Virginia', 'Maria', 'Heather', 'Diane', 'Julie'
            ],
            'last': [
                'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
                'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Wilson', 'Anderson', 'Thomas',
                'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Thompson', 'White', 'Harris',
                'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson', 'Walker', 'Young', 'Allen',
                'King', 'Wright', 'Scott', 'Torres', 'Nguyen', 'Hill', 'Flores', 'Green',
                'Adams', 'Nelson', 'Baker', 'Hall', 'Rivera', 'Campbell', 'Mitchell', 'Carter',
                'Roberts', 'Gomez', 'Phillips', 'Evans', 'Turner', 'Diaz', 'Parker', 'Cruz'
            ]
        },
        'spanish': {
            'male_first': [
                'Alejandro', 'Carlos', 'Diego', 'Fernando', 'Gabriel', 'Hector', 'Ignacio', 'Javier',
                'Jose', 'Luis', 'Manuel', 'Miguel', 'Nicolas', 'Oscar', 'Pablo', 'Rafael',
                'Ricardo', 'Santiago', 'Tomas', 'Victor', 'Adrian', 'Alberto', 'Andres', 'Antonio',
                'Arturo', 'Benjamin', 'Cesar', 'Daniel', 'Eduardo', 'Enrique', 'Esteban', 'Felipe',
                'Francisco', 'Gonzalo', 'Guillermo', 'Hugo', 'Ivan', 'Jorge', 'Juan', 'Leonardo',
                'Mario', 'Martin', 'Mateo', 'Mauricio', 'Nestor', 'Octavio', 'Pedro', 'Ramon',
                'Raul', 'Roberto', 'Rodrigo', 'Sebastian', 'Sergio', 'Valentin', 'Xavier'
            ],
            'female_first': [
                'Maria', 'Carmen', 'Isabel', 'Ana', 'Laura', 'Patricia', 'Guadalupe', 'Rosa',
                'Andrea', 'Monica', 'Sofia', 'Elena', 'Lucia', 'Paula', 'Marta', 'Cristina',
                'Beatriz', 'Diana', 'Fernanda', 'Gabriela', 'Alejandra', 'Valentina', 'Camila',
                'Isabella', 'Valeria', 'Natalia', 'Daniela', 'Mariana', 'Carolina', 'Adriana',
                'Elena', 'Claudia', 'Silvia', 'Raquel', 'Pilar', 'Dolores', 'Mercedes', 'Dolores',
                'Esperanza', 'Consuelo', 'Soledad', 'Amparo', 'Milagros', 'Rocio', 'Paloma',
                'Ines', 'Teresa', 'Angela', 'Catalina', 'Jimena', 'Ximena', 'Renata', 'Regina'
            ],
            'last': [
                'Garcia', 'Rodriguez', 'Gonzalez', 'Fernandez', 'Lopez', 'Martinez', 'Sanchez',
                'Perez', 'Gomez', 'Martin', 'Jimenez', 'Ruiz', 'Hernandez', 'Diaz', 'Moreno',
                'Alvarez', 'Munoz', 'Romero', 'Alonso', 'Gutierrez', 'Navarro', 'Torres', 'Dominguez',
                'Vazquez', 'Ramos', 'Gil', 'Ramirez', 'Serrano', 'Blanco', 'Suarez', 'Molina',
                'Morales', 'Ortega', 'Delgado', 'Castro', 'Ortiz', 'Rubio', 'Marin', 'Sanz',
                'Nunez', 'Iglesias', 'Medina', 'Garrido', 'Cortes', 'Castillo', 'Lozano', 'Guerrero',
                'Cano', 'Prieto', 'Mendez', 'Calvo', 'Cruz', 'Gallego', 'Vidal', 'Leon', 'Herrera'
            ]
        }
    }
    
    if request.method == 'POST':
        try:
            count = int(request.POST.get('count', '5'))
            name_type = request.POST.get('name_type', 'full')  # full, first_only, last_only
            gender = request.POST.get('gender', 'any')  # any, male, female
            regions = request.POST.getlist('regions')  # Can select multiple
            
            if count < 1:
                error = 'Count must be at least 1'
            elif count > 100:
                error = 'Count cannot exceed 100'
            elif not regions:
                error = 'Please select at least one region'
            else:
                # Collect names from selected regions
                all_male_first = []
                all_female_first = []
                all_last = []
                
                for region in regions:
                    if region in name_databases:
                        all_male_first.extend(name_databases[region]['male_first'])
                        all_female_first.extend(name_databases[region]['female_first'])
                        all_last.extend(name_databases[region]['last'])
                
                # Remove duplicates while preserving order
                all_male_first = list(dict.fromkeys(all_male_first))
                all_female_first = list(dict.fromkeys(all_female_first))
                all_last = list(dict.fromkeys(all_last))
                
                if not all_male_first or not all_female_first or not all_last:
                    error = 'No names available for selected regions'
                else:
                    generated_names = []
                    
                    for _ in range(count):
                        # Determine gender
                        if gender == 'male':
                            first_name_pool = all_male_first
                        elif gender == 'female':
                            first_name_pool = all_female_first
                        else:  # any
                            first_name_pool = random.choice([all_male_first, all_female_first])
                        
                        first_name = random.choice(first_name_pool)
                        last_name = random.choice(all_last)
                        
                        if name_type == 'full':
                            generated_names.append(f"{first_name} {last_name}")
                        elif name_type == 'first_only':
                            generated_names.append(first_name)
                        else:  # last_only
                            generated_names.append(last_name)
                    
                    result = {
                        'names': generated_names,
                        'count': len(generated_names),
                        'name_type': name_type,
                        'gender': gender,
                        'regions': regions,
                    }
        except ValueError:
            error = 'Please enter valid numbers'
        except Exception as e:
            error = str(e)
    
    context = {
        'result': result,
        'error': error,
    }
    return render(request, 'utilities/random_name_generator.html', context)

def word_lottery(request):
    """Word lottery - pick a random word/name from user's list"""
    result = None
    error = None
    input_text = ''
    
    if request.method == 'POST':
        try:
            input_text = request.POST.get('words', '').strip()
            input_format = request.POST.get('input_format', 'lines')  # lines or commas
            
            if not input_text:
                error = 'Please enter at least one word or name'
            else:
                # Parse input based on format
                if input_format == 'lines':
                    # Split by newlines
                    words = [line.strip() for line in input_text.split('\n') if line.strip()]
                else:  # commas
                    # Split by commas
                    words = [word.strip() for word in input_text.split(',') if word.strip()]
                
                # Remove duplicates while preserving order
                words = list(dict.fromkeys(words))
                
                if not words:
                    error = 'No valid words found. Please enter at least one word or name.'
                elif len(words) > 100:
                    error = f'Too many entries! You entered {len(words)} words. Maximum is 100.'
                else:
                    # Pick a random word
                    winner = random.choice(words)
                    
                    result = {
                        'winner': winner,
                        'total_entries': len(words),
                        'all_entries': words,
                    }
        except Exception as e:
            error = f'Error: {str(e)}'
    
    context = {
        'result': result,
        'error': error,
        'input_text': input_text,
    }
    return render(request, 'utilities/word_lottery.html', context)
