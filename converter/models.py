from django.db import models
from django.utils import timezone

class ConversionLog(models.Model):
    timestamp = models.DateTimeField(default=timezone.now)
    filename = models.CharField(max_length=255)
    bank_selected = models.CharField(max_length=50)
    include_summary = models.BooleanField(default=False)
    export_format = models.CharField(max_length=10)
    is_successful = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {self.filename} ({self.bank_selected})"
