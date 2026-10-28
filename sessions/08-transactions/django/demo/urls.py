from django.urls import path

from demo import views

urlpatterns = [
    path("accounts", views.accounts),
    path("accounts/reset", views.reset),
    path("accounts/<int:account_id>/withdraw", views.withdraw),
]
