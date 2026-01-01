"""
Constants for the Telegram Anonymous Chat Bot
"""

# Gender codes
GENDER_UNKNOWN = 0
GENDER_MALE = 1
GENDER_FEMALE = 2
GENDER_OTHER = 3
GENDER_PREFER_NOT_SAY = 4

GENDER_MAP = {
    GENDER_UNKNOWN: "Unknown",
    GENDER_MALE: "Male",
    GENDER_FEMALE: "Female",
    GENDER_OTHER: "Other",
    GENDER_PREFER_NOT_SAY: "Prefer not to say"
}

# Language preferences
LANGUAGE_MALAYALAM = "malayalam"
LANGUAGE_ENGLISH = "english"
LANGUAGE_HINDI = "hindi"
LANGUAGE_ANY = "any"

AVAILABLE_LANGUAGES = [LANGUAGE_MALAYALAM, LANGUAGE_ENGLISH, LANGUAGE_HINDI, LANGUAGE_ANY]

# User states
USER_STATE_ONBOARDING = "onboarding"
USER_STATE_WAITING = "waiting"
USER_STATE_CHATTING = "chatting"
USER_STATE_IDLE = "idle"

# Matchmaking constants
MATCH_TIMEOUT_SECONDS = 30  # Fallback to 'any' after 30 seconds
MAX_DISPLAY_NAME_LENGTH = 32
MAX_MESSAGES_PER_MINUTE = 10
PAIR_INACTIVITY_MINUTES = 5  # Auto-disconnect after 5 min inactivity
PAIR_EXPIRATION_HOURS = 24  # Cleanup pairs older than 24h

# Referral system
REFERRAL_UNLOCK_THRESHOLD = 5  # Number of referrals needed to unlock features
PARTNER_PREFERENCE_UNLOCK_THRESHOLD = 3  # Number of referrals needed to unlock partner preference
REFERRAL_PAYLOAD_PREFIX = "ref_"
ADMIN_PAYLOAD_PREFIX = "admin_"

# Admin session
ADMIN_SESSION_DURATION_HOURS = 2

# Moderation
MESSAGE_RETENTION_DAYS = 7
PROFANITY_WARNING_THRESHOLD = 3  # Temp ban after 3 violations
REPORT_CONVERSATION_EXCERPT_SIZE = 20  # Last N messages to include in report

# Redis queue keys
REDIS_QUEUE_PREFIX = "waiting"
REDIS_USER_STATE_PREFIX = "user_state"
REDIS_RATE_LIMIT_PREFIX = "rate_limit"

