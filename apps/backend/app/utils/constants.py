"""Application constants"""

# Task related constants
MAX_TASKS_PER_USER = 100
MAX_TASK_TITLE_LENGTH = 200
MAX_TASK_DESCRIPTION_LENGTH = 1000

# User related constants
MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 50
MIN_PASSWORD_LENGTH = 6

# Pagination defaults
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100

# API Response messages
MSG_SUCCESS = "Operation completed successfully"
MSG_CREATED = "Resource created successfully"
MSG_UPDATED = "Resource updated successfully"
MSG_DELETED = "Resource deleted successfully"
MSG_NOT_FOUND = "Resource not found"
MSG_UNAUTHORIZED = "Unauthorized access"
MSG_FORBIDDEN = "Forbidden action"