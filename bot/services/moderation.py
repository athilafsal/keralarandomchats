"""
Moderation utilities: profanity filter, spam detection
"""
import re
from typing import List

# Basic profanity filter (English keywords - expand as needed)
PROFANITY_WORDS = [
    # Add common profanity words here (keeping minimal for MVP)
    # This should be expanded with Malayalam and other language filters
]

def check_profanity(text: str) -> bool:
    """
    Check if text contains profanity
    Returns True if profanity detected
    """
    text_lower = text.lower()
    for word in PROFANITY_WORDS:
        if word.lower() in text_lower:
            return True
    return False


def detect_contact_info(text: str) -> bool:
    """
    Detect phone numbers, email addresses, or links
    Returns True if contact info detected
    """
    # Phone number patterns (Indian format)
    phone_pattern = r'(\+91[\s-]?)?[6-9]\d{9}'
    # Email pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    # URL pattern
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    
    if re.search(phone_pattern, text) or re.search(email_pattern, text) or re.search(url_pattern, text):
        return True
    return False


def sanitize_message(text: str) -> tuple[str, bool, str]:
    """
    Sanitize and check message
    Returns: (sanitized_text, is_valid, warning_message)
    """
    # Check for profanity
    if check_profanity(text):
        return text, False, "Message contains inappropriate content"
    
    # Check for contact info
    if detect_contact_info(text):
        return text, False, "Sharing contact information is not allowed for your safety"
    
    # Basic sanitization (remove excessive whitespace)
    sanitized = " ".join(text.split())
    
    return sanitized, True, ""

