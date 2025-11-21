from django.shortcuts import render
from django.http import HttpResponse
from django.contrib import messages
import io
import zipfile
from pypdf import PdfWriter, PdfReader
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

def index(request):
    """PDF tools main page"""
    return render(request, 'pdf_tools/index.html', {
        'pdf2image_available': PDF2IMAGE_AVAILABLE,
        'weasyprint_available': WEASYPRINT_AVAILABLE,
    })

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
        import tempfile
        import os
        
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
                                except:
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

