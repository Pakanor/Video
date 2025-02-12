from django.contrib.auth.password_validation import validate_password

from django.core.exceptions import ValidationError


class CustomValidationErrorPassword(ValidationError):
    """Custom validation error with predefined messages."""

    def __init__(self, message=None, code=None, params=None):
        default_message = "Password to weak"
        super().__init__(message or default_message, code, params)


class WeakPasswordError(Exception):
    pass


def custom_validate_password(password):
    try:
        validate_password(password)
    except ValidationError:
        raise WeakPasswordError(
            "Your password is not strong enough. Please try again.")


class Login_or_email_in_use(Exception):
    def __str__(self):
        return "Login or email already in use"
