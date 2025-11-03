# core/tasks.py

from core.models import ResumeUpload, ResumeAnalysis, LatexResume, JDMatch
from core.utils.extract_text import extract_text_from_pdf, extract_text_from_docx
from core.utils.normalize import normalize_text
from core.utils.local_checks import run_local_checks
from core.utils.general_cv_analysis import gemini_resume_analysis
from core.utils.latex_resume_generator import generate_latex_resume
from core.utils.latex_tools import compile_tex_to_pdf
from core.utils.jd_resume_analysis import match_resume_to_jd
from django.core.files.base import ContentFile
import base64
import traceback


def process_resume_upload(resume_id):
    """
    Background job: extract, analyze, and store resume analysis.
    """
    try:
        instance = ResumeUpload.objects.get(id=resume_id)
        file_path = instance.file.path

        # ---- Extract Text ----
        if file_path.lower().endswith(".pdf"):
            text = extract_text_from_pdf(file_path)
        elif file_path.lower().endswith(".docx"):
            text = extract_text_from_docx(file_path)
        else:
            ResumeAnalysis.objects.update_or_create(
                resume=instance,
                defaults={
                    "data": {
                        "status": "FAILED",
                        "error": "Unsupported file type"
                    }
                }
            )
            return

        text = normalize_text(text)

        # ---- Local Pre-checks ----
        local_check = run_local_checks(text)
        if local_check.get("failed", False):
            ResumeAnalysis.objects.update_or_create(
                resume=instance,
                defaults={
                    "data": {
                        "status": "FAILED_PRECHECK",
                        "local_check": local_check,
                    }
                }
            )
            return

        # ---- AI Analysis ----
        ai_result = gemini_resume_analysis(text)

        ResumeAnalysis.objects.update_or_create(
            resume=instance,
            defaults={
                "data": {
                    "status": "SUCCESS",
                    "local_check": local_check,
                    "ai_analysis": ai_result,
                }
            }
        )

    except Exception as e:
        ResumeAnalysis.objects.update_or_create(
            resume=instance,
            defaults={
                "data": {
                    "status": "FAILED",
                    "error": str(e),
                }
            }
        )



# -----------------------------------------------------------
# L A T E X   G E N E R A T I O N   T A S K
# -----------------------------------------------------------

def generate_latex_task(latex_resume_id):
    """
    Generate LaTeX & PDF for an existing LatexResume object.
    """
    try:
        latex_resume = LatexResume.objects.get(id=latex_resume_id)
        resume_upload = latex_resume.resume_upload
        ai_suggestions = latex_resume.ai_suggestions or {}

        file_path = resume_upload.file.path

        # Extract resume text
        if file_path.lower().endswith(".pdf"):
            resume_text = extract_text_from_pdf(file_path)
        elif file_path.lower().endswith(".docx"):
            resume_text = extract_text_from_docx(file_path)
        else:
            latex_resume.result_json = {"status": "FAILED", "error": "Unsupported file type"}
            latex_resume.save()
            return

        resume_text = normalize_text(resume_text)

        # Generate LaTeX
        latex_code = generate_latex_resume(resume_text, ai_suggestions)
        latex_resume.latex_code = latex_code

        # Compile to PDF
        pdf_bytes = compile_tex_to_pdf(latex_code)
        pdf_name = f"resume_{latex_resume_id}.pdf"
        latex_resume.pdf_file.save(pdf_name, ContentFile(pdf_bytes))

        # Base64 encode for browser preview
        pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
        latex_resume.result_json = {
            "status": "SUCCESS",
            "pdf_data_uri": f"data:application/pdf;base64,{pdf_base64}"
        }
        latex_resume.save()

    except Exception as e:
        latex_resume.result_json = {"status": "FAILED", "error": str(e)}
        latex_resume.save()






def process_jd_match(jd_id):
    jd_instance = JDMatch.objects.get(id=jd_id)

    try:
        resume_upload = jd_instance.resume
        file_path = resume_upload.file.path

        # Extract text directly (NO dependency on ResumeAnalysis)
        if file_path.lower().endswith(".pdf"):
            resume_text = extract_text_from_pdf(file_path)
        elif file_path.lower().endswith(".docx"):
            resume_text = extract_text_from_docx(file_path)
        else:
            raise ValueError("Unsupported resume format")

        resume_text = normalize_text(resume_text)
        jd_text = normalize_text(jd_instance.jd_text)

        # Run matching using GPT-5
        result = match_resume_to_jd(resume_text, jd_text)

        jd_instance.result_json = {
            "status": "SUCCESS",
            "match": result
        }
        jd_instance.status = "SUCCESS"
        jd_instance.save()

    except Exception as e:
        jd_instance.result_json = {
            "status": "FAILED",
            "error": str(e),
            "trace": traceback.format_exc()
        }
        jd_instance.status = "FAILED"
        jd_instance.save()
