"""
Tests for the one-step registration workflow.

"""

from django.apps import apps
from django.contrib.auth import get_user_model
from django.test import modify_settings, override_settings
from django.urls import reverse

from arbitex import signals

from .base import WorkflowTestCase


@modify_settings(INSTALLED_APPS={"remove": "arbitex"})
@override_settings(ROOT_URLCONF="arbitex.backends.one_step.urls")
class OneStepWorkflowViewTests(WorkflowTestCase):
    """
    Tests for the one-step workflow.

    """

    def test_registration(self):
        """
        Registration creates a new account and logs the user in.

        """
        user_model = get_user_model()
        with self.assertSignalSent(
            signals.user_registered, required_kwargs=["user", "request"]
        ) as signal_context:
            resp = self.client.post(
                reverse("arbitex_register"), data=self.valid_data
            )
            assert (
                signal_context.received_kwargs["user"].get_username()
                == self.valid_data[user_model.USERNAME_FIELD]
            )

        self.assertRedirects(resp, reverse("arbitex_complete"))

        new_user = user_model.objects.get(**self.user_lookup_kwargs)
        assert new_user.check_password(self.valid_data["password1"])
        assert new_user.email == self.valid_data["email"]

        # New user must be active.
        assert new_user.is_active

        # New user must be logged in.
        resp = self.client.get(reverse("arbitex_register"))
        assert resp.context["user"].is_authenticated


@override_settings(AUTH_USER_MODEL="tests.CustomUser")
@override_settings(ROOT_URLCONF="tests.urls.custom_user_one_step")
class OneStepWorkflowCustomUserTests(OneStepWorkflowViewTests):
    """
    Runs the one-step workflow's test suite, but with a custom user model.

    """

    def test_custom_user_configured(self):
        """
        Asserts that the user model in use is the custom user model
        defined in this test suite.

        """
        user_model = get_user_model()
        custom_user = apps.get_model("tests", "CustomUser")
        assert user_model is custom_user
