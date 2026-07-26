from pathlib import Path

from django.http import FileResponse, Http404
from django.shortcuts import render

from .models import AssessmentQuestion, Brochure

def home(request):
    questions = [
        question.as_quiz_dict()
        for question in AssessmentQuestion.objects.filter(is_active=True)
    ]
    brochure = Brochure.objects.filter(is_active=True).first()
    return render(request, "home.html", {
        "assessment_questions": questions,
        "brochure": brochure,
    })


def download_brochure(request):
    brochure = Brochure.objects.filter(is_active=True).first()
    if not brochure or not brochure.file:
        raise Http404("No programme brochure is currently available.")

    filename = Path(brochure.file.name).name
    return FileResponse(
        brochure.file.open("rb"),
        as_attachment=True,
        filename=filename,
        content_type="application/pdf",
    )
