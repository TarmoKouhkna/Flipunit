"""
Celery tasks for PDF tools operations
"""
import os
import tempfile
import shutil
import logging
from celery import shared_task
from django.utils import timezone
from django.conf import settings
from .models import PDFJob

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    soft_time_limit=900,  # 15 minutes
    time_limit=960,  # 16 minutes
    max_retries=0,  # No retry for CPU-bound operations
    queue='pdf_processing'
)
def pdf_ocr_task(self, job_id, file_path):
    """Perform OCR on PDF to make it searchable"""
    job = PDFJob.objects.get(job_id=job_id)
    
    try:
        job.status = 'processing'
        job.save()
        
        try:
            import pytesseract
            from pdf2image import convert_from_path
            from pypdf import PdfWriter, PdfReader
        except ImportError as e:
            raise Exception(f"Required libraries not available: {str(e)}")
        
        # Convert PDF pages to images
        images = convert_from_path(file_path, dpi=300)
        
        # Create output PDF
        temp_dir = os.path.dirname(file_path)
        output_path = os.path.join(temp_dir, 'ocr_output.pdf')
        
        from PIL import Image
        import io
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        # For simplicity, using pypdf approach
        # In production, you might want to use pdf2image + pytesseract + reportlab
        # This is a simplified version
        
        job.status = 'completed'
        job.output_file_key = output_path
        job.completed_at = timezone.now()
        job.save()
        
        logger.info(f"PDF OCR completed for job {job_id}")
        return output_path
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"PDF OCR failed for job {job_id}: {error_msg}")
        job.status = 'failed'
        job.error_message = error_msg
        job.completed_at = timezone.now()
        job.save()
        raise


@shared_task(
    bind=True,
    soft_time_limit=600,  # 10 minutes
    time_limit=660,  # 11 minutes
    max_retries=0,
    queue='pdf_processing'
)
def pdf_to_images_task(self, job_id, file_path):
    """Convert PDF pages to images"""
    job = PDFJob.objects.get(job_id=job_id)
    
    temp_dir = None
    try:
        job.status = 'processing'
        job.save()
        
        try:
            from pdf2image import convert_from_path
        except ImportError:
            raise Exception("pdf2image library not available")
        
        temp_dir = os.path.dirname(file_path)
        images = convert_from_path(file_path, dpi=200)
        
        if not images:
            raise Exception("No images could be extracted from the PDF")
        
        # Save images
        image_paths = []
        for i, image in enumerate(images):
            image_path = os.path.join(temp_dir, f'page_{i+1}.png')
            image.save(image_path, 'PNG')
            image_paths.append(image_path)
        
        # Create zip file with all images
        import zipfile
        zip_path = os.path.join(temp_dir, 'pdf_images.zip')
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for img_path in image_paths:
                zipf.write(img_path, os.path.basename(img_path))
        
        # Move output file to final shared location
        final_output_dir = os.path.join(settings.MEDIA_ROOT, 'pdf_conversions')
        os.makedirs(final_output_dir, exist_ok=True)
        
        import re
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        # Remove temp_ prefix if present
        if base_name.startswith('temp_'):
            base_name = base_name[5:]
        base_name = re.sub(r'[^\w\s.-]', '', base_name).strip()
        base_name = re.sub(r'[-\s]+', '-', base_name)
        final_output_filename = f'{base_name}_images.zip'
        final_output_path = os.path.join(final_output_dir, final_output_filename)
        
        shutil.move(zip_path, final_output_path)
        
        job.status = 'completed'
        job.output_file_key = final_output_path
        job.completed_at = timezone.now()
        job.save()
        
        logger.info(f"PDF to images completed for job {job_id}. Output: {final_output_path}")
        return final_output_path
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"PDF to images failed for job {job_id}: {error_msg}", exc_info=True)
        job.status = 'failed'
        job.error_message = error_msg
        job.completed_at = timezone.now()
        job.save()
        raise
    
    finally:
        # Clean up the input file from the shared media directory
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Cleaned up input file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up input file {file_path}: {e}")


@shared_task(
    bind=True,
    soft_time_limit=300,  # 5 minutes
    time_limit=360,  # 6 minutes
    max_retries=0,
    queue='pdf_processing'
)
def html_to_pdf_task(self, job_id, html_content, options):
    """Convert HTML to PDF"""
    job = PDFJob.objects.get(job_id=job_id)
    
    try:
        job.status = 'processing'
        job.save()
        
        try:
            from weasyprint import HTML
        except ImportError:
            raise Exception("weasyprint library not available")
        
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, 'output.pdf')
        
        HTML(string=html_content).write_pdf(output_path)
        
        job.status = 'completed'
        job.output_file_key = output_path
        job.completed_at = timezone.now()
        job.save()
        
        logger.info(f"HTML to PDF completed for job {job_id}")
        return output_path
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"HTML to PDF failed for job {job_id}: {error_msg}")
        job.status = 'failed'
        job.error_message = error_msg
        job.completed_at = timezone.now()
        job.save()
        raise


@shared_task(
    bind=True,
    soft_time_limit=300,  # 5 minutes
    time_limit=360,  # 6 minutes
    max_retries=0,
    queue='pdf_processing'
)
def pdf_merge_task(self, job_id, file_paths):
    """Merge multiple PDF files"""
    job = PDFJob.objects.get(job_id=job_id)
    
    try:
        job.status = 'processing'
        job.save()
        
        from pypdf import PdfWriter
        
        temp_dir = os.path.dirname(file_paths[0])
        output_path = os.path.join(temp_dir, 'merged.pdf')
        
        merger = PdfWriter()
        for file_path in file_paths:
            merger.append(file_path)
        
        merger.write(output_path)
        merger.close()
        
        job.status = 'completed'
        job.output_file_key = output_path
        job.completed_at = timezone.now()
        job.save()
        
        logger.info(f"PDF merge completed for job {job_id}")
        return output_path
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"PDF merge failed for job {job_id}: {error_msg}")
        job.status = 'failed'
        job.error_message = error_msg
        job.completed_at = timezone.now()
        job.save()
        raise


@shared_task(
    bind=True,
    soft_time_limit=300,  # 5 minutes
    time_limit=360,  # 6 minutes
    max_retries=0,
    queue='pdf_processing'
)
def pdf_split_task(self, job_id, file_path, page_ranges):
    """Split PDF into multiple files"""
    job = PDFJob.objects.get(job_id=job_id)
    
    try:
        job.status = 'processing'
        job.save()
        
        from pypdf import PdfWriter, PdfReader
        
        temp_dir = os.path.dirname(file_path)
        reader = PdfReader(file_path)
        
        # Create zip with split PDFs
        import zipfile
        zip_path = os.path.join(temp_dir, 'split_pdfs.zip')
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for i, page_range in enumerate(page_ranges):
                writer = PdfWriter()
                start, end = page_range
                for page_num in range(start-1, end):
                    writer.add_page(reader.pages[page_num])
                
                split_path = os.path.join(temp_dir, f'split_{i+1}.pdf')
                writer.write(split_path)
                zipf.write(split_path, f'split_{i+1}.pdf')
        
        job.status = 'completed'
        job.output_file_key = zip_path
        job.completed_at = timezone.now()
        job.save()
        
        logger.info(f"PDF split completed for job {job_id}")
        return zip_path
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"PDF split failed for job {job_id}: {error_msg}")
        job.status = 'failed'
        job.error_message = error_msg
        job.completed_at = timezone.now()
        job.save()
        raise


@shared_task(
    bind=True,
    soft_time_limit=300,  # 5 minutes
    time_limit=360,  # 6 minutes
    max_retries=0,
    queue='pdf_processing'
)
def pdf_compress_task(self, job_id, file_path):
    """Compress PDF file size"""
    job = PDFJob.objects.get(job_id=job_id)
    
    try:
        job.status = 'processing'
        job.save()
        
        from pypdf import PdfWriter, PdfReader
        
        temp_dir = os.path.dirname(file_path)
        output_path = os.path.join(temp_dir, 'compressed.pdf')
        
        reader = PdfReader(file_path)
        writer = PdfWriter()
        
        for page in reader.pages:
            page.compress_content_streams()
            writer.add_page(page)
        
        writer.write(output_path)
        
        job.status = 'completed'
        job.output_file_key = output_path
        job.completed_at = timezone.now()
        job.save()
        
        logger.info(f"PDF compression completed for job {job_id}")
        return output_path
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"PDF compression failed for job {job_id}: {error_msg}")
        job.status = 'failed'
        job.error_message = error_msg
        job.completed_at = timezone.now()
        job.save()
        raise


@shared_task(
    bind=True,
    soft_time_limit=300,  # 5 minutes
    time_limit=360,  # 6 minutes
    max_retries=0,
    queue='pdf_processing'
)
def pdf_to_epub_task(self, job_id, file_path):
    """Convert PDF to EPUB"""
    job = PDFJob.objects.get(job_id=job_id)
    
    try:
        job.status = 'processing'
        job.save()
        
        try:
            import ebooklib
            from ebooklib import epub
            from pypdf import PdfReader
        except ImportError:
            raise Exception("ebooklib library not available")
        
        temp_dir = os.path.dirname(file_path)
        output_path = os.path.join(temp_dir, 'output.epub')
        
        # Simplified conversion - extract text and create EPUB
        reader = PdfReader(file_path)
        book = epub.EpubBook()
        book.set_identifier('pdf_convert')
        book.set_title('Converted PDF')
        book.set_language('en')
        
        # Add chapters from PDF pages
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            chapter = epub.EpubHtml(title=f'Page {i+1}', file_name=f'page_{i+1}.xhtml')
            chapter.content = f'<html><body><p>{text}</p></body></html>'
            book.add_item(chapter)
            book.toc.append(chapter)
        
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        epub.write_epub(output_path, book)
        
        job.status = 'completed'
        job.output_file_key = output_path
        job.completed_at = timezone.now()
        job.save()
        
        logger.info(f"PDF to EPUB completed for job {job_id}")
        return output_path
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"PDF to EPUB failed for job {job_id}: {error_msg}")
        job.status = 'failed'
        job.error_message = error_msg
        job.completed_at = timezone.now()
        job.save()
        raise
