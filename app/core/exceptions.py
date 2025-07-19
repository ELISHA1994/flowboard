"""
Custom exceptions for the application
"""


class BaseException(Exception):
    """Base exception class"""
    pass


class NotFoundException(BaseException):
    """Raised when a resource is not found"""
    pass


class BadRequestException(BaseException):
    """Raised when the request is invalid"""
    pass


class ConflictException(BaseException):
    """Raised when there's a conflict (e.g., duplicate resource)"""
    pass


class UnauthorizedException(BaseException):
    """Raised when the user is not authorized"""
    pass


class ForbiddenException(BaseException):
    """Raised when the user doesn't have permission"""
    pass


class ValidationException(BaseException):
    """Raised when validation fails"""
    pass