"""Custom exceptions for parser service."""


class ApiRequestError(Exception):
    """Exception for API request failures."""
    
    def __init__(self, source: str, reason: str = "unknown error"):
        super().__init__(f"API request failed for {source}: {reason}")
        self.source = source
        self.reason = reason


class DataValidationError(Exception):
    """Exception for data validation failures."""
    
    def __init__(self, message: str = "Data validation failed"):
        super().__init__(message)