"""Repository module for data access abstraction."""
from repositories.firestore.user_repo import FirestoreUserRepository
from repositories.realtime_database.notification_repo import RealtimeDatabaseNotificationRepository
from repositories.firestore.password_reset_repo import FirestorePasswordResetRepository

# Factory functions to get the appropriate repository implementations
def get_user_repository():
    """Returns the configured user repository implementation."""
    return FirestoreUserRepository()

def get_notification_repository():
    """Returns the configured notification repository implementation."""
    return RealtimeDatabaseNotificationRepository()

def get_password_reset_repository():
    """Returns the configured password reset repository implementation."""
    return FirestorePasswordResetRepository()

