from django.urls import path

from demo import views

urlpatterns = [
    path("films", views.list_films),
    path("films/rental-rate", views.update_rental_rate),
    path("films/<int:film_id>/views", views.add_view),
    path("actors", views.create_actor),
]
