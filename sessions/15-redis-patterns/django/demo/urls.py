from django.urls import path, re_path

from demo import views

urlpatterns = [
    path("films/<int:film_id>/views", views.film_views),
    path("films/<int:film_id>/hash", views.film_hash),
    re_path(r"^visitors/(?P<day>\d{4}-\d{2}-\d{2})$", views.visitors),
    path("search", views.search),
    path("search/popular", views.popular_terms),
    path("customers/<int:customer_id>", views.customer),
    path("leaderboard/customers", views.leaderboard),
    path("leaderboard/customers/<int:customer_id>", views.leaderboard_customer),
]
