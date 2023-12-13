"""
Base classes for other test cases to inherit from.

"""
import json
from contextlib import contextmanager

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.http import HttpRequest
from django.test import TestCase, modify_settings, override_settings
from django.urls import reverse

from arbitex import signals
from arbitex.forms import RegistrationForm


class _AssertSignalSentContext:
    """
    Context manager for asserting a signal was sent.

    """

    def __init__(self, test_case, signal, required_kwargs=None):
        self.test_case = test_case
        self.signal = signal
        self.required_kwargs = required_kwargs

    def _listener(self, sender, **kwargs):
        """
        Listener function which will capture the sent signal.

        """
        # pylint: disable=attribute-defined-outside-init
        self.signal_sent = True
        self.received_kwargs = kwargs
        self.sender = sender

    def __enter__(self):
        # pylint: disable=attribute-defined-outside-init
        self.signal_sent = False
        self.received_kwargs = {}
        self.sender = None
        self.signal.connect(self._listener)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.signal.disconnect(self._listener)
        if not self.signal_sent:
            self.test_case.fail("Signal was not sent.")
            return
        if self.required_kwargs is not None:
            missing_kwargs = []
            for k in self.required_kwargs:
                if k not in self.received_kwargs:
                    missing_kwargs.append(k)
            if missing_kwargs:
                self.test_case.fail(
                    f"Signal missing required arguments: {','.join(missing_kwargs)}"
                )


class _AssertSignalNotSentContext(_AssertSignalSentContext):
    """
    Context manager for asserting a signal was not sent.

    """

    # pylint: disable=too-few-public-methods

    def __exit__(self, exc_type, exc_value, traceback):
        self.signal.disconnect(self._listener)
        if self.signal_sent:
            self.test_case.fail("Signal was unexpectedly sent.")


@override_settings(ACCOUNT_ACTIVATION_DAYS=7, REGISTRATION_OPEN=True)
class RegistrationTestCase(TestCase):
    """
    Base class for test cases, defining valid data for registering a
    user account and looking up the account after creation.

    """

    # pylint: disable=invalid-name

    @property
    def valid_data(self):
        """
        Return a set of valid data for user registration.

        """
        User = get_user_model()
        return {
            User.USERNAME_FIELD: "alice",
            "email": "alice@example.com",
            "password1": "swordfish",
            "password2": "swordfish",
        }

    @property
    def user_lookup_kwargs(self):
        """
        Return query arguments for querying the user registered by ``valid_data``.

        """
        User = get_user_model()
        return {User.USERNAME_FIELD: "alice"}

    @contextmanager
    def assertSignalSent(self, signal, required_kwargs=None):
        """
        Assert a signal was sent.

        """
        with _AssertSignalSentContext(self, signal, required_kwargs) as signal_context:
            yield signal_context

    @contextmanager
    def assertSignalNotSent(self, signal):
        """
        Assert a signal was not sent.

        """
        with _AssertSignalNotSentContext(self, signal) as signal_context:
            yield signal_context


class WorkflowTestCase(RegistrationTestCase):
    """
    Base class for the test cases which exercise the built-in
    workflows, including logic common to all of them (and which needs
    to be tested for each one).

    """

    def test_registration_open(self):
        """
        ``REGISTRATION_OPEN``, when ``True``, permits registration.

        """
        resp = self.client.get(reverse("arbitex_register"))
        assert resp.status_code == 200

    @override_settings(REGISTRATION_OPEN=False)
    def test_registration_closed(self):
        """
        ``REGISTRATION_OPEN``, when ``False``, disallows registration.

        """
        resp = self.client.get(reverse("arbitex_register"))
        self.assertRedirects(resp, reverse("arbitex_disallowed"))

        resp = self.client.post(
            reverse("arbitex_register"), data=self.valid_data
        )
        self.assertRedirects(resp, reverse("arbitex_disallowed"))

    def test_registration_get(self):
        """
        HTTP ``GET`` to the registration view uses the appropriate
        template and populates a registration form into the context.

        """
        resp = self.client.get(reverse("arbitex_register"))
        assert resp.status_code == 200
        self.assertTemplateUsed(resp, "arbitex/registration_form.html")
        assert isinstance(resp.context["form"], RegistrationForm)

    def test_registration(self):
        """
        Registration creates a new account.

        """
        with self.assertSignalSent(signals.user_registered):
            resp = self.client.post(
                reverse("arbitex_register"), data=self.valid_data
            )

        self.assertRedirects(resp, reverse("arbitex_complete"))

        user_model = get_user_model()
        new_user = user_model.objects.get(**self.user_lookup_kwargs)

        assert new_user.check_password(self.valid_data["password1"])
        assert new_user.email == self.valid_data["email"]

    def test_registration_failure(self):
        """
        Registering with invalid data fails.

        """
        data = self.valid_data.copy()
        data.update(password2="notsecret")

        with self.assertSignalNotSent(signals.user_registered):
            resp = self.client.post(reverse("arbitex_register"), data=data)

        assert resp.status_code == 200
        assert not resp.context["form"].is_valid()
        assert resp.context["form"].has_error("password2")

    def test_registration_signal(self):
        """
        Registering a new user account sends the registration signal.

        """
        # pylint: disable=invalid-name
        User = get_user_model()
        with self.assertSignalSent(signals.user_registered) as signal_context:
            self.client.post(
                reverse("arbitex_register"), data=self.valid_data
            )
            assert (
                signal_context.received_kwargs["user"].get_username()
                == self.valid_data[User.USERNAME_FIELD]
            )
            assert isinstance(signal_context.received_kwargs["request"], HttpRequest)


class ActivationTestCase(WorkflowTestCase):
    """
    Base class for testing the built-in workflows which involve an
    activation step.

    """

    # First few methods repeat parent class, but with added checks for
    # is_active status and sending of activation emails.
    def test_registration(self):
        """
        Registration creates a new inactive account and sends an
        activation email.

        """
        with self.assertSignalSent(signals.user_registered):
            super().test_registration()

        user_model = get_user_model()
        new_user = user_model.objects.get(**self.user_lookup_kwargs)

        # New user must not be active.
        assert not new_user.is_active

    @override_settings(ACCOUNT_ACTIVATION_DAYS=7)
    def test_registration_email(self):
        """
        The activation email is sent and contains the expected template variables.

        """
        super().test_registration()
        user_model = get_user_model()
        new_user = user_model.objects.get(**self.user_lookup_kwargs)

        # An activation email was sent.
        assert len(mail.outbox) == 1
        message = mail.outbox[0]

        subject_json, body_json = json.loads(message.subject), json.loads(message.body)
        assert subject_json == body_json

        assert len(body_json["activation_key"]) > 1
        assert body_json["expiration_days"] == settings.ACCOUNT_ACTIVATION_DAYS
        assert len(body_json["site"]) > 1
        assert body_json["user"] == new_user.username

    def test_registration_failure(self):
        """
        Registering with invalid data fails.

        """
        with self.assertSignalNotSent(signals.user_registered):
            super().test_registration_failure()

        # Activation email was not sent.
        assert 0 == len(mail.outbox)

    @modify_settings(INSTALLED_APPS={"remove": ["django.contrib.sites"]})
    def test_registration_no_sites(self):
        """
        Registration still functions properly when
        ``django.contrib.sites`` is not installed; the fallback will
        be a ``RequestSite`` instance.

        """
        with self.assertSignalSent(signals.user_registered):
            resp = self.client.post(
                reverse("arbitex_register"), data=self.valid_data
            )

        assert 302 == resp.status_code

        user_model = get_user_model()
        new_user = user_model.objects.get(**self.user_lookup_kwargs)

        assert new_user.check_password(self.valid_data["password1"])
        assert new_user.email == self.valid_data["email"]

    @override_settings(ACCOUNT_ACTIVATION_DAYS=7)
    @modify_settings(INSTALLED_APPS={"remove": ["django.contrib.sites"]})
    def test_registration_email_no_sites(self):
        """
        The activation email is sent and contains the expected template variables.

        """
        super().test_registration()
        user_model = get_user_model()
        new_user = user_model.objects.get(**self.user_lookup_kwargs)

        # An activation email was sent.
        assert len(mail.outbox) == 1
        message = mail.outbox[0]

        subject_json, body_json = json.loads(message.subject), json.loads(message.body)
        assert subject_json == body_json

        assert len(body_json["activation_key"]) > 1
        assert body_json["expiration_days"] == settings.ACCOUNT_ACTIVATION_DAYS
        assert len(body_json["site"]) > 1
        assert body_json["user"] == new_user.username
