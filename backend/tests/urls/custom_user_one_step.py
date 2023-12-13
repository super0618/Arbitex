"""
URLs used to test the one-step workflow with a custom user
model.

You should not use these in any sort of real environment.

"""

from django.urls import path
from django.views.generic.base import TemplateView

from arbitex.backends.one_step import views
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
        "register/",
        views.RegistrationView.as_view(form_class=CustomUserRegistrationForm),
        name="arbitex_register",
    ),
    path(
        "register/closed/",
        TemplateView.as_view(
            template_name="arbitex/registration_closed.html"
        ),
        name="arbitex_disallowed",
    ),
    path(
        "register/complete/",
        TemplateView.as_view(
            template_name="arbitex/registration_complete.html"
        ),
        name="arbitex_complete",
    ),
]
