from django.urls import path

from .views import (
    UserLoginView,
    UserLogoutView,
    RegisterView,
    UserPasswordResetView,
    UserPasswordResetDoneView,
    UserPasswordResetConfirmView,
    UserPasswordResetCompleteView,
)


urlpatterns = [

    path(
        "login/",
        UserLoginView.as_view(),
        name="login",
    ),

    path(
        "logout/",
        UserLogoutView.as_view(),
        name="logout",
    ),

    path(
        "register/",
        RegisterView.as_view(),
        name="register",
    ),

    path(
        "forgot-password/",
        UserPasswordResetView.as_view(),
        name="password_reset",
    ),

    path(
        "forgot-password/done/",
        UserPasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),

    path(
        "reset/<uidb64>/<token>/",
        UserPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),

    path(
        "reset/complete/",
        UserPasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
]