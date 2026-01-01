"""
Quick script to test if a bot token is valid.
Run this locally (not on Railway) to verify your token works.
"""
import asyncio
import os
from telegram import Bot
from telegram.error import InvalidToken, TelegramError

async def test_token():
    # Get token from environment or paste here for testing (delete after!)
    token = os.getenv("BOT_TOKEN", "")
    
    if not token:
        print("❌ No token found. Set BOT_TOKEN environment variable or edit this script.")
        print("\nTo test:")
        print("  export BOT_TOKEN='your_token_here'")
        print("  python test_token.py")
        return
    
    print(f"Testing token: {token[:10]}...{token[-5:]}")
    print("Connecting to Telegram...")
    
    try:
        bot = Bot(token=token)
        bot_info = await bot.get_me()
        print(f"\n✅ Token is VALID!")
        print(f"Bot username: @{bot_info.username}")
        print(f"Bot name: {bot_info.first_name}")
        print(f"Bot ID: {bot_info.id}")
        print("\n✅ You can use this token in Railway!")
    except InvalidToken:
        print("\n❌ Token is INVALID or REVOKED")
        print("Get a new token from @BotFather: https://t.me/BotFather")
    except TelegramError as e:
        print(f"\n❌ Error: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(test_token())

