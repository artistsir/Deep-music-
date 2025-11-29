from pyrogram import Client
import os
from dotenv import load_dotenv

load_dotenv()

async def generate_string_session():
    API_ID = int(os.getenv("API_ID", 1234567))
    API_HASH = os.getenv("API_HASH", "")
    
    if not API_ID or not API_HASH:
        print("❌ API_ID aur API_HASH .env file mein set karo!")
        return
    
    print("📱 String Session Generator")
    print("=" * 30)
    
    async with Client(
        "user_session",
        api_id=API_ID,
        api_hash=API_HASH
    ) as app:
        string_session = await app.export_session_string()
        
        print(f"\n✅ **String Session Generated Successfully!**")
        print(f"🔐 **Your String Session:**")
        print(f"`{string_session}`")
        print(f"\n📝 **Isse .env file mein SESSION_STRING ke value mein paste karo:**")
        print(f"SESSION_STRING={string_session}")
        
        # Session details
        me = await app.get_me()
        print(f"\n👤 **Logged in as:** {me.first_name}")
        print(f"📞 **Phone:** {me.phone_number}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(generate_string_session())
