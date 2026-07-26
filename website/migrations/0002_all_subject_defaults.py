from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("website", "0001_content_management")]

    operations = [
        migrations.AlterField(
            model_name="assessmentquestion",
            name="category",
            field=models.CharField(default="General Knowledge", help_text="For example: Mathematics, Science, English, Social Studies, or General Knowledge.", max_length=80),
        ),
        migrations.AlterField(
            model_name="brochure",
            name="title",
            field=models.CharField(default="All subjects programmes brochure", max_length=150),
        ),
    ]
