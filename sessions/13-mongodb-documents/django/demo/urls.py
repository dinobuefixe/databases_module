from django.urls import path

from demo import views

urlpatterns = [
    path("stores", views.stores_collection),
    path("stores/explain", views.explain),
    path("stores/<int:store_id>/staff", views.add_staff),
    path("stores/<int:store_id>/visits", views.add_visit),
]
