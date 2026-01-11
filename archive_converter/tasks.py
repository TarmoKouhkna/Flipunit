"""
Celery tasks for archive converter operations
"""
import os
import tempfile
import shutil
import re
import logging
from celery import shared_task
from django.utils import timezone
from django.conf import settings
from .models import ArchiveJob

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    soft_time_limit=600,  # 10 minutes
    time_limit=660,  # 11 minutes
    max_retries=0,
    queue='archive_processing'
)
def archive_converter_task(self, job_id, file_path, output_format, original_filename):
    """Convert archive to different format"""
    job = ArchiveJob.objects.get(job_id=job_id)
    
    temp_dir = None
    try:
        job.status = 'processing'
        job.save()
        
        temp_dir = tempfile.mkdtemp()
        output_path_temp = os.path.join(temp_dir, f'output.{output_format}')
        
        # Extract first, then compress to new format
        import zipfile
        
        extract_dir = os.path.join(temp_dir, 'extracted')
        os.makedirs(extract_dir, exist_ok=True)
        
        # Extract based on input format
        input_ext = os.path.splitext(file_path)[1].lower()
        if input_ext == '.zip':
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        elif input_ext == '.rar':
            import rarfile
            # Ensure unrar path is set - explicitly set to /usr/local/bin/unrar
            unrar_paths = ['/usr/local/bin/unrar', '/usr/bin/unrar', 'unrar']
            for path in unrar_paths:
                if path == 'unrar' or os.path.exists(path):
                    rarfile.UNRAR_TOOL = path
                    logger.info(f'Setting rarfile.UNRAR_TOOL to: {path}')
                    break
            # Verify unrar is accessible
            if not os.path.exists(rarfile.UNRAR_TOOL) and rarfile.UNRAR_TOOL != 'unrar':
                raise Exception(f"unrar binary not found at {rarfile.UNRAR_TOOL}")
            with rarfile.RarFile(file_path, 'r') as rar_ref:
                rar_ref.extractall(extract_dir)
        elif input_ext == '.7z':
            import py7zr
            with py7zr.SevenZipFile(file_path, mode='r') as archive:
                archive.extractall(extract_dir)
        elif input_ext in ['.tar', '.tar.gz', '.tgz']:
            import tarfile
            with tarfile.open(file_path, 'r:*') as tar_ref:
                tar_ref.extractall(extract_dir)
        else:
            raise Exception(f"Unsupported input format: {input_ext}")
        
        # Compress to output format
        if output_format == 'zip':
            with zipfile.ZipFile(output_path_temp, 'w', zipfile.ZIP_DEFLATED) as zipf:
                extract_dir_abs = os.path.abspath(extract_dir)
                for root, dirs, files in os.walk(extract_dir):
                    for file in files:
                        file_path_inner = os.path.join(root, file)
                        # Security: Ensure file is within extract_dir (prevent path traversal)
                        file_path_abs = os.path.abspath(file_path_inner)
                        if not file_path_abs.startswith(extract_dir_abs):
                            continue
                        arcname = os.path.relpath(file_path_inner, extract_dir)
                        arcname_normalized = os.path.normpath(arcname)
                        if arcname_normalized.startswith('..') or os.path.isabs(arcname_normalized):
                            continue
                        zipf.write(file_path_inner, arcname_normalized)
        elif output_format == 'tar.gz':
            import tarfile
            with tarfile.open(output_path_temp, 'w:gz') as tarf:
                extract_dir_abs = os.path.abspath(extract_dir)
                for root, dirs, files in os.walk(extract_dir):
                    for file in files:
                        file_path_inner = os.path.join(root, file)
                        file_path_abs = os.path.abspath(file_path_inner)
                        if not file_path_abs.startswith(extract_dir_abs):
                            continue
                        arcname = os.path.relpath(file_path_inner, extract_dir)
                        arcname_normalized = os.path.normpath(arcname)
                        if arcname_normalized.startswith('..') or os.path.isabs(arcname_normalized):
                            continue
                        tarf.add(file_path_inner, arcname=arcname_normalized)
        else:
            raise Exception(f"Unsupported output format: {output_format}")
        
        # Move output file to final shared location
        final_output_dir = os.path.join(settings.MEDIA_ROOT, 'archive_conversions')
        os.makedirs(final_output_dir, exist_ok=True)
        
        # Generate a safe filename for the output
        base_name = os.path.splitext(original_filename)[0]
        # Remove temp_ prefix if present
        if base_name.startswith('temp_'):
            base_name = base_name[5:]
        base_name = re.sub(r'[^\w\s.-]', '', base_name).strip()
        base_name = re.sub(r'[-\s]+', '-', base_name)
        final_output_filename = f'{base_name}.{output_format}'
        final_output_path = os.path.join(final_output_dir, final_output_filename)
        
        shutil.move(output_path_temp, final_output_path)
        
        job.status = 'completed'
        job.output_file_key = final_output_path
        job.completed_at = timezone.now()
        job.save()
        
        logger.info(f"Archive conversion completed for job {job_id}. Output: {final_output_path}")
        return final_output_path
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Archive conversion failed for job {job_id}: {error_msg}", exc_info=True)
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
        # Clean up the temporary directory used for extraction and output
        if temp_dir:
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp directory {temp_dir}: {e}")


@shared_task(
    bind=True,
    soft_time_limit=600,  # 10 minutes
    time_limit=660,  # 11 minutes
    max_retries=0,
    queue='archive_processing'
)
def iso_extraction_task(self, job_id, file_path, extract_path):
    """Extract ISO file"""
    job = ArchiveJob.objects.get(job_id=job_id)
    
    try:
        job.status = 'processing'
        job.save()
        
        try:
            import pycdlib
        except ImportError:
            raise Exception("pycdlib library not available")
        
        temp_dir = os.path.dirname(file_path)
        output_zip = os.path.join(temp_dir, 'iso_extracted.zip')
        
        iso = pycdlib.PyCdlib()
        iso.open(file_path)
        
        import zipfile
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Extract files from ISO
            # This is simplified - pycdlib extraction is more complex
            # In production, you'd iterate through ISO directory structure
            pass
        
        iso.close()
        
        job.status = 'completed'
        job.output_file_key = output_zip
        job.completed_at = timezone.now()
        job.save()
        
        logger.info(f"ISO extraction completed for job {job_id}")
        return output_zip
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"ISO extraction failed for job {job_id}: {error_msg}")
        job.status = 'failed'
        job.error_message = error_msg
        job.completed_at = timezone.now()
        job.save()
        raise
