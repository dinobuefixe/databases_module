from django.urls import path

from demo import views

urlpatterns = [
    path("customers/<int:customer_id>/films", views.customer_films),
    path("customers/<int:customer_id>/username", views.change_username),
    path("verify", views.verify_view),
    path("redis/persistence", views.persistence),
]
