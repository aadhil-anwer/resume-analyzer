import json
import django_rq
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from core.models import ResumeUpload, LatexResume

@require_POST
@login_required(login_url="/login/")
def generate_latex_view(request):
    result_json = request.POST.get("resume_text")
    if not result_json:
        return JsonResponse({"error": "No resume data received."}, status=400)

    data = json.loads(result_json)
    ai_suggestions = data.get("ai_analysis", {})

    resume_upload = ResumeUpload.objects.filter(user=request.user).last()
    if not resume_upload:
        return JsonResponse({"error": "No uploaded resume found."}, status=404)

    latex_resume = LatexResume.objects.create(
        user=request.user,
        resume_upload=resume_upload,
        ai_suggestions=ai_suggestions,
        result_json={"status": "PROCESSING"},
    )

    queue = django_rq.get_queue("default")
    job = queue.enqueue("core.tasks.generate_latex_task", resume_upload.id, ai_suggestions)

    return JsonResponse({
        "status": "PROCESSING_LATEX",
        "latex_resume_id": latex_resume.id,
        "job_id": job.id,
    })

def check_latex_status(request, latex_resume_id):
    instance = LatexResume.objects.get(id=latex_resume_id)
    return JsonResponse(instance.result_json or {"status": "PROCESSING"}, safe=False)
