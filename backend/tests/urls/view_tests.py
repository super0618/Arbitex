"""
URLs used in the unit tests for django-registration.

You should not attempt to use these URLs in any sort of real or
development environment.

"""

from django.urls import path
from django.views.generic.base import TemplateView

from arbitex.backends.activation.views import RegistrationView

from ..views import ActivateWithComplexRedirect

urlpatterns = [
    path(
        "",
        TemplateView.as_view(
            template_name="arbitex/activation_complete.html"
        ),
        name="simple_activation_redirect",
    ),
    path(
        "activate/complete/",
        TemplateView.as_view(
            template_name="arbitex/activation_complete.html"
        ),
        name="arbitex_activation_complete",
    ),
    path(
        "activate/<str:activation_key>/",
        ActivateWithComplexRedirect.as_view(),
        name="arbitex_activate",
    ),
    path("register/", RegistrationView.as_view(), name="arbitex_register"),
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
