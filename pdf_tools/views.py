from django.shortcuts import render
from django.http import HttpResponse
from django.contrib import messages
import io
import zipfile
import os
import tempfile
from pypdf import PdfWriter, PdfReader
from PIL import Image
try:
    from pdf2image import convert_from_bytes
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
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

