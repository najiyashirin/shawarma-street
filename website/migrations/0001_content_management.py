from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AssessmentPDF",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(default="Assessment question bank", max_length=150)),
                ("pdf_file", models.FileField(help_text="Upload a PDF containing assessment questions or teacher reference material.", upload_to="assessments/", validators=[django.core.validators.FileExtensionValidator(["pdf"])])),
                ("notes", models.TextField(blank=True, help_text="Optional notes for staff about the level, source, or intended use.")),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"verbose_name": "Assessment PDF", "verbose_name_plural": "Assessment PDFs", "ordering": ("-uploaded_at",)},
        ),
        migrations.CreateModel(
            name="AssessmentQuestion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("category", models.CharField(default="General English", help_text="For example: Grammar, Vocabulary, Reading, or Everyday English.", max_length=80)),
                ("question", models.TextField(help_text="Enter the question exactly as learners should see it.")),
                ("option_a", models.CharField(max_length=300, verbose_name="Answer A")),
                ("option_b", models.CharField(max_length=300, verbose_name="Answer B")),
                ("option_c", models.CharField(max_length=300, verbose_name="Answer C")),
                ("option_d", models.CharField(max_length=300, verbose_name="Answer D")),
                ("correct_option", models.PositiveSmallIntegerField(choices=[(0, "A"), (1, "B"), (2, "C"), (3, "D")], help_text="Select the correct answer.")),
                ("order", models.PositiveIntegerField(default=1, help_text="Questions appear from the lowest order number to the highest.")),
                ("is_active", models.BooleanField(default=True, help_text="Only published questions appear in the free assessment.", verbose_name="Published")),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name": "Assessment question", "verbose_name_plural": "Assessment questions", "ordering": ("order", "id")},
        ),
        migrations.CreateModel(
            name="Brochure",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(default="English programmes brochure", max_length=150)),
                ("file", models.FileField(help_text="Upload the PDF visitors should receive from “Explore Our Programmes”.", upload_to="brochures/", validators=[django.core.validators.FileExtensionValidator(["pdf"])])),
                ("is_active", models.BooleanField(default=True, help_text="The newest active brochure is used on the homepage.")),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ("-uploaded_at",)},
        ),
    ]
