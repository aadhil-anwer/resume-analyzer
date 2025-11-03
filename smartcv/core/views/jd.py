import json
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from core.models import ResumeUpload
from core.utils.extract_text import extract_text_from_docx, extract_text_from_pdf
from core.utils.normalize import normalize_text
from core.utils.local_checks import run_local_checks
from core.utils.jd_resume_analysis import match_resume_to_jd
import django_rq
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from core.models import ResumeUpload, JDMatch
from core.tasks import process_jd_match

@require_POST
@login_required(login_url="/login/")
def upload_resume_with_jd(request):
    file = request.FILES.get("resume")
    jd_text = request.POST.get("jd", "").strip()

    if not file or not jd_text:
        return render(request, "core/jd_upload.html", {"error": "Please upload resume and job description."})

    instance = ResumeUpload.objects.create(file=file, user=request.user)
    path = instance.file.path

    if path.lower().endswith(".pdf"):
        resume_text = extract_text_from_pdf(path)
    else:
        resume_text = extract_text_from_docx(path)

    resume_text = normalize_text(resume_text)
    jd_text = normalize_text(jd_text)

    local_check = run_local_checks(resume_text)
    ai_result = match_resume_to_jd(resume_text, jd_text)

    instance.result_json = {
        "status": "SUCCESS",
        "local_check": local_check,
        "ai_analysis": ai_result,
    }
    instance.save()

    return render(request, "core/jd_upload.html", {
        "result": json.dumps(instance.result_json, indent=2, ensure_ascii=False)
    })

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from core.models import ResumeUpload
from core.utils.extract_text import extract_text_from_pdf, extract_text_from_docx
from core.utils.normalize import normalize_text



@require_POST
@login_required(login_url="/login/")
def jd_match_api(request):
    file = request.FILES.get("resume")
    jd_text = request.POST.get("jd_text", "").strip()

    if not file:
        return JsonResponse({"error": "Resume file required."}, status=400)
    if not jd_text:
        return JsonResponse({"error": "Job Description required."}, status=400)

    resume = ResumeUpload.objects.create(user=request.user, file=file)

    jd_match = JDMatch.objects.create(
        user=request.user,
        resume=resume,
        jd_text=jd_text,
        status="PROCESSING",
        result_json={"status": "PROCESSING"},
    )

    queue = django_rq.get_queue("default")
    queue.enqueue("core.tasks.process_jd_match", jd_match.id)

    return JsonResponse({"status": "PROCESSING", "jd_id": jd_match.id})

@login_required(login_url="/login/")
def jd_match_status(request, jd_id):
    try:
        jd = JDMatch.objects.get(id=jd_id, user=request.user)
        return JsonResponse(jd.result_json)
    except JDMatch.DoesNotExist:
        return JsonResponse({"error": "No such job"}, status=404)
