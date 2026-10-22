from django.db import models
from django.utils import timezone
from django.conf import settings

class ConversionLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversion_logs'
    )
    timestamp = models.DateTimeField(default=timezone.now)
    filename = models.CharField(max_length=255)
    file_size_kb = models.FloatField(default=0.0)
    bank_selected = models.CharField(max_length=50)
    include_summary = models.BooleanField(default=False)
    export_format = models.CharField(max_length=10)
    transactions_count = models.IntegerField(default=0)
    reconciliation_status = models.CharField(max_length=50, blank=True, null=True)
    duration_seconds = models.FloatField(default=0.0)
    is_successful = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        user_str = self.user.username if self.user else "System"
        local_time = timezone.localtime(self.timestamp)
        return f"{local_time.strftime('%Y-%m-%d %H:%M')} - {user_str}: {self.filename} ({self.bank_selected})"
