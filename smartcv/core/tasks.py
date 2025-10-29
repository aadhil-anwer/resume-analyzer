import json
from django.utils.safestring import mark_safe
from .models import ResumeUpload


from core.utils.extract_text import extract_text_from_pdf, extract_text_from_docx
from core.utils.normalize import normalize_text
from core.utils.local_checks import run_local_checks
from core.utils.general_cv_analysis import gemini_resume_analysis

def process_resume_upload(resume_id):
    """Background job: process uploaded resume and update database."""
    try:
        instance = ResumeUpload.objects.get(id=resume_id)
        file_path = instance.file.path

        # Extract & normalize text
        if file_path.lower().endswith(".pdf"):
            text = extract_text_from_pdf(file_path)
        elif file_path.lower().endswith(".docx"):
            text = extract_text_from_docx(file_path)
        else:
            instance.result_json = {
                "status": "FAILED",
                "message": "Unsupported file type",
            }
            instance.save()
            return

        text = normalize_text(text)

        # 1️⃣ Run local pre-checks
        local_check = run_local_checks(text)

        if local_check["failed"]:
            result = {
                "status": "FAILED_PRECHECK",
                "local_check": local_check,
                "message": "Fix the flagged issues below before ATS scoring.",
            }
            instance.result_json = result
            instance.save()
            return

        # 2️⃣ AI resume analysis
        ai_result = gemini_resume_analysis(text)

        # 3️⃣ Combine results
        result = {
            "status": "SUCCESS",
            "local_check": local_check,
            "ai_analysis": ai_result,
        }

        instance.result_json = result
        instance.save()

    except Exception as e:
        instance.result_json = {
            "status": "ERROR",
            "message": str(e),
        }
        instance.save()



# core/tasks.py  — add this below your existing tasks

import tempfile
import base64
import subprocess
import os
from core.utils.extract_text import extract_text_from_pdf, extract_text_from_docx
from core.utils.normalize import normalize_text
from core.utils.latex_resume_generator import generate_latex_resume
from core.models import ResumeUpload

from core.models import ResumeUpload
from core.utils.extract_text import extract_text_from_pdf, extract_text_from_docx
from core.utils.normalize import normalize_text
from core.utils.latex_resume_generator import generate_latex_resume
from core.utils.latex_tools import compile_tex_to_pdf
  # reuse your helper
import base64
import tempfile

def generate_latex_task(resume_id, ai_suggestions):
    """
    Runs inside RQ worker to generate and compile LaTeX PDF.
    """
    try:
        instance = ResumeUpload.objects.get(id=resume_id)
        file_path = instance.file.path

        # Extract resume text
        if file_path.lower().endswith(".pdf"):
            resume_text = extract_text_from_pdf(file_path)
        elif file_path.lower().endswith(".docx"):
            resume_text = extract_text_from_docx(file_path)
        else:
            instance.result_json = {"status": "FAILED", "error": "Unsupported file type"}
            instance.save()
            return

        resume_text = normalize_text(resume_text)

        # Generate LaTeX and compile to PDF
        latex_output = generate_latex_resume(resume_text, ai_suggestions)
        pdf_bytes = compile_tex_to_pdf(latex_output)
        pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
        pdf_data_uri = f"data:application/pdf;base64,{pdf_base64}"

        # Save inside result_json
        result = instance.result_json or {}
        result["latex_result"] = {
            "status": "SUCCESS",
            "pdf_data_uri": pdf_data_uri
        }
        instance.result_json = result
        instance.save()

    except Exception as e:
        instance = ResumeUpload.objects.filter(id=resume_id).first()
        if instance:
            result = instance.result_json or {}
            result["latex_result"] = {"status": "FAILED", "error": str(e)}
            instance.result_json = result
            instance.save()
