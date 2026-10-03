"""
Email Validation Utility
RFC 5322 compliant regex and heuristic verification.
"""
import re

EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$"
)

DISALLOWED_DOMAINS = {'tempmail.com', 'throwaway.io', '10minutemail.com'}

def is_valid_email(email: str) -> bool:
    """Returns True if the email is structurally valid and non-disposable."""
    if not email or not isinstance(email, str):
        return False
    email = email.strip()
    if len(email) > 254:
        return False
    if not EMAIL_REGEX.match(email):
        return False
    domain = email.split('@')[-1].lower()
    if domain in DISALLOWED_DOMAINS:
        return False
    return True
