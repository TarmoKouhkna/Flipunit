"""
Celery tasks for media converter operations
"""
import os
import tempfile
import shutil
import subprocess
import logging
import re
from celery import shared_task
from django.utils import timezone
from django.conf import settings
from .models import MediaJob

logger = logging.getLogger(__name__)


def _check_ffmpeg():
    """Check if ffmpeg is available"""
    ffmpeg_path = shutil.which('ffmpeg') or '/usr/local/bin/ffmpeg'
    ffprobe_path = shutil.which('ffprobe') or '/usr/local/bin/ffprobe'
    
    if not os.path.exists(ffmpeg_path):
        return None, None, 'ffmpeg not found'
    if not os.path.exists(ffprobe_path):
        return None, None, 'ffprobe not found'
    
    return ffmpeg_path, ffprobe_path, None


@shared_task(
    bind=True,
    soft_time_limit=1200,  # 20 minutes
    time_limit=1260,  # 21 minutes
    max_retries=0,  # No retry for CPU-bound operations
    queue='media_processing'
)
def video_converter_task(self, job_id, file_path, output_format):
    """Convert video to different format"""
    job = MediaJob.objects.get(job_id=job_id)
    
    temp_dir = None
    try:
        job.status = 'processing'
        job.save()
        
        ffmpeg_path, ffprobe_path, error = _check_ffmpeg()
        if error:
            raise Exception(error)
        
        file_ext = os.path.splitext(file_path)[1]
        temp_dir = os.path.dirname(file_path)
        output_path = os.path.join(temp_dir, f'output.{output_format}')
        
        # Build FFmpeg command based on output format (matching view logic)
        if output_format == 'webm':
            cmd = [
                ffmpeg_path,
                '-i', file_path,
                '-c:v', 'libvpx-vp9',  # Video codec
                '-c:a', 'libopus',  # Audio codec
                '-speed', '4',  # Fast encoding (0-8, higher = faster)
                '-threads', '2',  # Limit to 2 threads to prevent system overload
                '-y',
                output_path
            ]
        elif output_format == 'avi':
            cmd = [
                ffmpeg_path,
                '-i', file_path,
                '-c:v', 'libx264',  # Video codec
                '-c:a', 'libmp3lame',  # Audio codec
                '-preset', 'ultrafast',  # Fastest encoding (less CPU intensive)
                '-crf', '28',  # Slightly lower quality but much faster
                '-threads', '2',  # Limit to 2 threads to prevent system overload
                '-y',
                output_path
            ]
        elif output_format == '3gp':
            cmd = [
                ffmpeg_path,
                '-i', file_path,
                '-c:v', 'libx264',  # Video codec
                '-c:a', 'aac',  # Audio codec
                '-preset', 'ultrafast',  # Fastest encoding (less CPU intensive)
                '-crf', '28',  # Slightly lower quality but much faster
                '-threads', '2',  # Limit to 2 threads to prevent system overload
                '-s', '320x240',  # Common 3GP resolution
                '-b:v', '128k',  # Video bitrate for 3GP
                '-b:a', '64k',  # Audio bitrate for 3GP
                '-y',
                output_path
            ]
        else:  # mp4, mov, mkv
            cmd = [
                ffmpeg_path,
                '-i', file_path,
                '-c:v', 'libx264',  # Video codec
                '-c:a', 'aac',  # Audio codec
                '-preset', 'ultrafast',  # Fastest encoding (less CPU intensive)
                '-crf', '28',  # Slightly lower quality but much faster
                '-threads', '2',  # Limit to 2 threads to prevent system overload
                '-movflags', '+faststart',  # Optimize for web playback
                '-y',
                output_path
            ]
        
        # Adjust timeout based on file size (larger files need more time)
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        timeout_seconds = 600  # 10 minutes default
        if file_size_mb > 300:
            timeout_seconds = 1200  # 20 minutes for very large files
        elif file_size_mb > 200:
            timeout_seconds = 900  # 15 minutes for large files
        
        logger.info(f"Running FFmpeg command for job {job_id}: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_seconds)
        
        if result.returncode != 0:
            error_msg = result.stderr if result.stderr else result.stdout if result.stdout else 'Unknown error during video conversion'
            full_error = error_msg[:1000] if len(error_msg) > 1000 else error_msg
            raise Exception(f"FFmpeg error: {full_error}")
        
        if not os.path.exists(output_path):
            error_msg = result.stderr if result.stderr else result.stdout if result.stdout else 'Unknown error - output file was not created'
            full_error = error_msg[:1000] if len(error_msg) > 1000 else error_msg
            raise Exception(f"Output file not created: {full_error}")
        
        # Verify file is not empty
        if os.path.getsize(output_path) == 0:
            raise Exception("Output file is empty. The video file may be corrupted or in an unsupported format.")
        
        # Move output file to final shared location
        final_output_dir = os.path.join(settings.MEDIA_ROOT, 'video_conversions')
        os.makedirs(final_output_dir, exist_ok=True)
        
        # Generate a safe filename for the output
        import re
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        # Remove temp_ prefix if present
        if base_name.startswith('temp_'):
            base_name = base_name[5:]
        base_name = re.sub(r'[^\w\s.-]', '', base_name).strip()
        base_name = re.sub(r'[-\s]+', '-', base_name)
        final_output_filename = f'{base_name}.{output_format}'
        final_output_path = os.path.join(final_output_dir, final_output_filename)
        
        shutil.move(output_path, final_output_path)
        
        job.status = 'completed'
        job.output_file_key = final_output_path
        job.completed_at = timezone.now()
        job.save()
        
        logger.info(f"Video conversion completed for job {job_id}. Output: {final_output_path}")
        return final_output_path
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Video conversion failed for job {job_id}: {error_msg}", exc_info=True)
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
    soft_time_limit=2400,  # 40 minutes
    time_limit=2460,  # 41 minutes
    max_retries=0,
    queue='media_processing'
)
def video_merge_task(self, job_id, file_paths, trim_params, total_size_mb):
    """Merge multiple video files with trimming and normalization support"""
    job = MediaJob.objects.get(job_id=job_id)
    
    try:
        job.status = 'processing'
        job.save()
        
        ffmpeg_path, _, error = _check_ffmpeg()
        if error:
            raise Exception(error)
        
        # Use same directory as input files (shared media directory)
        temp_dir = os.path.dirname(file_paths[0])
        output_path = os.path.join(temp_dir, f'merged_{job_id}.mp4')
        output_format = 'mp4'
        
        # Adjust timeout based on total file size
        timeout_seconds = 600  # 10 minutes default
        if total_size_mb > 3000:
            timeout_seconds = 2400  # 40 minutes for very large files (up to 5GB)
        elif total_size_mb > 2000:
            timeout_seconds = 1800  # 30 minutes for large files
        elif total_size_mb > 1000:
            timeout_seconds = 1200  # 20 minutes for medium-large files
        elif total_size_mb > 500:
            timeout_seconds = 900  # 15 minutes for medium files
        
        # Use concat filter instead of concat demuxer for better compatibility
        # The concat filter can handle videos with different properties
        # Build filter_complex string to normalize and concatenate all videos
        filter_parts = []
        input_args = []
        
        # Add all inputs
        for input_path in file_paths:
            input_args.extend(['-i', input_path])
        
        # Process each video: trim if needed, then normalize
        for i in range(len(file_paths)):
            trim = trim_params[i] if i < len(trim_params) else {'start': 0.0, 'end': None}
            
            # Apply trimming using trim filter if needed
            needs_trimming = (trim['start'] > 0) or (trim['end'] is not None)
            
            logger.info(f'Video {i} ({file_paths[i]}): needs_trimming={needs_trimming}, start={trim["start"]}, end={trim["end"]}')
            
            if needs_trimming:
                if trim['end'] is not None and trim['end'] > trim['start']:
                    # Trim with start and end (end is absolute time, not duration)
                    # Use duration instead of end for more reliable trimming
                    duration = trim['end'] - trim['start']
                    logger.info(f'Video {i}: Applying trim start={trim["start"]}, duration={duration}')
                    filter_parts.append(f'[{i}:v]trim=start={trim["start"]}:duration={duration},setpts=PTS-STARTPTS[v{i}_trim]')
                    filter_parts.append(f'[{i}:a]atrim=start={trim["start"]}:duration={duration},asetpts=PTS-STARTPTS[a{i}_trim]')
                elif trim['start'] > 0:
                    # Trim from start only (remove beginning)
                    logger.info(f'Video {i}: Applying trim start={trim["start"]} (no end)')
                    filter_parts.append(f'[{i}:v]trim=start={trim["start"]},setpts=PTS-STARTPTS[v{i}_trim]')
                    filter_parts.append(f'[{i}:a]atrim=start={trim["start"]},asetpts=PTS-STARTPTS[a{i}_trim]')
                else:
                    logger.info(f'Video {i}: Skipping trim (invalid parameters)')
                
                # Normalize the trimmed video
                filter_parts.append(f'[v{i}_trim]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30[v{i}]')
                filter_parts.append(f'[a{i}_trim]aformat=sample_rates=44100:channel_layouts=stereo[a{i}]')
            else:
                # No trimming, just normalize
                filter_parts.append(f'[{i}:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30[v{i}]')
                filter_parts.append(f'[{i}:a]aformat=sample_rates=44100:channel_layouts=stereo[a{i}]')
        
        # Concatenate all normalized videos
        # Build concat inputs (no semicolons between inputs in concat filter)
        concat_video_inputs = ''.join([f'[v{i}]' for i in range(len(file_paths))])
        concat_audio_inputs = ''.join([f'[a{i}]' for i in range(len(file_paths))])
        filter_parts.append(f'{concat_video_inputs}concat=n={len(file_paths)}:v=1:a=0[outv]')
        filter_parts.append(f'{concat_audio_inputs}concat=n={len(file_paths)}:v=0:a=1[outa]')
        
        filter_complex = ';'.join(filter_parts)
        
        # Always use MP4 format with H.264/AAC codecs
        cmd = [
            ffmpeg_path,
        ] + input_args + [
            '-filter_complex', filter_complex,
            '-map', '[outv]',
            '-map', '[outa]',
            '-c:v', 'libx264',  # Video codec
            '-c:a', 'aac',  # Audio codec
            '-preset', 'fast',  # Balance between speed and quality
            '-crf', '23',  # Good quality
            '-threads', '2',  # Limit threads to prevent system overload
            '-movflags', '+faststart',  # Optimize for web playback
            '-f', 'mp4',
            '-y',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_seconds)
        
        if result.returncode != 0 or not os.path.exists(output_path):
            error_msg = result.stderr if result.stderr else result.stdout if result.stdout else 'Unknown error'
            
            # Filter out FFmpeg version dumps and extract meaningful errors
            error_stripped = error_msg.strip()
            if error_stripped.startswith('ffmpeg version'):
                # This is a version dump, use friendly message
                full_error = 'Video merging failed. The video files may be corrupted, in incompatible formats, or have codec conflicts. Try using videos in the same format.'
            else:
                # Filter out version/config lines and extract actual error
                error_lines = error_msg.split('\n')
                meaningful_errors = []
                
                skip_patterns = [
                    'ffmpeg version', 'built with', 'configuration:', 'copyright',
                    'the ffmpeg developers', 'toolchain', 'libdir=', 'incdir=', 'arch=',
                    '--prefix=', '--extra-version=', '--enable-', '--disable-'
                ]
                
                for line in error_lines:
                    line_lower = line.lower().strip()
                    if not line_lower:
                        continue
                    should_skip = any(pattern in line_lower for pattern in skip_patterns) or line.strip().startswith('--')
                    if not should_skip:
                        meaningful_errors.append(line.strip())
                
                if meaningful_errors:
                    # Take last few meaningful error lines
                    error_text = '\n'.join(meaningful_errors[-5:])
                    full_error = error_text[:500].strip() if len(error_text) > 500 else error_text.strip()
                    if not full_error or len(full_error) < 10:
                        full_error = 'Video merging failed. The video files may be corrupted, in incompatible formats, or have codec conflicts.'
                else:
                    full_error = 'Video merging failed. The video files may be corrupted, in incompatible formats, or have codec conflicts.'
            
            raise Exception(full_error)
        
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise Exception('Merging failed - output file is empty.')
        
        job.status = 'completed'
        job.output_file_key = output_path
        job.completed_at = timezone.now()
        job.save()
        
        logger.info(f"Video merge completed for job {job_id}")
        return output_path
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Video merge failed for job {job_id}: {error_msg}")
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
    queue='media_processing'
)
def audio_converter_task(self, job_id, file_path, output_format, original_filename):
    """Convert audio to different format"""
    import re
    from django.conf import settings
    
    job = MediaJob.objects.get(job_id=job_id)
    
    try:
        job.status = 'processing'
        job.save()
        
        ffmpeg_path, _, error = _check_ffmpeg()
        if error:
            raise Exception(error)
        
        # Determine output extension
        if output_format == 'aac':
            output_ext = 'm4a'  # AAC uses m4a container
        elif output_format == 'aiff':
            output_ext = 'aiff'
        else:
            output_ext = output_format
        
        # Use same directory as input file (shared media directory)
        output_path = os.path.join(os.path.dirname(file_path), f'output_{job_id}.{output_ext}')
        
        # Codec mapping
        codec_map = {
            'mp3': 'libmp3lame',
            'wav': 'pcm_s16le',
            'ogg': 'libvorbis',
            'flac': 'flac',
            'aac': 'aac',
            'm4a': 'aac',  # M4A uses AAC codec
            'aiff': 'pcm_s16be',  # AIFF uses big-endian PCM
        }
        
        # Build FFmpeg command
        cmd = [
            ffmpeg_path,
            '-i', file_path,
            '-vn',  # No video
            '-map', '0:a',  # Map only audio stream
            '-c:a', codec_map[output_format],  # ALWAYS re-encode with specified codec
            '-ar', '44100',  # Set sample rate to ensure re-encoding
            '-ac', '2',  # Set to stereo
        ]
        
        # Format-specific settings
        if output_format == 'wav':
            cmd.extend(['-sample_fmt', 's16'])
            cmd.extend(['-f', 'wav'])
        elif output_format == 'flac':
            cmd.extend(['-compression_level', '5'])
            cmd.extend(['-f', 'flac'])
        elif output_format == 'aac':
            cmd.extend(['-b:a', '192k'])
            cmd.extend(['-f', 'mp4'])
            cmd.extend(['-movflags', '+faststart'])
        elif output_format == 'm4a':
            cmd.extend(['-b:a', '192k'])
            cmd.extend(['-f', 'mp4'])
            cmd.extend(['-movflags', '+faststart'])
        elif output_format == 'aiff':
            cmd.extend(['-sample_fmt', 's16'])
            cmd.extend(['-f', 'aiff'])
        elif output_format == 'mp3':
            cmd.extend(['-b:a', '192k'])
            cmd.extend(['-f', 'mp3'])
        elif output_format == 'ogg':
            cmd.extend(['-b:a', '192k'])
            cmd.extend(['-f', 'ogg'])
        
        # Add flags to prevent stream copy
        cmd.extend([
            '-avoid_negative_ts', 'make_zero',
            '-fflags', '+genpts',
            '-y',  # Overwrite output file
            output_path
        ])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode != 0:
            error_msg = result.stderr if result.stderr else result.stdout if result.stdout else 'Unknown error'
            error_lines = error_msg.split('\n')
            relevant_error = '\n'.join([line for line in error_lines if line.strip() and not line.startswith('frame=')][-5:])
            if not relevant_error.strip():
                relevant_error = error_msg[:500]
            raise Exception(f'Conversion failed: {relevant_error[:500]}')
        
        if not os.path.exists(output_path):
            raise Exception('Output file was not created')
        
        # Generate safe filename
        base_name = os.path.splitext(original_filename)[0]
        base_name = re.sub(r'[^\w\s.-]', '', base_name).strip()
        base_name = re.sub(r'[-\s]+', '-', base_name)
        safe_filename = f'{base_name}.{output_ext}'
        
        job.status = 'completed'
        job.output_file_key = output_path
        job.output_format = output_ext
        job.completed_at = timezone.now()
        job.save()
        
        logger.info(f"Audio conversion completed for job {job_id}")
        return output_path
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Audio conversion failed for job {job_id}: {error_msg}")
        job.status = 'failed'
        job.error_message = error_msg
        job.completed_at = timezone.now()
        job.save()
        raise
    finally:
        # Clean up input file after processing
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cleaned up input file: {file_path}")
        except Exception as cleanup_error:
            logger.warning(f"Failed to clean up file {file_path}: {cleanup_error}")


@shared_task(
    bind=True,
    soft_time_limit=600,  # 10 minutes
    time_limit=660,  # 11 minutes
    max_retries=0,
    queue='media_processing'
)
def audio_merge_task(self, job_id, file_paths, output_ext):
    """Merge multiple audio files with format conversion fallback"""
    job = MediaJob.objects.get(job_id=job_id)
    
    try:
        job.status = 'processing'
        job.save()
        
        ffmpeg_path, _, error = _check_ffmpeg()
        if error:
            raise Exception(error)
        
        # Use same directory as input files (shared media directory)
        temp_dir = os.path.dirname(file_paths[0])
        file_list_path = os.path.join(temp_dir, f'concat_list_{job_id}.txt')
        output_path = os.path.join(temp_dir, f'merged_{job_id}{output_ext}')
        
        # Create file list for FFmpeg concat
        with open(file_list_path, 'w') as f:
            for input_path in file_paths:
                # Escape single quotes and backslashes for FFmpeg
                escaped_path = input_path.replace("'", "'\\''").replace("\\", "\\\\")
                f.write(f"file '{escaped_path}'\n")
        
        # Build FFmpeg command to merge
        # First, convert all to same format if needed, then concat
        cmd = [
            ffmpeg_path,
            '-f', 'concat',
            '-safe', '0',
            '-i', file_list_path,
            '-c', 'copy',  # Copy streams (fast, no re-encoding if formats match)
            '-y',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        # If concat with copy fails (different formats), re-encode
        if result.returncode != 0:
            # Re-encode all to same format
            codec_map = {
                '.mp3': 'libmp3lame',
                '.wav': 'pcm_s16le',
                '.ogg': 'libvorbis',
                '.flac': 'flac',
                '.aac': 'aac',
                '.m4a': 'aac',
                '.aiff': 'pcm_s16be',
                '.aif': 'pcm_s16be',
            }
            
            codec = codec_map.get(output_ext, 'libmp3lame')
            format_map = {
                '.mp3': 'mp3',
                '.wav': 'wav',
                '.ogg': 'ogg',
                '.flac': 'flac',
                '.aac': 'mp4',
                '.m4a': 'mp4',
                '.aiff': 'aiff',
                '.aif': 'aiff',
            }
            output_format = format_map.get(output_ext, 'mp3')
            
            cmd = [
                ffmpeg_path,
                '-f', 'concat',
                '-safe', '0',
                '-i', file_list_path,
                '-c:a', codec,
                '-ar', '44100',
                '-ac', '2',
            ]
            
            if output_format == 'mp3':
                cmd.extend(['-b:a', '192k'])
            elif output_format == 'wav':
                cmd.extend(['-sample_fmt', 's16'])
            elif output_format in ['mp4', 'aac', 'm4a']:
                cmd.extend(['-b:a', '192k'])
                cmd.extend(['-movflags', '+faststart'])
            
            cmd.extend(['-f', output_format, '-y', output_path])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode != 0 or not os.path.exists(output_path):
            error_msg = result.stderr if result.stderr else result.stdout if result.stdout else 'Unknown error'
            full_error = error_msg[:1000] if len(error_msg) > 1000 else error_msg
            raise Exception(f'Merging failed: {full_error}')
        
        if os.path.getsize(output_path) == 0:
            raise Exception('Merging failed - output file is empty.')
        
        job.status = 'completed'
        job.output_file_key = output_path
        job.completed_at = timezone.now()
        job.save()
        
        logger.info(f"Audio merge completed for job {job_id}")
        return output_path
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Audio merge failed for job {job_id}: {error_msg}")
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
    queue='media_processing'
)
def video_to_gif_task(self, job_id, file_path):
    """Convert video to GIF"""
    job = MediaJob.objects.get(job_id=job_id)
    
    try:
        job.status = 'processing'
        job.save()
        
        ffmpeg_path, _, error = _check_ffmpeg()
        if error:
            raise Exception(error)
        
        temp_dir = os.path.dirname(file_path)
        output_path = os.path.join(temp_dir, 'output.gif')
        
        cmd = [
            ffmpeg_path, '-i', file_path,
            '-vf', 'fps=10,scale=320:-1:flags=lanczos',
            '-y', output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            raise Exception(f"FFmpeg error: {result.stderr}")
        
        job.status = 'completed'
        job.output_file_key = output_path
        job.completed_at = timezone.now()
        job.save()
        
        logger.info(f"Video to GIF completed for job {job_id}")
        return output_path
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Video to GIF failed for job {job_id}: {error_msg}")
        job.status = 'failed'
        job.error_message = error_msg
        job.completed_at = timezone.now()
        job.save()
        raise


@shared_task(
    bind=True,
    soft_time_limit=1200,  # 20 minutes
    time_limit=1260,  # 21 minutes
    max_retries=0,
    queue='media_processing'
)
def video_compressor_task(self, job_id, file_path, quality):
    """Compress video file"""
    job = MediaJob.objects.get(job_id=job_id)
    
    try:
        job.status = 'processing'
        job.save()
        
        ffmpeg_path, _, error = _check_ffmpeg()
        if error:
            raise Exception(error)
        
        temp_dir = os.path.dirname(file_path)
        output_path = os.path.join(temp_dir, 'compressed.mp4')
        
        # Quality: 0-51, lower = better quality but larger file
        crf = 28 if quality == 'low' else 23 if quality == 'medium' else 18
        
        cmd = [
            ffmpeg_path, '-i', file_path,
            '-c:v', 'libx264', '-crf', str(crf),
            '-preset', 'medium', '-threads', '2', '-y', output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1200)
        
        if result.returncode != 0:
            raise Exception(f"FFmpeg error: {result.stderr}")
        
        job.status = 'completed'
        job.output_file_key = output_path
        job.completed_at = timezone.now()
        job.save()
        
        logger.info(f"Video compression completed for job {job_id}")
        return output_path
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Video compression failed for job {job_id}: {error_msg}")
        job.status = 'failed'
        job.error_message = error_msg
        job.completed_at = timezone.now()
        job.save()
        raise
