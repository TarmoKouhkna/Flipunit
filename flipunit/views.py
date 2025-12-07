from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
import os
from .models import Feedback

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def home(request):
    """Home page"""
    if request.method == 'POST' and 'feedback' in request.POST:
        feedback_text = request.POST.get('feedback', '').strip()
        if feedback_text:
            # Validate length (1000 characters max)
            if len(feedback_text) > 1000:
                messages.error(request, 'Feedback is too long. Maximum 1000 characters allowed.')
            else:
                # Save feedback to database
                Feedback.objects.create(
                    message=feedback_text,
                    ip_address=get_client_ip(request)
                )
                # No success message - just redirect to prevent form resubmission
        # Always redirect after POST to prevent form resubmission on refresh (PRG pattern)
        return HttpResponseRedirect(reverse('home'))
    
    context = {
        'categories': [
            {
                'name': 'Color Code Generator & Picker',
                'url': 'color_picker:index',
                'description': 'Pick colors from screen, convert between color formats, and generate color codes',
                'icon': 'color-picker.svg'
            },
            {
                'name': 'Image Conversion & Editing',
                'url': 'image_converter:index',
                'description': 'Convert images between different formats and edit them',
                'icon': 'image-converters.svg'
            },
            {
                'name': 'Media Converters',
                'url': 'media_converter:index',
                'description': 'Convert media files and download audio.',
                'icon': 'media-converters.svg'
            },
            {
                'name': 'PDF Tools',
                'url': 'pdf_tools:index',
                'description': 'Merge, split, and convert PDF files',
                'icon': 'pdf-tools.svg'
            },
            {
                'name': 'Unit Converters',
                'url': 'converters:index',
                'description': 'Convert between different units of measurement',
                'icon': 'unit-converters.svg'
            },
            {
                'name': 'Utilities',
                'url': 'utilities:index',
                'description': 'Calculator, converters, generators, QR codes, text-to-speech, and more',
                'icon': 'utilities.svg'
            },
            {
                'name': 'Currency & Crypto',
                'url': 'currency_converter:index',
                'description': 'Convert between currencies and cryptocurrencies with real-time rates',
                'icon': 'currency-crypto.svg'
            },
            {
                'name': 'Archive Converters',
                'url': 'archive_converter:index',
                'description': 'Convert between ZIP, RAR, 7Z, and TAR.GZ formats. Extract ISO files.',
                'icon': 'archive-converters.svg'
            },
            {
                'name': 'Text & String Converters',
                'url': 'text_converter:index',
                'description': 'Convert text between formats: uppercase/lowercase, CamelCase/snake_case, JSON/XML/YAML, HTML/Markdown, Base64, and more',
                'icon': 'text-converters.svg'
            },
            {
                'name': 'Developer Converters',
                'url': 'developer_converter:index',
                'description': 'Developer tools: minify/unminify code, CSV/JSON conversion, SQL formatter, regex tester, JWT decoder, and more',
                'icon': 'developer-converters.svg'
            },
        ]
    }
    return render(request, 'home.html', context)


def _get_all_tools():
    """Build a comprehensive list of all tools and converters for search"""
    tools = []
    
    # Categories (main pages)
    categories = [
        {'name': 'Color Code Generator & Picker', 'url': 'color_picker:index', 'category': 'Color Picker', 'description': 'Pick colors from screen, convert between color formats, and generate color codes'},
        {'name': 'Image Conversion & Editing', 'url': 'image_converter:index', 'category': 'Image Converters', 'description': 'Convert images between different formats and edit them'},
        {'name': 'Media Converters', 'url': 'media_converter:index', 'category': 'Media Converters', 'description': 'Convert media files and download audio'},
        {'name': 'PDF Tools', 'url': 'pdf_tools:index', 'category': 'PDF Tools', 'description': 'Merge, split, and convert PDF files'},
        {'name': 'Unit Converters', 'url': 'converters:index', 'category': 'Unit Converters', 'description': 'Convert between different units of measurement'},
        {'name': 'Utilities', 'url': 'utilities:index', 'category': 'Utilities', 'description': 'Calculators, text utilities, QR codes and more'},
        {'name': 'Currency & Crypto', 'url': 'currency_converter:index', 'category': 'Currency & Crypto', 'description': 'Convert between currencies and cryptocurrencies with real-time rates'},
        {'name': 'Archive Converters', 'url': 'archive_converter:index', 'category': 'Archive Converters', 'description': 'Convert between ZIP, RAR, 7Z, and TAR.GZ formats'},
        {'name': 'Text & String Converters', 'url': 'text_converter:index', 'category': 'Text Converters', 'description': 'Convert text between formats'},
        {'name': 'Developer Converters', 'url': 'developer_converter:index', 'category': 'Developer Converters', 'description': 'Developer tools and code utilities'},
    ]
    tools.extend(categories)
    
    # Color Picker tools
    tools.extend([
        {'name': 'Color Picker', 'url': 'color_picker:picker', 'category': 'Color Picker', 'description': 'Pick colors from screen'},
        {'name': 'Pick Color from Image', 'url': 'color_picker:pick_from_image', 'category': 'Color Picker', 'description': 'Extract colors from images'},
    ])
    
    # Unit Converters
    tools.extend([
        {'name': 'Length Converter', 'url': ('converters:tool', 'length'), 'category': 'Unit Converters', 'description': 'Convert between meters, feet, inches, and more'},
        {'name': 'Weight Converter', 'url': ('converters:tool', 'weight'), 'category': 'Unit Converters', 'description': 'Convert between kilograms, pounds, ounces, and more'},
        {'name': 'Temperature Converter', 'url': ('converters:tool', 'temperature'), 'category': 'Unit Converters', 'description': 'Convert between Celsius, Fahrenheit, and Kelvin'},
        {'name': 'Volume Converter', 'url': ('converters:tool', 'volume'), 'category': 'Unit Converters', 'description': 'Convert between liters, gallons, cups, and more'},
        {'name': 'Area Converter', 'url': ('converters:tool', 'area'), 'category': 'Unit Converters', 'description': 'Convert between square meters, square feet, acres, and more'},
        {'name': 'Speed Converter', 'url': ('converters:tool', 'speed'), 'category': 'Unit Converters', 'description': 'Convert between km/h, mph, m/s, and more'},
    ])
    
    # Image Converters
    tools.extend([
        {'name': 'Universal Image Converter', 'url': 'image_converter:universal', 'category': 'Image Converters', 'description': 'Convert images to any format'},
        {'name': 'JPEG to PNG', 'url': ('image_converter:convert', 'jpeg-to-png'), 'category': 'Image Converters', 'description': 'Convert JPEG images to PNG'},
        {'name': 'PNG to JPG', 'url': ('image_converter:convert', 'png-to-jpg'), 'category': 'Image Converters', 'description': 'Convert PNG images to JPG'},
        {'name': 'Image Resizer', 'url': 'image_converter:resize', 'category': 'Image Converters', 'description': 'Resize images to custom dimensions'},
        {'name': 'Rotate & Flip', 'url': 'image_converter:rotate_flip', 'category': 'Image Converters', 'description': 'Rotate or flip images'},
        {'name': 'Remove EXIF', 'url': 'image_converter:remove_exif', 'category': 'Image Converters', 'description': 'Remove EXIF metadata from images'},
        {'name': 'Grayscale', 'url': 'image_converter:grayscale', 'category': 'Image Converters', 'description': 'Convert images to grayscale'},
        {'name': 'Merge Images', 'url': 'image_converter:merge', 'category': 'Image Converters', 'description': 'Merge multiple images'},
        {'name': 'Watermark', 'url': 'image_converter:watermark', 'category': 'Image Converters', 'description': 'Add watermark to images'},
    ])
    
    # Media Converters
    tools.extend([
        {'name': 'Audio Converter', 'url': 'media_converter:audio_converter', 'category': 'Media Converters', 'description': 'Convert between audio formats'},
        {'name': 'Video Converter', 'url': 'media_converter:video_converter', 'category': 'Media Converters', 'description': 'Convert between video formats'},
        {'name': 'MP4 to MP3', 'url': 'media_converter:mp4_to_mp3', 'category': 'Media Converters', 'description': 'Extract audio from MP4 videos'},
        {'name': 'Video to GIF', 'url': 'media_converter:video_to_gif', 'category': 'Media Converters', 'description': 'Convert video to animated GIF'},
        {'name': 'Audio Splitter', 'url': 'media_converter:audio_splitter', 'category': 'Media Converters', 'description': 'Split audio files into segments'},
        {'name': 'Audio Merge', 'url': 'media_converter:audio_merge', 'category': 'Media Converters', 'description': 'Merge multiple audio files'},
        {'name': 'Video Compressor', 'url': 'media_converter:video_compressor', 'category': 'Media Converters', 'description': 'Compress video files'},
        {'name': 'Mute Video Audio', 'url': 'media_converter:mute_video', 'category': 'Media Converters', 'description': 'Remove audio from video'},
        {'name': 'Reduce Audio Noise', 'url': 'media_converter:reduce_noise', 'category': 'Media Converters', 'description': 'Reduce background noise from audio'},
    ])
    
    # PDF Tools
    tools.extend([
        {'name': 'Universal PDF Converter', 'url': 'pdf_tools:universal', 'category': 'PDF Tools', 'description': 'Convert PDF to various formats and vice versa'},
        {'name': 'Merge PDFs', 'url': 'pdf_tools:pdf_merge', 'category': 'PDF Tools', 'description': 'Combine multiple PDF files'},
        {'name': 'Split PDF', 'url': 'pdf_tools:pdf_split', 'category': 'PDF Tools', 'description': 'Split PDF into individual pages'},
        {'name': 'PDF to Images', 'url': 'pdf_tools:pdf_to_images', 'category': 'PDF Tools', 'description': 'Convert PDF pages to images'},
        {'name': 'PDF to HTML', 'url': 'pdf_tools:pdf_to_html', 'category': 'PDF Tools', 'description': 'Convert PDF to HTML'},
        {'name': 'HTML to PDF', 'url': 'pdf_tools:html_to_pdf', 'category': 'PDF Tools', 'description': 'Convert HTML to PDF'},
        {'name': 'PDF to Text', 'url': 'pdf_tools:pdf_to_text', 'category': 'PDF Tools', 'description': 'Extract text from PDF'},
        {'name': 'Compress PDF', 'url': 'pdf_tools:pdf_compress', 'category': 'PDF Tools', 'description': 'Reduce PDF file size'},
        {'name': 'Rotate PDF', 'url': 'pdf_tools:pdf_rotate', 'category': 'PDF Tools', 'description': 'Rotate PDF pages'},
        {'name': 'OCR PDF', 'url': 'pdf_tools:pdf_ocr', 'category': 'PDF Tools', 'description': 'Make scanned PDFs searchable'},
        {'name': 'Remove PDF Metadata', 'url': 'pdf_tools:pdf_remove_metadata', 'category': 'PDF Tools', 'description': 'Remove metadata from PDF'},
    ])
    
    # Utilities
    tools.extend([
        {'name': 'Calculator', 'url': 'utilities:calculator', 'category': 'Utilities', 'description': 'Simple online calculator'},
        {'name': 'QR Code Generator', 'url': 'utilities:qr_code_generator', 'category': 'Utilities', 'description': 'Generate QR codes'},
        {'name': 'Time Zone Converter', 'url': 'utilities:timezone_converter', 'category': 'Utilities', 'description': 'Convert time between time zones'},
        {'name': 'Roman Numeral Converter', 'url': 'utilities:roman_numeral_converter', 'category': 'Utilities', 'description': 'Convert Roman and Arabic numerals'},
        {'name': 'Favicon Generator', 'url': 'utilities:favicon_generator', 'category': 'Utilities', 'description': 'Generate favicon from image'},
        {'name': 'Timestamp Converter', 'url': 'utilities:timestamp_converter', 'category': 'Utilities', 'description': 'Convert timestamps and dates'},
        {'name': 'Text-to-Speech', 'url': 'utilities:text_to_speech', 'category': 'Utilities', 'description': 'Convert text to speech audio'},
        {'name': 'Random Number Generator', 'url': 'utilities:random_number_generator', 'category': 'Utilities', 'description': 'Generate random numbers'},
        {'name': 'Lorem Ipsum Generator', 'url': 'utilities:lorem_ipsum_generator', 'category': 'Utilities', 'description': 'Generate Lorem Ipsum text'},
        {'name': 'Random Word Generator', 'url': 'utilities:random_word_generator', 'category': 'Utilities', 'description': 'Generate random words'},
        {'name': 'Random Name Generator', 'url': 'utilities:random_name_generator', 'category': 'Utilities', 'description': 'Generate random names'},
        {'name': 'Word Lottery', 'url': 'utilities:word_lottery', 'category': 'Utilities', 'description': 'Pick random word from list'},
    ])
    
    # Archive Converters
    tools.extend([
        {'name': 'RAR to ZIP', 'url': 'archive_converter:rar_to_zip', 'category': 'Archive Converters', 'description': 'Convert RAR archives to ZIP'},
        {'name': 'ZIP to 7Z', 'url': 'archive_converter:zip_to_7z', 'category': 'Archive Converters', 'description': 'Convert ZIP to 7Z format'},
        {'name': '7Z to ZIP', 'url': 'archive_converter:7z_to_zip', 'category': 'Archive Converters', 'description': 'Convert 7Z to ZIP format'},
        {'name': 'TAR.GZ to ZIP', 'url': 'archive_converter:targz_to_zip', 'category': 'Archive Converters', 'description': 'Convert TAR.GZ to ZIP'},
        {'name': 'ZIP to TAR.GZ', 'url': 'archive_converter:zip_to_targz', 'category': 'Archive Converters', 'description': 'Convert ZIP to TAR.GZ'},
        {'name': 'Extract ISO', 'url': 'archive_converter:extract_iso', 'category': 'Archive Converters', 'description': 'Extract files from ISO images'},
        {'name': 'Create ZIP', 'url': 'archive_converter:create_zip', 'category': 'Archive Converters', 'description': 'Create ZIP from multiple files'},
    ])
    
    # Text Converters
    tools.extend([
        {'name': 'Uppercase ↔ Lowercase', 'url': 'text_converter:uppercase_lowercase', 'category': 'Text Converters', 'description': 'Convert text case'},
        {'name': 'CamelCase ↔ snake_case', 'url': 'text_converter:camelcase_snakecase', 'category': 'Text Converters', 'description': 'Convert naming conventions'},
        {'name': 'Remove Special Characters', 'url': 'text_converter:remove_special', 'category': 'Text Converters', 'description': 'Remove special characters from text'},
        {'name': 'Remove Duplicate Lines', 'url': 'text_converter:remove_duplicates', 'category': 'Text Converters', 'description': 'Remove duplicate lines'},
        {'name': 'Sort Lines', 'url': 'text_converter:sort_lines', 'category': 'Text Converters', 'description': 'Sort lines alphabetically'},
        {'name': 'JSON ↔ XML', 'url': 'text_converter:json_xml', 'category': 'Text Converters', 'description': 'Convert between JSON and XML'},
        {'name': 'JSON ↔ YAML', 'url': 'text_converter:json_yaml', 'category': 'Text Converters', 'description': 'Convert between JSON and YAML'},
        {'name': 'HTML ↔ Markdown', 'url': 'text_converter:html_markdown', 'category': 'Text Converters', 'description': 'Convert between HTML and Markdown'},
        {'name': 'Text ↔ Base64', 'url': 'text_converter:text_base64', 'category': 'Text Converters', 'description': 'Encode/decode Base64'},
        {'name': 'Word Counter', 'url': 'text_converter:word_counter', 'category': 'Text Converters', 'description': 'Count words, characters, lines, and more'},
    ])
    
    # Developer Converters
    tools.extend([
        {'name': 'Minify Code', 'url': 'developer_converter:minify', 'category': 'Developer Converters', 'description': 'Minify HTML, CSS, or JavaScript'},
        {'name': 'Unminify Code', 'url': 'developer_converter:unminify', 'category': 'Developer Converters', 'description': 'Beautify minified code'},
        {'name': 'CSV to JSON', 'url': 'developer_converter:csv_to_json', 'category': 'Developer Converters', 'description': 'Convert CSV to JSON'},
        {'name': 'JSON to CSV', 'url': 'developer_converter:json_to_csv', 'category': 'Developer Converters', 'description': 'Convert JSON to CSV'},
        {'name': 'SQL Formatter', 'url': 'developer_converter:sql_formatter', 'category': 'Developer Converters', 'description': 'Format SQL queries'},
        {'name': 'CSS ↔ SCSS', 'url': 'developer_converter:css_scss', 'category': 'Developer Converters', 'description': 'Convert between CSS and SCSS'},
        {'name': 'Regex Tester', 'url': 'developer_converter:regex_tester', 'category': 'Developer Converters', 'description': 'Test regular expressions'},
        {'name': 'JWT Decoder', 'url': 'developer_converter:jwt_decoder', 'category': 'Developer Converters', 'description': 'Decode JWT tokens'},
        {'name': 'URL Encoder/Decoder', 'url': 'developer_converter:url_encoder', 'category': 'Developer Converters', 'description': 'Encode or decode URLs'},
        {'name': 'Hash Generator', 'url': 'developer_converter:hash_generator', 'category': 'Developer Converters', 'description': 'Generate MD5, SHA1, SHA256 hashes'},
    ])
    
    return tools


def search(request):
    """Global search for all tools and converters"""
    query = request.GET.get('q', '').strip().lower()
    results = []
    
    # Get categories for display
    categories = [
        {
            'name': 'Color Code Generator & Picker',
            'url': 'color_picker:index',
            'description': 'Pick colors from screen, convert between color formats, and generate color codes',
            'icon': 'color-picker.svg'
        },
        {
            'name': 'Image Conversion & Editing',
            'url': 'image_converter:index',
            'description': 'Convert images between different formats and edit them',
            'icon': 'image-converters.svg'
        },
        {
            'name': 'Media Converters',
            'url': 'media_converter:index',
            'description': 'Convert media files and download audio.',
            'icon': 'media-converters.svg'
        },
        {
            'name': 'PDF Tools',
            'url': 'pdf_tools:index',
            'description': 'Merge, split, and convert PDF files',
            'icon': 'pdf-tools.svg'
        },
        {
            'name': 'Unit Converters',
            'url': 'converters:index',
            'description': 'Convert between different units of measurement',
            'icon': 'unit-converters.svg'
        },
        {
            'name': 'Utilities',
            'url': 'utilities:index',
            'description': 'Calculators, text utilities, color converter, QR codes and more',
            'icon': 'utilities.svg'
        },
        {
            'name': 'Currency & Crypto',
            'url': 'currency_converter:index',
            'description': 'Convert between currencies and cryptocurrencies with real-time rates',
            'icon': 'currency-crypto.svg'
        },
        {
            'name': 'Archive Converters',
            'url': 'archive_converter:index',
            'description': 'Convert between ZIP, RAR, 7Z, and TAR.GZ formats. Extract ISO files.',
            'icon': 'archive-converters.svg'
        },
        {
            'name': 'Text & String Converters',
            'url': 'text_converter:index',
            'description': 'Convert text between formats: uppercase/lowercase, CamelCase/snake_case, JSON/XML/YAML, HTML/Markdown, Base64, and more',
            'icon': 'text-converters.svg'
        },
        {
            'name': 'Developer Converters',
            'url': 'developer_converter:index',
            'description': 'Developer tools: minify/unminify code, CSV/JSON conversion, SQL formatter, regex tester, JWT decoder, and more',
            'icon': 'developer-converters.svg'
        },
    ]
    
    if query:
        all_tools = _get_all_tools()
        
        for tool in all_tools:
            # Search in name, description, and category
            search_text = f"{tool['name']} {tool.get('description', '')} {tool.get('category', '')}".lower()
            
            if query in search_text:
                # Calculate relevance score (simple: count matches)
                score = search_text.count(query)
                
                # Build URL
                try:
                    if isinstance(tool['url'], tuple):
                        url = reverse(tool['url'][0], args=tool['url'][1:])
                    else:
                        url = reverse(tool['url'])
                except:
                    continue  # Skip if URL can't be reversed
                
                results.append({
                    'name': tool['name'],
                    'url': url,
                    'category': tool.get('category', ''),
                    'description': tool.get('description', ''),
                    'score': score,
                })
        
        # Sort by relevance (score) and then alphabetically
        results.sort(key=lambda x: (-x['score'], x['name']))
    
    return render(request, 'search_results.html', {
        'query': query,
        'results': results,
        'result_count': len(results),
        'categories': categories,
    })


def favicon_view(request):
    """Serve favicon.ico at root level for Google Search"""
    # Try STATICFILES_DIRS first (development), then STATIC_ROOT (production)
    favicon_path = None
    
    if settings.STATICFILES_DIRS:
        favicon_path = os.path.join(settings.STATICFILES_DIRS[0], 'images', 'favicon.ico')
        if not os.path.exists(favicon_path):
            favicon_path = None
    
    if not favicon_path or not os.path.exists(favicon_path):
        # Try STATIC_ROOT (production with collected static files)
        favicon_path = os.path.join(settings.STATIC_ROOT, 'images', 'favicon.ico')
    
    if favicon_path and os.path.exists(favicon_path):
        with open(favicon_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='image/x-icon')
            # Cache for 1 year
            response['Cache-Control'] = 'public, max-age=31536000'
            return response
    return HttpResponse(status=404)

