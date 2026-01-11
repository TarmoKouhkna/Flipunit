"""
Celery tasks for image converter operations
"""
import os
import tempfile
import shutil
import re
import logging
from celery import shared_task
from django.utils import timezone
from django.conf import settings
from .models import ImageJob

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    soft_time_limit=300,  # 5 minutes
    time_limit=360,  # 6 minutes
    max_retries=0,
    queue='image_processing'
)
def image_converter_task(self, job_id, file_path, output_format, original_filename, quality=95):
    """Convert image to different format"""
    job = ImageJob.objects.get(job_id=job_id)
    
    temp_dir = None
    try:
        job.status = 'processing'
        job.save()
        
        from PIL import Image
        
        temp_dir = os.path.dirname(file_path)
        output_path_temp = os.path.join(temp_dir, f'output.{output_format.lower()}')
        
        img = Image.open(file_path)
        
        # Convert RGBA to RGB if needed for formats that don't support transparency
        if output_format.lower() in ['jpg', 'jpeg'] and img.mode == 'RGBA':
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[3])
            img = rgb_img
        
        # Save with quality setting for formats that support it
        save_kwargs = {}
        if output_format.upper() in ['JPEG', 'WEBP', 'AVIF']:
            save_kwargs['quality'] = quality
            save_kwargs['optimize'] = True
        
        img.save(output_path_temp, format=output_format.upper(), **save_kwargs)
        
        # Move output file to final shared location
        final_output_dir = os.path.join(settings.MEDIA_ROOT, 'image_conversions')
        os.makedirs(final_output_dir, exist_ok=True)
        
        # Generate a safe filename for the output
        base_name = os.path.splitext(original_filename)[0]
        # Remove temp_ prefix if present
        if base_name.startswith('temp_'):
            base_name = base_name[5:]
        base_name = re.sub(r'[^\w\s.-]', '', base_name).strip()
        base_name = re.sub(r'[-\s]+', '-', base_name)
        final_output_filename = f'{base_name}.{output_format.lower()}'
        final_output_path = os.path.join(final_output_dir, final_output_filename)
        
        shutil.move(output_path_temp, final_output_path)
        
        job.status = 'completed'
        job.output_file_key = final_output_path
        job.completed_at = timezone.now()
        job.save()
        
        logger.info(f"Image conversion completed for job {job_id}. Output: {final_output_path}")
        return final_output_path
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Image conversion failed for job {job_id}: {error_msg}", exc_info=True)
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
        # Clean up the temporary directory used for output
        if temp_dir:
            try:
                # Only remove if it's a temp directory (not the shared media directory)
                if 'temp' in temp_dir or temp_dir != os.path.dirname(file_path):
                    shutil.rmtree(temp_dir)
                    logger.info(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp directory {temp_dir}: {e}")


@shared_task(
    bind=True,
    soft_time_limit=60,  # 1 minute
    time_limit=120,  # 2 minutes
    max_retries=0,
    queue='image_processing'
)
def image_resize_task(self, job_id, file_path, width, height):
    """Resize image"""
    job = ImageJob.objects.get(job_id=job_id)
    
    try:
        job.status = 'processing'
        job.save()
        
        from PIL import Image
        
        temp_dir = os.path.dirname(file_path)
        output_path = os.path.join(temp_dir, 'resized.png')
        
        img = Image.open(file_path)
        resized = img.resize((width, height), Image.Resampling.LANCZOS)
        resized.save(output_path)
        
        job.status = 'completed'
        job.output_file_key = output_path
        job.completed_at = timezone.now()
        job.save()
        
        logger.info(f"Image resize completed for job {job_id}")
        return output_path
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Image resize failed for job {job_id}: {error_msg}")
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
    queue='image_processing'
)
def image_merge_task(self, job_id, file_paths, layout):
    """Merge multiple images"""
    job = ImageJob.objects.get(job_id=job_id)
    
    try:
        job.status = 'processing'
        job.save()
        
        from PIL import Image
        
        temp_dir = os.path.dirname(file_paths[0])
        output_path = os.path.join(temp_dir, 'merged.png')
        
        images = [Image.open(fp) for fp in file_paths]
        
        if layout == 'horizontal':
            total_width = sum(img.width for img in images)
            max_height = max(img.height for img in images)
            merged = Image.new('RGB', (total_width, max_height))
            x_offset = 0
            for img in images:
                merged.paste(img, (x_offset, 0))
                x_offset += img.width
        else:  # vertical
            max_width = max(img.width for img in images)
            total_height = sum(img.height for img in images)
            merged = Image.new('RGB', (max_width, total_height))
            y_offset = 0
            for img in images:
                merged.paste(img, (0, y_offset))
                y_offset += img.height
        
        merged.save(output_path)
        
        job.status = 'completed'
        job.output_file_key = output_path
        job.completed_at = timezone.now()
        job.save()
        
        logger.info(f"Image merge completed for job {job_id}")
        return output_path
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Image merge failed for job {job_id}: {error_msg}")
        job.status = 'failed'
        job.error_message = error_msg
        job.completed_at = timezone.now()
        job.save()
        raise


@shared_task(
    bind=True,
    soft_time_limit=60,  # 1 minute
    time_limit=120,  # 2 minutes
    max_retries=0,
    queue='image_processing'
)
def svg_to_png_task(self, job_id, file_path, dpi=300):
    """Convert SVG to PNG"""
    job = ImageJob.objects.get(job_id=job_id)
    
    try:
        job.status = 'processing'
        job.save()
        
        try:
            import cairosvg
        except ImportError:
            raise Exception("cairosvg library not available")
        
        temp_dir = os.path.dirname(file_path)
        output_path = os.path.join(temp_dir, 'output.png')
        
        cairosvg.svg2png(url=file_path, write_to=output_path, dpi=dpi)
        
        job.status = 'completed'
        job.output_file_key = output_path
        job.completed_at = timezone.now()
        job.save()
        
        logger.info(f"SVG to PNG completed for job {job_id}")
        return output_path
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"SVG to PNG failed for job {job_id}: {error_msg}")
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
    queue='image_processing'
)
def batch_image_converter_task(self, job_id, file_paths, output_format):
    """Batch convert multiple images"""
    job = ImageJob.objects.get(job_id=job_id)
    
    try:
        job.status = 'processing'
        job.save()
        
        from PIL import Image
        import zipfile
        
        temp_dir = os.path.dirname(file_paths[0])
        zip_path = os.path.join(temp_dir, 'converted_images.zip')
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for i, file_path in enumerate(file_paths):
                img = Image.open(file_path)
                output_name = f'converted_{i+1}.{output_format}'
                output_path = os.path.join(temp_dir, output_name)
                
                if output_format.lower() in ['jpg', 'jpeg'] and img.mode == 'RGBA':
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    rgb_img.paste(img, mask=img.split()[3])
                    img = rgb_img
                
                img.save(output_path, format=output_format.upper())
                zipf.write(output_path, output_name)
        
        job.status = 'completed'
        job.output_file_key = zip_path
        job.completed_at = timezone.now()
        job.save()
        
        logger.info(f"Batch image conversion completed for job {job_id}")
        return zip_path
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Batch image conversion failed for job {job_id}: {error_msg}")
        job.status = 'failed'
        job.error_message = error_msg
        job.completed_at = timezone.now()
        job.save()
        raise
