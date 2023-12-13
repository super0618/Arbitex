"""
URLs used to test the activation workflow with a custom user
model.

You should not use these in any sort of real environment.

"""

from django.urls import path
from django.views.generic.base import TemplateView

from arbitex.backends.activation import views
from arbitex.forms import RegistrationForm

from ..models import CustomUser


class CustomUserRegistrationForm(RegistrationForm):
    """
    Registration form for the custom user model.

    """

    # pylint: disable=too-few-public-methods

    class Meta(RegistrationForm.Meta):
        model = CustomUser


urlpatterns = [
    path(
        "activate/complete/",
        TemplateView.as_view(
            template_name="arbitex/activation_complete.html"
        ),
        name="arbitex_activation_complete",
    ),
    path(
        "activate/<str:activation_key>/",
        views.ActivationView.as_view(),
        name="arbitex_activate",
    ),
    path(
        "register/",
        views.RegistrationView.as_view(form_class=CustomUserRegistrationForm),
        name="arbitex_register",
    ),
    path(
        "register/complete/",
        TemplateView.as_view(
            template_name="arbitex/registration_complete.html"
        ),
        name="arbitex_complete",
    ),
    path(
        "register/closed/",
        TemplateView.as_view(
            template_name="arbitex/registration_closed.html"
        ),
        name="arbitex_disallowed",
    ),
]
