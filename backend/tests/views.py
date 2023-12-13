"""
Viw classes to exercise options of the registration view behavior not
covered by the built-in workflows.

"""
from django.urls import reverse_lazy

from arbitex.backends.activation.views import ActivationView


class ActivateWithComplexRedirect(ActivationView):
    """
    An activation view with a ``success_url`` more complex than a simple string.

    """

    success_url = reverse_lazy("arbitex_activation_complete")
