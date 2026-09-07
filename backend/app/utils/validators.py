"""
Input validation utilities for sanitizing and validating user input
before it reaches any agent or LLM prompt.
"""

import re
from typing import Optional

from app.core.exceptions import ValidationError

# Character allowlist for patient messages (Urdu + English + common punctuation)
ALLOWED_CHARS_PATTERN = re.compile(
    r"^[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF"  # Arabic/Urdu
    r"a-zA-Z0-9\s\.\,\!\?\-\(\)\/\:\'\"]+$"  # English + punctuation
)

# Max lengths for different input types
MAX_MESSAGE_LENGTH = 2000
MAX_SYMPTOM_LENGTH = 200
MAX_NAME_LENGTH = 100


def sanitize_text(text: str, max_length: int = MAX_MESSAGE_LENGTH) -> str:
    """
    Sanitize free-text input by removing potentially dangerous characters.

    Args:
        text: Raw input text
        max_length: Maximum allowed length

    Returns:
        Sanitized text

    Raises:
        ValidationError: If text exceeds max length or contains invalid characters
    """
    if not text or not text.strip():
        raise ValidationError("Input text cannot be empty")

    if len(text) > max_length:
        raise ValidationError(
            f"Input text exceeds maximum length of {max_length} characters"
        )

    # Strip leading/trailing whitespace
    cleaned = text.strip()

    # Remove any control characters except newlines and tabs
    cleaned = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", cleaned)

    return cleaned


def validate_phone_number(phone: str) -> str:
    """
    Validate and normalize phone number format.

    Args:
        phone: Phone number string

    Returns:
        Normalized phone number with country code

    Raises:
        ValidationError: If phone number is invalid
    """
    # Remove spaces, dashes, and parentheses
    cleaned = re.sub(r"[\s\-\(\)]", "", phone)

    # Must start with + or digits
    if not re.match(r"^\+?[0-9]{10,15}$", cleaned):
        raise ValidationError("Invalid phone number format")

    # Add Pakistan country code if missing
    if cleaned.startswith("0"):
        cleaned = "+92" + cleaned[1:]
    elif not cleaned.startswith("+"):
        cleaned = "+" + cleaned

    return cleaned


def validate_location(latitude: Optional[float], longitude: Optional[float]) -> None:
    """
    Validate geographic coordinates.

    Args:
        latitude: Latitude in degrees (-90 to 90)
        longitude: Longitude in degrees (-180 to 180)

    Raises:
        ValidationError: If coordinates are out of valid range
    """
    if latitude is not None and (latitude < -90 or latitude > 90):
        raise ValidationError("Latitude must be between -90 and 90 degrees")

    if longitude is not None and (longitude < -180 or longitude > 180):
        raise ValidationError("Longitude must be between -180 and 180 degrees")
