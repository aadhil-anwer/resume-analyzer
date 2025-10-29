from django.db import models
from django.conf import settings
import os

def private_resume_path(instance, filename):
    """
    Store resumes under /PRIVATE_MEDIA_ROOT/<username>/<filename>
    for isolation per user.
    """
    if instance.user:
        return f"{instance.user.username}/{filename}"
    return filename

class ResumeUpload(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="resumes",
        null=True,
        blank=True,
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to=private_resume_path)
    result_json = models.JSONField(null=True, blank=True)

    def save(self, *args, **kwargs):
        """
        Override save() so files go to PRIVATE_MEDIA_ROOT instead of MEDIA_ROOT.
        """
        # Ensure this works even if PRIVATE_MEDIA_ROOT is missing
        private_root = getattr(settings, "PRIVATE_MEDIA_ROOT", settings.MEDIA_ROOT)
        self.file.storage.location = private_root
        super().save(*args, **kwargs)

    def __str__(self):
        username = self.user.username if self.user else "Anonymous"
        return f"{username} - {os.path.basename(self.file.name)}"
