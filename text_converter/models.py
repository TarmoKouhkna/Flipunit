from django.db import models
import uuid


class TranscriptionJob(models.Model):
    """Model to track audio transcription jobs"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    job_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    file_key = models.CharField(max_length=500)  # S3 key or local file path
    file_size = models.BigIntegerField()  # File size in bytes
    duration_seconds = models.FloatField(null=True, blank=True)  # Audio duration if available
    user_ip = models.GenericIPAddressField()
    transcription_text = models.TextField(null=True, blank=True)
    detected_language = models.CharField(max_length=10, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cost_estimate = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    actual_cost = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['user_ip', 'created_at']),
        ]
    
    def __str__(self):
        return f"TranscriptionJob {self.job_id} - {self.status}"


class UserQuota(models.Model):
    """Model to track per-IP quotas for API usage"""
    ip_address = models.GenericIPAddressField(unique=True)
    daily_count = models.IntegerField(default=0)
    monthly_count = models.IntegerField(default=0)
    last_reset_daily = models.DateField(auto_now=True)
    last_reset_monthly = models.DateField(auto_now=True)
    
    class Meta:
        ordering = ['-last_reset_daily']
        indexes = [
            models.Index(fields=['ip_address']),
        ]
    
    def __str__(self):
        return f"Quota for {self.ip_address} - Daily: {self.daily_count}, Monthly: {self.monthly_count}"
