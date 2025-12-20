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
        return HttpResponseRedirect('/')
    
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
                'description': 'Convert text formats: case, JSON/XML/YAML, HTML/Markdown, Base64, and more',
                'icon': 'text-converters.svg'
            },
            {
                'name': 'Developer Converters',
                'url': 'developer_converter:index',
                'description': 'Code minify, CSV/JSON, SQL, regex, JWT, and more',
                'icon': 'developer-converters.svg'
            },
            {
                'name': 'Website Status Checker',
                'url': 'isdown:index',
                'description': 'Check instantly if any website is online or down',
                'icon': 'website-status.svg'
            },
            {
                'name': 'YouTube Thumbnail Downloader',
                'url': 'youtube_thumbnail:index',
                'description': 'Download YouTube thumbnails (HD, HQ, MQ, Default)',
                'icon': 'youtube-thumbnail.svg'
            },
        ]
    }
    return render(request, 'home.html', context)


def _get_all_tools():
    """Build a comprehensive list of all tools and converters for search"""
    tools = []
    
    # Categories (main pages)
    categories = [
        {'name': 'Color Code Generator & Picker', 'url': 'color_picker:index', 'category': 'Color Picker', 'description': 'Pick colors from screen, convert between color formats, and generate color codes', 'keywords': 'color RGB HEX'},
        {'name': 'Image Conversion & Editing', 'url': 'image_converter:index', 'category': 'Image Converters', 'description': 'Convert images between different formats and edit them', 'keywords': 'JPEG JPG PNG WEBP BMP TIFF GIF'},
        {'name': 'Media Converters', 'url': 'media_converter:index', 'category': 'Media Converters', 'description': 'Convert media files and download audio', 'keywords': 'MP3 WAV FLAC MP4 AVI video audio'},
        {'name': 'PDF Tools', 'url': 'pdf_tools:index', 'category': 'PDF Tools', 'description': 'Merge, split, and convert PDF files', 'keywords': 'PDF'},
        {'name': 'Unit Converters', 'url': 'converters:index', 'category': 'Unit Converters', 'description': 'Convert between different units of measurement', 'keywords': 'meter kg pound watt kW'},
        {'name': 'Utilities', 'url': 'utilities:index', 'category': 'Utilities', 'description': 'Calculators, text utilities, QR codes and more', 'keywords': 'calculator QR code'},
        {'name': 'Currency & Crypto', 'url': 'currency_converter:index', 'category': 'Currency & Crypto', 'description': 'Convert between currencies and cryptocurrencies with real-time rates', 'keywords': 'currency crypto Bitcoin EUR USD GBP JPY AUD CAD CHF CNY INR BRL RUB ZAR MXN SGD HKD NZD SEK NOK DKK PLN TRY KRW THB AED SAR Euro Dollar Pound Yen'},
        {'name': 'Archive Converters', 'url': 'archive_converter:index', 'category': 'Archive Converters', 'description': 'Convert between ZIP, RAR, 7Z, and TAR.GZ formats', 'keywords': 'ZIP RAR 7Z TAR.GZ archive'},
        {'name': 'Text & String Converters', 'url': 'text_converter:index', 'category': 'Text Converters', 'description': 'Convert text between formats', 'keywords': 'JSON XML YAML HTML'},
        {'name': 'Developer Converters', 'url': 'developer_converter:index', 'category': 'Developer Converters', 'description': 'Developer tools and code utilities', 'keywords': 'HTML CSS JavaScript JSON CSV'},
        {'name': 'Website Status Checker', 'url': 'isdown:index', 'category': 'Network Tools', 'description': 'Check instantly if any website is online or down', 'keywords': 'website status down online'},
        {'name': 'YouTube Thumbnail Downloader', 'url': 'youtube_thumbnail:index', 'category': 'Media Converters', 'description': 'Download YouTube thumbnails (HD, HQ, MQ, Default)', 'keywords': 'YouTube thumbnail'},
    ]
    tools.extend(categories)
    
    # Color Picker tools
    tools.extend([
        {'name': 'Color Picker', 'url': 'color_picker:picker', 'category': 'Color Picker', 'description': 'Pick colors from screen', 'keywords': 'color picker RGB HEX'},
        {'name': 'Pick Color from Image', 'url': 'color_picker:pick_from_image', 'category': 'Color Picker', 'description': 'Extract colors from images', 'keywords': 'color picker image RGB HEX'},
    ])
    
    # Unit Converters
    tools.extend([
        {'name': 'Length Converter', 'url': ('converters:tool', 'length'), 'category': 'Unit Converters', 'description': 'Convert between meters, feet, inches, and more', 'keywords': 'meter m kilometer km centimeter cm millimeter mm mile mi foot ft inch in yard yd'},
        {'name': 'Weight Converter', 'url': ('converters:tool', 'weight'), 'category': 'Unit Converters', 'description': 'Convert between kilograms, pounds, ounces, and more', 'keywords': 'kilogram kg gram g pound lb ounce oz ton t stone st'},
        {'name': 'Temperature Converter', 'url': ('converters:tool', 'temperature'), 'category': 'Unit Converters', 'description': 'Convert between Celsius, Fahrenheit, and Kelvin', 'keywords': 'celsius fahrenheit kelvin C F K'},
        {'name': 'Volume Converter', 'url': ('converters:tool', 'volume'), 'category': 'Unit Converters', 'description': 'Convert between liters, gallons, cups, and more', 'keywords': 'liter L milliliter mL gallon gal quart qt pint pt cup fluid ounce fl oz'},
        {'name': 'Area Converter', 'url': ('converters:tool', 'area'), 'category': 'Unit Converters', 'description': 'Convert between square meters, square feet, acres, and more', 'keywords': 'square meter m² square foot ft² acre hectare'},
        {'name': 'Speed Converter', 'url': ('converters:tool', 'speed'), 'category': 'Unit Converters', 'description': 'Convert between km/h, mph, m/s, and more', 'keywords': 'km/h mph m/s ft/s knot'},
        {'name': 'Time Converter', 'url': ('converters:tool', 'time'), 'category': 'Unit Converters', 'description': 'Convert between seconds, minutes, hours, days, and more', 'keywords': 'second minute hour day week month year millisecond microsecond nanosecond'},
        {'name': 'Data Storage Converter', 'url': ('converters:tool', 'data-storage'), 'category': 'Unit Converters', 'description': 'Convert between bytes, KB, MB, GB, TB, and more', 'keywords': 'byte B kilobyte KB megabyte MB gigabyte GB terabyte TB petabyte PB kibibyte KiB mebibyte MiB gibibyte GiB tebibyte TiB bit'},
        {'name': 'Energy Converter', 'url': ('converters:tool', 'energy'), 'category': 'Unit Converters', 'description': 'Convert between joules, calories, watt-hours, and more', 'keywords': 'joule J kilojoule kJ calorie cal kilocalorie kcal watt-hour Wh kilowatt-hour kWh electronvolt eV BTU foot-pound ft-lb'},
        {'name': 'Power Converter', 'url': ('converters:tool', 'power'), 'category': 'Unit Converters', 'description': 'Convert between watts, kilowatts, horsepower, and more', 'keywords': 'watt W kilowatt kW megawatt MW horsepower hp PS BTU/h foot-pound per second ft-lb/s'},
        {'name': 'Pressure Converter', 'url': ('converters:tool', 'pressure'), 'category': 'Unit Converters', 'description': 'Convert between Pascal, bar, PSI, atmosphere, and more', 'keywords': 'pascal Pa kilopascal kPa bar atmosphere atm PSI torr mmHg inHg'},
        {'name': 'Force Converter', 'url': ('converters:tool', 'force'), 'category': 'Unit Converters', 'description': 'Convert between newtons, pounds-force, kilogram-force, and more', 'keywords': 'newton N kilonewton kN pound-force lbf kilogram-force kgf dyne ounce-force ozf'},
        {'name': 'Angle Converter', 'url': ('converters:tool', 'angle'), 'category': 'Unit Converters', 'description': 'Convert between degrees, radians, gradians, and turns', 'keywords': 'degree radian gradian turn arcminute arcsecond'},
        {'name': 'Fuel Consumption Converter', 'url': ('converters:tool', 'fuel-consumption'), 'category': 'Unit Converters', 'description': 'Convert between MPG, L/100km, km/L, and more', 'keywords': 'MPG L/100km km/L mi/L'},
        {'name': 'Frequency Converter', 'url': ('converters:tool', 'frequency'), 'category': 'Unit Converters', 'description': 'Convert between Hertz, kilohertz, megahertz, RPM, and more', 'keywords': 'hertz Hz kilohertz kHz megahertz MHz gigahertz GHz RPM RPS'},
        {'name': 'Data Transfer Rate Converter', 'url': ('converters:tool', 'data-transfer'), 'category': 'Unit Converters', 'description': 'Convert between Mbps, MB/s, Gbps, and more', 'keywords': 'bps Kbps Mbps Gbps B/s KB/s MB/s GB/s'},
    ])
    
    # Image Converters
    tools.extend([
        {'name': 'Universal Image Converter', 'url': 'image_converter:universal', 'category': 'Image Converters', 'description': 'Convert images to any format', 'keywords': 'JPEG JPG PNG WEBP BMP TIFF GIF ICO SVG AVIF HEIC'},
        {'name': 'JPEG to PNG', 'url': ('image_converter:convert', 'jpeg-to-png'), 'category': 'Image Converters', 'description': 'Convert JPEG images to PNG', 'keywords': 'JPEG JPG PNG'},
        {'name': 'PNG to JPG', 'url': ('image_converter:convert', 'png-to-jpg'), 'category': 'Image Converters', 'description': 'Convert PNG images to JPG', 'keywords': 'PNG JPEG JPG'},
        {'name': 'Image Resizer', 'url': 'image_converter:resize', 'category': 'Image Converters', 'description': 'Resize images to custom dimensions', 'keywords': 'JPEG JPG PNG WEBP BMP TIFF GIF resize'},
        {'name': 'Rotate & Flip', 'url': 'image_converter:rotate_flip', 'category': 'Image Converters', 'description': 'Rotate or flip images', 'keywords': 'JPEG JPG PNG rotate flip'},
        {'name': 'Remove EXIF', 'url': 'image_converter:remove_exif', 'category': 'Image Converters', 'description': 'Remove EXIF metadata from images', 'keywords': 'EXIF metadata JPEG JPG PNG'},
        {'name': 'Grayscale', 'url': 'image_converter:grayscale', 'category': 'Image Converters', 'description': 'Convert images to grayscale', 'keywords': 'grayscale JPEG JPG PNG'},
        {'name': 'Merge Images', 'url': 'image_converter:merge', 'category': 'Image Converters', 'description': 'Merge multiple images', 'keywords': 'JPEG JPG PNG merge combine'},
        {'name': 'Watermark', 'url': 'image_converter:watermark', 'category': 'Image Converters', 'description': 'Add watermark to images', 'keywords': 'watermark JPEG JPG PNG'},
    ])
    
    # Media Converters
    tools.extend([
        {'name': 'Audio Converter', 'url': 'media_converter:audio_converter', 'category': 'Media Converters', 'description': 'Convert between audio formats', 'keywords': 'MP3 WAV OGG FLAC AAC M4A AIFF audio'},
        {'name': 'Video Converter', 'url': 'media_converter:video_converter', 'category': 'Media Converters', 'description': 'Convert between video formats', 'keywords': 'MP4 AVI MOV MKV WebM FLV WMV 3GP video'},
        {'name': 'MP4 to MP3', 'url': 'media_converter:mp4_to_mp3', 'category': 'Media Converters', 'description': 'Extract audio from MP4 videos', 'keywords': 'MP4 MP3 extract audio video'},
        {'name': 'Video to GIF', 'url': 'media_converter:video_to_gif', 'category': 'Media Converters', 'description': 'Convert video to animated GIF', 'keywords': 'video GIF MP4 AVI animated'},
        {'name': 'Audio Splitter', 'url': 'media_converter:audio_splitter', 'category': 'Media Converters', 'description': 'Split audio files into segments', 'keywords': 'MP3 WAV OGG FLAC split audio'},
        {'name': 'Audio Merge', 'url': 'media_converter:audio_merge', 'category': 'Media Converters', 'description': 'Merge multiple audio files', 'keywords': 'MP3 WAV OGG FLAC merge combine audio'},
        {'name': 'Video Merge', 'url': 'media_converter:video_merge', 'category': 'Media Converters', 'description': 'Merge multiple video files into one', 'keywords': 'MP4 AVI MOV merge combine video'},
        {'name': 'Video Compressor', 'url': 'media_converter:video_compressor', 'category': 'Media Converters', 'description': 'Compress video files', 'keywords': 'MP4 AVI compress video'},
        {'name': 'Mute Video Audio', 'url': 'media_converter:mute_video', 'category': 'Media Converters', 'description': 'Remove audio from video', 'keywords': 'MP4 AVI mute remove audio video'},
        {'name': 'Reduce Audio Noise', 'url': 'media_converter:reduce_noise', 'category': 'Media Converters', 'description': 'Reduce background noise from audio', 'keywords': 'MP3 WAV OGG FLAC noise reduction audio'},
    ])
    
    # PDF Tools
    tools.extend([
        {'name': 'Universal PDF Converter', 'url': 'pdf_tools:universal', 'category': 'PDF Tools', 'description': 'Convert PDF to various formats and vice versa', 'keywords': 'PDF convert'},
        {'name': 'Merge PDFs', 'url': 'pdf_tools:pdf_merge', 'category': 'PDF Tools', 'description': 'Combine multiple PDF files', 'keywords': 'PDF merge combine'},
        {'name': 'Split PDF', 'url': 'pdf_tools:pdf_split', 'category': 'PDF Tools', 'description': 'Split PDF into individual pages', 'keywords': 'PDF split'},
        {'name': 'PDF to Images', 'url': 'pdf_tools:pdf_to_images', 'category': 'PDF Tools', 'description': 'Convert PDF pages to images', 'keywords': 'PDF image JPEG PNG'},
        {'name': 'PDF to HTML', 'url': 'pdf_tools:pdf_to_html', 'category': 'PDF Tools', 'description': 'Convert PDF to HTML', 'keywords': 'PDF HTML'},
        {'name': 'HTML to PDF', 'url': 'pdf_tools:html_to_pdf', 'category': 'PDF Tools', 'description': 'Convert HTML to PDF', 'keywords': 'HTML PDF'},
        {'name': 'PDF to Text', 'url': 'pdf_tools:pdf_to_text', 'category': 'PDF Tools', 'description': 'Extract text from PDF', 'keywords': 'PDF text extract'},
        {'name': 'Compress PDF', 'url': 'pdf_tools:pdf_compress', 'category': 'PDF Tools', 'description': 'Reduce PDF file size', 'keywords': 'PDF compress'},
        {'name': 'Rotate PDF', 'url': 'pdf_tools:pdf_rotate', 'category': 'PDF Tools', 'description': 'Rotate PDF pages', 'keywords': 'PDF rotate'},
        {'name': 'OCR PDF', 'url': 'pdf_tools:pdf_ocr', 'category': 'PDF Tools', 'description': 'Make scanned PDFs searchable', 'keywords': 'PDF OCR'},
        {'name': 'Remove PDF Metadata', 'url': 'pdf_tools:pdf_remove_metadata', 'category': 'PDF Tools', 'description': 'Remove metadata from PDF', 'keywords': 'PDF metadata'},
        {'name': 'PDF to Flipbook', 'url': 'pdf_tools:pdf_to_flipbook', 'category': 'PDF Tools', 'description': 'Convert PDF to interactive HTML flipbook', 'keywords': 'PDF flipbook interactive animation'},
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
        {'name': 'RAR to ZIP', 'url': 'archive_converter:rar_to_zip', 'category': 'Archive Converters', 'description': 'Convert RAR archives to ZIP', 'keywords': 'RAR ZIP archive'},
        {'name': 'ZIP to 7Z', 'url': 'archive_converter:zip_to_7z', 'category': 'Archive Converters', 'description': 'Convert ZIP to 7Z format', 'keywords': 'ZIP 7Z archive'},
        {'name': '7Z to ZIP', 'url': 'archive_converter:7z_to_zip', 'category': 'Archive Converters', 'description': 'Convert 7Z to ZIP format', 'keywords': '7Z ZIP archive'},
        {'name': 'TAR.GZ to ZIP', 'url': 'archive_converter:targz_to_zip', 'category': 'Archive Converters', 'description': 'Convert TAR.GZ to ZIP', 'keywords': 'TAR.GZ TAR GZ ZIP archive'},
        {'name': 'ZIP to TAR.GZ', 'url': 'archive_converter:zip_to_targz', 'category': 'Archive Converters', 'description': 'Convert ZIP to TAR.GZ', 'keywords': 'ZIP TAR.GZ TAR GZ archive'},
        {'name': 'Extract ISO', 'url': 'archive_converter:extract_iso', 'category': 'Archive Converters', 'description': 'Extract files from ISO images', 'keywords': 'ISO extract archive'},
        {'name': 'Create ZIP', 'url': 'archive_converter:create_zip', 'category': 'Archive Converters', 'description': 'Create ZIP from multiple files', 'keywords': 'ZIP create archive'},
    ])
    
    # Text Converters
    tools.extend([
        {'name': 'Uppercase ↔ Lowercase', 'url': 'text_converter:uppercase_lowercase', 'category': 'Text Converters', 'description': 'Convert text case', 'keywords': 'uppercase lowercase case'},
        {'name': 'CamelCase ↔ snake_case', 'url': 'text_converter:camelcase_snakecase', 'category': 'Text Converters', 'description': 'Convert naming conventions', 'keywords': 'CamelCase snake_case naming'},
        {'name': 'Remove Special Characters', 'url': 'text_converter:remove_special', 'category': 'Text Converters', 'description': 'Remove special characters from text', 'keywords': 'special characters text'},
        {'name': 'Remove Duplicate Lines', 'url': 'text_converter:remove_duplicates', 'category': 'Text Converters', 'description': 'Remove duplicate lines', 'keywords': 'duplicate lines text'},
        {'name': 'Sort Lines', 'url': 'text_converter:sort_lines', 'category': 'Text Converters', 'description': 'Sort lines alphabetically', 'keywords': 'sort lines text'},
        {'name': 'JSON ↔ XML', 'url': 'text_converter:json_xml', 'category': 'Text Converters', 'description': 'Convert between JSON and XML', 'keywords': 'JSON XML'},
        {'name': 'JSON ↔ YAML', 'url': 'text_converter:json_yaml', 'category': 'Text Converters', 'description': 'Convert between JSON and YAML', 'keywords': 'JSON YAML'},
        {'name': 'HTML ↔ Markdown', 'url': 'text_converter:html_markdown', 'category': 'Text Converters', 'description': 'Convert between HTML and Markdown', 'keywords': 'HTML Markdown MD'},
        {'name': 'Text ↔ Base64', 'url': 'text_converter:text_base64', 'category': 'Text Converters', 'description': 'Encode/decode Base64', 'keywords': 'Base64 encode decode'},
        {'name': 'Word Counter', 'url': 'text_converter:word_counter', 'category': 'Text Converters', 'description': 'Count words, characters, lines, and more', 'keywords': 'word count character'},
    ])
    
    # Developer Converters
    tools.extend([
        {'name': 'Minify Code', 'url': 'developer_converter:minify', 'category': 'Developer Converters', 'description': 'Minify HTML, CSS, or JavaScript', 'keywords': 'HTML CSS JavaScript minify'},
        {'name': 'Unminify Code', 'url': 'developer_converter:unminify', 'category': 'Developer Converters', 'description': 'Beautify minified code', 'keywords': 'HTML CSS JavaScript beautify unminify'},
        {'name': 'CSV to JSON', 'url': 'developer_converter:csv_to_json', 'category': 'Developer Converters', 'description': 'Convert CSV to JSON', 'keywords': 'CSV JSON'},
        {'name': 'JSON to CSV', 'url': 'developer_converter:json_to_csv', 'category': 'Developer Converters', 'description': 'Convert JSON to CSV', 'keywords': 'JSON CSV'},
        {'name': 'SQL Formatter', 'url': 'developer_converter:sql_formatter', 'category': 'Developer Converters', 'description': 'Format SQL queries', 'keywords': 'SQL format'},
        {'name': 'CSS ↔ SCSS', 'url': 'developer_converter:css_scss', 'category': 'Developer Converters', 'description': 'Convert between CSS and SCSS', 'keywords': 'CSS SCSS SASS'},
        {'name': 'Regex Tester', 'url': 'developer_converter:regex_tester', 'category': 'Developer Converters', 'description': 'Test regular expressions', 'keywords': 'regex regular expression'},
        {'name': 'JWT Decoder', 'url': 'developer_converter:jwt_decoder', 'category': 'Developer Converters', 'description': 'Decode JWT tokens', 'keywords': 'JWT token decode'},
        {'name': 'URL Encoder/Decoder', 'url': 'developer_converter:url_encoder', 'category': 'Developer Converters', 'description': 'Encode or decode URLs', 'keywords': 'URL encode decode'},
        {'name': 'Hash Generator', 'url': 'developer_converter:hash_generator', 'category': 'Developer Converters', 'description': 'Generate MD5, SHA1, SHA256 hashes', 'keywords': 'MD5 SHA1 SHA256 hash'},
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
            'description': 'Convert text formats: case, JSON/XML/YAML, HTML/Markdown, Base64, and more',
            'icon': 'text-converters.svg'
        },
        {
            'name': 'Developer Converters',
            'url': 'developer_converter:index',
            'description': 'Code minify, CSV/JSON, SQL, regex, JWT, and more',
            'icon': 'developer-converters.svg'
        },
        {
            'name': 'Website Status Checker',
            'url': 'isdown:index',
            'description': 'Check instantly if any website is online or down',
            'icon': 'website-status.svg'
        },
        {
            'name': 'YouTube Thumbnail Downloader',
            'url': 'youtube_thumbnail:index',
            'description': 'Download YouTube thumbnails in all available qualities',
            'icon': 'youtube-thumbnail.svg'
        },
    ]
    
    if query:
        all_tools = _get_all_tools()
        
        for tool in all_tools:
            # Search in name, description, category, and keywords
            keywords = tool.get('keywords', '')
            search_text = f"{tool['name']} {tool.get('description', '')} {tool.get('category', '')} {keywords}".lower()
            
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


def privacy_policy(request):
    """Privacy Policy page"""
    return render(request, 'privacy_policy.html')


def terms_of_service(request):
    """Terms of Service page"""
    return render(request, 'terms_of_service.html')


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

def bing_site_auth_view(request):
    """Serve BingSiteAuth.xml at root level for Bing Webmaster Tools verification"""
    # Try multiple locations for the verification file
    bing_auth_path = None
    
    # First, try in static directory (development)
    if settings.STATICFILES_DIRS:
        bing_auth_path = os.path.join(settings.STATICFILES_DIRS[0], 'BingSiteAuth.xml')
        if not os.path.exists(bing_auth_path):
            bing_auth_path = None
    
    # Try STATIC_ROOT (production with collected static files)
    if not bing_auth_path or not os.path.exists(bing_auth_path):
        bing_auth_path = os.path.join(settings.STATIC_ROOT, 'BingSiteAuth.xml')
    
    # Try in project root as fallback
    if not bing_auth_path or not os.path.exists(bing_auth_path):
        bing_auth_path = os.path.join(settings.BASE_DIR, 'BingSiteAuth.xml')
    
    if bing_auth_path and os.path.exists(bing_auth_path):
        with open(bing_auth_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/xml; charset=utf-8')
            # Cache for a shorter time than favicon (verification files may change)
            response['Cache-Control'] = 'public, max-age=3600'
            return response
    return HttpResponse(status=404)

