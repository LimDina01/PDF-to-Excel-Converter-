from django.contrib import admin
from django.utils.html import format_html
from .models import ConversionLog

@admin.register(ConversionLog)
class ConversionLogAdmin(admin.ModelAdmin):
    list_display = (
        'formatted_time',
        'user_display',
        'filename',
        'bank_badge',
        'transactions_count',
        'reconciliation_badge',
        'file_size_display',
        'duration_display',
        'status_badge'
    )
    list_filter = ('is_successful', 'bank_selected', 'reconciliation_status', 'export_format', 'timestamp', 'user')
    search_fields = ('filename', 'user__username', 'user__first_name', 'user__last_name', 'error_message')
    date_hierarchy = 'timestamp'
    readonly_fields = (
        'user',
        'timestamp',
        'filename',
        'file_size_kb',
        'bank_selected',
        'include_summary',
        'export_format',
        'transactions_count',
        'reconciliation_status',
        'duration_seconds',
        'is_successful',
        'error_message'
    )

    def formatted_time(self, obj):
        return obj.timestamp.strftime("%Y-%m-%d %H:%M")
    formatted_time.short_description = "Timestamp"
    formatted_time.admin_order_field = "timestamp"

    def user_display(self, obj):
        if not obj.user:
            return format_html('<span style="color:#94a3b8;">(Anonymous)</span>')
        full_name = obj.user.get_full_name()
        if full_name:
            return f"{obj.user.username} ({full_name})"
        return obj.user.username
    user_display.short_description = "User"
    user_display.admin_order_field = "user__username"

    def bank_badge(self, obj):
        return format_html(
            '<span style="font-weight:600; padding:2px 8px; border-radius:4px; background:#f1f5f9; color:#334155;">{}</span>',
            obj.bank_selected
        )
    bank_badge.short_description = "Bank"
    bank_badge.admin_order_field = "bank_selected"

    def file_size_display(self, obj):
        if obj.file_size_kb > 0:
            return f"{obj.file_size_kb:.1f} KB"
        return "-"
    file_size_display.short_description = "File Size"
    file_size_display.admin_order_field = "file_size_kb"

    def duration_display(self, obj):
        if obj.duration_seconds > 0:
            return f"{obj.duration_seconds:.2f}s"
        return "-"
    duration_display.short_description = "Duration"
    duration_display.admin_order_field = "duration_seconds"

    def reconciliation_badge(self, obj):
        if not obj.reconciliation_status:
            return "-"
        if "Balanced" in obj.reconciliation_status:
            return format_html(
                '<span style="background:rgba(16,185,129,0.15); color:#059669; font-weight:600; padding:2px 8px; border-radius:12px; font-size:0.75rem;">✓ {}</span>',
                obj.reconciliation_status
            )
        elif "Discrepanc" in obj.reconciliation_status:
            return format_html(
                '<span style="background:rgba(239,68,68,0.15); color:#dc2626; font-weight:600; padding:2px 8px; border-radius:12px; font-size:0.75rem;">⚠️ {}</span>',
                obj.reconciliation_status
            )
        return obj.reconciliation_status
    reconciliation_badge.short_description = "Ledger Audit"

    def status_badge(self, obj):
        if obj.is_successful:
            return format_html(
                '<span style="background:#10b981; color:#fff; font-weight:700; padding:3px 8px; border-radius:6px; font-size:0.7rem; letter-spacing:0.5px;">SUCCESS</span>'
            )
        return format_html(
            '<span style="background:#ef4444; color:#fff; font-weight:700; padding:3px 8px; border-radius:6px; font-size:0.7rem; letter-spacing:0.5px;">FAILED</span>'
        )
    status_badge.short_description = "Status"
    status_badge.admin_order_field = "is_successful"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
