from django.contrib import admin
from .models import Feedback

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'message_preview', 'ip_address']
    list_filter = ['created_at']
    search_fields = ['message']
    readonly_fields = ['created_at', 'ip_address']
    
    def message_preview(self, obj):
        return obj.message[:100] + '...' if len(obj.message) > 100 else obj.message
    message_preview.short_description = 'Message'















