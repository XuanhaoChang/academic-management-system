class BusinessError(Exception):
    """Base class for all business-domain errors."""


class AuthError(BusinessError):
    pass


class PermissionDeniedError(BusinessError):
    pass


class ValidationError(BusinessError):
    pass
