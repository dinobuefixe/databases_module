from django.urls import path

from demo import views

urlpatterns = [
    path("films/longest-per-rating", views.longest_per_rating),
    path("customers/<int:customer_id>/running-total", views.running_total),
    path("customers/<int:customer_id>/rental-gaps", views.rental_gaps),
    path("daily-rentals", views.daily_rentals),
    path("daily-rentals/refresh", views.refresh_daily_rentals),
]
