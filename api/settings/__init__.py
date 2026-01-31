import os

# Default to development settings if no environment specified
if "DJANGO_SETTINGS_MODULE" not in os.environ:
    from .development import *  # noqa: F401,F403
else:
    # Import base settings first, then environment-specific ones
    from .base import *  # noqa: F401,F403
