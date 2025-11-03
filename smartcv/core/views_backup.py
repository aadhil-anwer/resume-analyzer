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
from .models import ResumeUpload, LatexResume
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
def upload_resume(request):
    """
    Handles standard resume upload and performs AI analysis (without job description).
    Saves the result in ResumeUpload.result_json.
    """
    print("📥 upload_resume() triggered by user:", request.user)
    print("FILES:", request.FILES)

    file = request.FILES.get("resume")
    if not file:
        return render(request, "core/upload.html", {"error": "Please select a file to upload."})

    # Create DB entry for the uploaded resume
    instance = ResumeUpload.objects.create(file=file, user=request.user)
    file_path = instance.file.path

    # Extract text based on file type
    if file_path.lower().endswith(".pdf"):
        resume_text = extract_text_from_pdf(file_path)
    elif file_path.lower().endswith(".docx"):
        resume_text = extract_text_from_docx(file_path)
    else:
        return render(request, "core/upload.html", {"error": "Unsupported file type."})

    # Normalize and run local checks
    resume_text = normalize_text(resume_text)
    local_check = run_local_checks(resume_text)

    # Queue background AI analysis (via RQ)
    queue = django_rq.get_queue("default")
    job = queue.enqueue(process_resume_upload, instance.id)

    # Return initial response so frontend can start polling
    result = {
        "status": "PROCESSING",
        "message": "Resume uploaded successfully, starting AI analysis...",
        "resume_id": instance.id,
        "job_id": job.id,
    }

    return render(request, "core/upload.html", {
        "result": json.dumps(result, ensure_ascii=False)
    })
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











# -------------------------------------------------------------------
# LATEX GENERATION
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# LATEX GENERATION (Django View)
# -------------------------------------------------------------------

@login_required(login_url="/login/")
@require_POST
def generate_latex_view(request):
    """Handles LaTeX resume generation with separate tracking"""
    try:
        print("🔍 DEBUG generate_latex_view: Started")
        result_json = request.POST.get("resume_text")
        print(f"🔍 DEBUG: Received resume_text - {result_json}")
        
        if not result_json:
            print("❌ DEBUG: No resume_text received")
            return JsonResponse({"error": "No resume data received."}, status=400)

        result_data = json.loads(result_json)
        ai_suggestions = result_data.get("ai_analysis", {})
        print(f"🔍 DEBUG: AI suggestions keys - {ai_suggestions.keys()}")

        # Get the last resume upload for this user
        resume_upload = ResumeUpload.objects.filter(user=request.user).last()
        if not resume_upload or not resume_upload.file:
            print("❌ DEBUG: No uploaded resume found")
            return JsonResponse({"error": "No uploaded resume found."}, status=404)

        print(f"🔍 DEBUG: Found resume upload - {resume_upload.id}")

        # ✅ Create LatexResume record first
        latex_resume = LatexResume.objects.create(
            user=request.user,
            resume_upload=resume_upload,
            ai_suggestions=ai_suggestions,
            result_json={"status": "PROCESSING"}
        )

        print(f"🔍 DEBUG: Created LatexResume - {latex_resume.id}")

        # Queue background job with BOTH IDs
        queue = django_rq.get_queue("default")
        job = queue.enqueue("core.tasks.generate_latex_task", resume_upload.id, ai_suggestions)

        response_data = {
            "status": "PROCESSING_LATEX",
            "message": "Generating LaTeX resume...",
            "resume_id": resume_upload.id,
            "latex_resume_id": latex_resume.id,
            "job_id": job.id,
        }
        
        print(f"🔍 DEBUG: Returning response - {response_data}")
        
        return JsonResponse(response_data)

    except Exception as e:
        print(f"❌ DEBUG: Error in generate_latex_view: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": f"Error starting LaTeX generation: {str(e)}"}, status=500)
# ✅ NEW: Separate status check for LaTeX
def check_latex_status(request, latex_resume_id):
    """AJAX endpoint to check LaTeX generation status"""
    try:
        print(f"🔍 check_latex_status called for ID: {latex_resume_id}")
        instance = LatexResume.objects.get(id=latex_resume_id)
        
        response_data = instance.result_json or {"status": "PROCESSING"}
        print(f"🔍 Returning status: {response_data.get('status')}")
        print(f"🔍 Full response data: {response_data}")
        
        # Check if PDF file exists
        if instance.pdf_file:
            print(f"🔍 PDF file exists: {instance.pdf_file.name}, Size: {instance.pdf_file.size} bytes")
        else:
            print("🔍 No PDF file found")
            
        return JsonResponse(response_data, safe=False)
        
    except LatexResume.DoesNotExist:
        print(f"❌ LatexResume {latex_resume_id} not found")
        return JsonResponse({"error": "LaTeX resume not found."}, status=404)
    except Exception as e:
        print(f"❌ Error in check_latex_status: {e}")
        return JsonResponse({"error": str(e)}, status=500)
# -------------------------------------------------------------------
# STATUS CHECK
# -------------------------------------------------------------------

def check_resume_status(request, resume_id):
    """AJAX endpoint to fetch latest resume analysis result INCLUDING LaTeX status."""
    try:
        instance = ResumeUpload.objects.get(id=resume_id)
        result = instance.result_json or {"status": "PROCESSING"}
        
        # ✅ Ensure we return the complete result including latex_result
        return JsonResponse(result, safe=False)
        
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
