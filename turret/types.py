from unittest.mock import patch

from urllib3 import exceptions  # noqa

with patch("typing.TYPE_CHECKING", True):
    from sentry_sdk._types import Event  # noqa: F401
