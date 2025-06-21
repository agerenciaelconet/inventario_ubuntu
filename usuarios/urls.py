from django.urls import path
from django.contrib.auth import views as auth_views
from .views import CustomLoginView


urlpatterns = [
    path("login/", CustomLoginView.as_view(template_name="usuarios/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="/usuarios/login/"), name="logout"),
]
