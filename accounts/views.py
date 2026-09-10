from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import RegisterForm, LoginForm


class UserLoginView(LoginView):
    template_name = "store/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True
    next_page = reverse_lazy("home")

    def form_valid(self, form):
        messages.success(
            self.request,
            "Welcome back!"
        )
        return super().form_valid(form)


class UserLogoutView(LogoutView):
    next_page = reverse_lazy("home")


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = "store/register.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        response = super().form_valid(form)

        login(
            self.request,
            self.object
        )

        messages.success(
            self.request,
            "Account created successfully!"
        )

        return response


class UserPasswordResetView(PasswordResetView):
    template_name = "store/password_reset.html"
    email_template_name = "store/password_reset_email.txt"
    html_email_template_name = "store/password_reset_email.html"
    subject_template_name = "store/password_reset_subject.txt"
    success_url = reverse_lazy("password_reset_done")


class UserPasswordResetDoneView(PasswordResetDoneView):
    template_name = "store/password_reset_done.html"


class UserPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "store/password_reset_confirm.html"
    success_url = reverse_lazy("password_reset_complete")


class UserPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "store/password_reset_complete.html"