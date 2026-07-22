from django.urls import path

from . import views

urlpatterns = [
    path("register/", views.RegisterRequestView.as_view(), name="auth-register"),
    path("register/resend/", views.RegisterResendView.as_view(), name="auth-register-resend"),
    path("register/verify/", views.RegisterVerifyView.as_view(), name="auth-register-verify"),
    path("password-reset/", views.PasswordResetRequestView.as_view(), name="auth-password-reset"),
    path("password-reset/confirm/", views.PasswordResetConfirmView.as_view(), name="auth-password-reset-confirm"),
    path("login/", views.LoginView.as_view(), name="auth-login"),
    path("refresh/", views.RefreshView.as_view(), name="auth-refresh"),
    path("logout/", views.LogoutView.as_view(), name="auth-logout"),
    path("me/", views.MeView.as_view(), name="auth-me"),
    path("telegram/link-code/", views.TelegramLinkCodeView.as_view(), name="auth-telegram-link-code"),
]
