from django.urls import path

from demo import admin_views, views

urlpatterns = [
    path("films/search", views.search_films),
    path("films/<int:film_id>/reviews", views.film_reviews),
    path("customers/by-email", views.customer_by_email),
    path("customers/<int:customer_id>/profile", views.profile),
    path("activity/search", views.search_activity),
    path("admin/customers/<int:customer_id>/profile", admin_views.update_profile),
]
