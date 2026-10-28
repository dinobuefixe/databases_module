from django.urls import path

from demo import views

urlpatterns = [
    path("health", views.health),
    path("accounts/<int:account_id>", views.account),
    path("accounts/<int:account_id>/withdraw", views.withdraw),
    path("customers/<int:customer_id>/films", views.customer_films),
]
