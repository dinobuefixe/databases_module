from django.urls import path

from demo import views

urlpatterns = [
    path("customers/<int:customer_id>", views.customer_detail),
    path("customers/<int:customer_id>/charge", views.charge),
    path("customers/<int:customer_id>/top-up", views.top_up),
]
