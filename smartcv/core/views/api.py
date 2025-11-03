# core/views/api.py

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from core.tasks import process_jd_match
import json
import django_rq

from core.models import (
    ResumeUpload,
    ResumeAnalysis,
    LatexResume,
    JDMatch
)

from core.tasks import (
    process_resume_upload,
    generate_latex_task
)


# -------------------------------------------------------
# RESUME ANALYSIS
# -------------------------------------------------------
@login_required(login_url="/login/")
@require_POST
def api_resume_analyze(request):
    """
    Upload resume → Queue background analysis → Return job id + resume id
    """
    file = request.FILES.get("resume")
    if not file:
        return JsonResponse({"error": "Resume file is required."}, status=400)

    # Save the resume
    instance = ResumeUpload.objects.create(user=request.user, file=file)

    # Queue async processing
    queue = django_rq.get_queue("default")
    job = queue.enqueue(process_resume_upload, instance.id)

    return JsonResponse({
        "status": "PROCESSING",
        "resume_id": instance.id,
        "job_id": job.id
    })


@login_required(login_url="/login/")
def api_resume_status(request, resume_id):
    """
    Polling endpoint → Returns real-time analysis result
    """
    try:
        resume = ResumeUpload.objects.get(id=resume_id, user=request.user)
    except ResumeUpload.DoesNotExist:
        return JsonResponse({"error": "Resume not found."}, status=404)

    analysis = ResumeAnalysis.objects.filter(resume=resume).first()

    if not analysis:
        return JsonResponse({"status": "PROCESSING"})

    return JsonResponse(analysis.data)  # full analysis JSON


# -------------------------------------------------------
# LATEX RESUME GENERATOR
# -------------------------------------------------------
# -------------------------------------------------------
# LATEX RESUME GENERATOR
# -------------------------------------------------------
@login_required(login_url="/login/")
@require_POST
def api_latex_generate(request):
    """
    Convert the user's most recently analyzed resume → Generate LaTeX → Compile to PDF.
    """
    try:
        resume_upload = ResumeUpload.objects.filter(user=request.user).last()
        if not resume_upload:
            return JsonResponse({"error": "No resume found to convert."}, status=404)

        analysis = ResumeAnalysis.objects.filter(resume=resume_upload).first()
        if not analysis or analysis.data.get("status") != "SUCCESS":
            return JsonResponse({"error": "Resume analysis not ready or failed."}, status=400)

        ai_suggestions = analysis.data.get("ai_analysis", {})

        # ✅ Create ONE latex resume record (this is the one we will update in the task)
        latex_instance = LatexResume.objects.create(
            user=request.user,
            resume_upload=resume_upload,
            ai_suggestions=ai_suggestions,
            result_json={"status": "PROCESSING"}
        )

        # ✅ Pass latex_instance.id to task (NOT resume_upload.id)
        queue = django_rq.get_queue("default")
        job = queue.enqueue(generate_latex_task, latex_instance.id)

        return JsonResponse({
            "status": "PROCESSING_LATEX",
            "latex_resume_id": latex_instance.id,
            "resume_id": resume_upload.id,
            "job_id": job.id,
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required(login_url="/login/")
def api_latex_status(request, latex_resume_id):
    """
    Polling endpoint → Returns LaTeX/PDF generation results
    """
    try:
        latex_instance = LatexResume.objects.get(id=latex_resume_id, user=request.user)
    except LatexResume.DoesNotExist:
        return JsonResponse({"error": "LaTeX resume not found."}, status=404)

    return JsonResponse(latex_instance.result_json or {"status": "PROCESSING"})





@login_required(login_url="/login/")
@require_POST
def api_jd_match(request):
    jd_text = request.POST.get("jd_text", "").strip()
    if not jd_text:
        return JsonResponse({"error": "JD text is required."}, status=400)

    resume_upload = ResumeUpload.objects.filter(user=request.user).last()
    if not resume_upload:
        return JsonResponse({"error": "Upload a resume first."}, status=400)

    jd_instance = JDMatch.objects.create(
        user=request.user,
        resume=resume_upload,
        jd_text=jd_text,
        result_json={"status": "PROCESSING"}
    )

    queue = django_rq.get_queue("default")
    job = queue.enqueue(process_jd_match, jd_instance.id)

    return JsonResponse({
        "status": "PROCESSING",
        "jd_id": jd_instance.id,
        "job_id": job.id
    })


@login_required(login_url="/login/")
def api_jd_status(request, jd_id):
    try:
        jd_instance = JDMatch.objects.get(id=jd_id, user=request.user)
    except JDMatch.DoesNotExist:
        return JsonResponse({"error": "Not found"}, status=404)

    return JsonResponse(jd_instance.result_json or {"status": "PROCESSING"})
