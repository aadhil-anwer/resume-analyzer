from django.urls import path, include
from core.views import base, auth, api, jd

urlpatterns = [
    # Pages
    path("", base.home_page, name="home"),
    path("dashboard/", base.dashboard, name="dashboard"),

    # ✅ ADD THIS
    path("dashboard/partial/<str:tool>/", base.load_tool_partial, name="tool_partial"),

    # Auth
    path("signup/", auth.signup_view, name="signup"),
    path("login/", auth.login_view, name="login"),
    path("logout/", auth.logout_view, name="logout"),

    # Resume API
    path("api/resume/analyze/", api.api_resume_analyze, name="api_resume_analyze"),
    path("api/resume/status/<int:resume_id>/", api.api_resume_status, name="api_resume_status"),

    

    # LaTeX API
    path("api/latex/generate/", api.api_latex_generate, name="api_latex_generate"),
    path("api/latex/status/<int:latex_resume_id>/", api.api_latex_status, name="api_latex_status"),

    # Background Worker UI
    path("django-rq/", include("django_rq.urls")),
    path("api/jd/match/", jd.jd_match_api, name="jd_match_api"),
    path("api/jd/status/<int:jd_id>/", jd.jd_match_status, name="jd_match_status"),

]
