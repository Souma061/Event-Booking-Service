"""
Security middleware for adding security headers to responses.
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    """

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
        except Exception as e:
            logger.exception(f"Error processing request: {e}")
            # Create a basic response to ensure we still send security headers
            response = Response(
                content="Internal Server Error",
                status_code=500
            )

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response
    