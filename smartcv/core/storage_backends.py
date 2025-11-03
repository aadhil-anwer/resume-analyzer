# core/storage_backend.py
from django.core.files.storage import FileSystemStorage
from django.conf import settings

class PrivateMediaStorage(FileSystemStorage):
    """
    Files stored here are NOT publicly accessible.
    Access is only allowed through backend-controlled endpoints.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(location=settings.PRIVATE_MEDIA_ROOT, base_url=None)
