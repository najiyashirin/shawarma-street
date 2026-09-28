from django.urls import path

from .views import restaurant_home, restaurant_menu

app_name = "restaurant"
urlpatterns = [path("", restaurant_home, name="restaurant_home"), path("menu/", restaurant_menu, name="restaurant_menu")]
