from django.urls import path

from . import views

urlpatterns = [
    # fmt: off
    path("sign-up", views.SignUpView.as_view(), name="sign_up_view"),
    path("sign-in", views.SignInView.as_view(), name="sign_in_view"),
    path("logout", views.LogoutView.as_view(), name="logout_view"),
    path("email-confirmation", views.EmailConfirmationView.as_view(), name="email_confirmation_view"),
    # fmt: on
]
