from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LogoutView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from formtools.wizard.views import SessionWizardView

from apps.talent.models import Person

from .forms import (
    CustomPasswordResetForm,
    CustomSetPasswordForm,
    SignInForm,
    SignUpStepOneForm,
    SignUpStepThreeForm,
    SignUpStepTwoForm,
)
from .models import User, SignUpRequest
from .services import UserService
from .utils import extract_device_info


class SignUpWizard(SessionWizardView):
    form_list = [SignUpStepOneForm, SignUpStepTwoForm, SignUpStepThreeForm]
    template_name = "security/sign_up/sign_up.html"
    initial_dict = {"0": {}, "1": {}, "2": {}}

    def process_step(self, form):
        data = super().process_step(form)

        if self.get_step_index() == 0:
            self.request.session["verification_code"] = form.cleaned_data["verification_code"]

        elif self.get_step_index() == 1:
            expected_code = self.request.session.get("verification_code")
            actual_code = form.cleaned_data.get("verification_code")

            if expected_code != actual_code:
                form.add_error(None, _("Invalid verification code. Please try again."))

        return data

    def done(self, form_list, **kwargs):
        first_form_data = form_list[0].cleaned_data
        third_form_data = form_list[2].cleaned_data

        full_name = first_form_data.get("full_name")
        preferred_name = first_form_data.get("preferred_name")
        email = first_form_data.get("email")
        username = third_form_data.get("username")
        password = third_form_data.get("password")

        user = UserService.create(
            username=username,
            password=password,
            email=email,
        )

        _ = Person.objects.create(
            full_name=full_name,
            preferred_name=preferred_name,
            user=user,
        )

        device_info = extract_device_info(self.request)
        SignUpRequest.objects.filter(email=email).update(user=user, successful=True)

        authenticated_user = authenticate(self.request, username=username, password=password)
        login(self.request, authenticated_user)
        return redirect(reverse("bounties"))


class SignInView(TemplateView):
    form_class = SignInForm
    initial = {}
    template_name = "security/sign_in/sign_in.html"

    def get(self, request, *args, **kwargs):
        context = {
            "form": self.form_class(),
            "next": request.GET.get("next", ""),
            "auth_provider": settings.AUTH_PROVIDER,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            username_or_email = form.cleaned_data["username_or_email"]
            password = form.cleaned_data["password"]
            remember_me = form.cleaned_data["remember_me"]
            if not remember_me:
                request.session.set_expiry(0)

            user_obj = User.objects.get_user_by_username_or_email(username_or_email)
            if not user_obj:
                form.add_error(None, _("This username or e-mail is not registered"))
                return render(
                    request,
                    self.template_name,
                    {
                        "form": form,
                        "auth_provider": settings.AUTH_PROVIDER,
                    },
                )

            user = authenticate(request, username=username_or_email, password=password)

            if user is not None:
                login(request, user)
                next_url = request.GET.get("next")
                if next_url:
                    return redirect(next_url)
                else:
                    return redirect("bounties")
            else:
                if user_obj.password_reset_required:
                    return redirect("password_reset_required")
                else:
                    user_obj.update_failed_login_budget_and_check_reset()
                    form.add_error(None, _("The given credentials are not correct!"))

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "auth_provider": settings.AUTH_PROVIDER,
            },
        )


class PasswordResetRequiredView(TemplateView):
    template_name = "security/sign_in/password_reset_required.html"


class PasswordResetView(PasswordResetView):
    form_class = CustomPasswordResetForm
    template_name = "security/password_reset/password_reset.html"

    def get(self, request, *args, **kwargs):
        form = self.form_class(initial=self.initial)
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            email = form.cleaned_data["email"]
            if User.objects.filter(email=email).exists():
                return self.form_valid(form)
            else:
                form.add_error(None, _("This e-mail does not exist"))

        return render(request, self.template_name, {"form": form})


class PasswordResetDoneView(PasswordResetDoneView):
    template_name = "security/password_reset/password_reset_done.html"


class PasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "security/password_reset/password_reset_confirm.html"
    form_class = CustomSetPasswordForm


class PasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "security/password_reset/password_reset_complete.html"


class LogoutView(LoginRequiredMixin, LogoutView):
    template_name = "security/logout.html"
    login_url = "sign_in"

    def post(self, request, *args, **kwargs):
        logout(request)
        return redirect("home")
