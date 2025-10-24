import os
import json
import re

from django.shortcuts import render
from django.views.decorators.http import require_POST
from .models import ResumeUpload


from django.views.decorators.csrf import csrf_protect
from django.utils.html import escape
from django.core.exceptions import SuspiciousOperation, ValidationError
from django.conf import settings


from core.utils.extract_text import extract_text_from_docx, extract_text_from_pdf 
from core.utils.normalize import normalize_text
from core.utils.local_checks import run_local_checks
from core.utils.general_cv_analysis import gemini_resume_analysis
from core.utils.jd_resume_analysis import gemini_resume_jd_match_analysis
from core.utils.latex_resume_generator import generate_latex_resume

import unicodedata
import io

import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime

today = datetime.now().strftime("%B %d, %Y")
load_dotenv()

# ------------------ ROUTES ------------------
def upload_page(request):
    return render(request, "core/upload.html")


def jd_upload_page(request):
    return render(request, "core/jd_upload.html")


@require_POST
def upload_resume(request):
    file = request.FILES.get("resume")
    if not file:
        return render(request, "core/upload.html", {"error": "No file uploaded"})

    # Save upload
    instance = ResumeUpload.objects.create(file=file)
    file_path = instance.file.path

    # Extract & normalize text
    if file_path.lower().endswith(".pdf"):
        text = extract_text_from_pdf(file_path)
    elif file_path.lower().endswith(".docx"):
        text = extract_text_from_docx(file_path)
    else:
        return render(request, "core/upload.html", {"error": "Unsupported file type"})

    text = normalize_text(text)

    # 1️⃣ Run local pre-checks
    local_check = run_local_checks(text)

    if local_check["failed"]:
        # if fails, return immediately without AI call
        result = {
            "status": "FAILED_PRECHECK",
            "local_check": local_check,
            "message": "Fix the flagged issues below before ATS scoring."
        }
        instance.result_json = result
        instance.save()
        return render(request, "core/upload.html", {"result": json.dumps(result, indent=2)})

    # 2️⃣ Send to Gemini for ATS & quality scoring
    ai_result = gemini_resume_analysis(text)

    # 3️⃣ Combine results
    result = {
        "status": "SUCCESS",
        "local_check": local_check,
        "ai_analysis": ai_result
    }

    instance.result_json = result
    instance.save()

    return render(request, "core/upload.html", {"result": json.dumps(result, ensure_ascii=False, indent=2)})










@require_POST
def upload_resume_with_jd(request):
    file = request.FILES.get("resume")
    jd_text = request.POST.get("jd", "").strip()

    if not file or not jd_text:
        return render(request, "core/jd_upload.html", {"error": "Upload resume and paste job description."})

    instance = ResumeUpload.objects.create(file=file)
    file_path = instance.file.path

    # Extract resume text
    if file_path.lower().endswith(".pdf"):
        resume_text = extract_text_from_pdf(file_path)
    elif file_path.lower().endswith(".docx"):
        resume_text = extract_text_from_docx(file_path)
    else:
        return render(request, "core/jd_upload.html", {"error": "Unsupported file type"})

    resume_text = normalize_text(resume_text)
    jd_text = normalize_text(jd_text)

    # Local pre-check (optional)
    local_check = run_local_checks(resume_text)

    # AI scoring (resume + JD)
    ai_result = gemini_resume_jd_match_analysis(resume_text, jd_text)

    result = {
        "status": "SUCCESS",
        "local_check": local_check,
        "ai_analysis": ai_result
    }

    instance.result_json = result
    instance.save()

    return render(request, "core/jd_upload.html", {"result": json.dumps(result, ensure_ascii=False, indent=2)})


@require_POST
def generate_latex_view(request):
    """
    Takes AI review result and resume text, then generates LaTeX using GPT-5-mini.
    (View-only — does NOT save to DB)
    """
    try:
        result_json = request.POST.get("resume_text")
        if not result_json:
            return render(request, "core/upload.html", {"error": "No resume data received."})

        # Parse JSON safely
        result_data = json.loads(result_json)
        ai_suggestions = result_data.get("ai_analysis", {})

        # ✅ Load the latest uploaded resume (without saving anything)
        instance = ResumeUpload.objects.last()
        if not instance or not instance.file:
            return render(request, "core/upload.html", {"error": "No uploaded resume file found."})

        file_path = instance.file.path

        # ✅ Re-extract resume text
        if file_path.lower().endswith(".pdf"):
            resume_text = extract_text_from_pdf(file_path)
        elif file_path.lower().endswith(".docx"):
            resume_text = extract_text_from_docx(file_path)
        else:
            return render(request, "core/upload.html", {"error": "Unsupported file type."})

        resume_text = normalize_text(resume_text)

        # ✅ Generate the LaTeX using GPT-5-mini
        latex_output = generate_latex_resume(resume_text, ai_suggestions)

        # ✅ Just render the LaTeX on screen — no save
        return render(
            request,
            "core/upload.html",
            {
                "result": json.dumps(result_data, indent=2, ensure_ascii=False),
                "latex": latex_output,
            },
        )

    except Exception as e:
        return render(request, "core/upload.html", {"error": f"Error generating LaTeX: {str(e)}"})
