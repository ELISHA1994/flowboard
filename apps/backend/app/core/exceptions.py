"""
Custom exceptions for the application
"""


class BaseException(Exception):
    """Base exception class"""


class NotFoundException(BaseException):
    """Raised when a resource is not found"""


class BadRequestException(BaseException):
    """Raised when the request is invalid"""


class ConflictException(BaseException):
    """Raised when there's a conflict (e.g., duplicate resource)"""


class UnauthorizedException(BaseException):
    """Raised when the user is not authorized"""


class ForbiddenException(BaseException):
    """Raised when the user doesn't have permission"""


class ValidationException(BaseException):
    """Raised when validation fails"""


class CacheError(BaseException):
    """Raised when cache operations fail"""


class NotFoundError(NotFoundException):
    """Alias for NotFoundException for backward compatibility"""


class PermissionDeniedError(ForbiddenException):
    """Alias for ForbiddenException for backward compatibility"""
