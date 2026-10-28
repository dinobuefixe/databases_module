from django.urls import path, re_path

from demo import views

urlpatterns = [
    path("health", views.health),
    path("accounts/<int:account_id>", views.account),
    path("accounts/<int:account_id>/withdraw", views.withdraw),
    path("rentals", views.create_rental),
    path("customers/<int:customer_id>/films", views.customer_films),
    path("verify", views.verify_view),
    re_path(r"^reports/monthly/(?P<month>\d{4}-\d{2})$", views.monthly_report),
]
