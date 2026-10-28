from django.urls import path

from demo import views

urlpatterns = [
    path("recipes", views.recipes),
    path("recipes/<int:recipe_id>", views.recipe_detail),
    path("recipes/<int:recipe_id>/ingredients", views.recipe_ingredients),
]
