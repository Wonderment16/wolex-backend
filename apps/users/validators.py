from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class SymbolNumberPasswordValidator:
    """Validates that the password meets product requirements:
    - at least 8 characters (MinimumLengthValidator also handles this)
    - contains at least one digit
    - contains at least one non-alphanumeric symbol
    """

    def validate(self, password, user=None):
        if password is None:
            return
        if len(password) < 8:
            raise ValidationError(
                _("This password must contain at least 8 characters."),
                code='password_too_short',
            )
        if not any(c.isdigit() for c in password):
            raise ValidationError(
                _("This password must contain at least one digit."),
                code='password_no_number',
            )
        if password.isalnum():
            raise ValidationError(
                _("This password must contain at least one symbol (non-alphanumeric character)."),
                code='password_no_symbol',
            )

    def get_help_text(self):
        return _(
            "Your password must be at least 8 characters long, contain at least one digit, "
            "and at least one symbol."
        )
