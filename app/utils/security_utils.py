"""
Security utilities for input validation, sanitization, and security enhancements.
"""
import re
import html
import logging
from typing import Any, Dict, Optional
from fastapi import HTTPException, status
from urllib.parse import quote
import bleach

logger = logging.getLogger(__name__)

# Security constants
MAX_STRING_LENGTH = 1000

def sanitize_input(text: str, allow_html: bool = False) -> str:
    """
    Sanitize user input to prevent XSS and injection attacks.

    Args:
        text: Input string to sanitize
        allow_html: Whether to allow limited HTML tags (default: False)

    Returns:
        Sanitized string
    """
    if not isinstance(text, str):
        return ""

    # Limit string length to prevent DoS
    if len(text) > MAX_STRING_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Input exceeds maximum allowed length"
        )

    # Basic sanitization - strip whitespace
    text = text.strip()

    # If HTML is not allowed, escape all HTML
    if not allow_html:
        return html.escape(text)

    # If HTML is allowed, use bleach to sanitize and allow only safe tags
    sanitized = bleach.clean(
        text,
        tags=['p', 'br', 'strong', 'em', 'ul', 'ol', 'li'],
        strip=True
    )
    return sanitized


def validate_and_sanitize_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and sanitize all input fields in a data dictionary.

    Args:
        data: Dictionary containing user input data

    Returns:
        Sanitized data dictionary
    """
    sanitized_data = {}

    for key, value in data.items():
        if isinstance(value, str):
            # Apply different sanitization based on field type
            if key in ['email']:
                if validate_email(value):
                    sanitized_data[key] = value
                else:
                    logger.warning(f"Invalid email format: {value}")
                    sanitized_data[key] = ""
            elif key in ['phone']:
                if validate_phone(value):
                    sanitized_data[key] = value
                else:
                    logger.warning(f"Invalid phone format: {value}")
                    sanitized_data[key] = ""
            elif key in ['password']:
                # Don't sanitize passwords, but check length
                if len(value) > MAX_STRING_LENGTH:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Password exceeds maximum allowed length"
                    )
                sanitized_data[key] = value
            else:
                sanitized_data[key] = sanitize_input(value)
        elif isinstance(value, dict):
            sanitized_data[key] = validate_and_sanitize_input(value)
        elif isinstance(value, list):
            sanitized_data[key] = [validate_and_sanitize_input(item) if isinstance(item, dict) else item for item in value]
        else:
            sanitized_data[key] = value

    return sanitized_data


def validate_email(email: str) -> bool:
    """
    Validate email format with additional security checks.

    Args:
        email: Email string to validate

    Returns:
        True if valid, False otherwise
    """
    if not email or len(email) > 254:  # RFC 5321 limit
        return False

    # Basic email format validation
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        return False

    # Check for suspicious patterns
    if re.search(r'[\x00-\x1f\x7f-\x9f]', email):  # Control characters
        return False

    return True


def validate_phone(phone: str) -> bool:
    """
    Validate phone number format with security checks.

    Args:
        phone: Phone number string to validate

    Returns:
        True if valid, False otherwise
    """
    if not phone:
        return False

    # Check for control characters and excessive length
    if len(phone) > 20 or re.search(r'[\x00-\x1f\x7f-\x9f]', phone):
        return False

    # Validate E.164 format (already in schema but double-checking)
    phone_regex = r'^\+?[1-9]\d{9,14}$'
    return bool(re.match(phone_regex, phone))


def log_security_event(event_type: str, details: Dict[str, Any], user_id: Optional[int] = None) -> None:
    """
    Log security-related events for monitoring.

    Args:
        event_type: Type of security event
        details: Event details
        user_id: Optional user ID
    """
    security_event = {
        "event_type": event_type,
        "user_id": user_id,
        "details": details
    }
    logger.warning(f"Security event: {security_event}")