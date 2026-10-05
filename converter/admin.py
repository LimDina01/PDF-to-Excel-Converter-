from django.contrib import admin
from .models import ConversionLog

@admin.register(ConversionLog)
class ConversionLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'filename', 'bank_selected', 'export_format', 'is_successful')
    list_filter = ('is_successful', 'bank_selected', 'export_format', 'timestamp')
    search_fields = ('filename', 'error_message')
    readonly_fields = ('timestamp', 'filename', 'bank_selected', 'include_summary', 'export_format', 'is_successful', 'error_message')
    
    # Prevent editing or adding logs manually
    def has_add_permission(self, request):
        return False
        
    def has_change_permission(self, request, obj=None):
        return False
