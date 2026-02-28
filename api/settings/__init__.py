import os

from .base import *  # noqa: F401,F403

settings_module = os.environ.get("DJANGO_SETTINGS_MODULE", "api.settings.development")

if settings_module == "api.settings.production":
    from .production import *  # noqa: F401,F403
else:
    from .development import *  # noqa: F401,F403
