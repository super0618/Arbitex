"""
URLconf for registration using django-registration's one-step
workflow.

"""

from django.urls import path
from django.views.generic.base import TemplateView

from . import views

urlpatterns = [
    path(
        "register/",
        views.RegistrationView.as_view(),
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
