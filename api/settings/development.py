from .base import *

# Development settings
DEBUG = True

# Development database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Development CORS settings (more permissive)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]

CORS_ALLOW_ALL_ORIGINS = True  # Only for development

# Development email backend
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Development media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Debug toolbar (if installed)
try:
    import debug_toolbar

    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
    INTERNAL_IPS = ["127.0.0.1"]
except ImportError:
    pass
