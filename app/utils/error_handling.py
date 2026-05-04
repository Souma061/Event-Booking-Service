"""
Enhanced error handling and logging for the Event Booking Service.
"""
import logging
from fastapi import HTTPException, status
from typing import Dict, Any

from app.utils.security_utils import log_security_event

logger = logging.getLogger(__name__)

class AppHTTPException(HTTPException):
    """
    Custom HTTP exception with enhanced logging and security features.
    """
    def __init__(self, status_code: int, detail: str, log_event: bool = True,
                 event_data: Dict[str, Any] = None, user_id: int = None):
        super().__init__(status_code=status_code, detail=detail)
        self.log_event = log_event
        self.event_data = event_data or {}
        self.user_id = user_id

    def log_error(self, error_type: str, additional_data: Dict[str, Any] = None):
        """
        Log the error with security context.

        Args:
            error_type: Type of error for logging
            additional_data: Additional data to include in the log
        """
        if self.log_event:
            data = self.event_data or {}
            data.update(additional_data or {})
            log_security_event(error_type, data, self.user_id)

class ErrorLogger:
    """
    Comprehensive error logging utility.
    """

    @staticmethod
    def log_validation_error(field: str, value: str, user_id: int = None):
        """Log validation errors."""
        log_security_event("validation_error", {
            "field": field,
            "value": value,
            "reason": "input_validation_failed"
        }, user_id)

    @staticmethod
    def log_authentication_error(attempt_type: str, reason: str, user_id: int = None):
        """Log authentication-related errors."""
        log_security_event("authentication_error", {
            "attempt_type": attempt_type,
            "reason": reason
        }, user_id)

    @staticmethod
    def log_rate_limit_error(endpoint: str, client_ip: str, user_id: int = None):
        """Log rate limit violations."""
        log_security_event("rate_limit_violation", {
            "endpoint": endpoint,
            "client_ip": client_ip
        }, user_id)

    @staticmethod
    def log_security_violation(violation_type: str, details: Dict[str, Any], user_id: int = None):
        """Log security violations."""
        log_security_event(f"security_{violation_type}", details, user_id)

# Custom exception classes for specific error types
class ValidationError(AppHTTPException):
    """Custom validation error."""
    def __init__(self, field: str, value: str, user_id: int = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field}: {value}",
            event_data={
                "field": field,
                "value": value
            },
            user_id=user_id
        )
        self.field = field
        self.value = value

class AuthenticationError(AppHTTPException):
    """Custom authentication error."""
    def __init__(self, reason: str = "authentication_failed", user_id: int = None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            event_data={"reason": reason},
            user_id=user_id
        )

class AuthorizationError(AppHTTPException):
    """Custom authorization error."""
    def __init__(self, reason: str = "insufficient_privileges", user_id: int = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
            event_data={"reason": reason},
            user_id=user_id
        )

class RateLimitError(AppHTTPException):
    """Custom rate limit error."""
    def __init__(self, endpoint: str, client_ip: str, user_id: int = None):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later.",
            event_data={
                "endpoint": endpoint,
                "client_ip": client_ip
            },
            user_id=user_id
        )
        ErrorLogger.log_rate_limit_error(endpoint, client_ip, user_id)

# Exception handler functions
def handle_validation_error(field: str, value: str, user_id: int = None):
    """Handle and log validation errors."""
    ErrorLogger.log_validation_error(field, value, user_id)
    return ValidationError(field, value, user_id)

def handle_authentication_error(reason: str, user_id: int = None):
    """Handle and log authentication errors."""
    ErrorLogger.log_authentication_error("authentication", reason, user_id)
    return AuthenticationError(reason, user_id)

def handle_authorization_error(reason: str, user_id: int = None):
    """Handle and log authorization errors."""
    ErrorLogger.log_authentication_error("authorization", reason, user_id)
    return AuthorizationError(reason, user_id)

def handle_rate_limit_error(endpoint: str, client_ip: str, user_id: int = None):
    """Handle and log rate limit errors."""
    ErrorLogger.log_rate_limit_error(endpoint, client_ip, user_id)
    return RateLimitError(endpoint, client_ip, user_id)