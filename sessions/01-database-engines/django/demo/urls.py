from django.urls import path

from demo import views

urlpatterns = [
    path("health", views.health),
    path("hello", views.hello),
]
