import asyncio
from datetime import datetime, timedelta
from pyrogram import filters
from pyrogram.types import Message

import config
from AnonXMusic import app
from AnonXMusic.misc import SUDOERS
from AnonXMusic.utils.database import get_top_groups_by_requests, get_served_chats
from AnonXMusic.utils.decorators.language import language
from config import BANNED_USERS

@app.on_message(filters.command(["topgc", "topgroups"]) & ~BANNED_USERS)
@language
async def top_groups_command(client, message: Message, _):
    """Show top 10 groups by song requests"""
    
    # Send initial message
    msg = await message.reply_text("🔍 **Fetching top groups data...**")
    
    try:
        # Get top groups from database
        top_groups = await get_top_groups_by_requests(10)
        
        if not top_groups:
            return await msg.edit_text(
                "❌ **No group statistics found!**\n\n"
                "*Groups need to request songs to appear in rankings.*"
            )
        
        # Build the ranking message
        text = f"🏆 **TOP 10 GROUPS BY SONG REQUESTS**\n\n"
        text += f"📊 **Ranked by total song requests**\n"
        text += f"🎵 **Bot:** {app.mention}\n\n"
        
        # Add rankings
        for i, group in enumerate(top_groups, 1):
            chat_id = group.get("chat_id", "Unknown")
            chat_title = group.get("chat_title", "Unknown Group")
            total_requests = group.get("total_requests", 0)
            last_request = group.get("last_request")
            last_query = group.get("last_query", "Unknown")
            
            # Truncate long group names
            if len(chat_title) > 25:
                chat_title = chat_title[:22] + "..."
            
            # Truncate long queries
            if len(last_query) > 20:
                last_query = last_query[:17] + "..."
            
            # Format last request time
            if last_request:
                try:
                    if isinstance(last_request, str):
                        time_str = "Recently"
                    else:
                        # Calculate time difference
                        now = datetime.now()
                        diff = now - last_request
                        
                        if diff.days > 0:
                            time_str = f"{diff.days}d ago"
                        elif diff.seconds > 3600:
                            hours = diff.seconds // 3600
                            time_str = f"{hours}h ago"
                        elif diff.seconds > 60:
                            minutes = diff.seconds // 60
                            time_str = f"{minutes}m ago"
                        else:
                            time_str = "Just now"
                except:
                    time_str = "Unknown"
            else:
                time_str = "Unknown"
            
            # Add ranking emoji
            if i == 1:
                emoji = "🥇"
            elif i == 2:
                emoji = "🥈"
            elif i == 3:
                emoji = "🥉"
            else:
                emoji = f"{i}."
            
            text += f"{emoji} **{chat_title}**\n"
            text += f"    ├ 🎵 Requests: `{total_requests:,}`\n"
            text += f"    ├ 🎤 Last Song: `{last_query}`\n"
            text += f"    └ ⏰ Last Active: `{time_str}`\n\n"
        
        # Add footer
        try:
            total_served = len(await get_served_chats())
            text += f"📈 **Total Served Groups:** `{total_served:,}`\n"
        except:
            text += f"📈 **Active Groups:** `{len(top_groups)}`\n"
        
        text += f"🔄 **Updated:** `{datetime.now().strftime('%d/%m/%Y %H:%M')}`\n"
        text += f"💡 **Tip:** Use `/stats` for bot statistics"
        
        # Send the ranking
        await msg.edit_text(text, disable_web_page_preview=True)
        
    except Exception as e:
        await msg.edit_text(
            f"❌ **Error occurred while fetching data!**\n\n"
            f"**Error:** `{str(e)}`\n\n"
            f"*Please try again later or contact support.*"
        )

# Optional: Add a detailed group stats command for admins/sudoers
@app.on_message(filters.command(["groupstats"]) & filters.group & ~BANNED_USERS)
@language
async def group_stats_command(client, message: Message, _):
    """Show detailed stats for current group"""
    
    if message.from_user.id not in SUDOERS:
        return await message.reply_text("❌ **This command is only for sudo users.**")
    
    try:
        from AnonXMusic.utils.database import get_group_request_stats
        
        stats = await get_group_request_stats(message.chat.id)
        
        if not stats:
            return await message.reply_text("❌ **No statistics found for this group.**")
        
        # Get today's requests
        today = datetime.now().strftime("%Y-%m-%d")
        today_requests = stats.get("daily_requests", {}).get(today, 0)
        
        # Get top user
        top_users = stats.get("top_users", {})
        if top_users:
            top_user_id = max(top_users.keys(), key=lambda x: top_users[x])
            top_user_requests = top_users[top_user_id]
        else:
            top_user_id = "Unknown"
            top_user_requests = 0
        
        text = f"📊 **GROUP STATISTICS**\n\n"
        text += f"🏷 **Group:** {stats.get('chat_title', 'Unknown')}\n"
        text += f"🆔 **Chat ID:** `{stats.get('chat_id')}`\n\n"
        text += f"🎵 **Total Requests:** `{stats.get('total_requests', 0):,}`\n"
        text += f"📅 **Today's Requests:** `{today_requests}`\n"
        text += f"👑 **Top User ID:** `{top_user_id}` (`{top_user_requests}` requests)\n\n"
        text += f"🎤 **Last Song:** `{stats.get('last_query', 'Unknown')}`\n"
        text += f"⏰ **Last Request:** `{stats.get('last_request', 'Unknown')}`"
        
        await message.reply_text(text, disable_web_page_preview=True)
        
    except Exception as e:
        await message.reply_text(f"❌ **Error:** `{str(e)}`")
