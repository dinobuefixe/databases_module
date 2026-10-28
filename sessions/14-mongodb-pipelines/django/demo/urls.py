from django.urls import path, re_path

from demo import views

urlpatterns = [
    path("films/per-rating", views.films_per_rating),
    path("actors/top", views.top_actors),
    path("rentals/per-month", views.rentals_per_month),
    path("customers/by-activity", views.customers_by_activity),
    path("customers/summary", views.customers_summary),
    path("rentals/latest", views.latest_rentals),
    path("rentals/match-position", views.match_position),
    path("reports/rentals-per-month", views.rentals_per_month_report),
    re_path(r"^reports/monthly/(?P<month>\d{4}-\d{2})$", views.monthly_report),
]
