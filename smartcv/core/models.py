from django.db import models
from django.conf import settings
import os

def private_resume_path(instance, filename):
    # Custom path — just returns filename, not full path
    return filename

class ResumeUpload(models.Model):
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to=private_resume_path)
    result_json = models.JSONField(null=True, blank=True)

    def save(self, *args, **kwargs):
        """
        Override save() so the file actually goes to PRIVATE_MEDIA_ROOT
        instead of MEDIA_ROOT.
        """
        self.file.storage.location = getattr(settings, "PRIVATE_MEDIA_ROOT", settings.MEDIA_ROOT)
        super().save(*args, **kwargs)

    def __str__(self):
        return os.path.basename(self.file.name)
