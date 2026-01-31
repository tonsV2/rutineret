# Rutineret Django API

Django REST API with JWT authentication and role-based access control.

## Quick Start

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Setup and run
uv venv
uv sync
uv run manage.py migrate
uv run manage.py setup_initial_data
uv run poe dev  # Start development server
```

## Available Scripts

- `uv run poe dev` - Start development server
- `uv run poe test` - Run tests with coverage
- `uv run poe test-verbose` - Run tests with detailed output and HTML coverage
- `uv run poe migrate` - Run database migrations
- `uv run poe setup` - Run initial data setup
- `uv run poe shell` - Django shell
- `uv run poe shell-plus` - Django shell_plus (if django-extensions is installed)
- `uv run poe reset-db` - Reset database (destructive)
- `uv run poe collectstatic` - Collect static files
- `uv run poe createsuperuser` - Create superuser
- `uv run poe makemigrations` - Create migrations
- `uv run poe check` - Run ruff linter
- `uv run poe format` - Format code with ruff
- `uv run poe fix` - Fix code with ruff
- `uv run poe lint` - Run both linting and format checking

## Features

- JWT Authentication with access/refresh tokens
- Role-based access control with JSON permissions
- User profiles with avatars and extended fields
- OpenAPI/Swagger documentation
- CORS support for frontend integration
- Comprehensive testing suite

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`

## Development

This project uses:
- **Python 3.14+**
- **Django 5.2.10**
- **uv** for dependency management
- **pytest** for testing
- **ruff** for linting and formatting