from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("brochure/download/", views.download_brochure, name="download_brochure"),
]
