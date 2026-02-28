import os

from .base import *  # noqa: F401,F403

if os.environ.get("DJANGO_SETTINGS_MODULE") == "api.settings.production":
    from .production import *  # noqa: F401,F403
elif os.environ.get("DJANGO_SETTINGS_MODULE") == "api.settings.development":
    from .development import *  # noqa: F401,F403
