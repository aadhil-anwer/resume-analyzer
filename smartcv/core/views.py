import os
import json
import re
import django_rq
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
from dotenv import load_dotenv
from datetime import datetime

# Models & Tasks
from .models import ResumeUpload
from core.tasks import process_resume_upload, generate_latex_task

# Utils
from core.utils.extract_text import extract_text_from_docx, extract_text_from_pdf
from core.utils.normalize import normalize_text
from core.utils.local_checks import run_local_checks
from core.utils.general_cv_analysis import gemini_resume_analysis
from core.utils.jd_resume_analysis import gemini_resume_jd_match_analysis

load_dotenv()
today = datetime.now().strftime("%B %d, %Y")
User = get_user_model()

# -------------------------------------------------------------------
# PAGES
# -------------------------------------------------------------------

def home_page(request):
    """Simple landing/homepage."""
    return render(request, "core/home.html")

def upload_page(request):
    """Render resume upload page."""
    return render(request, "core/upload.html")

def jd_upload_page(request):
    """Render job description upload page."""
    return render(request, "core/jd_upload.html")

# -------------------------------------------------------------------
# RESUME ANALYSIS
# -------------------------------------------------------------------

@require_POST
@login_required(login_url="/login/")
def upload_resume_with_jd(request):
    """
    Handles resume + job description upload and performs JD-based AI analysis.
    Saves the result in ResumeUpload.result_json.
    """
    file = request.FILES.get("resume")
    jd_text = request.POST.get("jd", "").strip()

    if not file or not jd_text:
        return render(request, "core/jd_upload.html", {
            "error": "Please upload a resume and paste the job description."
        })

    # ✅ Attach resume to logged-in user
    instance = ResumeUpload.objects.create(file=file, user=request.user)
    file_path = instance.file.path

    # ✅ Extract resume text safely
    if file_path.lower().endswith(".pdf"):
        resume_text = extract_text_from_pdf(file_path)
    elif file_path.lower().endswith(".docx"):
        resume_text = extract_text_from_docx(file_path)
    else:
        return render(request, "core/jd_upload.html", {"error": "Unsupported file type."})

    # ✅ Normalize both texts
    resume_text = normalize_text(resume_text)
    jd_text = normalize_text(jd_text)

    # ✅ Local static checks
    local_check = run_local_checks(resume_text)

    # ✅ AI analysis (resume vs JD)
    ai_result = gemini_resume_jd_match_analysis(resume_text, jd_text)

    # ✅ Save full result JSON
    result = {
        "status": "SUCCESS",
        "local_check": local_check,
        "ai_analysis": ai_result,
    }
    instance.result_json = result
    instance.save()

    return render(request, "core/jd_upload.html", {
        "result": json.dumps(result, ensure_ascii=False, indent=2)
    })

@require_POST
def upload_resume(request):
    """Handle resume upload and queue AI analysis."""
    file = request.FILES.get("resume")
    if not file:
        return render(request, "core/upload.html", {"error": "No file uploaded."})

    # ✅ Attach user if logged in
    user = request.user if request.user.is_authenticated else None
    instance = ResumeUpload.objects.create(file=file, user=user)

    # ✅ Enqueue async processing
    queue = django_rq.get_queue("default")
    queue.enqueue(process_resume_upload, instance.id)

    result = {
        "status": "PROCESSING",
        "message": "Your resume is being analyzed. Please wait a moment.",
        "resume_id": instance.id,
    }
    return render(request, "core/upload.html", {"result": json.dumps(result, ensure_ascii=False)})



@login_required(login_url="/login/")
@require_POST
def generate_latex_view(request):
    """
    Enqueue LaTeX generation task for the latest resume of the logged-in user.
    """
    try:
        result_json = request.POST.get("resume_text")
        if not result_json:
            return render(request, "core/upload.html", {"error": "No resume data received."})

        # ✅ Safely parse JSON
        result_data = json.loads(result_json)
        ai_suggestions = result_data.get("ai_analysis", {})

        # ✅ Fetch latest resume *for this user only*
        instance = ResumeUpload.objects.filter(user=request.user).order_by("-uploaded_at").first()
        if not instance or not instance.file:
            return render(request, "core/upload.html", {"error": "No uploaded resume found."})

        # ✅ Queue LaTeX generation task
        queue = django_rq.get_queue("default")
        job = queue.enqueue(generate_latex_task, instance.id, ai_suggestions)

        # ✅ Return processing status for frontend polling
        result = {
            "status": "PROCESSING_LATEX",
            "message": "Generating LaTeX resume...",
            "resume_id": instance.id,
            "job_id": job.id,
        }
        return render(request, "core/upload.html", {"result": json.dumps(result, ensure_ascii=False)})

    except Exception as e:
        return render(request, "core/upload.html", {"error": f"Error starting LaTeX generation: {str(e)}"})
    

@require_POST
def upload_resume(request):
    """Handle resume upload and queue AI analysis."""
    file = request.FILES.get("resume")
    if not file:
        return render(request, "core/upload.html", {"error": "No file uploaded."})

    # ✅ Attach user if logged in
    user = request.user if request.user.is_authenticated else None
    instance = ResumeUpload.objects.create(file=file, user=user)

    # ✅ Enqueue async processing
    queue = django_rq.get_queue("default")
    queue.enqueue(process_resume_upload, instance.id)

    result = {
        "status": "PROCESSING",
        "message": "Your resume is being analyzed. Please wait a moment.",
        "resume_id": instance.id,
    }
    return render(request, "core/upload.html", {"result": json.dumps(result, ensure_ascii=False)})



@login_required(login_url="/login/")
@require_POST
def generate_latex_view(request):
    """
    Enqueue LaTeX generation task for the latest resume of the logged-in user.
    """
    try:
        result_json = request.POST.get("resume_text")
        if not result_json:
            return render(request, "core/upload.html", {"error": "No resume data received."})

        # ✅ Safely parse JSON
        result_data = json.loads(result_json)
        ai_suggestions = result_data.get("ai_analysis", {})

        # ✅ Fetch latest resume *for this user only*
        instance = ResumeUpload.objects.filter(user=request.user).order_by("-uploaded_at").first()
        if not instance or not instance.file:
            return render(request, "core/upload.html", {"error": "No uploaded resume found."})

        # ✅ Queue LaTeX generation task
        queue = django_rq.get_queue("default")
        job = queue.enqueue(generate_latex_task, instance.id, ai_suggestions)

        # ✅ Return processing status for frontend polling
        result = {
            "status": "PROCESSING_LATEX",
            "message": "Generating LaTeX resume...",
            "resume_id": instance.id,
            "job_id": job.id,
        }
        return render(request, "core/upload.html", {"result": json.dumps(result, ensure_ascii=False)})

    except Exception as e:
        return render(request, "core/upload.html", {"error": f"Error starting LaTeX generation: {str(e)}"})

# -------------------------------------------------------------------
# LATEX GENERATION
# -------------------------------------------------------------------

@login_required(login_url="/login/")
@require_POST
def generate_latex_view(request):
    """Queue LaTeX generation for latest user resume."""
    try:
        result_json = request.POST.get("resume_text")
        if not result_json:
            return render(request, "core/upload.html", {"error": "No resume data received."})

        result_data = json.loads(result_json)
        ai_suggestions = result_data.get("ai_analysis", {})

        instance = ResumeUpload.objects.filter(user=request.user).last()
        if not instance or not instance.file:
            return render(request, "core/upload.html", {"error": "No uploaded resume found."})

        queue = django_rq.get_queue("default")
        job = queue.enqueue(generate_latex_task, instance.id, ai_suggestions)

        return render(request, "core/upload.html", {
            "result": json.dumps({
                "status": "PROCESSING_LATEX",
                "message": "Generating LaTeX resume...",
                "resume_id": instance.id,
                "job_id": job.id,
            }, ensure_ascii=False)
        })

    except Exception as e:
        return render(request, "core/upload.html", {"error": f"Error starting LaTeX generation: {str(e)}"})

# -------------------------------------------------------------------
# STATUS CHECK
# -------------------------------------------------------------------

def check_resume_status(request, resume_id):
    """AJAX endpoint to fetch latest resume analysis result."""
    try:
        instance = ResumeUpload.objects.get(id=resume_id)
        return JsonResponse(instance.result_json or {"status": "PROCESSING"}, safe=False)
    except ResumeUpload.DoesNotExist:
        return JsonResponse({"error": "Resume not found."}, status=404)

# -------------------------------------------------------------------
# AUTH
# -------------------------------------------------------------------

def signup_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        password2 = request.POST.get("password2", "").strip()

        if not username or not password:
            return render(request, "auth/signup.html", {"error": "Username and password are required."})
        if password != password2:
            return render(request, "auth/signup.html", {"error": "Passwords do not match."})
        if User.objects.filter(username=username).exists():
            return render(request, "auth/signup.html", {"error": "Username already taken."})

        user = User.objects.create_user(username=username, password=password)
        login(request, user)
        return redirect("home")

    return render(request, "auth/signup.html")

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(request.GET.get("next") or "home")
        else:
            return render(request, "auth/login.html", {"error": "Invalid username or password."})
    return render(request, "auth/login.html")

@login_required(login_url="/login/")
def logout_view(request):
    """Logout user and show confirmation page."""
    logout(request)
    return render(request, "auth/logout_success.html")
