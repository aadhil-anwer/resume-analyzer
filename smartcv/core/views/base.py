# core/views/base.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def home_page(request):
    return render(request, "core/home.html")

def upload_page(request):
    return render(request, "core/upload.html")

def jd_upload_page(request):
    return render(request, "core/jd_upload.html")

@login_required(login_url="/login/")
def dashboard(request):
    return render(request, "core/dashboard.html")

@login_required(login_url="/login/")
def load_tool_partial(request, tool):
    return render(request, f"core/partials/{tool}_form.html")