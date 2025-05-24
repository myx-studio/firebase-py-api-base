# Firebase Python API

Firebase Cloud Functions API template for Python applications.

## Project Structure

- `api/` - API endpoints organized by version
- `config/` - Configuration settings for different environments
- `middlewares/` - Request processing middleware
- `models/` - Data models and schemas
- `repositories/` - Data access layer with Firestore implementation
- `services/` - Business logic services
- `utils/` - Utility functions for auth, logging, and validation

## Setup

1. Install dependencies:
   ```
   cd functions
   pip install -r requirements.txt
   ```

2. Configure Firebase:
   - Create a Firebase project
   - Set up Firestore database
   - Download service account key 
   - Add Firebase service account credentials to your environment

3. Update Firebase Functions Package:
   ```
   pip install firebase-functions>=0.4.0
   ```
   This ensures compatibility with the latest Firebase Functions SDK

4. Configure environment variables:
   - Copy the sample env file: `cp functions/.env.example functions/.env`
   - Edit the `.env` file with your settings:
     ```
     # App Environment
     ENVIRONMENT=development  # development, testing, production

     # Firebase Configuration
     # IMPORTANT: Do not use FIREBASE_ prefix as it's reserved by Firebase Functions
     WEB_API_KEY=your-firebase-web-api-key
     PROJECT_ID=your-firebase-project-id
     STORAGE_BUCKET=your-firebase-storage-bucket
     DATABASE_URL=your-firebase-database-url

     # Security
     JWT_SECRET=your-jwt-secret-key  # Generate with: python -c "import secrets; print(secrets.token_hex(32))"

     # Expo Push Notification
     EXPO_TOKEN=your-expo-push-notification-token  # From Expo account
     
     # Mailgun Email Configuration
     MAILGUN_API_KEY=your-mailgun-api-key  # From Mailgun account
     MAILGUN_DOMAIN=your-mailgun-domain    # e.g., mail.yourdomain.com
     MAILGUN_FROM_EMAIL=noreply@yourdomain.com
     MAILGUN_FROM_NAME=Firebase Python API

     # Logging
     LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
     ```

## Development

- Run functions locally:
  ```
  firebase emulators:start
  ```

## Deployment

1. Set up Firebase project and authentication:
   ```
   firebase login
   firebase use your-project-id
   ```

2. Set up Application Default Credentials:
   ```
   gcloud auth application-default login
   ```

3. Configure environment variables in `.env` file (see above)

4. Deploy functions to Firebase:
   ```
   firebase deploy
   ```

### Common Deployment Issues

- **Reserved Environment Variable Prefixes**: Firebase Functions reserves certain environment variable prefixes including `FIREBASE_`, `X_GOOGLE_`, and `EXT_`. Use alternative names for your environment variables (e.g., `PROJECT_ID` instead of `FIREBASE_PROJECT_ID`).

- **Artifact Registry Permissions**: If deployment fails with Artifact Registry permission errors, ensure your service accounts have the necessary permissions:
  ```
  gcloud projects add-iam-policy-binding your-project-id --member=serviceAccount:service-account-name@your-project-id.iam.gserviceaccount.com --role=roles/artifactregistry.reader
  ```

## Testing

First, install development dependencies:

```bash
pip install -r functions/requirements-dev.txt
```

Running tests using pytest directly:

```bash
# Run all tests with PYTHONPATH set (recommended approach)
cd functions
PYTHONPATH=/path/to/firebase-py-api/functions pytest tests/

# Run unit tests only
PYTHONPATH=/path/to/firebase-py-api/functions pytest tests/unit/

# Run integration tests only
PYTHONPATH=/path/to/firebase-py-api/functions pytest tests/integration/

# Run specific test file
PYTHONPATH=/path/to/firebase-py-api/functions pytest tests/unit/test_user_model.py

# Run specific test function
PYTHONPATH=/path/to/firebase-py-api/functions pytest tests/unit/test_user_model.py::TestUserModel::test_user_initialization

# Run tests with coverage report
PYTHONPATH=/path/to/firebase-py-api/functions pytest --cov=. tests/

# Run tests with verbose output
PYTHONPATH=/path/to/firebase-py-api/functions pytest -v tests/
```

You can also use the provided test runner scripts:

```bash
# Run all tests
python functions/tests/run_tests.py

# Run unit tests only
python functions/tests/run_tests.py --unit

# Run integration tests only
python functions/tests/run_tests.py --integration

# Run specific test file
python functions/tests/run_tests.py -f functions/tests/path/to/test_file.py

# Run tests with coverage report
python functions/tests/run_tests.py --coverage

# Run tests with verbose output
python functions/tests/run_tests.py -v
```

### Note About Testing Environment

The test environment requires proper Python path configuration to resolve module imports correctly. 
The project uses module mocking to handle dependencies during testing, particularly for the `utils` package.

If you encounter import errors, make sure to:
1. Run tests with the PYTHONPATH set to the functions directory
2. Clear any Python cache files if needed with `find . -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true`

See the [Test Suite README](functions/tests/README.md) and [Testing Guide](functions/tests/TESTING_GUIDE.md) for more details on the test structure and how to extend the tests.

## Code Quality

```
# Linting
pylint functions/

# Type checking
mypy functions/
```

## API Endpoints

### Authentication
- `POST /v1/auth/login` - User login with email/password
- `POST /v1/auth/register` - New user registration
- `GET /v1/auth/me` - Get authenticated user profile
- `POST /v1/auth/token` - Login with custom token

### Users
- `GET /v1/users` - List all users
- `GET /v1/users/{userId}` - Get user by Firebase UID
- `POST /v1/users` - Create new user
- `PUT /v1/users/{userId}` - Update user data by Firebase UID (supports base64 profile picture upload)
- `DELETE /v1/users` - Delete current authenticated user
- `DELETE /v1/users/{userId}` - Delete user account by Firebase UID
- `POST /v1/users/{userId}/onboarding` - Update user onboarding status
- `POST /v1/users/photo` - Update user profile photo (supports base64 upload)

### Notifications
- `GET /v1/notifications` - Get user's notifications
- `GET /v1/notifications/unread` - Get unread notification count
- `POST /v1/notifications/{notificationId}/read` - Mark notification as read
- `POST /v1/notifications/read-all` - Mark all notifications as read
- `DELETE /v1/notifications/{notificationId}` - Delete notification
- `POST /v1/devices` - Register device for push notifications
- `DELETE /v1/devices/{deviceId}` - Unregister device from push notifications

### Password Management
- `POST /v1/password/reset-request` - Request password reset
- `POST /v1/password/reset` - Reset password with token
- `POST /v1/password/change` - Change password (authenticated)

## Architecture

The application follows a clean architecture pattern with:
- Repository pattern for data access
- Service layer for business logic
- Middleware for cross-cutting concerns
- Input validation with validators
- Consistent error handling and logging
- Centralized configuration

### API Implementation Pattern

The API uses a consistent Flask pattern with Firebase Functions adapter:

1. **Route Registration**: All routes are registered in the `api/v1/__init__.py` file using Flask decorators:
   ```python
   @flask_app.route(f"{API_PREFIX}/health", methods=['GET'])
   @request_logger
   def flask_health_check():
       from flask import request
       return health_check(request)
   ```

2. **Handler Functions**: The actual handler functions are implemented in their respective module files:
   ```python
   def health_check(req: Any) -> Any:
       """
       Health check endpoint for API monitoring.

       Args:
           req: The Flask request object

       Returns:
           A JSON response with the API health status
       """
       return create_response(
           data={"status": "ok"},
           message="API is running"
       )
   ```

3. **Authentication**: The `require_auth` middleware is applied at the route registration level to secure endpoints

This pattern provides several benefits:
- Separation of route registration from handler implementation
- Consistent request handling across all endpoints
- Simplified testing of handler functions
- Easier maintenance and refactoring

### Data Storage
- **Firestore**: Core application data (users, password_resets, device_tokens)
- **Firebase Realtime Database**: Notifications for real-time updates
- **Firebase Authentication**: User authentication and account management
- **Firebase Storage**: File uploads (profile photos, documents)

### Collections Structure

The application uses the following Firestore collections:
- `users` - User profiles and authentication data
- `password_resets` - Password reset tokens and metadata
- `device_tokens` - Push notification device tokens
- `notifications` - User notifications (also stored in Realtime Database)

### User ID Management

The application uses Firebase UID consistently for user identification:

- **User Document IDs**: Firebase UID is used as the document ID in Firestore
- **API Endpoints**: All user endpoints use Firebase UID in paths: `/{firebase_uid}`
- **Authentication**: The `require_auth` middleware adds the Firebase user info to requests
- **Data Access**: The repository layer directly uses Firebase UID for document lookups

This approach provides several benefits:
- Eliminates the need for separate document IDs and Firebase UIDs
- Simplifies data access with direct document lookups (no queries needed)
- Provides consistency across the authentication and data layers
- Improves performance by avoiding additional queries

### Configuration System

The application uses a centralized configuration system:

1. **Environment Variables**: Loaded from `.env` file
2. **Config Module**: `/functions/config/` handles loading settings
3. **Environment-Specific Config**:
   - `dev.py` - Development environment settings
   - `prod.py` - Production environment settings
   - `settings.py` - Common settings shared across environments

Configure the application by setting the `ENVIRONMENT` variable:

```
ENVIRONMENT=development  # dev.py
ENVIRONMENT=production   # prod.py
ENVIRONMENT=testing      # test-specific settings
```

#### Environment Configuration

The application loads core settings from environment variables and/or config files. Configuration priority:

1. Environment variables (highest priority)
2. Environment-specific config files (`dev.py`, `prod.py`)
3. Common settings (`settings.py`)

Key configuration sections:

```python
# Mailgun Email Settings
MAILGUN_CONFIG = {
    "api_key": "your-mailgun-api-key",
    "domain": "your-mailgun-domain",
    "from_email": "noreply@yourdomain.com",
    "from_name": "Firebase Python API"
}

# Firebase Settings
FIREBASE_CONFIG = {
    "web_api_key": "your-firebase-web-api-key",
    "project_id": "your-project-id",
    "storage_bucket": "your-storage-bucket",
    "database_url": "your-database-url"
}

# Expo Push Notification
EXPO_CONFIG = {
    "token": "your-expo-push-token",
    "push_url": "https://exp.host/--/api/v2/push/send"
}
```

These configuration values are used throughout the application by importing the `CONFIG` object:

```python
from config import CONFIG

# Access configuration values
mailgun_api_key = CONFIG.get("mailgun", {}).get("api_key")
firebase_project_id = CONFIG.get("firebase", {}).get("project_id")
expo_token = CONFIG.get("expo", {}).get("token")
```

#### CORS Configuration

The API supports Cross-Origin Resource Sharing (CORS) for mobile app access. CORS settings are loaded from the central configuration:

```python
# In settings.py
COMMON_CONFIG = {
    # ...
    "cors_origins": ["*"],  # Allow all origins
    "cors_allow_headers": ["Content-Type", "Authorization", ...], 
    "cors_allow_methods": ["GET", "POST", "PUT", "DELETE", ...],
    # ...
}
```

These settings are automatically applied to all API responses.

### Authentication & Authorization

The API uses Firebase Auth for authentication with middleware to validate user requests:

1. **Auth Middleware**: Validates JWT tokens and attaches user information to request objects
2. **Authentication Flow**:
   - The `require_auth` decorator intercepts requests and verifies Firebase ID tokens
   - Upon successful authentication, the user's information (including Firebase UID) is added to the request object
   - API handlers access the authenticated user with `req.user.get("uid")` to get the Firebase UID
3. **API to Database Connection**:
   - The Firebase UID from authentication is used directly as the document ID in Firestore
   - This creates a seamless connection between authentication and data access
   - Endpoints that update user data can use the authenticated user's Firebase UID directly
4. **Error Handling**:
   - 401 Unauthorized: Missing or invalid token
   - 403 Forbidden: Valid token but insufficient permissions
   - 404 Not Found: Valid authentication but user record not found in database

**Required Firebase Version**: Firebase Functions v0.4.0+ is required for proper authentication handling.

For more details on the authentication implementation, see the `middlewares/auth_middleware.py` file.

### Core Components
- **User Management**: Authentication, registration, profile management with base64 image support
- **Password Management**: Secure password reset with email verification
- **File Storage**: Profile photo uploads with Firebase Storage, base64 encoding support, and automatic format detection
- **Notification System**: In-app notifications, push notifications via Expo, and email notifications via Mailgun
- **Device Management**: Push notification device token management

### Tech Stack
- **Firebase Functions** (v0.4.0+): Serverless API hosting
- **Python**: Core language for backend services
- **Firebase Admin SDK**: Firestore and Authentication integration
- **Firebase Realtime Database**: Real-time notification storage
- **Firebase Storage**: File storage with security rules
- **Expo Push Notifications**: Mobile push notification delivery
- **Mailgun**: Email notification service
- **Flask**: Web framework for API endpoints

## Notifications

The application provides multiple notification channels to deliver real-time alerts to users.

### Push Notifications

The application uses Expo Push Notifications to deliver real-time alerts to mobile devices.

#### Push Notification Setup

1. Create an Expo Push Token in your Expo account: https://expo.dev/notifications
2. Add the token to your `.env` file:
   ```
   EXPO_TOKEN=your-expo-push-notification-token
   ```
3. When running the API, the token will be automatically loaded from the environment

#### How Push Notifications Work

1. Mobile clients register their device tokens with the API
2. The backend stores these tokens in Firestore
3. When a notification is triggered, the API:
   - Creates a notification record in the database
   - Sends push notifications to registered devices using Expo Server SDK
   - Handles errors and device token management

### Email Notifications

The application also sends email notifications using Mailgun for key events.

#### Email Notification Setup

1. Create a Mailgun account and get your API key: https://www.mailgun.com/
2. Set up a domain in Mailgun
3. Add the Mailgun configuration to your `.env` file:
   ```
   MAILGUN_API_KEY=your-mailgun-api-key
   MAILGUN_DOMAIN=your-mailgun-domain
   MAILGUN_FROM_EMAIL=noreply@yourdomain.com
   MAILGUN_FROM_NAME=Firebase Python API
   ```

#### How Email Notifications Work

1. The system uses HTML templates stored in `/functions/email_templates/`
2. When a notification is triggered, the API:
   - Creates a notification record in the database
   - Sends a push notification (if device tokens are registered)
   - Sends an email notification using Mailgun
   - Respects user email notification preferences

#### Email Templates

- HTML email templates are stored in `/functions/email_templates/`
- Templates use template variables for dynamic content
- Responsive design for mobile and desktop
- Available templates:
  - `password_reset.html`: For password reset notifications

### Notification Types

- **Password Reset**: When a user requests a password reset
- **Account Activity**: Login notifications and security alerts
- **System Updates**: Maintenance notifications and feature announcements

### Testing Notifications

You can test push notifications with the included test functionality in the notification service.

For testing email notifications, make sure your Mailgun configuration is set up correctly.

## Security

### Firebase Security Rules

The application includes comprehensive security rules for all Firebase services:

#### Firestore Rules (`firestore.rules`)
- Users can only read/write their own data
- Password resets are backend-only accessible
- Device tokens are user-specific
- Notifications are user-specific

#### Storage Rules (`storage.rules`)
- Profile photos: Users can read all, write only their own
- File size limits: 5MB for profile photos, 10MB for general uploads
- Content type validation for images
- User-isolated file access

#### Realtime Database Rules (`database.rules.json`)
- Users can only access their own notifications
- Proper indexing for performance
- Default deny for security

### Authentication Security
- Firebase Auth integration with JWT tokens
- Middleware-based request validation
- User session management
- Secure password reset flow

### File Upload Security
- File size validation
- Content type checking
- User-specific upload paths
- Automatic file cleanup

## API Documentation

The API is documented using OpenAPI Specification. You can find the API specification in the `openapi.yaml` file.

To view the API documentation:
1. Use an OpenAPI viewer like Swagger UI or Redoc
2. Import the `openapi.yaml` file to explore endpoints

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.