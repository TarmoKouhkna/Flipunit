from django.db import models
import uuid


class ArchiveJob(models.Model):
    """Model to track archive processing jobs"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    OPERATION_CHOICES = [
        ('archive_converter', 'Archive Converter'),
        ('iso_extraction', 'ISO Extraction'),
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
        return f"ArchiveJob {self.job_id} - {self.operation} - {self.status}"
