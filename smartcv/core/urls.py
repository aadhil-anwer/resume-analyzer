from django.urls import path, include
from . import views

urlpatterns = [
   path("", views.home_page, name="home"),  # New landing page
    path("upload/", views.upload_page, name="upload_resume"),  # Existing resume upload
    path("jd-upload/", views.jd_upload_page, name="jd_upload_page"),  # for GET form view
    path("jd-upload/submit/", views.upload_resume_with_jd, name="upload_resume_with_jd"),  # POST submission
    path("generate_latex/", views.generate_latex_view, name="generate_latex"),
    path("django-rq/", include("django_rq.urls")),
    path("check-status/<int:resume_id>/", views.check_resume_status, name="check_status"),

    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("django-rq/", include("django_rq.urls")),
]
