import json
import django_rq
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from core.models import ResumeUpload
from core.tasks import process_resume_upload
from core.utils.extract_text import extract_text_from_docx, extract_text_from_pdf
from core.utils.normalize import normalize_text
from core.utils.local_checks import run_local_checks

@require_POST
@login_required(login_url="/login/")
def upload_resume(request):
    file = request.FILES.get("resume")
    if not file:
        return render(request, "core/upload.html", {"error": "Please select a file to upload."})

    instance = ResumeUpload.objects.create(file=file, user=request.user)
    file_path = instance.file.path

    if file_path.lower().endswith(".pdf"):
        resume_text = extract_text_from_pdf(file_path)
    elif file_path.lower().endswith(".docx"):
        resume_text = extract_text_from_docx(file_path)
    else:
        return render(request, "core/upload.html", {"error": "Unsupported file type."})

    resume_text = normalize_text(resume_text)
    local_check = run_local_checks(resume_text)

    queue = django_rq.get_queue("default")
    job = queue.enqueue(process_resume_upload, instance.id)

    result = {
        "status": "PROCESSING",
        "resume_id": instance.id,
        "job_id": job.id,
    }

    return render(request, "core/upload.html", {"result": json.dumps(result, ensure_ascii=False)})

def check_resume_status(request, resume_id):
    instance = ResumeUpload.objects.get(id=resume_id)
    return JsonResponse(instance.result_json or {"status": "PROCESSING"}, safe=False)
