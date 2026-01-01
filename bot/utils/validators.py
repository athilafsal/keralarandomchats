"""
Input validation utilities
"""
from config.constants import MAX_DISPLAY_NAME_LENGTH


def validate_display_name(name: str) -> tuple[bool, str]:
    """
    Validate display name
    Returns: (is_valid, error_message)
    """
    if not name:
        return True, ""  # Display name is optional
    
    if len(name) > MAX_DISPLAY_NAME_LENGTH:
        return False, f"Display name must be {MAX_DISPLAY_NAME_LENGTH} characters or less"
    
    # Check for only whitespace
    if name.strip() == "":
        return False, "Display name cannot be only whitespace"
    
    return True, ""


def validate_age_range(age_range: str) -> tuple[bool, str]:
    """
    Validate age range format
    Expected format: "18-25" or "26-35", etc.
    Returns: (is_valid, error_message)
    """
    if not age_range:
        return True, ""  # Age range is optional
    
    try:
        parts = age_range.split("-")
        if len(parts) != 2:
            return False, "Age range must be in format '18-25'"
        
        start, end = int(parts[0]), int(parts[1])
        if start < 13 or end > 100:
            return False, "Age range must be between 13 and 100"
        if start >= end:
            return False, "Start age must be less than end age"
        
        return True, ""
    except ValueError:
        return False, "Age range must contain valid numbers"


def sanitize_text(text: str) -> str:
    """
    Basic text sanitization
    """
    # Remove excessive whitespace
    return " ".join(text.split())

