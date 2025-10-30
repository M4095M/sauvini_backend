# Sauvini Django Backend

A complete Django REST Framework backend that serves as a drop-in replacement for the Rust backend, maintaining exact API compatibility with the frontend.

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Virtual environment (recommended)
- PostgreSQL (optional, SQLite works for development)

### Setup

```bash
# Clone and navigate to the project
cd sauvini_backend_django

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp env.example .env
# Edit .env with your configuration

# Run migrations
python manage.py migrate

# Create default data (admin user, academic streams)
python manage.py create_default_data

# Start the server
python manage.py runserver 0.0.0.0:4000
```

## 📁 Project Structure

```
sauvini_backend_django/
├── manage.py
├── requirements.txt
├── env.example
├── sauvini/              # Main Django project
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── authentication/   # Auth endpoints (login, register, password reset)
│   ├── users/           # User models (Student, Professor, Admin)
│   ├── courses/         # Course models (Module, Chapter, Lesson)
│   ├── assessments/     # Assessment models (Quiz, Exercise, Exam)
│   ├── purchases/       # Purchase management
│   ├── progress/        # Student progress tracking
│   └── notifications/   # Notification system
└── core/                # Shared utilities
    ├── storage.py       # MinIO integration
    ├── email.py         # Email service
    ├── permissions.py   # Custom DRF permissions
    └── middleware.py    # Custom middleware
```

## 🔧 Features

### ✅ Implemented

- **JWT Authentication**: Complete JWT system matching Rust backend

  - Access and refresh tokens
  - Token expiration matching Rust config
  - Role-based authentication (admin/professor/student)
  - Email verification via JWT tokens
  - Password reset via JWT tokens

- **User Management**: Multi-role user system

  - Student registration and login
  - Professor registration and login
  - Admin login
  - Email verification
  - Password reset functionality

- **Database Models**: Complete model mapping from Rust

  - User, Student, Professor, Admin models
  - Module, Chapter, Lesson models
  - Quiz, Exercise, Exam, Question models
  - Purchase and Progress tracking
  - Academic Streams

- **API Endpoints**: Exact route matching with Rust backend
  - All authentication endpoints
  - Health check endpoints
  - Same request/response formats

### 🚧 In Development

- Course management endpoints
- Assessment endpoints
- Purchase management
- Progress tracking
- File upload handling
- Admin management features

## 🔗 API Endpoints

### Authentication (Matching Rust Backend Exactly)

- `POST /api/v1/auth/student/register` - Student registration
- `POST /api/v1/auth/student/login` - Student login
- `POST /api/v1/auth/student/send-verification-email` - Send verification email
- `GET /api/v1/auth/student/verify-email` - Verify email
- `POST /api/v1/auth/student/forgot-password` - Send password reset
- `POST /api/v1/auth/student/reset-password` - Reset password
- `POST /api/v1/auth/student/refresh-token` - Refresh token

- `POST /api/v1/auth/professor/register` - Professor registration
- `POST /api/v1/auth/professor/login` - Professor login
- `POST /api/v1/auth/professor/send-verification-email` - Send verification email
- `GET /api/v1/auth/professor/verify-email` - Verify email
- `POST /api/v1/auth/professor/forgot-password` - Send password reset
- `POST /api/v1/auth/professor/reset-password` - Reset password
- `POST /api/v1/auth/professor/refresh-token` - Refresh token

- `POST /api/v1/auth/admin/login` - Admin login
- `POST /api/v1/auth/admin/forgot-password` - Send password reset
- `POST /api/v1/auth/admin/reset-password` - Reset password
- `POST /api/v1/auth/admin/refresh-token` - Refresh token

### Admin Only (Protected)

- `POST /api/v1/auth/admin/approve-professor` - Approve professor
- `POST /api/v1/auth/admin/reject-professor` - Reject professor
- `GET /api/v1/auth/admin/all-professors` - Get all professors

### Health Check

- `GET /api/v1/health` - Health check
- `GET /api/v1/health/live` - Liveness check

## 🗄️ Database Configuration

### SQLite (Development)

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### PostgreSQL (Production)

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'sauvini_db'),
        'USER': os.getenv('DB_USER', 'sauvini_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'sauvini_password'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}
```

## ⚙️ Environment Variables

Key configuration options in `.env`:

```bash
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database
DB_NAME=sauvini_db
DB_USER=sauvini_user
DB_PASSWORD=sauvini_password
DB_HOST=localhost
DB_PORT=5432

# JWT Configuration (matching Rust backend)
JWT_SECRET=your-jwt-secret-here
JWT_ACCESS_TOKEN_EXPIRY=15
JWT_REFRESH_TOKEN_EXPIRY=10080

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# MinIO Configuration
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
AWS_STORAGE_BUCKET_NAME=sauvini
AWS_S3_ENDPOINT_URL=http://localhost:9000
```

## 🧪 Testing

### Test Authentication

```bash
# Test health check
curl -X GET http://localhost:4000/api/v1/health

# Test student registration
curl -X POST http://localhost:4000/api/v1/auth/student/register \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "wilaya": "Algiers",
    "phone_number": "0555123456",
    "academic_stream": "Mathematics",
    "password": "testpassword123",
    "password_confirm": "testpassword123",
    "email": "john.doe@example.com"
  }'

# Test student login
curl -X POST http://localhost:4000/api/v1/auth/student/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "password": "testpassword123",
    "user_type": "student"
  }'
```

## 🔄 Migration from Rust Backend

This Django backend is designed as a **drop-in replacement** for the Rust backend:

1. **Same API Endpoints**: All routes match exactly
2. **Same Request/Response Format**: JSON structure is identical
3. **Same Authentication**: JWT tokens work the same way
4. **Same Error Handling**: Error responses match Rust format
5. **Same Status Codes**: HTTP status codes are identical

### Frontend Compatibility

- No frontend changes required
- Same API base URL: `http://localhost:4000/api/v1/`
- Same authentication headers: `Authorization: Bearer <token>`
- Same response formats for all endpoints

## 📊 Admin Interface

Access Django admin at `http://localhost:4000/admin/`

Default admin credentials:

- Email: `frihaouimohamed@gmail.com`
- Password: `07vk640xz`

## 🚀 Deployment

### Development

```bash
python manage.py runserver 0.0.0.0:4000
```

### Production

```bash
# Install production dependencies
pip install gunicorn

# Run with Gunicorn
gunicorn sauvini.wsgi:application --bind 0.0.0.0:4000
```

## 📚 API Documentation

Interactive API documentation available at:

- Swagger UI: `http://localhost:4000/api/docs/`
- Schema: `http://localhost:4000/api/schema/`

## 🔒 Security Features

- JWT token authentication
- Password hashing with Django's built-in system
- CORS protection
- SQL injection protection via Django ORM
- XSS protection via Django's template system
- CSRF protection (where applicable)

## 📈 Performance

- Database query optimization via Django ORM
- Connection pooling (when using PostgreSQL)
- Caching system (database-based)
- Efficient serialization with DRF

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.
