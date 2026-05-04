"""
Input validation and sanitization utilities for the Event Booking Service.
"""
from fastapi import Request, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any
import re
import html
from app.utils.security_utils import validate_and_sanitize_input, sanitize_input

class InputValidationMiddleware:
    """
    Middleware to validate and sanitize input for all incoming requests.
    """

    @staticmethod
    def validate_input_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and sanitize input data before processing.

        Args:
            data: Dictionary containing user input data

        Returns:
            Sanitized data dictionary
        """
        return validate_and_sanitize_input(data)

    @staticmethod
    def validate_full_name(name: str) -> str:
        """
        Validate and sanitize full name input.

        Args:
            name: Full name string to validate

        Returns:
            Sanitized name string
        """
        if not name or not isinstance(name, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Full name is required"
            )

        # Check for excessive length
        if len(name) > 120:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Full name exceeds maximum allowed length"
            )

        # Basic sanitization with HTML escaping
        sanitized = html.escape(name.strip())
        return sanitized

    @staticmethod
    def validate_description(description: str) -> str:
        """
        Validate and sanitize description input.

        Args:
            description: Description string to validate

        Returns:
            Sanitized description string
        """
        if not description:
            return ""

        # Check for excessive length
        if len(description) > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Description exceeds maximum allowed length"
            )

        # Sanitize with HTML escaping
        sanitized = html.escape(description.strip())
        return sanitized

    @staticmethod
    def validate_category(category: str) -> str:
        """
        Validate and sanitize category input.

        Args:
            category: Category string to validate

        Returns:
            Sanitized category string
        """
        if not category or not isinstance(category, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category is required"
            )

        # Check for excessive length
        if len(category) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category exceeds maximum allowed length"
            )

        # Basic sanitization
        sanitized = html.escape(category.strip())
        return sanitized