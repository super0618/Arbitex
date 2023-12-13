"""
URLconf for registration and activation, using django-registration's
HMAC activation workflow.

"""

from django.urls import path
from django.views.generic.base import TemplateView

from . import views

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
        views.RegistrationView.as_view(),
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
