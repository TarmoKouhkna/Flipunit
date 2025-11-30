from django.shortcuts import render
from django.http import HttpResponse
from django.contrib import messages
import io
import zipfile
import tarfile
import os
import tempfile
import shutil
import logging

# Check for optional dependencies
try:
    import py7zr
    PY7ZR_AVAILABLE = True
except ImportError:
    PY7ZR_AVAILABLE = False

try:
    import rarfile
    RARFILE_AVAILABLE = True
    # Set unrar path explicitly - rarfile needs to find unrar binary
    # Check common locations for unrar
    unrar_paths = [
        os.path.expanduser('~/bin/unrar'),
        '/usr/local/bin/unrar',
        '/usr/bin/unrar',
        'unrar'  # Fallback to PATH
    ]
    for path in unrar_paths:
        if path == 'unrar' or os.path.exists(path):
            rarfile.UNRAR_TOOL = path
            break
except ImportError:
    RARFILE_AVAILABLE = False

try:
    import pycdlib
    PYCDLIB_AVAILABLE = True
except ImportError:
    PYCDLIB_AVAILABLE = False


def index(request):
    """Archive converters main page"""
    # Clear any stale messages on index page
    list(messages.get_messages(request))
    return render(request, 'archive_converter/index.html', {
        'py7zr_available': PY7ZR_AVAILABLE,
        'rarfile_available': RARFILE_AVAILABLE,
        'pycdlib_available': PYCDLIB_AVAILABLE,
    })
def rar_to_zip(request):
    """Convert RAR to ZIP"""
    if request.method != 'POST':
        # Clear any stale rarfile error messages on GET requests
        if RARFILE_AVAILABLE:
            list(messages.get_messages(request))
        return render(request, 'archive_converter/rar_to_zip.html', {
            'rarfile_available': RARFILE_AVAILABLE,
        })
    
    if 'archive_file' not in request.FILES:
        messages.error(request, 'Please upload a RAR file.')
        return render(request, 'archive_converter/rar_to_zip.html', {
            'rarfile_available': RARFILE_AVAILABLE,
        })
    
    uploaded_file = request.FILES['archive_file']
    
    # Validate file type
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    if file_ext not in ['.rar', '.cbr']:
        messages.error(request, 'Please upload a RAR or CBR file.')
        return render(request, 'archive_converter/rar_to_zip.html', {
            'rarfile_available': RARFILE_AVAILABLE,
        })
    
    # Validate file size (max 500MB)
    max_size = 500 * 1024 * 1024
    if uploaded_file.size > max_size:
        messages.error(request, f'File size exceeds 500MB limit. Your file is {uploaded_file.size / (1024 * 1024):.1f}MB.')
        return render(request, 'archive_converter/rar_to_zip.html', {
            'rarfile_available': RARFILE_AVAILABLE,
        })
    
    if not RARFILE_AVAILABLE:
        messages.error(request, 'RAR support requires rarfile library. Install with: pip install rarfile')
        return render(request, 'archive_converter/rar_to_zip.html', {
            'rarfile_available': RARFILE_AVAILABLE,
        })
    
    temp_dir = None
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        
        # Save uploaded RAR - read entire file to ensure it's complete
        rar_path = os.path.join(temp_dir, 'input.rar')
        uploaded_file.seek(0)  # Reset file pointer
        file_content = uploaded_file.read()  # Read entire file into memory
        
        # Write to disk
        with open(rar_path, 'wb') as f:
            f.write(file_content)
            f.flush()
            os.fsync(f.fileno())  # Ensure data is written to disk
        
        # Verify file was written correctly
        if not os.path.exists(rar_path) or os.path.getsize(rar_path) == 0:
            messages.error(request, 'Failed to save uploaded file. Please try again.')
            return render(request, 'archive_converter/rar_to_zip.html', {
                'rarfile_available': RARFILE_AVAILABLE,
            })
        
        # Verify file size matches
        if os.path.getsize(rar_path) != uploaded_file.size:
            messages.error(request, 'File upload incomplete. Please try uploading again.')
            return render(request, 'archive_converter/rar_to_zip.html', {
                'rarfile_available': RARFILE_AVAILABLE,
            })
        
        # Extract RAR
        extract_dir = os.path.join(temp_dir, 'extracted')
        os.makedirs(extract_dir, exist_ok=True)
        
        try:
            # Verify file is readable and has content
            file_size = os.path.getsize(rar_path)
            if file_size < 100:  # RAR files should be at least 100 bytes
                messages.error(request, f'File is too small ({file_size} bytes) to be a valid RAR archive.')
                return render(request, 'archive_converter/rar_to_zip.html', {
                    'rarfile_available': RARFILE_AVAILABLE,
                })
            
            # Open RAR file and extract
            # Ensure unrar path is set
            if RARFILE_AVAILABLE and hasattr(rarfile, 'UNRAR_TOOL'):
                # Verify unrar is accessible
                unrar_tool = rarfile.UNRAR_TOOL
                if unrar_tool != 'unrar' and not os.path.exists(unrar_tool):
                    # Try to find unrar again
                    for path in [os.path.expanduser('~/bin/unrar'), '/usr/local/bin/unrar', '/usr/bin/unrar']:
                        if os.path.exists(path):
                            rarfile.UNRAR_TOOL = path
                            break
            
            with rarfile.RarFile(rar_path, 'r') as rar_ref:
                # Test if RAR file is valid
                file_list = rar_ref.namelist()
                if not file_list:
                    messages.error(request, 'The RAR file appears to be empty or corrupted.')
                    return render(request, 'archive_converter/rar_to_zip.html', {
                        'rarfile_available': RARFILE_AVAILABLE,
                    })
                rar_ref.extractall(extract_dir)
        except rarfile.RarCannotExec:
            messages.error(request, 'RAR extraction requires unrar binary. Please install unrar (brew install unrar on macOS, apt-get install unrar on Linux).')
            return render(request, 'archive_converter/rar_to_zip.html', {
                'rarfile_available': RARFILE_AVAILABLE,
            })
        except (rarfile.RarOpenError, rarfile.RarCRCError, rarfile.RarFatalError, rarfile.RarNoFilesError) as e:
            messages.error(request, f'RAR file error: {str(e)}. The file may be corrupted, incomplete, or not a valid RAR archive.')
            return render(request, 'archive_converter/rar_to_zip.html', {
                'rarfile_available': RARFILE_AVAILABLE,
            })
        except Exception as rar_error:
            # Catch any other rarfile-specific errors
            error_str = str(rar_error)
            if 'Failed the read enough data' in error_str or 'req=' in error_str:
                messages.error(request, 'The RAR file appears to be incomplete or corrupted. Please ensure the file was uploaded completely.')
            else:
                messages.error(request, f'RAR processing error: {error_str}')
            return render(request, 'archive_converter/rar_to_zip.html', {
                'rarfile_available': RARFILE_AVAILABLE,
            })
        
        # Create ZIP with path traversal protection
        output_zip = io.BytesIO()
        extract_dir_abs = os.path.abspath(extract_dir)
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zip_out:
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Security: Ensure file is within extract_dir (prevent path traversal)
                    file_path_abs = os.path.abspath(file_path)
                    if not file_path_abs.startswith(extract_dir_abs):
                        continue  # Skip files outside extract directory
                    arcname = os.path.relpath(file_path, extract_dir)
                    # Additional security: Normalize path and check for path traversal
                    arcname_normalized = os.path.normpath(arcname)
                    if arcname_normalized.startswith('..') or os.path.isabs(arcname_normalized):
                        continue  # Skip malicious paths
                    zip_out.write(file_path, arcname_normalized)
        
        output_zip.seek(0)
        
        # Generate output filename
        base_name = os.path.splitext(uploaded_file.name)[0]
        safe_filename = f'{base_name}.zip'
        
        response = HttpResponse(output_zip.read(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{safe_filename}"'
        return response
        
    except (IOError, OSError) as e:
        error_msg = str(e)
        if 'Failed the read enough data' in error_msg or 'req=' in error_msg:
            messages.error(request, 'The RAR file appears to be incomplete or corrupted. Please ensure the file was uploaded completely and is a valid RAR archive.')
        else:
            messages.error(request, f'File I/O error: {str(e)}')
        return render(request, 'archive_converter/rar_to_zip.html', {
            'rarfile_available': RARFILE_AVAILABLE,
        })
    except Exception as e:
        error_msg = str(e)
        if 'Failed the read enough data' in error_msg:
            messages.error(request, 'The RAR file appears to be incomplete or corrupted. Please try uploading the file again or verify it is a valid RAR archive.')
        else:
            messages.error(request, f'Error processing file: {str(e)}')
        return render(request, 'archive_converter/rar_to_zip.html', {
            'rarfile_available': RARFILE_AVAILABLE,
        })
    finally:
        if temp_dir:
            try:
                shutil.rmtree(temp_dir)
            except (OSError, PermissionError):
                pass


def zip_to_7z(request):
    """Convert ZIP to 7Z"""
    if request.method != 'POST':
        # Clear any stale py7zr error messages on GET requests
        if PY7ZR_AVAILABLE:
            list(messages.get_messages(request))
        return render(request, 'archive_converter/zip_to_7z.html', {
            'py7zr_available': PY7ZR_AVAILABLE,
        })
    
    if 'archive_file' not in request.FILES:
        messages.error(request, 'Please upload a ZIP file.')
        return render(request, 'archive_converter/zip_to_7z.html', {
            'py7zr_available': PY7ZR_AVAILABLE,
        })
    
    uploaded_file = request.FILES['archive_file']
    
    # Validate file type
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    if file_ext != '.zip':
        messages.error(request, 'Please upload a ZIP file.')
        return render(request, 'archive_converter/zip_to_7z.html', {
            'py7zr_available': PY7ZR_AVAILABLE,
        })
    
    # Validate file size (max 500MB)
    max_size = 500 * 1024 * 1024
    if uploaded_file.size > max_size:
        messages.error(request, f'File size exceeds 500MB limit. Your file is {uploaded_file.size / (1024 * 1024):.1f}MB.')
        return render(request, 'archive_converter/zip_to_7z.html', {
            'py7zr_available': PY7ZR_AVAILABLE,
        })
    
    if not PY7ZR_AVAILABLE:
        messages.error(request, '7Z support requires py7zr library. Install with: pip install py7zr')
        return render(request, 'archive_converter/zip_to_7z.html', {
            'py7zr_available': PY7ZR_AVAILABLE,
        })
    
    temp_dir = None
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        
        # Save uploaded ZIP
        zip_path = os.path.join(temp_dir, 'input.zip')
        with open(zip_path, 'wb') as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)
        
        # Extract ZIP
        extract_dir = os.path.join(temp_dir, 'extracted')
        os.makedirs(extract_dir, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # Create 7Z with path traversal protection
        output_7z = io.BytesIO()
        extract_dir_abs = os.path.abspath(extract_dir)
        with py7zr.SevenZipFile(output_7z, 'w') as archive:
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Security: Ensure file is within extract_dir (prevent path traversal)
                    file_path_abs = os.path.abspath(file_path)
                    if not file_path_abs.startswith(extract_dir_abs):
                        continue  # Skip files outside extract directory
                    arcname = os.path.relpath(file_path, extract_dir)
                    # Additional security: Normalize path and check for path traversal
                    arcname_normalized = os.path.normpath(arcname)
                    if arcname_normalized.startswith('..') or os.path.isabs(arcname_normalized):
                        continue  # Skip malicious paths
                    archive.write(file_path, arcname_normalized)
        
        output_7z.seek(0)
        
        # Generate output filename
        base_name = os.path.splitext(uploaded_file.name)[0]
        safe_filename = f'{base_name}.7z'
        
        response = HttpResponse(output_7z.read(), content_type='application/x-7z-compressed')
        response['Content-Disposition'] = f'attachment; filename="{safe_filename}"'
        return response
        
    except Exception as e:
        messages.error(request, f'Error processing file: {str(e)}')
        return render(request, 'archive_converter/zip_to_7z.html', {
            'py7zr_available': PY7ZR_AVAILABLE,
        })
    finally:
        if temp_dir:
            try:
                shutil.rmtree(temp_dir)
            except (OSError, PermissionError):
                pass


def sevenz_to_zip(request):
    """Convert 7Z to ZIP"""
    if request.method != 'POST':
        # Clear any stale py7zr error messages on GET requests
        if PY7ZR_AVAILABLE:
            list(messages.get_messages(request))
        return render(request, 'archive_converter/7z_to_zip.html', {
            'py7zr_available': PY7ZR_AVAILABLE,
        })
    
    if 'archive_file' not in request.FILES:
        messages.error(request, 'Please upload a 7Z file.')
        return render(request, 'archive_converter/7z_to_zip.html', {
            'py7zr_available': PY7ZR_AVAILABLE,
        })
    
    uploaded_file = request.FILES['archive_file']
    
    # Validate file type
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    if file_ext != '.7z':
        messages.error(request, 'Please upload a 7Z file.')
        return render(request, 'archive_converter/7z_to_zip.html', {
            'py7zr_available': PY7ZR_AVAILABLE,
        })
    
    # Validate file size (max 500MB)
    max_size = 500 * 1024 * 1024
    if uploaded_file.size > max_size:
        messages.error(request, f'File size exceeds 500MB limit. Your file is {uploaded_file.size / (1024 * 1024):.1f}MB.')
        return render(request, 'archive_converter/7z_to_zip.html', {
            'py7zr_available': PY7ZR_AVAILABLE,
        })
    
    if not PY7ZR_AVAILABLE:
        messages.error(request, '7Z support requires py7zr library. Install with: pip install py7zr')
        return render(request, 'archive_converter/7z_to_zip.html', {
            'py7zr_available': PY7ZR_AVAILABLE,
        })
    
    temp_dir = None
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        
        # Save uploaded 7Z
        sevenz_path = os.path.join(temp_dir, 'input.7z')
        with open(sevenz_path, 'wb') as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)
        
        # Extract 7Z
        extract_dir = os.path.join(temp_dir, 'extracted')
        os.makedirs(extract_dir, exist_ok=True)
        
        with py7zr.SevenZipFile(sevenz_path, mode='r') as archive:
            archive.extractall(path=extract_dir)
        
        # Create ZIP with path traversal protection
        output_zip = io.BytesIO()
        extract_dir_abs = os.path.abspath(extract_dir)
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zip_out:
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Security: Ensure file is within extract_dir (prevent path traversal)
                    file_path_abs = os.path.abspath(file_path)
                    if not file_path_abs.startswith(extract_dir_abs):
                        continue  # Skip files outside extract directory
                    arcname = os.path.relpath(file_path, extract_dir)
                    # Additional security: Normalize path and check for path traversal
                    arcname_normalized = os.path.normpath(arcname)
                    if arcname_normalized.startswith('..') or os.path.isabs(arcname_normalized):
                        continue  # Skip malicious paths
                    zip_out.write(file_path, arcname_normalized)
        
        output_zip.seek(0)
        
        # Generate output filename
        base_name = os.path.splitext(uploaded_file.name)[0]
        safe_filename = f'{base_name}.zip'
        
        response = HttpResponse(output_zip.read(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{safe_filename}"'
        return response
        
    except Exception as e:
        messages.error(request, f'Error processing file: {str(e)}')
        return render(request, 'archive_converter/7z_to_zip.html', {
            'py7zr_available': PY7ZR_AVAILABLE,
        })
    finally:
        if temp_dir:
            try:
                shutil.rmtree(temp_dir)
            except (OSError, PermissionError):
                pass


def targz_to_zip(request):
    """Convert TAR.GZ to ZIP"""
    if request.method != 'POST':
        return render(request, 'archive_converter/targz_to_zip.html')
    
    if 'archive_file' not in request.FILES:
        messages.error(request, 'Please upload a TAR.GZ file.')
        return render(request, 'archive_converter/targz_to_zip.html')
    
    uploaded_file = request.FILES['archive_file']
    
    # Validate file type
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    file_name_lower = uploaded_file.name.lower()
    if not (file_name_lower.endswith('.tar.gz') or file_name_lower.endswith('.tgz') or file_ext == '.gz'):
        messages.error(request, 'Please upload a TAR.GZ or TGZ file.')
        return render(request, 'archive_converter/targz_to_zip.html')
    
    # Validate file size (max 500MB)
    max_size = 500 * 1024 * 1024
    if uploaded_file.size > max_size:
        messages.error(request, f'File size exceeds 500MB limit. Your file is {uploaded_file.size / (1024 * 1024):.1f}MB.')
        return render(request, 'archive_converter/targz_to_zip.html')
    
    temp_dir = None
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        
        # Save uploaded TAR.GZ
        targz_path = os.path.join(temp_dir, 'input.tar.gz')
        with open(targz_path, 'wb') as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)
        
        # Extract TAR.GZ
        extract_dir = os.path.join(temp_dir, 'extracted')
        os.makedirs(extract_dir, exist_ok=True)
        
        with tarfile.open(targz_path, 'r:gz') as tar_ref:
            tar_ref.extractall(extract_dir)
        
        # Create ZIP with path traversal protection
        output_zip = io.BytesIO()
        extract_dir_abs = os.path.abspath(extract_dir)
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zip_out:
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Security: Ensure file is within extract_dir (prevent path traversal)
                    file_path_abs = os.path.abspath(file_path)
                    if not file_path_abs.startswith(extract_dir_abs):
                        continue  # Skip files outside extract directory
                    arcname = os.path.relpath(file_path, extract_dir)
                    # Additional security: Normalize path and check for path traversal
                    arcname_normalized = os.path.normpath(arcname)
                    if arcname_normalized.startswith('..') or os.path.isabs(arcname_normalized):
                        continue  # Skip malicious paths
                    zip_out.write(file_path, arcname_normalized)
        
        output_zip.seek(0)
        
        # Generate output filename
        base_name = uploaded_file.name
        if base_name.endswith('.tar.gz'):
            base_name = base_name[:-7]
        elif base_name.endswith('.tgz'):
            base_name = base_name[:-4]
        elif base_name.endswith('.gz'):
            base_name = base_name[:-3]
        safe_filename = f'{base_name}.zip'
        
        response = HttpResponse(output_zip.read(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{safe_filename}"'
        return response
        
    except Exception as e:
        messages.error(request, f'Error processing file: {str(e)}')
        return render(request, 'archive_converter/targz_to_zip.html')
    finally:
        if temp_dir:
            try:
                shutil.rmtree(temp_dir)
            except (OSError, PermissionError):
                pass


def zip_to_targz(request):
    """Convert ZIP to TAR.GZ"""
    if request.method != 'POST':
        return render(request, 'archive_converter/zip_to_targz.html')
    
    if 'archive_file' not in request.FILES:
        messages.error(request, 'Please upload a ZIP file.')
        return render(request, 'archive_converter/zip_to_targz.html')
    
    uploaded_file = request.FILES['archive_file']
    
    # Validate file type
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    if file_ext != '.zip':
        messages.error(request, 'Please upload a ZIP file.')
        return render(request, 'archive_converter/zip_to_targz.html')
    
    # Validate file size (max 500MB)
    max_size = 500 * 1024 * 1024
    if uploaded_file.size > max_size:
        messages.error(request, f'File size exceeds 500MB limit. Your file is {uploaded_file.size / (1024 * 1024):.1f}MB.')
        return render(request, 'archive_converter/zip_to_targz.html')
    
    temp_dir = None
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        
        # Save uploaded ZIP
        zip_path = os.path.join(temp_dir, 'input.zip')
        with open(zip_path, 'wb') as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)
        
        # Extract ZIP
        extract_dir = os.path.join(temp_dir, 'extracted')
        os.makedirs(extract_dir, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # Create TAR.GZ with path traversal protection
        output_targz = io.BytesIO()
        extract_dir_abs = os.path.abspath(extract_dir)
        with tarfile.open(fileobj=output_targz, mode='w:gz') as tar_out:
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Security: Ensure file is within extract_dir (prevent path traversal)
                    file_path_abs = os.path.abspath(file_path)
                    if not file_path_abs.startswith(extract_dir_abs):
                        continue  # Skip files outside extract directory
                    arcname = os.path.relpath(file_path, extract_dir)
                    # Additional security: Normalize path and check for path traversal
                    arcname_normalized = os.path.normpath(arcname)
                    if arcname_normalized.startswith('..') or os.path.isabs(arcname_normalized):
                        continue  # Skip malicious paths
                    tar_out.add(file_path, arcname=arcname_normalized)
        
        output_targz.seek(0)
        
        # Generate output filename
        base_name = os.path.splitext(uploaded_file.name)[0]
        safe_filename = f'{base_name}.tar.gz'
        
        response = HttpResponse(output_targz.read(), content_type='application/gzip')
        response['Content-Disposition'] = f'attachment; filename="{safe_filename}"'
        return response
        
    except Exception as e:
        messages.error(request, f'Error processing file: {str(e)}')
        return render(request, 'archive_converter/zip_to_targz.html')
    finally:
        if temp_dir:
            try:
                shutil.rmtree(temp_dir)
            except (OSError, PermissionError):
                pass


def extract_iso(request):
    """Extract ISO file"""
    if request.method != 'POST':
        # Clear any stale pycdlib error messages on GET requests
        if PYCDLIB_AVAILABLE:
            list(messages.get_messages(request))
        return render(request, 'archive_converter/extract_iso.html', {
            'pycdlib_available': PYCDLIB_AVAILABLE,
        })
    
    if 'archive_file' not in request.FILES:
        messages.error(request, 'Please upload an ISO file.')
        return render(request, 'archive_converter/extract_iso.html', {
            'pycdlib_available': PYCDLIB_AVAILABLE,
        })
    
    uploaded_file = request.FILES['archive_file']
    
    # Validate file type
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    if file_ext not in ['.iso', '.img']:
        messages.error(request, 'Please upload an ISO or IMG file.')
        return render(request, 'archive_converter/extract_iso.html', {
            'pycdlib_available': PYCDLIB_AVAILABLE,
        })
    
    # Validate file size (max 4GB)
    max_size = 4 * 1024 * 1024 * 1024
    if uploaded_file.size > max_size:
        messages.error(request, f'File size exceeds 4GB limit. Your file is {uploaded_file.size / (1024 * 1024 * 1024):.1f}GB.')
        return render(request, 'archive_converter/extract_iso.html', {
            'pycdlib_available': PYCDLIB_AVAILABLE,
        })
    
    if not PYCDLIB_AVAILABLE:
        messages.error(request, 'ISO extraction requires pycdlib library. Install with: pip install pycdlib')
        return render(request, 'archive_converter/extract_iso.html', {
            'pycdlib_available': PYCDLIB_AVAILABLE,
        })
    
    temp_dir = None
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        
        # Save uploaded ISO
        iso_path = os.path.join(temp_dir, 'input.iso')
        with open(iso_path, 'wb') as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)
        
        # Extract ISO
        extract_dir = os.path.join(temp_dir, 'extracted')
        os.makedirs(extract_dir, exist_ok=True)
        
        iso = pycdlib.PyCdlib()
        iso.open(iso_path)
        
        # Recursive function to extract files from ISO with proper error handling
        extract_dir_abs = os.path.abspath(extract_dir)
        failed_files = []
        
        def extract_iso_recursive(iso_path_internal, extract_path):
            nonlocal failed_files
            try:
                children = iso.list_children(iso_path=iso_path_internal)
                for child in children:
                    # Skip . and .. entries
                    if child in ['.', '..']:
                        continue
                    
                    # Security: Validate child name (prevent path traversal)
                    if '..' in child or '/' in child or '\\' in child:
                        failed_files.append(f"Invalid path in ISO: {child}")
                        continue
                    
                    child_path = iso_path_internal
                    if not child_path.endswith('/'):
                        child_path += '/'
                    child_path += child
                    
                    child_extract_path = os.path.join(extract_path, child)
                    
                    # Security: Ensure extract path stays within extract_dir (prevent path traversal)
                    child_extract_path_abs = os.path.abspath(child_extract_path)
                    if not child_extract_path_abs.startswith(extract_dir_abs):
                        failed_files.append(f"Path traversal attempt blocked: {child_path}")
                        continue
                    
                    try:
                        if iso.is_file(iso_path=child_path):
                            # Create directory if needed
                            os.makedirs(extract_path, exist_ok=True)
                            # Extract file
                            with iso.open_file_from_iso(iso_path=child_path) as infp:
                                with open(child_extract_path, 'wb') as outfp:
                                    outfp.write(infp.read())
                        elif iso.is_dir(iso_path=child_path):
                            # Recursively extract directory
                            extract_iso_recursive(child_path, child_extract_path)
                    except Exception as e:
                        # Log the error instead of silently suppressing
                        error_msg = f"Failed to extract {child_path}: {str(e)}"
                        failed_files.append(error_msg)
                        logger = logging.getLogger(__name__)
                        logger.warning(error_msg, exc_info=True)
                        continue
            except Exception as e:
                # Log the error instead of silently suppressing
                error_msg = f"Error listing children in ISO path {iso_path_internal}: {str(e)}"
                failed_files.append(error_msg)
                logger = logging.getLogger(__name__)
                logger.warning(error_msg, exc_info=True)
        
        # Start extraction from root
        extract_iso_recursive('/', extract_dir)
        
        iso.close()
        
        # Log any failed files
        if failed_files:
            logger = logging.getLogger(__name__)
            logger.warning(f"ISO extraction completed with {len(failed_files)} failed files: {failed_files[:5]}")
        
        # Create ZIP of extracted files with path traversal protection
        output_zip = io.BytesIO()
        extract_dir_abs = os.path.abspath(extract_dir)
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zip_out:
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Security: Ensure file is within extract_dir (prevent path traversal)
                    file_path_abs = os.path.abspath(file_path)
                    if not file_path_abs.startswith(extract_dir_abs):
                        continue  # Skip files outside extract directory
                    arcname = os.path.relpath(file_path, extract_dir)
                    # Additional security: Normalize path and check for path traversal
                    arcname_normalized = os.path.normpath(arcname)
                    if arcname_normalized.startswith('..') or os.path.isabs(arcname_normalized):
                        continue  # Skip malicious paths
                    zip_out.write(file_path, arcname_normalized)
        
        output_zip.seek(0)
        
        # Generate output filename
        base_name = os.path.splitext(uploaded_file.name)[0]
        safe_filename = f'{base_name}_extracted.zip'
        
        response = HttpResponse(output_zip.read(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{safe_filename}"'
        return response
        
    except Exception as e:
        messages.error(request, f'Error processing file: {str(e)}')
        return render(request, 'archive_converter/extract_iso.html', {
            'pycdlib_available': PYCDLIB_AVAILABLE,
        })
    finally:
        if temp_dir:
            try:
                shutil.rmtree(temp_dir)
            except (OSError, PermissionError):
                pass


def create_zip_from_files(request):
    """Create ZIP from multiple uploaded files"""
    if request.method != 'POST':
        return render(request, 'archive_converter/create_zip.html')
    
    if 'files' not in request.FILES:
        messages.error(request, 'Please upload at least one file.')
        return render(request, 'archive_converter/create_zip.html')
    
    uploaded_files = request.FILES.getlist('files')
    
    if not uploaded_files:
        messages.error(request, 'Please upload at least one file.')
        return render(request, 'archive_converter/create_zip.html')
    
    # Validate total size (max 500MB)
    total_size = sum(f.size for f in uploaded_files)
    max_size = 500 * 1024 * 1024
    if total_size > max_size:
        messages.error(request, f'Total file size exceeds 500MB limit. Your files total {total_size / (1024 * 1024):.1f}MB.')
        return render(request, 'archive_converter/create_zip.html')
    
    temp_dir = None
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        
        # Save uploaded files
        for uploaded_file in uploaded_files:
            file_path = os.path.join(temp_dir, uploaded_file.name)
            # Handle duplicate names
            counter = 1
            while os.path.exists(file_path):
                name, ext = os.path.splitext(uploaded_file.name)
                file_path = os.path.join(temp_dir, f'{name}_{counter}{ext}')
                counter += 1
            
            with open(file_path, 'wb') as f:
                for chunk in uploaded_file.chunks():
                    f.write(chunk)
        
        # Create ZIP
        output_zip = io.BytesIO()
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zip_out:
            for file in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, file)
                if os.path.isfile(file_path):
                    zip_out.write(file_path, file)
        
        output_zip.seek(0)
        
        # Generate output filename
        zip_name = request.POST.get('zip_name', 'archive').strip()
        if not zip_name:
            zip_name = 'archive'
        # Sanitize filename
        zip_name = ''.join(c for c in zip_name if c.isalnum() or c in (' ', '-', '_')).strip()
        if not zip_name:
            zip_name = 'archive'
        safe_filename = f'{zip_name}.zip'
        
        response = HttpResponse(output_zip.read(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{safe_filename}"'
        return response
        
    except Exception as e:
        messages.error(request, f'Error processing files: {str(e)}')
        return render(request, 'archive_converter/create_zip.html')
    finally:
        if temp_dir:
            try:
                shutil.rmtree(temp_dir)
            except (OSError, PermissionError):
                pass

