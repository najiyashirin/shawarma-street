from django.contrib import admin

from .models import AssessmentPDF, AssessmentQuestion, Brochure


admin.site.site_header = "Omni-at Administration"
admin.site.site_title = "Omni-at Admin"
admin.site.index_title = "Website content and assessment management"
admin.site.index_template = "admin.html"


@admin.register(AssessmentQuestion)
class AssessmentQuestionAdmin(admin.ModelAdmin):
    list_display = ("short_question", "category", "order", "correct_answer", "is_active", "updated_at")
    list_editable = ("order", "is_active")
    list_filter = ("is_active", "category")
    search_fields = ("question", "option_a", "option_b", "option_c", "option_d")
    ordering = ("order", "id")
    save_on_top = True
    fieldsets = (
        ("Question details", {
            "fields": ("category", "question"),
            "description": "Write one clear assessment question for any subject.",
        }),
        ("Answer choices", {
            "fields": ("option_a", "option_b", "option_c", "option_d", "correct_option"),
            "description": "Provide four choices and identify the correct one.",
        }),
        ("Publishing", {
            "fields": ("order", "is_active"),
            "description": "Control where the question appears and whether learners can see it.",
        }),
    )

    @admin.display(description="Question")
    def short_question(self, obj):
        return obj.question[:80]

    @admin.display(description="Correct answer")
    def correct_answer(self, obj):
        options = [obj.option_a, obj.option_b, obj.option_c, obj.option_d]
        return f"{obj.get_correct_option_display()}: {options[obj.correct_option][:40]}"


@admin.register(AssessmentPDF)
class AssessmentPDFAdmin(admin.ModelAdmin):
    list_display = ("title", "pdf_file", "uploaded_at")
    search_fields = ("title", "notes")
    readonly_fields = ("uploaded_at",)
    fieldsets = (
        ("Assessment document", {
            "fields": ("title", "pdf_file", "notes"),
            "description": "Store PDF question banks and reference exams for your teaching team.",
        }),
        ("Upload information", {"fields": ("uploaded_at",)}),
    )


@admin.register(Brochure)
class BrochureAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "uploaded_at")
    list_editable = ("is_active",)
    list_filter = ("is_active",)
    readonly_fields = ("uploaded_at",)
    fieldsets = (
        ("Programme brochure", {
            "fields": ("title", "file", "is_active"),
            "description": "The newest active PDF is downloaded from the homepage button.",
        }),
        ("Upload information", {"fields": ("uploaded_at",)}),
    )
