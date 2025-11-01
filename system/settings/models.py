from django.db import models

class SystemSetting(models.Model):
    """
    A key-value store for simple, site-wide settings.
    e.g., ('site_name', 'WBPMIS UESO'), ('maintenance_mode', 'False')
    """
    key = models.CharField(max_length=100, primary_key=True, unique=True, help_text="The unique identifier for the setting (e.g., 'site_name')")
    value = models.TextField(blank=True, help_text="The value of the setting.")
    description = models.CharField(max_length=255, blank=True, null=True, help_text="A brief description of what this setting does.")

    def __str__(self):
        return self.key

    class Meta:
        verbose_name = "System Setting"
        verbose_name_plural = "System Settings"
        ordering = ['key']