from django.urls import path

from demo import views

urlpatterns = [
    path("authors", views.create_author),
    path("ingredients", views.create_ingredient),
    path("recipes", views.create_recipe),
]
