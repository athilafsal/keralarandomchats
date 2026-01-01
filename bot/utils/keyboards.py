"""
Inline keyboard utilities for Telegram bot
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config.constants import (
    GENDER_MALE, GENDER_FEMALE, GENDER_OTHER, GENDER_PREFER_NOT_SAY,
    LANGUAGE_MALAYALAM, LANGUAGE_ENGLISH, LANGUAGE_HINDI, LANGUAGE_ANY
)


def get_gender_keyboard():
    """Get inline keyboard for gender selection"""
    keyboard = [
        [
            InlineKeyboardButton("👨 Male", callback_data="gender_1"),
            InlineKeyboardButton("👩 Female", callback_data="gender_2"),
        ],
        [
            InlineKeyboardButton("⚧️ Other", callback_data="gender_3"),
            InlineKeyboardButton("🚫 Prefer not to say", callback_data="gender_4"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_language_keyboard():
    """Get inline keyboard for language selection"""
    keyboard = [
        [
            InlineKeyboardButton("🇮🇳 Malayalam", callback_data="lang_malayalam"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_english"),
        ],
        [
            InlineKeyboardButton("🇮🇳 Hindi", callback_data="lang_hindi"),
            InlineKeyboardButton("🌍 Any", callback_data="lang_any"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_age_range_keyboard():
    """Get inline keyboard for age range selection"""
    keyboard = [
        [
            InlineKeyboardButton("18-24", callback_data="age_18-24"),
            InlineKeyboardButton("25-34", callback_data="age_25-34"),
        ],
        [
            InlineKeyboardButton("35-44", callback_data="age_35-44"),
            InlineKeyboardButton("45+", callback_data="age_45+"),
        ],
        [
            InlineKeyboardButton("Any", callback_data="age_any"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_main_menu_keyboard():
    """Get main menu keyboard (when not in chat)"""
    keyboard = [
        [
            InlineKeyboardButton("🔍 Find Chat", callback_data="find_chat"),
            InlineKeyboardButton("📊 My Stats", callback_data="my_stats"),
        ],
        [
            InlineKeyboardButton("🔗 Invite Friends", callback_data="invite"),
            InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
        ],
        [
            InlineKeyboardButton("ℹ️ Help", callback_data="help"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_chat_actions_keyboard():
    """Get keyboard for actions during active chat"""
    keyboard = [
        [
            InlineKeyboardButton("⏹️ Stop Chat", callback_data="stop_chat"),
            InlineKeyboardButton("⏭️ Next Person", callback_data="next_person"),
        ],
        [
            InlineKeyboardButton("🚫 Block", callback_data="block_user"),
            InlineKeyboardButton("⚠️ Report", callback_data="report_user"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_waiting_keyboard():
    """Get keyboard shown while waiting for match"""
    keyboard = [
        [
            InlineKeyboardButton("❌ Cancel Search", callback_data="cancel_search"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_admin_keyboard():
    """Get admin panel keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("👥 Online Users", callback_data="admin_list_online"),
            InlineKeyboardButton("📊 Statistics", callback_data="admin_stats"),
        ],
        [
            InlineKeyboardButton("🔍 View Pair", callback_data="admin_view_pair_menu"),
            InlineKeyboardButton("🔗 Force Pair", callback_data="admin_force_pair_menu"),
        ],
        [
            InlineKeyboardButton("🚫 Ban User", callback_data="admin_ban_menu"),
            InlineKeyboardButton("✅ Unban User", callback_data="admin_unban_menu"),
        ],
        [
            InlineKeyboardButton("🔌 Disconnect", callback_data="admin_disconnect_menu"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_settings_keyboard():
    """Get settings keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("🌐 Change Language", callback_data="settings_language"),
            InlineKeyboardButton("👤 Edit Profile", callback_data="settings_profile"),
        ],
        [
            InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_skip_keyboard():
    """Get skip button for optional fields"""
    keyboard = [
        [
            InlineKeyboardButton("⏭️ Skip", callback_data="skip"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_confirm_keyboard(action: str, data: str = ""):
    """Get confirmation keyboard for actions"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes", callback_data=f"confirm_{action}_{data}"),
            InlineKeyboardButton("❌ No", callback_data="cancel"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

