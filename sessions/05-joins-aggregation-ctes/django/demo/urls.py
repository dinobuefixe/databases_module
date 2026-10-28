from django.urls import path

from demo import views

urlpatterns = [path("reports/<slug:name>", views.report)]
