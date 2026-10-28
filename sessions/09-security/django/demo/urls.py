from django.urls import path

from demo import views

urlpatterns = [
    path("whoami", views.whoami),
    path("customers/search", views.search_customers),
    path("reports/customers-per-store", views.customers_per_store),
    path("login", views.login),
    # UNSAFE, local demo only. These routes exist only when DJANGO_DEBUG=true.
    path("unsafe/customers/search", views.search_customers_unsafe),
    path("unsafe/login", views.login_unsafe),
]
