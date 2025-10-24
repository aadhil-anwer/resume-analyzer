from django.urls import path
from . import views

urlpatterns = [
    path("", views.upload_page, name="upload_page"),
    path("upload/", views.upload_resume, name="upload_resume"),
    path("jd-upload/", views.jd_upload_page, name="jd_upload_page"),  # for GET form view
    path("jd-upload/submit/", views.upload_resume_with_jd, name="upload_resume_with_jd"),  # POST submission
    path("generate_latex/", views.generate_latex_view, name="generate_latex"),
]
