from django.db import models

class Feedback(models.Model):
    """User feedback model"""
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Feedback'
        verbose_name_plural = 'Feedback'
    
    def __str__(self):
        return f"Feedback from {self.created_at.strftime('%Y-%m-%d %H:%M')}"


















