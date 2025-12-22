from django.shortcuts import render
from django.http import HttpResponse
from django.contrib import messages
import io
import zipfile
import os
import tempfile
import subprocess
import shutil
from pypdf import PdfWriter, PdfReader
from PIL import Image

def _check_poppler_available():
    """Check if poppler utilities are available on the system"""
    # Check if pdftoppm (a poppler utility) is available
    return shutil.which('pdftoppm') is not None

# Check if pdf2image package is installed
try:
    from pdf2image import convert_from_bytes
    PDF2IMAGE_PACKAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_PACKAGE_AVAILABLE = False
    convert_from_bytes = None

# PDF2IMAGE is only available if both the package AND poppler are available
PDF2IMAGE_AVAILABLE = PDF2IMAGE_PACKAGE_AVAILABLE and _check_poppler_available()
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
try:
    import cairosvg
    CAIROSVG_AVAILABLE = True
except ImportError:
    CAIROSVG_AVAILABLE = False
try:
    import pypandoc
    PYPANDOC_AVAILABLE = True
except ImportError:
    PYPANDOC_AVAILABLE = False
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
try:
    import ebooklib
    from ebooklib import epub
    EBOOKLIB_AVAILABLE = True
except ImportError:
    EBOOKLIB_AVAILABLE = False
    epub = None

def _get_universal_context():
    """Helper function to get context for universal converter template"""
    return {
        'pdf2image_available': PDF2IMAGE_AVAILABLE,
        'weasyprint_available': WEASYPRINT_AVAILABLE,
        'pdfplumber_available': PDFPLUMBER_AVAILABLE,
        'cairosvg_available': CAIROSVG_AVAILABLE,
        'pypandoc_available': PYPANDOC_AVAILABLE,
        'pymupdf_available': PYMUPDF_AVAILABLE,
    }

def index(request):
    """PDF tools main page"""
    return render(request, 'pdf_tools/index.html', {
        'pdf2image_available': PDF2IMAGE_AVAILABLE,
        'weasyprint_available': WEASYPRINT_AVAILABLE,
    })

def universal_converter(request):
    """Universal PDF converter - convert between PDF and various formats"""
    if request.method != 'POST':
        # Clear any stale PyMuPDF error messages from session on GET requests
        # Since PyMuPDF is confirmed available, consume all messages to clear stale ones
        if PYMUPDF_AVAILABLE:
            # Consume all messages - this clears them from the session
            # The JavaScript in base.html will also hide any PyMuPDF messages that slip through
            list(messages.get_messages(request))
        
        return render(request, 'pdf_tools/universal.html', _get_universal_context())
    
    output_format = request.POST.get('output_format', '').lower()
    
    # Handle conversions TO PDF (HTML, SVG, RTF to PDF)
    if output_format == 'pdf':
        # Check if file is uploaded or HTML content is provided
        input_file = None
        if 'input_file' in request.FILES:
            input_file = request.FILES['input_file']
            file_ext = os.path.splitext(input_file.name)[1].lower()
        else:
            file_ext = None
        
        # PNG/JPG to PDF
        if input_file and file_ext in ['.png', '.jpg', '.jpeg']:
            try:
                max_size = 50 * 1024 * 1024  # 50MB
                if input_file.size > max_size:
                    messages.error(request, f'File size exceeds 50MB limit. Your file is {input_file.size / (1024 * 1024):.1f}MB.')
                    return render(request, 'pdf_tools/universal.html', _get_universal_context())
                
                # Read image
                image_data = input_file.read()
                image = Image.open(io.BytesIO(image_data))
                
                # Convert RGBA to RGB for JPEG images
                if image.mode == 'RGBA' and file_ext in ['.jpg', '.jpeg']:
                    rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                    rgb_image.paste(image, mask=image.split()[3])
                    image = rgb_image
                elif image.mode == 'RGBA':
                    # Keep RGBA for PNG
                    pass
                elif image.mode not in ['RGB', 'L']:
                    image = image.convert('RGB')
                
                # Convert image to PDF
                pdf_buffer = io.BytesIO()
                image.save(pdf_buffer, format='PDF', resolution=100.0)
                pdf_buffer.seek(0)
                
                response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="converted.pdf"'
                return response
                
            except Exception as e:
                messages.error(request, f'Error converting image to PDF: {str(e)}')
                return render(request, 'pdf_tools/universal.html', _get_universal_context())
        
        # Text to PDF
        elif input_file and file_ext == '.txt':
            if not WEASYPRINT_AVAILABLE:
                messages.error(request, 'Text to PDF conversion requires weasyprint. Install with: pip install weasyprint')
                return render(request, 'pdf_tools/universal.html', _get_universal_context())
            
            try:
                max_size = 10 * 1024 * 1024  # 10MB for text
                if input_file.size > max_size:
                    messages.error(request, f'File size exceeds 10MB limit. Your file is {input_file.size / (1024 * 1024):.1f}MB.')
                    return render(request, 'pdf_tools/universal.html', _get_universal_context())
                
                # Read text content
                text_content = input_file.read().decode('utf-8', errors='ignore')
                
                # Convert text to HTML (preserve line breaks)
                html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @page {{
            margin: 2cm;
            size: A4;
        }}
        body {{
            font-family: Arial, Helvetica, sans-serif;
            line-height: 1.6;
            white-space: pre-wrap;
        }}
        pre {{
            font-family: Arial, Helvetica, sans-serif;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
    </style>
</head>
<body>
<pre>{text_content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')}</pre>
</body>
</html>'''
                
                pdf_buffer = io.BytesIO()
                html_doc = HTML(string=html_content)
                html_doc.write_pdf(pdf_buffer, stylesheets=None, presentational_hints=True)
                pdf_buffer.seek(0)
                
                response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="converted.pdf"'
                return response
                
            except Exception as e:
                messages.error(request, f'Error converting text to PDF: {str(e)}')
                return render(request, 'pdf_tools/universal.html', _get_universal_context())
        
        # SVG to PDF
        elif input_file and file_ext in ['.svg', '.svgz']:
            if not CAIROSVG_AVAILABLE:
                messages.error(request, 'SVG to PDF conversion requires cairosvg. Install with: pip install cairosvg')
                return render(request, 'pdf_tools/universal.html', _get_universal_context())
            
            try:
                svg_data = input_file.read()
                pdf_data = cairosvg.svg2pdf(bytestring=svg_data)
                
                response = HttpResponse(pdf_data, content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="converted.pdf"'
                return response
                
            except Exception as e:
                messages.error(request, f'Error converting SVG to PDF: {str(e)}. Make sure Cairo is installed (brew install cairo on macOS).')
                return render(request, 'pdf_tools/universal.html', _get_universal_context())
        
        # RTF to PDF
        elif input_file and file_ext == '.rtf':
            if not PYPANDOC_AVAILABLE:
                messages.error(request, 'RTF to PDF conversion requires pypandoc and pandoc. Install with: pip install pypandoc && install pandoc (brew install pandoc on macOS)')
                return render(request, 'pdf_tools/universal.html', _get_universal_context())
            
            if not WEASYPRINT_AVAILABLE:
                messages.error(request, 'RTF to PDF conversion requires weasyprint. Install with: pip install weasyprint')
                return render(request, 'pdf_tools/universal.html', _get_universal_context())
            
            max_size = 50 * 1024 * 1024  # 50MB
            if input_file.size > max_size:
                messages.error(request, f'File size exceeds 50MB limit. Your file is {input_file.size / (1024 * 1024):.1f}MB.')
                return render(request, 'pdf_tools/universal.html', _get_universal_context())
            
            tmp_input_path = None
            tmp_html_path = None
            try:
                # Step 1: Convert RTF to HTML using pandoc (doesn't require PDF engine)
                with tempfile.NamedTemporaryFile(delete=False, suffix='.rtf') as tmp_input:
                    for chunk in input_file.chunks():
                        tmp_input.write(chunk)
                    tmp_input_path = tmp_input.name
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as tmp_html:
                    tmp_html_path = tmp_html.name
                
                # Convert RTF to HTML using pandoc
                pypandoc.convert_file(
                    tmp_input_path,
                    'html',
                    format='rtf',
                    outputfile=tmp_html_path
                )
                
                # Step 2: Convert HTML to PDF using weasyprint
                with open(tmp_html_path, 'rb') as html_file:
                    html_content = html_file.read().decode('utf-8')
                
                pdf_buffer = io.BytesIO()
                html_doc = HTML(string=html_content)
                html_doc.write_pdf(pdf_buffer, stylesheets=None, presentational_hints=True)
                pdf_buffer.seek(0)
                
                response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="converted.pdf"'
                
                # Clean up temporary files
                if tmp_input_path and os.path.exists(tmp_input_path):
                    os.unlink(tmp_input_path)
                if tmp_html_path and os.path.exists(tmp_html_path):
                    os.unlink(tmp_html_path)
                
                return response
                
            except Exception as e:
                import traceback
                error_msg = str(e)
                error_details = traceback.format_exc()
                
                # Log the full error for debugging
                print(f"RTF to PDF conversion error: {error_msg}")
                print(f"Traceback: {error_details}")
                
                # Clean up temporary files
                if tmp_input_path and os.path.exists(tmp_input_path):
                    try:
                        os.unlink(tmp_input_path)
                    except:
                        pass
                if tmp_html_path and os.path.exists(tmp_html_path):
                    try:
                        os.unlink(tmp_html_path)
                    except:
                        pass
                
                # Check for specific error types
                if 'pandoc' in error_msg.lower() and ('not found' in error_msg.lower() or 'died' in error_msg.lower()):
                    messages.error(request, 'Pandoc is required for RTF to PDF conversion. Install with: brew install pandoc (macOS) or apt-get install pandoc (Linux)')
                elif 'pandoc' in error_msg.lower():
                    messages.error(request, f'Pandoc error: {error_msg}. Please ensure pandoc is properly installed.')
                elif 'weasyprint' in error_msg.lower():
                    messages.error(request, f'WeasyPrint error: {error_msg}. Please ensure weasyprint is properly installed.')
                else:
                    messages.error(request, f'Error converting RTF to PDF: {error_msg}')
                return render(request, 'pdf_tools/universal.html', _get_universal_context())
        
        # HTML to PDF (default when output is PDF)
        else:
            if not WEASYPRINT_AVAILABLE:
                messages.error(request, 'HTML to PDF conversion requires weasyprint. Install with: pip install weasyprint')
                return render(request, 'pdf_tools/universal.html', _get_universal_context())
            
            html_content = request.POST.get('html_content', '').strip()
            
            if input_file:
                max_size = 10 * 1024 * 1024  # 10MB for HTML
                if input_file.size > max_size:
                    messages.error(request, f'File size exceeds 10MB limit. Your file is {input_file.size / (1024 * 1024):.1f}MB.')
                    return render(request, 'pdf_tools/universal.html', _get_universal_context())
                html_content = input_file.read().decode('utf-8', errors='ignore')
            
            if not html_content:
                messages.error(request, 'Please provide HTML content or upload an HTML file.')
                return render(request, 'pdf_tools/universal.html', _get_universal_context())
            
            try:
                import re
                
                def process_images(html):
                    img_pattern = r'<img([^>]*?)src=["\']([^"\']*?)["\']([^>]*?)>'
                    def replace_img(match):
                        src = match.group(2)
                        if src.startswith('data:'):
                            return match.group(0)
                        return match.group(0)
                    return re.sub(img_pattern, replace_img, html, flags=re.IGNORECASE)
                
                processed_html = process_images(html_content)
                
                if not processed_html.strip().startswith('<!DOCTYPE') and not processed_html.strip().startswith('<html'):
                    processed_html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @page {{
            margin: 2cm;
            size: A4;
        }}
        body {{
            font-family: Arial, Helvetica, sans-serif;
        }}
        * {{
            box-sizing: border-box;
        }}
    </style>
</head>
<body>
{processed_html}
</body>
</html>'''
                
                pdf_buffer = io.BytesIO()
                html_doc = HTML(string=processed_html)
                html_doc.write_pdf(pdf_buffer, stylesheets=None, presentational_hints=True)
                pdf_buffer.seek(0)
                
                response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="converted.pdf"'
                return response
                
            except Exception as e:
                error_msg = str(e)
                if 'image' in error_msg.lower() or 'url' in error_msg.lower():
                    messages.error(request, f'Error loading resources: {error_msg}. Make sure all images use absolute URLs or data URIs.')
                else:
                    messages.error(request, f'Error converting HTML to PDF: {error_msg}')
                return render(request, 'pdf_tools/universal.html', _get_universal_context())
    
    # Handle PDF to other formats
    if 'input_file' not in request.FILES:
        messages.error(request, 'Please upload a file.')
        return render(request, 'pdf_tools/universal.html', _get_universal_context())
    
    input_file = request.FILES['input_file']
    max_size = 50 * 1024 * 1024  # 50MB
    if input_file.size > max_size:
        messages.error(request, f'File size exceeds 50MB limit. Your file is {input_file.size / (1024 * 1024):.1f}MB.')
        return render(request, 'pdf_tools/universal.html', _get_universal_context())
    
    # PDF to Images
    if output_format in ['png', 'jpg', 'jpeg']:
        if not PDF2IMAGE_AVAILABLE:
            messages.error(request, 'PDF to images conversion requires pdf2image and poppler. Install with: brew install poppler (macOS) or apt-get install poppler-utils (Linux)')
            return render(request, 'pdf_tools/universal.html', _get_universal_context())
        
        if not input_file.name.lower().endswith('.pdf'):
            messages.error(request, 'Please upload a valid PDF file.')
            return render(request, 'pdf_tools/universal.html', _get_universal_context())
        
        try:
            pdf_data = input_file.read()
            images = convert_from_bytes(pdf_data, dpi=200)
            
            if not images:
                messages.error(request, 'No images could be extracted from the PDF.')
                return render(request, 'pdf_tools/universal.html', _get_universal_context())
            
            image_format = 'JPEG' if output_format in ['jpg', 'jpeg'] else 'PNG'
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for i, image in enumerate(images):
                    img_buffer = io.BytesIO()
                    image.save(img_buffer, format=image_format)
                    img_buffer.seek(0)
                    ext = 'jpg' if output_format in ['jpg', 'jpeg'] else 'png'
                    zip_file.writestr(f'page_{i + 1}.{ext}', img_buffer.read())
            
            zip_buffer.seek(0)
            response = HttpResponse(zip_buffer.read(), content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename="pdf_images.zip"'
            return response
            
        except Exception as e:
            error_msg = str(e)
            if 'poppler' in error_msg.lower() or 'pdftoppm' in error_msg.lower():
                messages.error(request, 'Poppler is required for PDF to images conversion. Install with: brew install poppler (macOS)')
            else:
                messages.error(request, f'Error converting PDF to images: {error_msg}')
            return render(request, 'pdf_tools/universal.html', _get_universal_context())
    
    # PDF to HTML
    elif output_format == 'html':
        if not input_file.name.lower().endswith('.pdf'):
            messages.error(request, 'Please upload a valid PDF file.')
            return render(request, 'pdf_tools/universal.html', _get_universal_context())
        
        try:
            import base64
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                for chunk in input_file.chunks():
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name
            
            try:
                html_content = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>PDF Content</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }
        .page {
            background: white;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            max-width: 100%;
            margin-left: auto;
            margin-right: auto;
        }
        .page-header {
            border-bottom: 2px solid #333;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        .content {
            line-height: 1.6;
            color: #333;
        }
        img {
            max-width: 100%;
            height: auto;
            margin: 10px 0;
            display: block;
        }
        p {
            margin: 10px 0;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
            border: 1px solid #ddd;
        }
        table th, table td {
            border: 1px solid #ddd;
            padding: 8px 12px;
            text-align: left;
        }
        table th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        table tr:nth-child(even) {
            background-color: #f9f9f9;
        }
    </style>
</head>
<body>
'''
                
                if PDFPLUMBER_AVAILABLE:
                    with pdfplumber.open(tmp_path) as pdf:
                        for page_num, page in enumerate(pdf.pages, 1):
                            html_content += f'<div class="page">\n'
                            html_content += f'<div class="page-header"><h2>Page {page_num}</h2></div>\n'
                            html_content += '<div class="content">\n'
                            
                            tables = page.extract_tables()
                            if tables:
                                for table in tables:
                                    if table and len(table) > 0:
                                        html_content += '<table>\n'
                                        is_first = True
                                        for row in table:
                                            if row and any(cell for cell in row if cell):
                                                html_content += '<tr>\n'
                                                for cell in row:
                                                    cell_text = str(cell).strip() if cell else ''
                                                    cell_text = cell_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                                                    tag = 'th' if is_first else 'td'
                                                    html_content += f'<{tag}>{cell_text}</{tag}>\n'
                                                html_content += '</tr>\n'
                                                is_first = False
                                        html_content += '</table>\n'
                            
                            text = page.extract_text()
                            if text and text.strip():
                                paragraphs = text.split('\n\n')
                                for para in paragraphs:
                                    para = para.strip()
                                    if para and len(para) > 2:
                                        para = para.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                                        para = para.replace('\n', '<br>')
                                        html_content += f'<p>{para}</p>\n'
                            
                            if page.images:
                                for img in page.images:
                                    try:
                                        cropped = page.crop((img['x0'], img['top'], img['x1'], img['bottom']))
                                        img_obj = cropped.to_image(resolution=150)
                                        img_buffer = io.BytesIO()
                                        img_obj.save(img_buffer, format='PNG')
                                        img_buffer.seek(0)
                                        img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
                                        html_content += f'<img src="data:image/png;base64,{img_base64}" alt="Image" />\n'
                                    except (OSError, PermissionError):
                                        pass
                            
                            html_content += '</div>\n'
                            html_content += '</div>\n'
                else:
                    pdf_reader = PdfReader(open(tmp_path, 'rb'))
                    for page_num, page in enumerate(pdf_reader.pages, 1):
                        html_content += f'<div class="page">\n'
                        html_content += f'<div class="page-header"><h2>Page {page_num}</h2></div>\n'
                        html_content += '<div class="content">\n'
                        
                        text = page.extract_text()
                        if text.strip():
                            paragraphs = text.split('\n\n')
                            for para in paragraphs:
                                para = para.strip()
                                if para:
                                    para = para.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                                    para = para.replace('\n', '<br>')
                                    html_content += f'<p>{para}</p>\n'
                        
                        html_content += '</div>\n'
                        html_content += '</div>\n'
                
                html_content += '</body></html>'
                
                response = HttpResponse(html_content, content_type='text/html; charset=utf-8')
                response['Content-Disposition'] = 'attachment; filename="converted.html"'
                return response
                
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            
        except Exception as e:
            messages.error(request, f'Error converting PDF to HTML: {str(e)}')
            return render(request, 'pdf_tools/universal.html', _get_universal_context())
    
    # PDF to Text
    elif output_format == 'txt':
        if not input_file.name.lower().endswith('.pdf'):
            messages.error(request, 'Please upload a valid PDF file.')
            return render(request, 'pdf_tools/universal.html', _get_universal_context())
        
        try:
            pdf_reader = PdfReader(input_file)
            text_content = []
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                text = page.extract_text()
                if text.strip():
                    text_content.append(f'--- Page {page_num} ---\n{text}\n')
            
            if not text_content:
                messages.error(request, 'No text could be extracted from the PDF.')
                return render(request, 'pdf_tools/universal.html', _get_universal_context())
            
            full_text = '\n'.join(text_content)
            
            response = HttpResponse(full_text, content_type='text/plain; charset=utf-8')
            response['Content-Disposition'] = 'attachment; filename="extracted_text.txt"'
            return response
            
        except Exception as e:
            messages.error(request, f'Error extracting text from PDF: {str(e)}')
            return render(request, 'pdf_tools/universal.html', _get_universal_context())
    
    # PDF to SVG
    elif output_format == 'svg':
        if not input_file:
            messages.error(request, 'Please upload a PDF file.')
            return render(request, 'pdf_tools/universal.html', _get_universal_context())
        
        if not input_file.name.lower().endswith('.pdf'):
            messages.error(request, 'Please upload a valid PDF file.')
            return render(request, 'pdf_tools/universal.html', _get_universal_context())
        
        # PyMuPDF is required for PDF to SVG conversion
        if not PYMUPDF_AVAILABLE:
            messages.error(request, 'PDF to SVG conversion requires PyMuPDF. Install with: pip install pymupdf')
            return render(request, 'pdf_tools/universal.html', _get_universal_context())
        
        # Import fitz (PyMuPDF)
        try:
            import fitz
        except ImportError as import_err:
            messages.error(request, f'PyMuPDF import failed: {str(import_err)}. Please ensure PyMuPDF is installed: pip install pymupdf')
            return render(request, 'pdf_tools/universal.html', _get_universal_context())
        
        try:
            # Reset file pointer to beginning in case it was read before
            if hasattr(input_file, 'seek'):
                input_file.seek(0)
            
            # Write uploaded file to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                for chunk in input_file.chunks():
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name
            
            try:
                # Open PDF with PyMuPDF
                doc = fitz.open(tmp_path)
                num_pages = len(doc)
                
                if num_pages == 0:
                    messages.error(request, 'The PDF file appears to be empty.')
                    doc.close()
                    return render(request, 'pdf_tools/universal.html', _get_universal_context())
                
                # If single page, return single SVG file
                if num_pages == 1:
                    page = doc[0]
                    svg_data = page.get_svg_image()
                    doc.close()
                    
                    if not svg_data:
                        messages.error(request, 'Failed to generate SVG from PDF. The PDF may be corrupted or contain unsupported content.')
                        return render(request, 'pdf_tools/universal.html', _get_universal_context())
                    
                    # Ensure SVG data is properly encoded as bytes
                    if isinstance(svg_data, str):
                        svg_data = svg_data.encode('utf-8')
                    
                    response = HttpResponse(svg_data, content_type='image/svg+xml; charset=utf-8')
                    response['Content-Disposition'] = 'attachment; filename="converted.svg"'
                    return response
                
                # Multiple pages - create ZIP
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for page_num in range(num_pages):
                        page = doc[page_num]
                        svg_data = page.get_svg_image()
                        if not svg_data:
                            continue  # Skip empty pages
                        # Ensure SVG data is bytes for ZIP
                        if isinstance(svg_data, str):
                            svg_data = svg_data.encode('utf-8')
                        zip_file.writestr(f'page_{page_num + 1}.svg', svg_data)
                
                doc.close()
                zip_buffer.seek(0)
                
                response = HttpResponse(zip_buffer.read(), content_type='application/zip')
                response['Content-Disposition'] = 'attachment; filename="pdf_svg.zip"'
                return response
                
            finally:
                if os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass  # Ignore cleanup errors
            
        except Exception as e:
            import traceback
            error_msg = str(e)
            error_details = traceback.format_exc()
            # Log full error for debugging (in production, use proper logging)
            print(f"PDF to SVG conversion error: {error_msg}")
            print(f"Traceback: {error_details}")
            
            # Provide user-friendly error message
            if 'fitz' in error_msg.lower() or 'pymupdf' in error_msg.lower():
                messages.error(request, f'Error with PyMuPDF library: {error_msg}. Please ensure PyMuPDF is properly installed.')
            elif 'permission' in error_msg.lower() or 'access' in error_msg.lower():
                messages.error(request, f'File access error: {error_msg}. Please try again.')
            else:
                messages.error(request, f'Error converting PDF to SVG: {error_msg}')
            return render(request, 'pdf_tools/universal.html', _get_universal_context())
    
    # PDF to RTF
    elif output_format == 'rtf':
        if not input_file.name.lower().endswith('.pdf'):
            messages.error(request, 'Please upload a valid PDF file.')
            return render(request, 'pdf_tools/universal.html', _get_universal_context())
        
        try:
            # Extract text from PDF
            pdf_reader = PdfReader(input_file)
            text_content = []
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                text = page.extract_text()
                if text.strip():
                    text_content.append(text)
            
            if not text_content:
                messages.error(request, 'No text could be extracted from the PDF.')
                return render(request, 'pdf_tools/universal.html', _get_universal_context())
            
            # Create RTF document with Unicode support
            # RTF header with Unicode code page
            rtf_content = '{\\rtf1\\ansi\\ansicpg1252\\deff0\\nouicompat\\deflang1033\n'
            rtf_content += '{\\fonttbl{\\f0\\fnil\\fcharset0 Times New Roman;}}\n'
            rtf_content += '{\\colortbl;\\red0\\green0\\blue0;}\n'
            rtf_content += '\\f0\\fs24\\lang1033\n'
            
            # Add text content with proper Unicode encoding
            full_text = '\n\n'.join(text_content)
            
            # Convert text to RTF format with proper Unicode encoding
            def encode_rtf_text(text):
                """Encode text to RTF format with Unicode support"""
                result = []
                for char in text:
                    code = ord(char)
                    # ASCII characters (0-127) - escape special RTF characters
                    if code < 128:
                        if char == '\\':
                            result.append('\\\\')
                        elif char == '{':
                            result.append('\\{')
                        elif char == '}':
                            result.append('\\}')
                        elif char == '\n':
                            result.append('\\par\n')
                        elif char == '\r':
                            result.append('')
                        elif char == '\t':
                            result.append('\\tab ')
                        else:
                            result.append(char)
                    # Unicode characters (128+) - use RTF Unicode escape
                    else:
                        # RTF Unicode format: \uN? where N is signed 16-bit integer
                        # For characters > 32767, we need to handle them differently
                        if code <= 32767:
                            result.append(f'\\u{code}?')
                        else:
                            # For characters beyond 16-bit, use UTF-8 encoding
                            # But RTF doesn't support this well, so we'll try to represent it
                            result.append(f'\\u{code & 0xFFFF}?')
                return ''.join(result)
            
            rtf_text = encode_rtf_text(full_text)
            
            rtf_content += rtf_text
            rtf_content += '\n}'
            
            # Convert to bytes with proper encoding
            # RTF files should use Windows-1252 encoding for best compatibility
            try:
                rtf_data = rtf_content.encode('windows-1252', errors='replace')
            except (LookupError, UnicodeEncodeError):
                # Fallback to UTF-8 if windows-1252 is not available
                rtf_data = rtf_content.encode('utf-8')
            
            response = HttpResponse(rtf_data, content_type='application/rtf')
            response['Content-Disposition'] = 'attachment; filename="converted.rtf"'
            return response
            
        except Exception as e:
            error_msg = str(e)
            messages.error(request, f'Error converting PDF to RTF: {error_msg}')
            return render(request, 'pdf_tools/universal.html', _get_universal_context())
    
    else:
        messages.error(request, 'Invalid output format selected.')
        return render(request, 'pdf_tools/universal.html', _get_universal_context())

def pdf_merge(request):
    """Merge multiple PDF files into one"""
    if request.method != 'POST':
        return render(request, 'pdf_tools/pdf_merge.html')
    
    if 'pdf_files' not in request.FILES:
        messages.error(request, 'Please upload at least one PDF file.')
        return render(request, 'pdf_tools/pdf_merge.html')
    
    pdf_files = request.FILES.getlist('pdf_files')
    
    if len(pdf_files) < 2:
        messages.error(request, 'Please upload at least 2 PDF files to merge.')
        return render(request, 'pdf_tools/pdf_merge.html')
    
    # Validate file sizes (max 50MB per PDF for merge)
    max_size = 50 * 1024 * 1024  # 50MB
    for pdf_file in pdf_files:
        if pdf_file.size > max_size:
            messages.error(request, f'{pdf_file.name} exceeds 50MB limit. Your file is {pdf_file.size / (1024 * 1024):.1f}MB.')
            return render(request, 'pdf_tools/pdf_merge.html')
    
    try:
        merger = PdfWriter()
        
        for pdf_file in pdf_files:
            if not pdf_file.name.lower().endswith('.pdf'):
                messages.error(request, f'{pdf_file.name} is not a PDF file.')
                return render(request, 'pdf_tools/pdf_merge.html')
            
            pdf_reader = PdfReader(pdf_file)
            for page in pdf_reader.pages:
                merger.add_page(page)
        
        # Create merged PDF in memory
        output = io.BytesIO()
        merger.write(output)
        output.seek(0)
        
        # Return merged PDF
        response = HttpResponse(output.read(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="merged.pdf"'
        return response
        
    except Exception as e:
        messages.error(request, f'Error merging PDFs: {str(e)}')
        return render(request, 'pdf_tools/pdf_merge.html')

def pdf_split(request):
    """Split PDF into individual pages"""
    if request.method != 'POST':
        return render(request, 'pdf_tools/pdf_split.html')
    
    if 'pdf_file' not in request.FILES:
        messages.error(request, 'Please upload a PDF file.')
        return render(request, 'pdf_tools/pdf_split.html')
    
    pdf_file = request.FILES['pdf_file']
    
    # Validate file size (max 50MB for PDFs)
    max_size = 50 * 1024 * 1024  # 50MB
    if pdf_file.size > max_size:
        messages.error(request, f'File size exceeds 50MB limit. Your file is {pdf_file.size / (1024 * 1024):.1f}MB.')
        return render(request, 'pdf_tools/pdf_split.html')
    
    if not pdf_file.name.lower().endswith('.pdf'):
        messages.error(request, 'Please upload a valid PDF file.')
        return render(request, 'pdf_tools/pdf_split.html')
    
    try:
        pdf_reader = PdfReader(pdf_file)
        num_pages = len(pdf_reader.pages)
        
        if num_pages == 0:
            messages.error(request, 'The PDF file appears to be empty.')
            return render(request, 'pdf_tools/pdf_split.html')
        
        # Create ZIP file with all pages
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for page_num in range(num_pages):
                writer = PdfWriter()
                writer.add_page(pdf_reader.pages[page_num])
                
                page_output = io.BytesIO()
                writer.write(page_output)
                page_output.seek(0)
                
                zip_file.writestr(f'page_{page_num + 1}.pdf', page_output.read())
        
        zip_buffer.seek(0)
        
        # Return ZIP file
        response = HttpResponse(zip_buffer.read(), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="split_pages.zip"'
        return response
        
    except Exception as e:
        messages.error(request, f'Error splitting PDF: {str(e)}')
        return render(request, 'pdf_tools/pdf_split.html')

def pdf_to_images(request):
    """Convert PDF pages to images"""
    if not PDF2IMAGE_AVAILABLE:
        messages.error(request, 'PDF to images conversion requires pdf2image and poppler. Install with: brew install poppler (macOS) or apt-get install poppler-utils (Linux)')
        return render(request, 'pdf_tools/pdf_to_images.html')
    
    if request.method != 'POST':
        return render(request, 'pdf_tools/pdf_to_images.html')
    
    if 'pdf_file' not in request.FILES:
        messages.error(request, 'Please upload a PDF file.')
        return render(request, 'pdf_tools/pdf_to_images.html')
    
    pdf_file = request.FILES['pdf_file']
    
    # Validate file size (max 50MB for PDFs)
    max_size = 50 * 1024 * 1024  # 50MB
    if pdf_file.size > max_size:
        messages.error(request, f'File size exceeds 50MB limit. Your file is {pdf_file.size / (1024 * 1024):.1f}MB.')
        return render(request, 'pdf_tools/pdf_to_images.html')
    
    if not pdf_file.name.lower().endswith('.pdf'):
        messages.error(request, 'Please upload a valid PDF file.')
        return render(request, 'pdf_tools/pdf_to_images.html')
    
    try:
        pdf_data = pdf_file.read()
        images = convert_from_bytes(pdf_data, dpi=200)
        
        if not images:
            messages.error(request, 'No images could be extracted from the PDF.')
            return render(request, 'pdf_tools/pdf_to_images.html')
        
        # Create ZIP file with all images
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for i, image in enumerate(images):
                img_buffer = io.BytesIO()
                image.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                zip_file.writestr(f'page_{i + 1}.png', img_buffer.read())
        
        zip_buffer.seek(0)
        
        # Return ZIP file
        response = HttpResponse(zip_buffer.read(), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="pdf_images.zip"'
        return response
        
    except Exception as e:
        error_msg = str(e)
        if 'poppler' in error_msg.lower() or 'pdftoppm' in error_msg.lower():
            messages.error(request, 'Poppler is required for PDF to images conversion. Install with: brew install poppler (macOS)')
        else:
            messages.error(request, f'Error converting PDF to images: {error_msg}')
        return render(request, 'pdf_tools/pdf_to_images.html')

def pdf_to_html(request):
    """Convert PDF to HTML with better formatting and table preservation"""
    if request.method != 'POST':
        return render(request, 'pdf_tools/pdf_to_html.html', {
            'pdfplumber_available': PDFPLUMBER_AVAILABLE
        })
    
    if 'pdf_file' not in request.FILES:
        messages.error(request, 'Please upload a PDF file.')
        return render(request, 'pdf_tools/pdf_to_html.html', {
            'pdfplumber_available': PDFPLUMBER_AVAILABLE
        })
    
    pdf_file = request.FILES['pdf_file']
    
    max_size = 50 * 1024 * 1024  # 50MB
    if pdf_file.size > max_size:
        messages.error(request, f'File size exceeds 50MB limit. Your file is {pdf_file.size / (1024 * 1024):.1f}MB.')
        return render(request, 'pdf_tools/pdf_to_html.html', {
            'pdfplumber_available': PDFPLUMBER_AVAILABLE
        })
    
    if not pdf_file.name.lower().endswith('.pdf'):
        messages.error(request, 'Please upload a valid PDF file.')
        return render(request, 'pdf_tools/pdf_to_html.html', {
            'pdfplumber_available': PDFPLUMBER_AVAILABLE
        })
    
    try:
        import base64
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            for chunk in pdf_file.chunks():
                tmp_file.write(chunk)
            tmp_path = tmp_file.name
        
        try:
            html_content = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>PDF Content</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }
        .page {
            background: white;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            max-width: 100%;
            margin-left: auto;
            margin-right: auto;
        }
        .page-header {
            border-bottom: 2px solid #333;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        .content {
            line-height: 1.6;
            color: #333;
        }
        img {
            max-width: 100%;
            height: auto;
            margin: 10px 0;
            display: block;
        }
        p {
            margin: 10px 0;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
            border: 1px solid #ddd;
        }
        table th, table td {
            border: 1px solid #ddd;
            padding: 8px 12px;
            text-align: left;
        }
        table th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        table tr:nth-child(even) {
            background-color: #f9f9f9;
        }
    </style>
</head>
<body>
'''
            
            # Use pdfplumber if available for better table extraction
            if PDFPLUMBER_AVAILABLE:
                with pdfplumber.open(tmp_path) as pdf:
                    for page_num, page in enumerate(pdf.pages, 1):
                        html_content += f'<div class="page">\n'
                        html_content += f'<div class="page-header"><h2>Page {page_num}</h2></div>\n'
                        html_content += '<div class="content">\n'
                        
                        # Extract tables first
                        tables = page.extract_tables()
                        if tables:
                            for table in tables:
                                if table and len(table) > 0:
                                    html_content += '<table>\n'
                                    # First row as header if it looks like one
                                    is_first = True
                                    for row in table:
                                        if row and any(cell for cell in row if cell):
                                            html_content += '<tr>\n'
                                            for cell in row:
                                                cell_text = str(cell).strip() if cell else ''
                                                cell_text = cell_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                                                tag = 'th' if is_first else 'td'
                                                html_content += f'<{tag}>{cell_text}</{tag}>\n'
                                            html_content += '</tr>\n'
                                            is_first = False
                                    html_content += '</table>\n'
                        
                        # Extract text (excluding table text to avoid duplication)
                        text = page.extract_text()
                        if text and text.strip():
                            # Split into paragraphs
                            paragraphs = text.split('\n\n')
                            for para in paragraphs:
                                para = para.strip()
                                if para and len(para) > 2:  # Skip very short fragments
                                    # Escape HTML
                                    para = para.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                                    # Preserve line breaks
                                    para = para.replace('\n', '<br>')
                                    html_content += f'<p>{para}</p>\n'
                        
                        # Extract images
                        if page.images:
                            for img in page.images:
                                try:
                                    # Try to extract image
                                    cropped = page.crop((img['x0'], img['top'], img['x1'], img['bottom']))
                                    img_obj = cropped.to_image(resolution=150)
                                    img_buffer = io.BytesIO()
                                    img_obj.save(img_buffer, format='PNG')
                                    img_buffer.seek(0)
                                    img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
                                    html_content += f'<img src="data:image/png;base64,{img_base64}" alt="Image" />\n'
                                except (OSError, PermissionError):
                                    pass
                        
                        html_content += '</div>\n'
                        html_content += '</div>\n'
            else:
                # Fallback to pypdf if pdfplumber not available
                pdf_reader = PdfReader(open(tmp_path, 'rb'))
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    html_content += f'<div class="page">\n'
                    html_content += f'<div class="page-header"><h2>Page {page_num}</h2></div>\n'
                    html_content += '<div class="content">\n'
                    
                    text = page.extract_text()
                    if text.strip():
                        paragraphs = text.split('\n\n')
                        for para in paragraphs:
                            para = para.strip()
                            if para:
                                para = para.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                                para = para.replace('\n', '<br>')
                                html_content += f'<p>{para}</p>\n'
                    
                    html_content += '</div>\n'
                    html_content += '</div>\n'
            
            html_content += '</body></html>'
            
            response = HttpResponse(html_content, content_type='text/html; charset=utf-8')
            response['Content-Disposition'] = 'attachment; filename="converted.html"'
            return response
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        
    except Exception as e:
        messages.error(request, f'Error converting PDF to HTML: {str(e)}')
        return render(request, 'pdf_tools/pdf_to_html.html', {
            'pdfplumber_available': PDFPLUMBER_AVAILABLE
        })

def html_to_pdf(request):
    """Convert HTML to PDF with better design preservation"""
    if not WEASYPRINT_AVAILABLE:
        messages.error(request, 'HTML to PDF conversion requires weasyprint. Install with: pip install weasyprint')
        return render(request, 'pdf_tools/html_to_pdf.html')
    
    if request.method != 'POST':
        return render(request, 'pdf_tools/html_to_pdf.html')
    
    html_content = request.POST.get('html_content', '').strip()
    html_file = None
    
    if 'html_file' in request.FILES:
        html_file = request.FILES['html_file']
        max_size = 10 * 1024 * 1024  # 10MB for HTML
        if html_file.size > max_size:
            messages.error(request, f'File size exceeds 10MB limit. Your file is {html_file.size / (1024 * 1024):.1f}MB.')
            return render(request, 'pdf_tools/html_to_pdf.html')
        html_content = html_file.read().decode('utf-8', errors='ignore')
    
    if not html_content:
        messages.error(request, 'Please provide HTML content or upload an HTML file.')
        return render(request, 'pdf_tools/html_to_pdf.html')
    
    try:
        import re
        from urllib.parse import urljoin, urlparse
        
        # Process HTML to handle relative URLs and embedded resources
        # Convert relative image URLs to data URIs if possible
        def process_images(html):
            # Find all img tags with src attributes
            img_pattern = r'<img([^>]*?)src=["\']([^"\']*?)["\']([^>]*?)>'
            def replace_img(match):
                attrs_before = match.group(1)
                src = match.group(2)
                attrs_after = match.group(3)
                
                # If it's already a data URI, keep it
                if src.startswith('data:'):
                    return match.group(0)
                
                # If it's a relative path, try to convert to absolute
                # For now, we'll keep relative paths and let WeasyPrint handle them
                return match.group(0)
            
            return re.sub(img_pattern, replace_img, html, flags=re.IGNORECASE)
        
        # Process the HTML
        processed_html = process_images(html_content)
        
        # Ensure HTML has proper structure if it's just a fragment
        if not processed_html.strip().startswith('<!DOCTYPE') and not processed_html.strip().startswith('<html'):
            processed_html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @page {{
            margin: 2cm;
            size: A4;
        }}
        body {{
            font-family: Arial, Helvetica, sans-serif;
        }}
        /* Preserve common CSS properties */
        * {{
            box-sizing: border-box;
        }}
    </style>
</head>
<body>
{processed_html}
</body>
</html>'''
        
        # Create PDF with better options
        pdf_buffer = io.BytesIO()
        
        # Use WeasyPrint with better settings
        html_doc = HTML(string=processed_html)
        html_doc.write_pdf(
            pdf_buffer,
            stylesheets=None,  # CSS is already in HTML
            presentational_hints=True,  # Preserve presentational hints
        )
        pdf_buffer.seek(0)
        
        response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="converted.pdf"'
        return response
        
    except Exception as e:
        error_msg = str(e)
        # Provide more helpful error messages
        if 'image' in error_msg.lower() or 'url' in error_msg.lower():
            messages.error(request, f'Error loading resources: {error_msg}. Make sure all images use absolute URLs or data URIs.')
        else:
            messages.error(request, f'Error converting HTML to PDF: {error_msg}')
        return render(request, 'pdf_tools/html_to_pdf.html')

def pdf_to_text(request):
    """Extract text from PDF"""
    if request.method != 'POST':
        return render(request, 'pdf_tools/pdf_to_text.html')
    
    if 'pdf_file' not in request.FILES:
        messages.error(request, 'Please upload a PDF file.')
        return render(request, 'pdf_tools/pdf_to_text.html')
    
    pdf_file = request.FILES['pdf_file']
    
    max_size = 50 * 1024 * 1024  # 50MB
    if pdf_file.size > max_size:
        messages.error(request, f'File size exceeds 50MB limit. Your file is {pdf_file.size / (1024 * 1024):.1f}MB.')
        return render(request, 'pdf_tools/pdf_to_text.html')
    
    if not pdf_file.name.lower().endswith('.pdf'):
        messages.error(request, 'Please upload a valid PDF file.')
        return render(request, 'pdf_tools/pdf_to_text.html')
    
    try:
        pdf_reader = PdfReader(pdf_file)
        text_content = []
        
        for page_num, page in enumerate(pdf_reader.pages, 1):
            text = page.extract_text()
            if text.strip():
                text_content.append(f'--- Page {page_num} ---\n{text}\n')
        
        if not text_content:
            messages.error(request, 'No text could be extracted from the PDF.')
            return render(request, 'pdf_tools/pdf_to_text.html')
        
        full_text = '\n'.join(text_content)
        
        response = HttpResponse(full_text, content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="extracted_text.txt"'
        return response
        
    except Exception as e:
        messages.error(request, f'Error extracting text from PDF: {str(e)}')
        return render(request, 'pdf_tools/pdf_to_text.html')

def pdf_compress(request):
    """Compress PDF file size"""
    if request.method != 'POST':
        return render(request, 'pdf_tools/pdf_compress.html')
    
    if 'pdf_file' not in request.FILES:
        messages.error(request, 'Please upload a PDF file.')
        return render(request, 'pdf_tools/pdf_compress.html')
    
    pdf_file = request.FILES['pdf_file']
    
    max_size = 50 * 1024 * 1024  # 50MB
    if pdf_file.size > max_size:
        messages.error(request, f'File size exceeds 50MB limit. Your file is {pdf_file.size / (1024 * 1024):.1f}MB.')
        return render(request, 'pdf_tools/pdf_compress.html')
    
    if not pdf_file.name.lower().endswith('.pdf'):
        messages.error(request, 'Please upload a valid PDF file.')
        return render(request, 'pdf_tools/pdf_compress.html')
    
    try:
        pdf_reader = PdfReader(pdf_file)
        writer = PdfWriter()
        
        # Copy all pages
        for page in pdf_reader.pages:
            writer.add_page(page)
        
        # Compress by removing unnecessary objects and optimizing
        writer.compress_identical_objects = True
        
        output = io.BytesIO()
        writer.write(output)
        output.seek(0)
        
        compressed_data = output.read()
        original_size = pdf_file.size
        compressed_size = len(compressed_data)
        
        # If compression didn't help much, return original
        if compressed_size >= original_size * 0.95:
            messages.info(request, f'PDF could not be compressed further. Original: {original_size / 1024:.1f}KB, Compressed: {compressed_size / 1024:.1f}KB')
        
        response = HttpResponse(compressed_data, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="compressed.pdf"'
        return response
        
    except Exception as e:
        messages.error(request, f'Error compressing PDF: {str(e)}')
        return render(request, 'pdf_tools/pdf_compress.html')

def pdf_rotate(request):
    """Rotate PDF pages"""
    if request.method != 'POST':
        return render(request, 'pdf_tools/pdf_rotate.html')
    
    if 'pdf_file' not in request.FILES:
        messages.error(request, 'Please upload a PDF file.')
        return render(request, 'pdf_tools/pdf_rotate.html')
    
    pdf_file = request.FILES['pdf_file']
    
    max_size = 50 * 1024 * 1024  # 50MB
    if pdf_file.size > max_size:
        messages.error(request, f'File size exceeds 50MB limit. Your file is {pdf_file.size / (1024 * 1024):.1f}MB.')
        return render(request, 'pdf_tools/pdf_rotate.html')
    
    if not pdf_file.name.lower().endswith('.pdf'):
        messages.error(request, 'Please upload a valid PDF file.')
        return render(request, 'pdf_tools/pdf_rotate.html')
    
    try:
        rotation = int(request.POST.get('rotation', 90))
        if rotation not in [90, 180, 270]:
            rotation = 90
        
        pdf_reader = PdfReader(pdf_file)
        writer = PdfWriter()
        
        for page in pdf_reader.pages:
            page.rotate(rotation)
            writer.add_page(page)
        
        output = io.BytesIO()
        writer.write(output)
        output.seek(0)
        
        response = HttpResponse(output.read(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="rotated.pdf"'
        return response
        
    except Exception as e:
        messages.error(request, f'Error rotating PDF: {str(e)}')
        return render(request, 'pdf_tools/pdf_rotate.html')

def pdf_ocr(request):
    """OCR PDF to make it searchable"""
    if request.method != 'POST':
        return render(request, 'pdf_tools/pdf_ocr.html', {
            'pytesseract_available': PYTESSERACT_AVAILABLE,
            'pdf2image_available': PDF2IMAGE_AVAILABLE,
        })
    
    if 'pdf_file' not in request.FILES:
        messages.error(request, 'Please upload a PDF file.')
        return render(request, 'pdf_tools/pdf_ocr.html', {
            'pytesseract_available': PYTESSERACT_AVAILABLE,
            'pdf2image_available': PDF2IMAGE_AVAILABLE,
        })
    
    pdf_file = request.FILES['pdf_file']
    
    max_size = 50 * 1024 * 1024  # 50MB
    if pdf_file.size > max_size:
        messages.error(request, f'File size exceeds 50MB limit. Your file is {pdf_file.size / (1024 * 1024):.1f}MB.')
        return render(request, 'pdf_tools/pdf_ocr.html', {
            'pytesseract_available': PYTESSERACT_AVAILABLE,
            'pdf2image_available': PDF2IMAGE_AVAILABLE,
        })
    
    if not pdf_file.name.lower().endswith('.pdf'):
        messages.error(request, 'Please upload a valid PDF file.')
        return render(request, 'pdf_tools/pdf_ocr.html', {
            'pytesseract_available': PYTESSERACT_AVAILABLE,
            'pdf2image_available': PDF2IMAGE_AVAILABLE,
        })
    
    if not PYTESSERACT_AVAILABLE or not PDF2IMAGE_AVAILABLE:
        messages.error(request, 'OCR requires pytesseract and pdf2image. Install with: pip install pytesseract pdf2image && install tesseract-ocr (brew install tesseract on macOS or apt-get install tesseract-ocr on Linux). Also install poppler: brew install poppler (macOS) or apt-get install poppler-utils (Linux)')
        return render(request, 'pdf_tools/pdf_ocr.html', {
            'pytesseract_available': PYTESSERACT_AVAILABLE,
            'pdf2image_available': PDF2IMAGE_AVAILABLE,
        })
    
    try:
        pdf_data = pdf_file.read()
        images = convert_from_bytes(pdf_data, dpi=300)  # Higher DPI for better OCR
        
        if not images:
            messages.error(request, 'No images could be extracted from the PDF.')
            return render(request, 'pdf_tools/pdf_ocr.html', {
                'pytesseract_available': PYTESSERACT_AVAILABLE,
                'pdf2image_available': PDF2IMAGE_AVAILABLE,
            })
        
        # Use PyMuPDF to create searchable PDF
        if not PYMUPDF_AVAILABLE:
            messages.error(request, 'Creating searchable PDF requires PyMuPDF. Install with: pip install pymupdf')
            return render(request, 'pdf_tools/pdf_ocr.html', {
                'pytesseract_available': PYTESSERACT_AVAILABLE,
                'pdf2image_available': PDF2IMAGE_AVAILABLE,
            })
        
        # Create new PDF with OCR text
        doc = fitz.open()  # Create new PDF
        
        for i, image in enumerate(images):
            # Convert PIL image to bytes
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            # Perform OCR
            ocr_text = pytesseract.image_to_string(image, lang='eng')
            
            # Create page with image
            page = doc.new_page(width=image.width, height=image.height)
            
            # Insert image
            img_rect = fitz.Rect(0, 0, image.width, image.height)
            page.insert_image(img_rect, stream=img_buffer.getvalue())
            
            # Add invisible text layer for searchability
            if ocr_text.strip():
                # Create text blocks from OCR results
                # Note: This is a simplified approach - for better results, use pytesseract.image_to_data
                text_rect = fitz.Rect(0, 0, image.width, image.height)
                page.insert_text(text_rect.tl, ocr_text, fontsize=1, color=(0, 0, 0), render_mode=3)  # render_mode=3 is invisible
        
        # Save to bytes
        pdf_bytes = doc.tobytes()
        doc.close()
        
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="ocr_searchable.pdf"'
        return response
        
    except Exception as e:
        error_msg = str(e)
        if 'tesseract' in error_msg.lower() or 'tesseract-ocr' in error_msg.lower():
            messages.error(request, 'Tesseract OCR is required. Install with: brew install tesseract (macOS) or apt-get install tesseract-ocr (Linux)')
        else:
            messages.error(request, f'Error performing OCR: {error_msg}')
        return render(request, 'pdf_tools/pdf_ocr.html', {
            'pytesseract_available': PYTESSERACT_AVAILABLE,
            'pdf2image_available': PDF2IMAGE_AVAILABLE,
        })

def pdf_remove_metadata(request):
    """Remove metadata from PDF"""
    if request.method != 'POST':
        return render(request, 'pdf_tools/pdf_remove_metadata.html')
    
    if 'pdf_file' not in request.FILES:
        messages.error(request, 'Please upload a PDF file.')
        return render(request, 'pdf_tools/pdf_remove_metadata.html')
    
    pdf_file = request.FILES['pdf_file']
    
    max_size = 50 * 1024 * 1024  # 50MB
    if pdf_file.size > max_size:
        messages.error(request, f'File size exceeds 50MB limit. Your file is {pdf_file.size / (1024 * 1024):.1f}MB.')
        return render(request, 'pdf_tools/pdf_remove_metadata.html')
    
    if not pdf_file.name.lower().endswith('.pdf'):
        messages.error(request, 'Please upload a valid PDF file.')
        return render(request, 'pdf_tools/pdf_remove_metadata.html')
    
    try:
        pdf_reader = PdfReader(pdf_file)
        writer = PdfWriter()
        
        # Copy all pages
        for page in pdf_reader.pages:
            writer.add_page(page)
        
        # Remove all metadata
        writer.add_metadata({})  # Empty metadata
        
        output = io.BytesIO()
        writer.write(output)
        output.seek(0)
        
        response = HttpResponse(output.read(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="no_metadata.pdf"'
        return response
        
    except Exception as e:
        messages.error(request, f'Error removing metadata: {str(e)}')
        return render(request, 'pdf_tools/pdf_remove_metadata.html')

def pdf_to_flipbook(request):
    """Convert PDF to interactive HTML flipbook"""
    if not PDF2IMAGE_AVAILABLE:
        messages.error(request, 'PDF to flipbook conversion requires pdf2image and poppler. Install with: brew install poppler (macOS) or apt-get install poppler-utils (Linux)')
        return render(request, 'pdf_tools/pdf_to_flipbook.html', {
            'pdf2image_available': PDF2IMAGE_AVAILABLE,
        })
    
    if request.method != 'POST':
        return render(request, 'pdf_tools/pdf_to_flipbook.html', {
            'pdf2image_available': PDF2IMAGE_AVAILABLE,
        })
    
    if 'pdf_files' not in request.FILES:
        messages.error(request, 'Please upload at least one PDF file.')
        return render(request, 'pdf_tools/pdf_to_flipbook.html', {
            'pdf2image_available': PDF2IMAGE_AVAILABLE,
        })
    
    pdf_files = request.FILES.getlist('pdf_files')
    
    if len(pdf_files) == 0:
        messages.error(request, 'Please upload at least one PDF file.')
        return render(request, 'pdf_tools/pdf_to_flipbook.html', {
            'pdf2image_available': PDF2IMAGE_AVAILABLE,
        })
    
    # Validate all files
    max_size = 50 * 1024 * 1024  # 50MB
    pdf_file_names = []
    for pdf_file in pdf_files:
        if not pdf_file.name.lower().endswith('.pdf'):
            messages.error(request, f'{pdf_file.name} is not a valid PDF file.')
            return render(request, 'pdf_tools/pdf_to_flipbook.html', {
                'pdf2image_available': PDF2IMAGE_AVAILABLE,
            })
        
        if pdf_file.size > max_size:
            messages.error(request, f'{pdf_file.name} exceeds 50MB limit. Your file is {pdf_file.size / (1024 * 1024):.1f}MB.')
            return render(request, 'pdf_tools/pdf_to_flipbook.html', {
                'pdf2image_available': PDF2IMAGE_AVAILABLE,
            })
        
        pdf_file_names.append(pdf_file.name)
    
    try:
        import base64
        import json
        import gc
        
        # Process all PDFs and combine pages
        all_image_data_uris = []
        pdf_metadata = []  # Track which PDF each page belongs to
        
        for pdf_file in pdf_files:
            images = None
            pdf_data = None
            try:
                # Convert PDF to images - use lower DPI to reduce memory usage
                pdf_data = pdf_file.read()
                images = convert_from_bytes(pdf_data, dpi=120)
            except Exception as conv_error:
                messages.warning(request, f'Could not convert {pdf_file.name}: {str(conv_error)}. Skipping.')
                continue
            finally:
                # Free PDF data from memory immediately
                if pdf_data is not None:
                    del pdf_data
                gc.collect()
            
            if not images:
                messages.warning(request, f'No images could be extracted from {pdf_file.name}. Skipping.')
                continue
            
            # Track metadata for this PDF
            start_page = len(all_image_data_uris)
            pdf_metadata.append({
                'name': pdf_file.name,
                'start_page': start_page,
                'end_page': start_page + len(images) - 1,
                'page_count': len(images)
            })
            
            # Convert images to base64 one at a time to save memory
            for i, image in enumerate(images):
                img_buffer = io.BytesIO()
                # Use JPEG with compression for smaller file size
                image.save(img_buffer, format='JPEG', quality=75, optimize=True)
                img_buffer.seek(0)
                img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
                all_image_data_uris.append(f'data:image/jpeg;base64,{img_base64}')
                # Clear the buffer
                img_buffer.close()
            
            # Free images from memory after processing each PDF
            if images is not None:
                del images
            gc.collect()
        
        if not all_image_data_uris:
            messages.error(request, 'No images could be extracted from any of the PDF files.')
            return render(request, 'pdf_tools/pdf_to_flipbook.html', {
                'pdf2image_available': PDF2IMAGE_AVAILABLE,
            })
        
        # Format image array for JavaScript (escape quotes properly)
        images_json = json.dumps(all_image_data_uris)
        pdf_metadata_json = json.dumps(pdf_metadata)
        
        # Check if this is a preview request
        is_preview = request.POST.get('preview', 'false').lower() == 'true'
        
        # Generate HTML flipbook
        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF Flipbook</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
            overflow-x: hidden;
        }}
        
        .flipbook-container {{
            background: #fff;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 20px;
            max-width: 1200px;
            width: 100%;
            margin: 20px auto;
            position: relative;
        }}
        
        .toolbar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 10px;
        }}
        
        .toolbar-left, .toolbar-right {{
            display: flex;
            gap: 10px;
            align-items: center;
            flex-wrap: wrap;
        }}
        
        .btn {{
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.3s;
            background: #667eea;
            color: white;
        }}
        
        .btn:hover {{
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }}
        
        .btn:active {{
            transform: translateY(0);
        }}
        
        .btn-secondary {{
            background: #6c757d;
        }}
        
        .btn-secondary:hover {{
            background: #5a6268;
        }}
        
        .page-info {{
            font-size: 16px;
            font-weight: 600;
            color: #333;
            min-width: 120px;
            text-align: center;
        }}
        
        .zoom-controls {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        
        .zoom-btn {{
            width: 36px;
            height: 36px;
            padding: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
        }}
        
        .zoom-level {{
            min-width: 60px;
            text-align: center;
            font-weight: 600;
            color: #333;
        }}
        
        .flipbook-viewer {{
            position: relative;
            width: 100%;
            min-height: 600px;
            display: flex;
            justify-content: center;
            align-items: center;
            perspective: 2000px;
            padding: 20px;
            background: #f0f0f0;
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .page-container {{
            position: relative;
            width: 100%;
            max-width: 800px;
            height: auto;
            display: flex;
            justify-content: center;
            align-items: center;
            transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        
        .page-container.zoomed {{
            transform-origin: center center;
        }}
        
        .page {{
            position: relative;
            background: white;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            border-radius: 4px;
            overflow: hidden;
            transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
            max-width: 100%;
            height: auto;
        }}
        
        .page img {{
            width: 100%;
            height: auto;
            display: block;
            user-select: none;
            pointer-events: none;
        }}
        
        .page.flipping {{
            transform: rotateY(-180deg);
        }}
        
        .page.prev-page {{
            transform: translateX(-100%) rotateY(-180deg);
            opacity: 0;
        }}
        
        .page.next-page {{
            transform: translateX(100%) rotateY(180deg);
            opacity: 0;
        }}
        
        .navigation-hint {{
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            width: 50%;
            height: 100%;
            cursor: pointer;
            z-index: 10;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            transition: opacity 0.3s;
        }}
        
        .navigation-hint:hover {{
            opacity: 0.1;
        }}
        
        .navigation-hint.prev {{
            left: 0;
        }}
        
        .navigation-hint.next {{
            right: 0;
        }}
        
        .fullscreen-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: #000;
            z-index: 9999;
            display: none;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        
        .fullscreen-overlay.active {{
            display: flex;
        }}
        
        .fullscreen-toolbar {{
            position: absolute;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 10px;
            z-index: 10000;
        }}
        
        .fullscreen-viewer {{
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: auto;
        }}
        
        .fullscreen-page-container {{
            max-width: 90%;
            max-height: 90%;
        }}
        
        .fullscreen-page {{
            max-width: 100%;
            max-height: 100%;
            box-shadow: 0 0 40px rgba(255,255,255,0.1);
        }}
        
        .fullscreen-page img {{
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }}
        
        @media (max-width: 768px) {{
            .toolbar {{
                flex-direction: column;
            }}
            
            .toolbar-left, .toolbar-right {{
                width: 100%;
                justify-content: center;
            }}
            
            .flipbook-viewer {{
                min-height: 400px;
            }}
            
            .btn {{
                padding: 8px 16px;
                font-size: 12px;
            }}
        }}
        
        .loading {{
            display: none;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            z-index: 100;
        }}
        
        .loading.active {{
            display: block;
        }}
        
        .spinner {{
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
        }}
        
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
</head>
<body>
    <div class="flipbook-container">
        <div class="toolbar">
            <div class="toolbar-left">
                <button class="btn" onclick="previousPage()" id="prevBtn">← Previous</button>
                <div class="page-info" id="pageInfo">Page 1 of {len(all_image_data_uris)}</div>
                <button class="btn" onclick="nextPage()" id="nextBtn">Next →</button>
            </div>
            <div class="toolbar-right">
                <div class="zoom-controls">
                    <button class="btn btn-secondary zoom-btn" onclick="zoomOut()">−</button>
                    <div class="zoom-level" id="zoomLevel">100%</div>
                    <button class="btn btn-secondary zoom-btn" onclick="zoomIn()">+</button>
                </div>
                <button class="btn btn-secondary" onclick="resetZoom()">Reset Zoom</button>
                <button class="btn btn-secondary" onclick="toggleFullscreen()">Fullscreen</button>
                <button class="btn btn-secondary" onclick="downloadFlipbook()">Download</button>
            </div>
        </div>
        
        <div class="flipbook-viewer" id="flipbookViewer">
            <div class="loading" id="loading">
                <div class="spinner"></div>
            </div>
            <div class="page-container" id="pageContainer">
                <div class="page" id="currentPage">
                    <img src="{all_image_data_uris[0] if all_image_data_uris else ''}" alt="Page 1" id="pageImage">
                </div>
            </div>
            <div class="navigation-hint prev" onclick="previousPage()"></div>
            <div class="navigation-hint next" onclick="nextPage()"></div>
        </div>
    </div>
    
    <div class="fullscreen-overlay" id="fullscreenOverlay">
        <div class="fullscreen-toolbar">
            <button class="btn" onclick="previousPage()">← Prev</button>
            <div class="page-info" id="fullscreenPageInfo">Page 1 of {len(all_image_data_uris)}</div>
            <button class="btn" onclick="nextPage()">Next →</button>
            <button class="btn btn-secondary" onclick="toggleFullscreen()">Exit Fullscreen</button>
        </div>
        <div class="fullscreen-viewer">
            <div class="fullscreen-page-container">
                <div class="fullscreen-page" id="fullscreenPage">
                    <img src="{all_image_data_uris[0] if all_image_data_uris else ''}" alt="Page 1" id="fullscreenImage">
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const images = {images_json};
        const pdfMetadata = {pdf_metadata_json};
        let currentPage = 0;
        let zoomLevel = 1;
        let isFullscreen = false;
        
        function getPdfInfo(pageIndex) {{
            if (!pdfMetadata || pdfMetadata.length === 0) return null;
            for (let i = 0; i < pdfMetadata.length; i++) {{
                if (pageIndex >= pdfMetadata[i].start_page && pageIndex <= pdfMetadata[i].end_page) {{
                    const localPage = pageIndex - pdfMetadata[i].start_page + 1;
                    return {{
                        name: pdfMetadata[i].name,
                        localPage: localPage,
                        totalPages: pdfMetadata[i].page_count
                    }};
                }}
            }}
            return null;
        }}
        
        function updatePage() {{
            const pageInfo = document.getElementById('pageInfo');
            const fullscreenPageInfo = document.getElementById('fullscreenPageInfo');
            const pageImage = document.getElementById('pageImage');
            const fullscreenImage = document.getElementById('fullscreenImage');
            const prevBtn = document.getElementById('prevBtn');
            const nextBtn = document.getElementById('nextBtn');
            
            const pdfInfo = getPdfInfo(currentPage);
            let pageText = `Page ${{currentPage + 1}} of ${{images.length}}`;
            if (pdfInfo && pdfMetadata.length > 1) {{
                pageText += ` (${{pdfInfo.name}} - Page ${{pdfInfo.localPage}}/${{pdfInfo.totalPages}})`;
            }}
            
            if (pageInfo) pageInfo.textContent = pageText;
            if (fullscreenPageInfo) fullscreenPageInfo.textContent = pageText;
            
            if (pageImage) {{
                pageImage.src = images[currentPage];
                pageImage.alt = `Page ${{currentPage + 1}}`;
            }}
            
            if (fullscreenImage) {{
                fullscreenImage.src = images[currentPage];
                fullscreenImage.alt = `Page ${{currentPage + 1}}`;
            }}
            
            if (prevBtn) prevBtn.disabled = currentPage === 0;
            if (nextBtn) nextBtn.disabled = currentPage === images.length - 1;
            
            applyZoom();
        }}
        
        function previousPage() {{
            if (currentPage > 0) {{
                const page = document.getElementById(isFullscreen ? 'fullscreenPage' : 'currentPage');
                if (page) {{
                    page.classList.add('flipping');
                    setTimeout(() => {{
                        currentPage--;
                        updatePage();
                        page.classList.remove('flipping');
                    }}, 300);
                }} else {{
                    currentPage--;
                    updatePage();
                }}
            }}
        }}
        
        function nextPage() {{
            if (currentPage < images.length - 1) {{
                const page = document.getElementById(isFullscreen ? 'fullscreenPage' : 'currentPage');
                if (page) {{
                    page.classList.add('flipping');
                    setTimeout(() => {{
                        currentPage++;
                        updatePage();
                        page.classList.remove('flipping');
                    }}, 300);
                }} else {{
                    currentPage++;
                    updatePage();
                }}
            }}
        }}
        
        function zoomIn() {{
            if (zoomLevel < 3) {{
                zoomLevel = Math.min(zoomLevel + 0.25, 3);
                applyZoom();
            }}
        }}
        
        function zoomOut() {{
            if (zoomLevel > 0.5) {{
                zoomLevel = Math.max(zoomLevel - 0.25, 0.5);
                applyZoom();
            }}
        }}
        
        function resetZoom() {{
            zoomLevel = 1;
            applyZoom();
        }}
        
        function applyZoom() {{
            const pageContainer = document.getElementById('pageContainer');
            const zoomLevelEl = document.getElementById('zoomLevel');
            
            if (pageContainer) {{
                pageContainer.style.transform = `scale(${{zoomLevel}})`;
                pageContainer.classList.add('zoomed');
            }}
            
            if (zoomLevelEl) {{
                zoomLevelEl.textContent = `${{Math.round(zoomLevel * 100)}}%`;
            }}
        }}
        
        function toggleFullscreen() {{
            const overlay = document.getElementById('fullscreenOverlay');
            if (!overlay) return;
            
            isFullscreen = !isFullscreen;
            
            if (isFullscreen) {{
                overlay.classList.add('active');
                updatePage();
            }} else {{
                overlay.classList.remove('active');
            }}
        }}
        
        function downloadFlipbook() {{
            const link = document.createElement('a');
            link.href = 'data:text/html;charset=utf-8,' + encodeURIComponent(document.documentElement.outerHTML);
            link.download = 'flipbook.html';
            link.click();
        }}
        
        // Keyboard navigation
        document.addEventListener('keydown', function(e) {{
            if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {{
                e.preventDefault();
                previousPage();
            }} else if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {{
                e.preventDefault();
                nextPage();
            }} else if (e.key === 'Escape' && isFullscreen) {{
                toggleFullscreen();
            }} else if (e.key === '+' || e.key === '=') {{
                e.preventDefault();
                zoomIn();
            }} else if (e.key === '-') {{
                e.preventDefault();
                zoomOut();
            }} else if (e.key === '0') {{
                e.preventDefault();
                resetZoom();
            }}
        }});
        
        // Mouse wheel zoom
        const flipbookViewer = document.getElementById('flipbookViewer');
        if (flipbookViewer) {{
            flipbookViewer.addEventListener('wheel', function(e) {{
                if (e.ctrlKey || e.metaKey) {{
                    e.preventDefault();
                    if (e.deltaY < 0) {{
                        zoomIn();
                    }} else {{
                        zoomOut();
                    }}
                }}
            }}, {{ passive: false }});
        }}
        
        // Touch gestures for mobile
        let touchStartX = 0;
        let touchStartY = 0;
        
        document.addEventListener('touchstart', function(e) {{
            touchStartX = e.touches[0].clientX;
            touchStartY = e.touches[0].clientY;
        }}, {{ passive: true }});
        
        document.addEventListener('touchend', function(e) {{
            if (!touchStartX || !touchStartY) return;
            
            const touchEndX = e.changedTouches[0].clientX;
            const touchEndY = e.changedTouches[0].clientY;
            
            const diffX = touchStartX - touchEndX;
            const diffY = touchStartY - touchEndY;
            
            if (Math.abs(diffX) > Math.abs(diffY)) {{
                if (diffX > 50) {{
                    nextPage();
                }} else if (diffX < -50) {{
                    previousPage();
                }}
            }}
            
            touchStartX = 0;
            touchStartY = 0;
        }}, {{ passive: true }});
        
        // Initialize
        updatePage();
    </script>
</body>
</html>'''
        
        # Return HTML - either for preview (inline) or download (attachment)
        response = HttpResponse(html_content, content_type='text/html; charset=utf-8')
        if not is_preview:
            response['Content-Disposition'] = 'attachment; filename="flipbook.html"'
        return response
        
    except Exception as e:
        error_msg = str(e)
        if 'poppler' in error_msg.lower() or 'pdftoppm' in error_msg.lower():
            messages.error(request, 'Poppler is required for PDF to flipbook conversion. Install with: brew install poppler (macOS) or apt-get install poppler-utils (Linux)')
        else:
            messages.error(request, f'Error converting PDF to flipbook: {error_msg}')
        return render(request, 'pdf_tools/pdf_to_flipbook.html', {
            'pdf2image_available': PDF2IMAGE_AVAILABLE,
        })

def pdf_to_epub(request):
    """Convert PDF to EPUB format"""
    if not EBOOKLIB_AVAILABLE:
        messages.error(request, 'PDF to EPUB conversion requires ebooklib. Install with: pip install ebooklib')
        return render(request, 'pdf_tools/pdf_to_epub.html', {
            'ebooklib_available': EBOOKLIB_AVAILABLE,
        })
    
    if request.method != 'POST':
        return render(request, 'pdf_tools/pdf_to_epub.html', {
            'ebooklib_available': EBOOKLIB_AVAILABLE,
        })
    
    if 'pdf_files' not in request.FILES:
        messages.error(request, 'Please upload at least one PDF file.')
        return render(request, 'pdf_tools/pdf_to_epub.html', {
            'ebooklib_available': EBOOKLIB_AVAILABLE,
        })
    
    pdf_files = request.FILES.getlist('pdf_files')
    
    if len(pdf_files) == 0:
        messages.error(request, 'Please upload at least one PDF file.')
        return render(request, 'pdf_tools/pdf_to_epub.html', {
            'ebooklib_available': EBOOKLIB_AVAILABLE,
        })
    
    # Validate all files
    max_size = 50 * 1024 * 1024  # 50MB
    pdf_file_names = []
    for pdf_file in pdf_files:
        if not pdf_file.name.lower().endswith('.pdf'):
            messages.error(request, f'{pdf_file.name} is not a valid PDF file.')
            return render(request, 'pdf_tools/pdf_to_epub.html', {
                'ebooklib_available': EBOOKLIB_AVAILABLE,
            })
        
        if pdf_file.size > max_size:
            messages.error(request, f'{pdf_file.name} exceeds 50MB limit. Your file is {pdf_file.size / (1024 * 1024):.1f}MB.')
            return render(request, 'pdf_tools/pdf_to_epub.html', {
                'ebooklib_available': EBOOKLIB_AVAILABLE,
            })
        
        pdf_file_names.append(pdf_file.name)
    
    try:
        import gc
        import base64
        import re
        from html import escape
        
        # Get custom title from request or use default
        epub_title = request.POST.get('epub_title', '').strip()
        if not epub_title:
            epub_title = 'PDF to EPUB Conversion'
        
        # Check if user wants to preserve page breaks
        preserve_page_breaks = request.POST.get('preserve_page_breaks', 'off') == 'on'
        
        # Create EPUB book
        book = epub.EpubBook()
        
        # Set metadata
        book.set_identifier('pdf_to_epub_conversion')
        book.set_title(epub_title)
        book.set_language('en')
        book.add_author('PDF Converter')
        
        # Handle cover image if provided
        cover_image_file = None
        if 'cover_image' in request.FILES:
            cover_image_file = request.FILES['cover_image']
            # Validate cover image
            if cover_image_file.size > 5 * 1024 * 1024:  # 5MB limit
                messages.warning(request, 'Cover image exceeds 5MB limit. Skipping cover image.')
                cover_image_file = None
            else:
                # Validate image format
                allowed_types = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp']
                if cover_image_file.content_type not in allowed_types:
                    messages.warning(request, f'Cover image format {cover_image_file.content_type} not supported. Use PNG, JPG, or WebP. Skipping cover image.')
                    cover_image_file = None
        
        # Store chapters and spine
        chapters = []
        spine = ['nav']
        
        # Process all PDFs
        for pdf_file in pdf_files:
            pdf_data = None
            try:
                pdf_data = pdf_file.read()
                
                # Create temporary file for PDF processing
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
                    tmp_pdf.write(pdf_data)
                    tmp_pdf_path = tmp_pdf.name
                
                # Extract content from PDF
                pdf_content = []
                images_dict = {}  # Store images by page number
                
                if PDFPLUMBER_AVAILABLE:
                    # Use pdfplumber for better text extraction
                    with pdfplumber.open(tmp_pdf_path) as pdf:
                        for page_num, page in enumerate(pdf.pages, 1):
                            page_content = []
                            
                            # Extract tables
                            tables = page.extract_tables()
                            if tables:
                                for table in tables:
                                    if table and len(table) > 0:
                                        table_html = '<table style="border-collapse: collapse; width: 100%; margin: 15px 0;">\n'
                                        is_first = True
                                        for row in table:
                                            if row and any(cell for cell in row if cell):
                                                table_html += '<tr>\n'
                                                for cell in row:
                                                    cell_text = str(cell).strip() if cell else ''
                                                    cell_text = escape(cell_text)
                                                    tag = 'th' if is_first else 'td'
                                                    table_html += f'<{tag} style="border: 1px solid #ddd; padding: 8px;">{cell_text}</{tag}>\n'
                                                table_html += '</tr>\n'
                                                is_first = False
                                        table_html += '</table>\n'
                                        page_content.append(table_html)
                            
                            # Extract text
                            text = page.extract_text()
                            if text and text.strip():
                                paragraphs = text.split('\n\n')
                                for para in paragraphs:
                                    para = para.strip()
                                    if para and len(para) > 2:
                                        para = escape(para)
                                        para = para.replace('\n', '<br>')
                                        page_content.append(f'<p>{para}</p>')
                            
                            # Extract images
                            if page.images:
                                for img_idx, img in enumerate(page.images):
                                    try:
                                        cropped = page.crop((img['x0'], img['top'], img['x1'], img['bottom']))
                                        img_obj = cropped.to_image(resolution=150)
                                        img_buffer = io.BytesIO()
                                        img_obj.save(img_buffer, format='PNG')
                                        img_buffer.seek(0)
                                        img_data = img_buffer.read()
                                        img_buffer.close()
                                        
                                        # Store image for later embedding
                                        img_id = f'img_{pdf_file.name}_{page_num}_{img_idx}'.replace('.', '_').replace('/', '_')
                                        images_dict[img_id] = img_data
                                        page_content.append(f'<p><img src="{img_id}.png" alt="Image" style="max-width: 100%; height: auto;" /></p>')
                                    except Exception as img_error:
                                        # Skip images that can't be extracted
                                        continue
                            
                            if page_content:
                                pdf_content.append({
                                    'page_num': page_num,
                                    'content': '\n'.join(page_content)
                                })
                
                else:
                    # Fallback to PyPDF2
                    pdf_reader = PdfReader(io.BytesIO(pdf_data))
                    for page_num, page in enumerate(pdf_reader.pages, 1):
                        text = page.extract_text()
                        if text.strip():
                            paragraphs = text.split('\n\n')
                            page_content = []
                            for para in paragraphs:
                                para = para.strip()
                                if para:
                                    para = escape(para)
                                    para = para.replace('\n', '<br>')
                                    page_content.append(f'<p>{para}</p>')
                            
                            if page_content:
                                pdf_content.append({
                                    'page_num': page_num,
                                    'content': '\n'.join(page_content)
                                })
                
                # Create chapter(s) for this PDF
                if pdf_content:
                    # Create one chapter per PDF, or split into multiple chapters if too long
                    pdf_name = pdf_file.name.replace('.pdf', '').replace('.PDF', '')
                    chapter_title = escape(pdf_name)
                    
                    # Combine all pages into one chapter
                    full_content = []
                    if preserve_page_breaks:
                        # Preserve page breaks: each page gets its own div with header
                        for page_data in pdf_content:
                            full_content.append(f'<div class="page"><h3>Page {page_data["page_num"]}</h3>{page_data["content"]}</div>')
                    else:
                        # Continuous flow: combine all content without page breaks
                        for page_data in pdf_content:
                            full_content.append(f'<div class="page-content">{page_data["content"]}</div>')
                    
                    # Build CSS based on page break preference
                    if preserve_page_breaks:
                        page_css = '''
        .page {
            margin-bottom: 30px;
            page-break-after: always;
        }
        h3 {
            color: #333;
            border-bottom: 2px solid #ddd;
            padding-bottom: 5px;
        }'''
                    else:
                        page_css = '''
        .page-content {
            margin-bottom: 20px;
        }'''
                    
                    chapter_html = f'''<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta charset="UTF-8"/>
    <title>{chapter_title}</title>
    <style>
        body {{
            font-family: Georgia, serif;
            line-height: 1.6;
            margin: 20px;
            padding: 0;
        }}{page_css}
        p {{
            margin: 10px 0;
            text-align: justify;
        }}
        img {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 15px auto;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
        }}
        table th, table td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        table th {{
            background-color: #f2f2f2;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <h1>{chapter_title}</h1>
    {''.join(full_content)}
</body>
</html>'''
                    
                    # Create chapter
                    chapter_id = f'chapter_{pdf_file.name}'.replace('.', '_').replace('/', '_')
                    chapter = epub.EpubHtml(title=chapter_title, file_name=f'{chapter_id}.xhtml', lang='en')
                    chapter.content = chapter_html
                    
                    # Add images to chapter
                    for img_id, img_data in images_dict.items():
                        book.add_item(epub.EpubItem(uid=img_id, file_name=f'{img_id}.png', media_type='image/png', content=img_data))
                    
                    book.add_item(chapter)
                    chapters.append(chapter)
                    spine.append(chapter)
                
                # Clean up temporary file
                if os.path.exists(tmp_pdf_path):
                    os.unlink(tmp_pdf_path)
                
                # Free memory
                if pdf_data is not None:
                    del pdf_data
                gc.collect()
                
            except Exception as conv_error:
                messages.warning(request, f'Could not convert {pdf_file.name}: {str(conv_error)}. Skipping.')
                continue
        
        if not chapters:
            messages.error(request, 'No content could be extracted from any of the PDF files.')
            return render(request, 'pdf_tools/pdf_to_epub.html', {
                'ebooklib_available': EBOOKLIB_AVAILABLE,
            })
        
        # Add cover image if provided
        if cover_image_file:
            try:
                # Read cover image data
                cover_data = cover_image_file.read()
                
                # Determine image format and media type
                cover_image_file.seek(0)  # Reset file pointer
                img = Image.open(cover_image_file)
                
                # Convert to RGB if needed (for JPEG compatibility)
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create white background for transparent images
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Add title text overlay on the cover image
                from PIL import ImageDraw, ImageFont
                draw = ImageDraw.Draw(img)
                
                # Calculate text size and position
                img_width, img_height = img.size
                
                # Try to use bold Helvetica font - prioritize heaviest variants
                font_size = max(48, int(img_height * 0.08))
                font = None
                
                # Try to load boldest Helvetica fonts (macOS)
                # HelveticaNeue.ttc typically has: 0=UltraLight, 1=Thin, 2=Light, 3=Regular, 4=Medium, 5=Bold, 6=Heavy, 7=Black
                # Helvetica.ttc typically has: 0=Regular, 1=Bold
                font_paths_with_indices = [
                    ("/System/Library/Fonts/HelveticaNeue.ttc", 7),  # Black (boldest)
                    ("/System/Library/Fonts/HelveticaNeue.ttc", 6),  # Heavy (very bold)
                    ("/System/Library/Fonts/HelveticaNeue.ttc", 5),  # Bold
                    ("/System/Library/Fonts/Helvetica.ttc", 1),      # Bold
                    ("/System/Library/Fonts/HelveticaNeue.ttc", 4),  # Medium (fallback)
                    ("/System/Library/Fonts/Helvetica.ttc", 0),       # Regular (fallback)
                ]
                
                for font_path, font_index in font_paths_with_indices:
                    try:
                        if os.path.exists(font_path):
                            font = ImageFont.truetype(font_path, font_size, index=font_index)
                            break
                    except (OSError, IOError):
                        continue
                
                # Fallback to regular Helvetica if bold not found
                if not font:
                    try:
                        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
                    except:
                        try:
                            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
                        except:
                            font = ImageFont.load_default()
                
                # Wrap text to fit within image width
                text = epub_title
                max_text_width = img_width - int(img_width * 0.1)  # 5% padding on each side
                
                # Helper function to get text width
                def get_text_width(text, font):
                    try:
                        bbox = draw.textbbox((0, 0), text, font=font)
                        return bbox[2] - bbox[0]
                    except AttributeError:
                        return draw.textsize(text, font=font)[0]
                
                # Helper function to get text height
                def get_text_height(text, font):
                    try:
                        bbox = draw.textbbox((0, 0), text, font=font)
                        return bbox[3] - bbox[1]
                    except AttributeError:
                        return draw.textsize(text, font=font)[1]
                
                # Wrap text into lines
                words = text.split()
                lines = []
                current_line = []
                
                for word in words:
                    # Test if adding this word would exceed the width
                    test_line = ' '.join(current_line + [word])
                    test_width = get_text_width(test_line, font)
                    
                    if test_width <= max_text_width:
                        current_line.append(word)
                    else:
                        if current_line:
                            lines.append(' '.join(current_line))
                        # If a single word is too long, add it anyway (will be truncated visually)
                        current_line = [word]
                
                # Add the last line
                if current_line:
                    lines.append(' '.join(current_line))
                
                # If no lines (empty text), create one empty line
                if not lines:
                    lines = ['']
                
                # Calculate total height of all lines
                line_height = get_text_height('A', font)  # Approximate line height
                line_spacing = int(line_height * 0.2)  # 20% spacing between lines
                total_height = (len(lines) * line_height) + ((len(lines) - 1) * line_spacing)
                
                # Position text block at bottom center
                y_start = img_height - total_height - int(img_height * 0.1)  # 10% from bottom
                
                # Draw text with bold stroke effect for extra boldness
                # Use white text with a bold dark outline/stroke
                stroke_color = (0, 0, 0)  # Black stroke
                text_color = (255, 255, 255)  # White text
                stroke_width = 3  # Increased stroke width for bolder appearance
                
                # Draw each line
                for line_idx, line in enumerate(lines):
                    line_width = get_text_width(line, font)
                    x = (img_width - line_width) // 2  # Center each line
                    y = y_start + (line_idx * (line_height + line_spacing))
                    
                    # Draw bold stroke by drawing text multiple times with offsets
                    for adj_x in range(-stroke_width, stroke_width + 1):
                        for adj_y in range(-stroke_width, stroke_width + 1):
                            if abs(adj_x) + abs(adj_y) <= stroke_width:
                                draw.text((x + adj_x, y + adj_y), line, font=font, fill=stroke_color)
                    
                    # Draw main text on top
                    draw.text((x, y), line, font=font, fill=text_color)
                
                # Save the modified image
                cover_format = img.format.lower() if img.format else 'png'
                
                # Convert to JPEG for better compatibility
                img_buffer = io.BytesIO()
                img.save(img_buffer, format='JPEG', quality=90)
                cover_data = img_buffer.getvalue()
                media_type = 'image/jpeg'
                file_ext = 'jpg'
                
                # Create cover image item
                cover_item = epub.EpubItem(
                    uid='cover',
                    file_name=f'cover.{file_ext}',
                    media_type=media_type,
                    content=cover_data
                )
                book.add_item(cover_item)
                
                # Set cover
                book.set_cover(file_name=f'cover.{file_ext}', content=cover_data)
                
            except Exception as cover_error:
                messages.warning(request, f'Error processing cover image: {str(cover_error)}. EPUB will be created without cover.')
        
        # Add table of contents
        book.toc = [(chapter, chapter.title) for chapter in chapters]
        
        # Add navigation files
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        
        # Set spine
        book.spine = spine
        
        # Generate EPUB file
        epub_buffer = io.BytesIO()
        epub.write_epub(epub_buffer, book, {})
        epub_buffer.seek(0)
        
        # Generate safe filename from title
        safe_filename = re.sub(r'[^\w\s-]', '', epub_title).strip()
        safe_filename = re.sub(r'[-\s]+', '-', safe_filename)
        if not safe_filename:
            safe_filename = 'converted'
        safe_filename = safe_filename[:100]  # Limit length
        if not safe_filename.endswith('.epub'):
            safe_filename += '.epub'
        
        # Return EPUB file
        response = HttpResponse(epub_buffer.read(), content_type='application/epub+zip')
        response['Content-Disposition'] = f'attachment; filename="{safe_filename}"'
        return response
        
    except Exception as e:
        error_msg = str(e)
        messages.error(request, f'Error converting PDF to EPUB: {error_msg}')
        return render(request, 'pdf_tools/pdf_to_epub.html', {
            'ebooklib_available': EBOOKLIB_AVAILABLE,
        })

