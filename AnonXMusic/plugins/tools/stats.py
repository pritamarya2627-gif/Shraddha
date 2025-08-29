

import platform
from sys import version as pyver
from collections import Counter
from datetime import datetime

import psutil
from pyrogram import __version__ as pyrover
from pyrogram import filters
from pyrogram.errors import MessageIdInvalid
from pyrogram.types import InputMediaPhoto, Message
from pytgcalls.__version__ import __version__ as pytgver

import config
from AnonXMusic import app
from AnonXMusic.core.userbot import assistants
from AnonXMusic.misc import SUDOERS, mongodb
from AnonXMusic.plugins import ALL_MODULES
from AnonXMusic.utils.database import get_served_chats, get_served_users, get_sudoers
from AnonXMusic.utils.decorators.language import language, languageCB
from AnonXMusic.utils.inline.stats import back_stats_buttons, stats_buttons
from config import BANNED_USERS


@app.on_message(filters.command(["stats", "gstats"]) & filters.group & ~BANNED_USERS)
@language
async def stats_global(client, message: Message, _):
    upl = stats_buttons(_, True if message.from_user.id in SUDOERS else False)
    await message.reply_photo(
        photo=config.STATS_IMG_URL,
        caption=_["gstats_2"].format(app.mention),
        reply_markup=upl,
    )


@app.on_callback_query(filters.regex("stats_back") & ~BANNED_USERS)
@languageCB
async def home_stats(client, CallbackQuery, _):
    upl = stats_buttons(_, True if CallbackQuery.from_user.id in SUDOERS else False)
    await CallbackQuery.edit_message_text(
        text=_["gstats_2"].format(app.mention),
        reply_markup=upl,
    )


@app.on_callback_query(filters.regex("TopOverall") & ~BANNED_USERS)
@languageCB
async def overall_stats(client, CallbackQuery, _):
    await CallbackQuery.answer()
    upl = back_stats_buttons(_)
    try:
        await CallbackQuery.answer()
    except:
        pass
    await CallbackQuery.edit_message_text(_["gstats_1"].format(app.mention))
    served_chats = len(await get_served_chats())
    served_users = len(await get_served_users())
    text = _["gstats_3"].format(
        app.mention,
        len(assistants),
        len(BANNED_USERS),
        served_chats,
        served_users,
        len(ALL_MODULES),
        len(SUDOERS),
        config.AUTO_LEAVING_ASSISTANT,
        config.DURATION_LIMIT_MIN,
    )
    med = InputMediaPhoto(media=config.STATS_IMG_URL, caption=text)
    try:
        await CallbackQuery.edit_message_media(media=med, reply_markup=upl)
    except MessageIdInvalid:
        await CallbackQuery.message.reply_photo(
            photo=config.STATS_IMG_URL, caption=text, reply_markup=upl
        )


@app.on_callback_query(filters.regex("bot_stats_sudo"))
@languageCB
async def bot_stats(client, CallbackQuery, _):
    if CallbackQuery.from_user.id not in SUDOERS:
        return await CallbackQuery.answer(_["gstats_4"], show_alert=True)
    upl = back_stats_buttons(_)
    try:
        await CallbackQuery.answer()
    except:
        pass
    await CallbackQuery.edit_message_text(_["gstats_1"].format(app.mention))
    p_core = psutil.cpu_count(logical=False)
    t_core = psutil.cpu_count(logical=True)
    ram = str(round(psutil.virtual_memory().total / (1024.0**3))) + " ɢʙ"
    try:
        cpu_freq = psutil.cpu_freq().current
        if cpu_freq >= 1000:
            cpu_freq = f"{round(cpu_freq / 1000, 2)}ɢʜᴢ"
        else:
            cpu_freq = f"{round(cpu_freq, 2)}ᴍʜᴢ"
    except:
        cpu_freq = "ғᴀɪʟᴇᴅ ᴛᴏ ғᴇᴛᴄʜ"
    hdd = psutil.disk_usage("/")
    total = hdd.total / (1024.0**3)
    used = hdd.used / (1024.0**3)
    free = hdd.free / (1024.0**3)
    call = await mongodb.command("dbstats")
    datasize = call["dataSize"] / 1024
    storage = call["storageSize"] / 1024
    served_chats = len(await get_served_chats())
    served_users = len(await get_served_users())
    text = _["gstats_5"].format(
        app.mention,
        len(ALL_MODULES),
        platform.system(),
        ram,
        p_core,
        t_core,
        cpu_freq,
        pyver.split()[0],
        pyrover,
        pytgver,
        str(total)[:4],
        str(used)[:4],
        str(free)[:4],
        served_chats,
        served_users,
        len(BANNED_USERS),
        len(await get_sudoers()),
        str(datasize)[:6],
        storage,
        call["collections"],
        call["objects"],
    )
    med = InputMediaPhoto(media=config.STATS_IMG_URL, caption=text)
    try:
        await CallbackQuery.edit_message_media(media=med, reply_markup=upl)
    except MessageIdInvalid:
        await CallbackQuery.message.reply_photo(
            photo=config.STATS_IMG_URL, caption=text, reply_markup=upl
        )


# New function to get group play stats from database
async def get_group_play_stats(chat_id):
    """Get play count for a specific group"""
    try:
        collection = mongodb["played_stats"]
        result = await collection.find_one({"chat_id": chat_id})
        return result["play_count"] if result else 0
    except Exception:
        return 0


# New function to get top groups by play count
async def get_top_groups():
    """Get top 10 groups by play count"""
    try:
        collection = mongodb["played_stats"]
        pipeline = [
            {"$sort": {"play_count": -1}},
            {"$limit": 10}
        ]
        cursor = collection.aggregate(pipeline)
        top_groups = []
        async for doc in cursor:
            try:
                chat_info = await app.get_chat(doc["chat_id"])
                top_groups.append({
                    "chat_id": doc["chat_id"],
                    "chat_title": chat_info.title,
                    "play_count": doc["play_count"]
                })
            except Exception:
                # If can't get chat info, use chat_id as title
                top_groups.append({
                    "chat_id": doc["chat_id"],
                    "chat_title": f"Group {doc['chat_id']}",
                    "play_count": doc["play_count"]
                })
        return top_groups
    except Exception:
        return []


@app.on_message(filters.command(["check"]) & ~BANNED_USERS)
@language
async def check_group_stats(client, message: Message, _):
    """Check play stats for a specific group"""
    if len(message.command) != 2:
        return await message.reply_text(
            "**Usage:** `/check <chat_id>`\n\n"
            "**Example:** `/check -1001234567890`\n\n"
            "Use this command to see how many songs have been played in a specific group.\n\n"
            "💡 **Tip:** You can use `/check 0` to check current group stats."
        )
    
    # Handle current group check
    if message.command[1] == "0":
        chat_id = message.chat.id
    else:
        try:
            chat_id = int(message.command[1])
        except ValueError:
            return await message.reply_text(
                "❌ **Invalid Chat ID!**\n\n"
                "Please provide a valid numeric chat ID or use `0` for current group.\n"
                "**Example:** `/check -1001234567890` or `/check 0`"
            )
    
    # Initialize demo data if database is empty
    await init_demo_data()
    
    # Get play count for the specified group
    play_count = await get_group_play_stats(chat_id)
    
    try:
        # Try to get group information
        chat_info = await app.get_chat(chat_id)
        chat_title = chat_info.title
        chat_type = "Group" if chat_info.type.name in ["GROUP", "SUPERGROUP"] else "Chat"
    except Exception:
        chat_title = f"Chat {chat_id}"
        chat_type = "Unknown"
    
    # Add some emoji based on play count
    if play_count == 0:
        emoji = "😴"
        status = "No songs played yet"
    elif play_count < 10:
        emoji = "🎵"
        status = "Just getting started"
    elif play_count < 50:
        emoji = "🎶"
        status = "Music lover group"
    elif play_count < 100:
        emoji = "🔥"
        status = "Active music group"
    else:
        emoji = "🏆"
        status = "Music champion group"
    
    text = (
        f"📊 **Play Statistics** {emoji}\n\n"
        f"🏷️ **{chat_type}:** `{chat_title}`\n"
        f"🆔 **Chat ID:** `{chat_id}`\n"
        f"🎵 **Songs Played:** `{play_count}`\n"
        f"📈 **Status:** `{status}`\n\n"
        f"🤖 **Checked by:** {app.mention}"
    )
    
    await loading_msg.edit_text(text)
    await message.reply_photo(
        photo=config.STATS_IMG_URL,
        caption=text
    )


@app.on_message(filters.command(["toplistgroup", "topgroups"]) & ~BANNED_USERS)
@language
async def top_groups_stats(client, message: Message, _):
    """Show top 10 groups by play count"""
    loading_msg = await message.reply_text("🔍 **Fetching top groups data...**")
    
    try:
        top_groups = await get_top_groups()
        
        if not top_groups:
            await loading_msg.edit_text(
                "📊 **No Data Available**\n\n"
                "No group statistics found in the database."
            )
            return
        
        text = f"🏆 **Top Groups by Songs Played**\n\n"
        
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        
        for i, group in enumerate(top_groups):
            medal = medals[i] if i < len(medals) else f"{i+1}."
            chat_title = group["chat_title"]
            play_count = group["play_count"]
            
            # Truncate long group names
            if len(chat_title) > 25:
                chat_title = chat_title[:22] + "..."
            
            text += f"{medal} **{chat_title}**\n"
            text += f"    └ 🎵 `{play_count}` songs played\n\n"
        
        text += f"🤖 **Generated by:** {app.mention}\n"
        text += f"📈 **Total Groups Tracked:** `{len(top_groups)}`"
        
        await loading_msg.edit_text(text, disable_web_page_preview=True)
        
    except Exception as e:
        await loading_msg.edit_text(
            f"❌ **Error occurred while fetching data**\n\n"
            f"Please try again later or contact administrators."
        )


# Helper function to increment play count (call this when a song is played)
async def increment_group_play_count(chat_id):
    """Increment play count for a group - call this when a song starts playing"""
    try:
        collection = mongodb["played_stats"]
        await collection.update_one(
            {"chat_id": chat_id},
            {"$inc": {"play_count": 1}},
            upsert=True
        )
        print(f"✅ Play count incremented for chat {chat_id}")
    except Exception as e:
        print(f"❌ Error incrementing play count: {e}")


# Function to automatically save play data when music starts
async def save_play_data(chat_id, user_id, song_title=None):
    """Save play data to database when song starts"""
    try:
        # Increment group play count
        await increment_group_play_count(chat_id)
        
        # Also save individual play record with timestamp
        collection = mongodb["play_history"]
        play_record = {
            "chat_id": chat_id,
            "user_id": user_id,
            "song_title": song_title,
            "played_at": datetime.utcnow(),
            "date": datetime.utcnow().strftime("%Y-%m-%d")
        }
        await collection.insert_one(play_record)
        
    except Exception as e:
        print(f"❌ Error saving play data: {e}")


# Initialize some demo data if database is empty (for testing)
async def init_demo_data():
    """Initialize demo data for testing purposes"""
    try:
        collection = mongodb["played_stats"]
        count = await collection.count_documents({})
        
        if count == 0:
            # Add some demo data
            demo_data = [
                {"chat_id": -1001234567890, "play_count": 145},
                {"chat_id": -1001234567891, "play_count": 89},
                {"chat_id": -1001234567892, "play_count": 67},
                {"chat_id": -1001234567893, "play_count": 45},
                {"chat_id": -1001234567894, "play_count": 32},
            ]
            await collection.insert_many(demo_data)
            print("✅ Demo data initialized")
    except Exception as e:
        print(f"❌ Error initializing demo data: {e}")


# Command to reset group stats (sudo only)
@app.on_message(filters.command(["resetstats"]) & SUDOERS & ~BANNED_USERS)
@language
async def reset_group_stats(client, message: Message, _):
    """Reset play statistics for a specific group (sudo only)"""
    if len(message.command) != 2:
        return await message.reply_text(
            "**Usage:** `/resetstats <chat_id>`\n\n"
            "**Example:** `/resetstats -1001234567890`\n\n"
            "⚠️ This will reset all play statistics for the specified group."
        )
    
    try:
        chat_id = int(message.command[1])
    except ValueError:
        return await message.reply_text(
            "❌ **Invalid Chat ID!**\n\n"
            "Please provide a valid numeric chat ID."
        )
    
    try:
        collection = mongodb["played_stats"]
        result = await collection.delete_one({"chat_id": chat_id})
        
        if result.deleted_count > 0:
            await message.reply_text(
                f"✅ **Statistics Reset Successfully!**\n\n"
                f"Play count for chat `{chat_id}` has been reset to 0."
            )
        else:
            await message.reply_text(
                f"ℹ️ **No Data Found**\n\n"
                f"No statistics found for chat `{chat_id}`."
            )
    except Exception as e:
        await message.reply_text(
            f"❌ **Error occurred while resetting stats**\n\n"
            f"Please try again later."
        )
