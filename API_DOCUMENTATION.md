# Django REST API with JWT Authentication

This Django REST project provides a complete user authentication and management system with JWT tokens, extended user profiles, and role-based access control.

## Features

- **JWT Authentication**: Stateless authentication with access and refresh tokens
- **Custom User Model**: Extended user fields including phone, date of birth, etc.
- **User Profiles**: Extended profiles with bio, avatar, location, website
- **Role-Based Access Control**: Flexible permission system with JSON-stored permissions
- **Secure Password Management**: Password validation and change functionality
- **CORS Support**: Configured for frontend integration

## API Endpoints

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login (returns JWT tokens)
- `POST /api/auth/logout/` - User logout (blacklist refresh token)
- `POST /api/auth/token/refresh/` - Refresh access token

### User Management
- `GET /api/auth/me/` - Get current user info
- `GET/PUT /api/auth/user/` - Get/update current user details
- `GET /api/auth/users/` - List all users (with optional role filtering)
- `GET/PUT /api/auth/profile/` - Get/update user profile

### Additional Features
- `POST /api/auth/change-password/` - Change user password
- `GET /api/auth/roles/` - List all available roles

## Usage Examples

### Register a new user
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "password": "securepass123",
    "password_confirm": "securepass123"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "securepass123"
  }'
```

### Access protected endpoint
```bash
curl -X GET http://localhost:8000/api/auth/me/ \
  -H "Authorization: Bearer $YOUR_ACCESS_TOKEN"
```

### Update user profile
```bash
curl -X PUT http://localhost:8000/api/auth/profile/ \
  -H "Authorization: Bearer $YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bio": "Software developer passionate about Python",
    "location": "San Francisco, CA",
    "website": "https://johndoe.dev",
    "role_ids": [2]
  }'
```

## Default Credentials

An admin user is created for testing:
- **Email**: admin@example.com
- **Username**: admin
- **Password**: admin123

## Default Roles

Three roles are created by default:

### Admin
- Full administrative access
- User management: ✅
- Content management: ✅
- System settings: ✅

### Editor
- Content editor with limited permissions
- User management: ❌
- Content management: ✅
- System settings: ❌

### Viewer
- Read-only access
- User management: ❌
- Content management: ❌
- System settings: ❌

## JWT Token Configuration

- **Access Token Lifetime**: 60 minutes
- **Refresh Token Lifetime**: 7 days
- **Token Rotation**: Enabled
- **Blacklisting**: Enabled after rotation

## Security Features

- Password validation using Django's built-in validators
- CORS configuration for frontend integration
- JWT token blacklisting on logout
- Secure token configuration with HS256 algorithm
- Permission-based access control

## Setup Instructions

1. Install dependencies:
```bash
pip install djangorestframework djangorestframework-simplejwt django-cors-headers Pillow
```

2. Run migrations:
```bash
python3.11 manage.py migrate
```

3. Create superuser and roles:
```bash
python3.11 create_superuser.py
```

4. Start the development server:
```bash
python3.11 manage.py runserver
```

## API Response Format

All API responses follow a consistent format:

### Success Response
```json
{
  "data": { ... },
  "message": "Operation successful"
}
```

### Error Response
```json
{
  "error": "Error description",
  "details": { ... }
}
```

### Authentication Response
```json
{
  "user": { ... },
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "message": "Login successful"
}
```

## Frontend Integration

The API is configured to work with frontend applications running on:
- http://localhost:3000
- http://127.0.0.1:3000

To add more origins, update the `CORS_ALLOWED_ORIGINS` setting in `api/settings.py`.