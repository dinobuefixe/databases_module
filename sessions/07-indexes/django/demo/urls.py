from django.urls import path

from demo import views

urlpatterns = [
    path("indexes", views.index_list),
    path("explain/<slug:name>", views.explain),
]
