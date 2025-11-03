# core/models.py

from django.db import models
from django.conf import settings
from datetime import datetime
from core.storage_backends import PrivateMediaStorage


def private_resume_path(instance, filename):
    """
    Store resume files under:
    private_media/resumes/<username>/<filename>
    """
    username = instance.user.username if instance.user else "anonymous"
    return f"resumes/{username}/{filename}"


class ResumeUpload(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="resumes",
        null=True,
        blank=True,
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # ✅ Resume files stored privately (NOT accessible via /media/)
    file = models.FileField(storage=PrivateMediaStorage(), upload_to=private_resume_path)

    def __str__(self):
        return f"{self.user.username if self.user else 'Anonymous'} • {self.file.name}"


class ResumeAnalysis(models.Model):
    """
    Stores AI resume analysis output tied to an uploaded resume.
    Can be cleaned later (30-day retention policy).
    """
    resume = models.OneToOneField(
        ResumeUpload,
        on_delete=models.CASCADE,
        related_name="analysis"
    )
    data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return (datetime.now() - self.created_at).days > 30

    def __str__(self):
        return f"Analysis → {self.resume}"


class LatexResume(models.Model):
    """
    Stores LaTeX generated resume versions.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    resume_upload = models.ForeignKey(ResumeUpload, on_delete=models.CASCADE)
    ai_suggestions = models.JSONField(null=True, blank=True)

    latex_code = models.TextField(blank=True)

    # ✅ Store generated PDF privately as well
    pdf_file = models.FileField(
        storage=PrivateMediaStorage(),
        upload_to="latex_resumes/",
        null=True,
        blank=True
    )

    result_json = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"LaTeX Resume → {self.resume_upload}"
class JDMatch(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    resume = models.ForeignKey(ResumeUpload, on_delete=models.CASCADE)  # KEEP mandatory
    jd_text = models.TextField()
    result_json = models.JSONField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        default="PROCESSING"  # PROCESSING | SUCCESS | FAILED
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"JD Match → {self.user.username} [{self.status}]"
