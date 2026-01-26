from django.db import models
import uuid


class MediaJob(models.Model):
    """Model to track media conversion jobs (video/audio)"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    OPERATION_CHOICES = [
        ('video_converter', 'Video Converter'),
        ('video_merge', 'Video Merge'),
        ('audio_converter', 'Audio Converter'),
        ('audio_merge', 'Audio Merge'),
        ('video_to_gif', 'Video to GIF'),
        ('video_compressor', 'Video Compressor'),
        ('mp4_to_mp3', 'MP4 to MP3'),
        ('mute_video', 'Mute Video'),
        ('reduce_noise', 'Reduce Noise'),
        ('audio_splitter', 'Audio Splitter'),
    ]
    
    job_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    operation = models.CharField(max_length=30, choices=OPERATION_CHOICES)
    file_key = models.CharField(max_length=500)  # Input file path or S3 key
    output_file_key = models.CharField(max_length=500, null=True, blank=True)  # Output file path or S3 key
    file_size = models.BigIntegerField(null=True, blank=True)
    output_format = models.CharField(max_length=20, null=True, blank=True)
    user_ip = models.GenericIPAddressField()
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    progress = models.IntegerField(default=0)  # Progress percentage (0-100)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['user_ip', 'created_at']),
        ]
    
    def __str__(self):
        return f"MediaJob {self.job_id} - {self.operation} - {self.status}"
