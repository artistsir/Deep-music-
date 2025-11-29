import os
import asyncio
import logging
import time
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    API_ID = int(os.getenv("API_ID", 1234567))
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    MONGO_URL = os.getenv("MONGO_URL", "")
    ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
    SESSION_STRING = os.getenv("SESSION_STRING", "")
    ASSISTANT_ID = int(os.getenv("ASSISTANT_ID", 0))
    PORT = int(os.getenv("PORT", 8080))

# String Session Generator Function
async def generate_string_session():
    """String session generate karta hai agar .env file mein na ho"""
    print("\n" + "="*60)
    print("🔐 STRING SESSION GENERATOR")
    print("="*60)
    
    API_ID = input("📋 Enter your API_ID: ").strip()
    API_HASH = input("📋 Enter your API_HASH: ").strip()
    
    if not API_ID or not API_HASH:
        print("❌ API_ID aur API_HASH required hai!")
        return None
    
    try:
        API_ID = int(API_ID)
    except ValueError:
        print("❌ API_ID number hona chahiye!")
        return None
    
    print(f"\n🔧 API Details:")
    print(f"   API ID: {API_ID}")
    print(f"   API Hash: {API_HASH}")
    
    input("\n📍 Press Enter continue karne ke liye...")
    
    try:
        from pyrogram import Client
        
        async with Client(
            "user_session",
            api_id=API_ID,
            api_hash=API_HASH
        ) as app:
            print("\n🔑 Login Required:")
            print("   Aapko ab apna phone number aur verification code enter karna hoga")
            
            # Session generate karo
            string_session = await app.export_session_string()
            
            print("\n" + "="*60)
            print("✅ STRING SESSION GENERATED SUCCESSFULLY!")
            print("="*60)
            
            print(f"\n🔐 Your String Session:")
            print("="*50)
            print(string_session)
            print("="*50)
            
            # User details
            me = await app.get_me()
            print(f"\n👤 Account Details:")
            print(f"   Name: {me.first_name} {me.last_name or ''}")
            print(f"   Username: @{me.username}" if me.username else "   Username: None")
            print(f"   User ID: {me.id}")
            print(f"   Phone: {me.phone_number}")
            
            # .env file update karo
            env_content = f"""# Telegram API Credentials
API_ID={API_ID}
API_HASH={API_HASH}

# Bot Token from @BotFather
BOT_TOKEN=your_bot_token_here

# MongoDB Connection String
MONGO_URL=your_mongodb_connection_string_here

# Your Telegram User ID (Admin)
ADMIN_ID=your_user_id_here

# String Session (generated automatically)
SESSION_STRING={string_session}

# Assistant Bot ID (Optional)
ASSISTANT_ID=assistant_bot_id_here

# Web Server Port
PORT=8080
"""
            
            with open(".env", "w") as f:
                f.write(env_content)
            
            print(f"\n💾 .env file update ho gaya!")
            print("📝 Ab aap .env file mein BOT_TOKEN aur MONGO_URL add kar sakte hain")
            
            return string_session
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\n💡 Possible Solutions:")
        print("   1. API_ID aur API_HASH check karo")
        print("   2. Internet connection check karo")
        print("   3. Phone number sahi enter karo")
        print("   4. Verification code sahi enter karo")
        return None

# Check if session generation required
if len(sys.argv) > 1 and sys.argv[1] == "generate_session":
    print("🚀 Starting String Session Generator...")
    generated_session = asyncio.run(generate_string_session())
    
    if generated_session:
        print("\n🎉 Process Complete!")
        print("📋 Next Steps:")
        print("   1. .env file mein BOT_TOKEN aur MONGO_URL add karo")
        print("   2. Run: python main.py (bot start karne ke liye)")
    else:
        print("\n❌ Session generation failed!")
    
    sys.exit(0)

# Continue with main bot code if session exists
if not Config.SESSION_STRING:
    print("\n❌ SESSION_STRING .env file mein nahi hai!")
    print("💡 String session generate karne ke liye:")
    print("   python main.py generate_session")
    print("\n📝 Ya manually .env file mein SESSION_STRING add karo")
    sys.exit(1)

# Check other required environment variables
required_vars = ["API_ID", "API_HASH", "BOT_TOKEN", "MONGO_URL"]
missing_vars = [var for var in required_vars if not getattr(Config, var, None)]

if missing_vars:
    logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    print(f"\n❌ Missing environment variables: {', '.join(missing_vars)}")
    print("💡 .env file check karo aur saare required variables add karo")
    sys.exit(1)

# Import remaining modules after session check
import yt_dlp
from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatType, MessageEntityType
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped
from pytgcalls.types.input_stream import AudioParameters
from pytgcalls.types import StreamAudioEnded
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from aiohttp import web

# MongoDB Setup
try:
    mongo_client = MongoClient(Config.MONGO_URL, serverSelectionTimeoutMS=5000)
    mongo_client.server_info()  # Test connection
    db = mongo_client["music_bot"]
    users_collection = db["users"]
    playlists_collection = db["playlists"]
    history_collection = db["history"]
    logger.info("✅ MongoDB Connected Successfully!")
except ConnectionFailure as e:
    logger.error(f"❌ MongoDB Connection Failed: {e}")
    print(f"❌ MongoDB Connection Failed: {e}")
    sys.exit(1)

# Music Player Class
class MusicPlayer:
    def __init__(self):
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'ytsearch',
            'source_address': '0.0.0.0',
            'extractaudio': True,
            'audioformat': 'mp3',
            'noprogress': True
        }
    
    async def get_song_info(self, query: str):
        """YouTube se song information fetch karta hai"""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(query, download=False)
                
                if 'entries' in info:
                    info = info['entries'][0]
                
                return {
                    'title': info.get('title', 'Unknown Title'),
                    'url': info.get('url'),
                    'duration': info.get('duration', 0),
                    'thumbnail': info.get('thumbnail'),
                    'uploader': info.get('uploader', 'Unknown Artist'),
                    'webpage_url': info.get('webpage_url', ''),
                    'id': info.get('id', '')
                }
        except Exception as e:
            logger.error(f"Error getting song info: {e}")
            return None
    
    async def search_songs(self, query: str, limit: int = 5):
        """Multiple songs search karta hai"""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
                
                songs = []
                for entry in info['entries']:
                    if entry:
                        songs.append({
                            'title': entry.get('title', 'Unknown'),
                            'url': entry.get('url'),
                            'duration': self.format_duration(entry.get('duration', 0)),
                            'uploader': entry.get('uploader', 'Unknown')
                        })
                return songs
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def format_duration(self, duration: int):
        """Duration ko format karta hai"""
        if not duration:
            return "Unknown"
        minutes, seconds = divmod(duration, 60)
        return f"{minutes}:{seconds:02d}"

# Initialize Music Player
music_player = MusicPlayer()

# Active chats track karne ke liye
active_chats = {}
queues = {}

# Global variables for clients
bot_client = None
user_client = None
call_py = None
start_time = time.time()

# Database Functions
def add_user(user_id, username, first_name):
    user_data = {
        "user_id": user_id,
        "username": username,
        "first_name": first_name,
        "joined_date": datetime.now(),
        "total_songs_played": 0,
        "is_banned": False,
        "last_active": datetime.now()
    }
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": user_data},
        upsert=True
    )

def add_to_history(chat_id, user_id, song_name, song_url):
    history_data = {
        "chat_id": chat_id,
        "user_id": user_id,
        "song_name": song_name,
        "song_url": song_url,
        "timestamp": datetime.now()
    }
    history_collection.insert_one(history_data)

def get_user_stats(user_id):
    return users_collection.find_one({"user_id": user_id})

def update_song_count(user_id):
    users_collection.update_one(
        {"user_id": user_id},
        {"$inc": {"total_songs_played": 1}},
        upsert=True
    )

# Stream End Handler
async def stream_end_handler(_, update):
    if isinstance(update, StreamAudioEnded):
        chat_id = update.chat_id
        logger.info(f"Stream ended in chat {chat_id}")
        await play_next_in_queue(chat_id)

async def play_next_in_queue(chat_id):
    """Queue mein next song play karta hai"""
    try:
        if chat_id in queues and queues[chat_id]:
            next_song = queues[chat_id].pop(0)
            song_info = await music_player.get_song_info(next_song['query'])
            
            if song_info:
                await call_py.change_stream(
                    chat_id,
                    AudioPiped(
                        song_info['url'],
                        AudioParameters(
                            bitrate=48000,
                        )
                    )
                )
                
                # History mein add karo
                add_to_history(chat_id, next_song['user_id'], song_info['title'], song_info['url'])
                update_song_count(next_song['user_id'])
                
                # Now playing message
                now_playing_text = f"""
🎵 **Now Playing:** {song_info['title']}
👤 **Requested By:** {next_song['user_name']}
⏱ **Duration:** {music_player.format_duration(song_info['duration'])}
🔗 **Source:** YouTube
                """
                
                await bot_client.send_message(chat_id, now_playing_text)
                
                # Update active chat
                if chat_id in active_chats:
                    active_chats[chat_id]['now_playing'] = song_info['title']
        else:
            # Queue empty, leave voice chat
            if chat_id in active_chats:
                active_chats[chat_id]['is_playing'] = False
                active_chats[chat_id]['now_playing'] = None
    except Exception as e:
        logger.error(f"Error playing next song: {e}")

# Web Server for Health Checks
async def health_check(request):
    """Health check endpoint for Render"""
    try:
        # Check MongoDB connection
        mongo_client.server_info()
        
        # Check if bots are running
        bot_status = await bot_client.get_me() if bot_client else None
        user_status = await user_client.get_me() if user_client else None
        
        status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "uptime": get_uptime(),
            "mongo_db": "connected",
            "bot_client": "running" if bot_status else "stopped",
            "user_client": "running" if user_status else "stopped",
            "active_chats": len(active_chats),
            "total_queues": sum(len(q) for q in queues.values())
        }
        
        return web.json_response(status)
    
    except Exception as e:
        error_status = {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        return web.json_response(error_status, status=500)

async def root_handler(request):
    """Root endpoint"""
    return web.json_response({
        "message": "Telegram Music Bot is running!",
        "status": "active",
        "uptime": get_uptime(),
        "version": "1.0.0"
    })

def get_uptime():
    """Calculate bot uptime"""
    uptime_seconds = int(time.time() - start_time)
    hours = uptime_seconds // 3600
    minutes = (uptime_seconds % 3600) // 60
    seconds = uptime_seconds % 60
    return f"{hours}h {minutes}m {seconds}s"

# Bot Handlers
def setup_handlers():
    """All bot handlers setup karta hai"""
    
    @bot_client.on_message(filters.command("start"))
    async def start_command(client, message: Message):
        user = message.from_user
        add_user(user.id, user.username, user.first_name)
        
        welcome_text = """
🎵 **Welcome to Advanced Music Bot!** 🎵

**I'm a powerful Telegram Voice Chat Music Bot with these features:**

✨ **Main Commands:**
/play [song] - Play a song
/stream [url] - Stream from URL  
/pause - Pause music
/resume - Resume music
/skip - Skip current song
/stop - Stop music
/queue - Show queue

📋 **Playlist Commands:**
/playlist - Your playlists
/create [name] - Create playlist
/add [name] [song] - Add to playlist

👨‍💻 **Admin Commands:**
/auth [user_id] - Authorize user
/unauth [user_id] - Unauthorize user
/stats - Bot statistics

🔍 **Other Commands:**
/search [song] - Search songs
/lyrics [song] - Get lyrics
/ping - Bot status

**⚡ Powered by:** Pyrogram & PyTgCalls
**👨‍💻 Developer:** Your Name

Use /help for detailed command info!
        """
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📚 Commands Help", callback_data="help_commands"),
             InlineKeyboardButton("🎵 Support Group", url="https://t.me/your_group")],
            [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/your_id"),
             InlineKeyboardButton("⭐ Rate Bot", callback_data="rate_bot")]
        ])
        
        await message.reply_text(welcome_text, reply_markup=keyboard)

    @bot_client.on_callback_query(filters.regex("help_commands"))
    async def help_callback(client, callback_query):
        help_text = """
**📚 All Available Commands:**

**🎵 Music Commands:**
/play [song name] - Play a song
/stream [url] - Stream from URL
/song [song name] - Download song
/lyrics [song name] - Get song lyrics

**⏯ Playback Controls:**
/pause - Pause music
/resume - Resume music  
/skip - Skip current song
/stop - Stop music
/volume [1-200] - Change volume

**📋 Queue Management:**
/queue - Show current queue
/shuffle - Shuffle queue
/clear - Clear queue

**📁 Playlist Management:**
/playlist - Your playlists
/create [name] - Create playlist
/delete [name] - Delete playlist
/add [name] [song] - Add to playlist
/remove [name] [number] - Remove from playlist

**👨‍💻 Admin Commands:**
/auth [user_id] - Authorize user
/unauth [user_id] - Unauthorize user
/banned - Show banned users
/stats - Bot statistics

**🔍 Utility Commands:**
/search [query] - Search songs
/ping - Check bot status
/help - This message
        """
        
        await callback_query.message.edit_text(help_text)

    @bot_client.on_message(filters.command("play"))
    async def play_command(client, message: Message):
        if len(message.command) < 2:
            await message.reply_text("""
❌ **Invalid Usage!**

**Correct Usage:** 
`/play song name`
`/play https://youtube.com/...`

**Examples:**
`/play shape of you`
`/play https://youtube.com/watch?v=xyz`
            """)
            return
        
        user = message.from_user
        query = " ".join(message.command[1:])
        
        # Check if user is in voice chat
        if not message.chat.id:
            await message.reply_text("❌ Please join a voice chat first!")
            return
        
        await message.reply_text("🔍 **Searching for your song...**")
        
        # Get song information
        song_info = await music_player.get_song_info(query)
        
        if not song_info:
            await message.reply_text("❌ Song not found! Please try another search.")
            return
        
        # Initialize queues
        if message.chat.id not in queues:
            queues[message.chat.id] = []
        
        if message.chat.id not in active_chats:
            active_chats[message.chat.id] = {
                'now_playing': None,
                'is_playing': False
            }
        
        # Add to queue
        queues[message.chat.id].append({
            'query': query,
            'user_id': user.id,
            'user_name': user.first_name
        })
        
        # If not playing, start playing
        if not active_chats[message.chat.id]['is_playing']:
            try:
                await call_py.join_group_call(
                    message.chat.id,
                    AudioPiped(
                        song_info['url'],
                        AudioParameters(
                            bitrate=48000,
                        )
                    )
                )
                
                active_chats[message.chat.id]['is_playing'] = True
                active_chats[message.chat.id]['now_playing'] = song_info['title']
                
                # Add to history and update count
                add_to_history(message.chat.id, user.id, song_info['title'], song_info['url'])
                update_song_count(user.id)
                
                # Now playing message
                now_playing_text = f"""
🎵 **Now Playing:** {song_info['title']}
👤 **Requested By:** {user.first_name}
⏱ **Duration:** {music_player.format_duration(song_info['duration'])}
🔗 **Source:** YouTube

💫 **Enjoy the music!** 🎧
                """
                
                await message.reply_text(now_playing_text)
                
            except Exception as e:
                logger.error(f"Error joining voice chat: {e}")
                await message.reply_text("❌ Error joining voice chat! Make sure I'm added as admin.")
        else:
            # Already playing, just add to queue
            queue_position = len(queues[message.chat.id])
            await message.reply_text(f"✅ **Added to queue at position #{queue_position}**")

    # ... (Other command handlers same as before)

# Main function
async def main():
    global bot_client, user_client, call_py
    
    # Create downloads directory
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
    if not os.path.exists("temp"):
        os.makedirs("temp")
    
    logger.info("🎵 Starting Advanced Music Bot...")
    
    try:
        # Initialize clients
        bot_client = Client(
            "music_bot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN
        )
        
        user_client = Client(
            "user_session",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            session_string=Config.SESSION_STRING
        )
        
        # PyTgCalls setup user client ke saath
        call_py = PyTgCalls(user_client)
        
        # Setup stream end handler
        call_py.on_stream_end()(stream_end_handler)
        
        # Start web server
        app = web.Application()
        app.router.add_get('/', root_handler)
        app.router.add_get('/health', health_check)
        
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(runner, '0.0.0.0', Config.PORT)
        await site.start()
        logger.info(f"🌐 Web server started on port {Config.PORT}")
        
        # Start both clients
        await bot_client.start()
        logger.info("✅ Bot Client Started!")
        
        await user_client.start()
        logger.info("✅ User Client Started!")
        
        await call_py.start()
        logger.info("✅ PyTgCalls Started!")
        
        # Setup handlers
        setup_handlers()
        
        # Bot info
        bot = await bot_client.get_me()
        user = await user_client.get_me()
        
        logger.info(f"🤖 Bot: @{bot.username}")
        logger.info(f"👤 User: {user.first_name}")
        logger.info("🚀 Bot is now running...")
        
        # Send startup message to admin
        if Config.ADMIN_ID:
            try:
                await bot_client.send_message(
                    Config.ADMIN_ID,
                    f"✅ **Music Bot Started Successfully!**\n\n"
                    f"🤖 **Bot:** @{bot.username}\n"
                    f"👤 **Assistant:** {user.first_name}\n"
                    f"⏰ **Start Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"🌐 **Web Server:** Running on port {Config.PORT}\n"
                    f"🔧 **Status:** Running on Render with Docker\n\n"
                    f"**Ready to play music!** 🎵"
                )
            except Exception as e:
                logger.warning(f"Could not send startup message to admin: {e}")
        
        # Keep running
        while True:
            await asyncio.sleep(3600)  # Sleep for 1 hour
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
    finally:
        # Cleanup
        if bot_client:
            await bot_client.stop()
        if user_client:
            await user_client.stop()
        logger.info("Bot stopped!")

if __name__ == "__main__":
    # Check if session generation requested
    if len(sys.argv) > 1 and sys.argv[1] == "generate_session":
        asyncio.run(generate_string_session())
    else:
        # Normal bot startup
        asyncio.run(main())