from django.core.validators import FileExtensionValidator
from django.db import models


class AssessmentQuestion(models.Model):
    OPTION_CHOICES = (
        (0, "A"),
        (1, "B"),
        (2, "C"),
        (3, "D"),
    )

    category = models.CharField(
        max_length=80,
        default="General Knowledge",
        help_text="For example: Mathematics, Science, English, Social Studies, or General Knowledge.",
    )
    question = models.TextField(help_text="Enter the question exactly as learners should see it.")
    option_a = models.CharField("Answer A", max_length=300)
    option_b = models.CharField("Answer B", max_length=300)
    option_c = models.CharField("Answer C", max_length=300)
    option_d = models.CharField("Answer D", max_length=300)
    correct_option = models.PositiveSmallIntegerField(
        choices=OPTION_CHOICES,
        help_text="Select the correct answer.",
    )
    order = models.PositiveIntegerField(
        default=1,
        help_text="Questions appear from the lowest order number to the highest.",
    )
    is_active = models.BooleanField(
        "Published",
        default=True,
        help_text="Only published questions appear in the free assessment.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("order", "id")
        verbose_name = "Assessment question"
        verbose_name_plural = "Assessment questions"

    def __str__(self):
        return f"{self.order}. {self.question[:70]}"

    def as_quiz_dict(self):
        return {
            "category": self.category,
            "question": self.question,
            "options": [self.option_a, self.option_b, self.option_c, self.option_d],
            "answer": self.correct_option,
        }


class AssessmentPDF(models.Model):
    title = models.CharField(max_length=150, default="Assessment question bank")
    pdf_file = models.FileField(
        upload_to="assessments/",
        validators=[FileExtensionValidator(["pdf"])],
        help_text="Upload a PDF containing assessment questions or teacher reference material.",
    )
    notes = models.TextField(
        blank=True,
        help_text="Optional notes for staff about the level, source, or intended use.",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-uploaded_at",)
        verbose_name = "Assessment PDF"
        verbose_name_plural = "Assessment PDFs"

    def __str__(self):
        return self.title


class Brochure(models.Model):
    title = models.CharField(max_length=150, default="All subjects programmes brochure")
    file = models.FileField(
        upload_to="brochures/",
        validators=[FileExtensionValidator(["pdf"])],
        help_text="Upload the PDF visitors should receive from “Explore Our Programmes”.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="The newest active brochure is used on the homepage.",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-uploaded_at",)

    def __str__(self):
        return self.title
