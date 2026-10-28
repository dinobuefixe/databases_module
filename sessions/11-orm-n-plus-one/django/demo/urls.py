from django.urls import path

from demo import views

urlpatterns = [
    path("customers", views.customers),
    path("customers/top", views.top_customers),
    path("rentals", views.rentals),
]
