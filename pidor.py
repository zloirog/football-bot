import os
import random
from datetime import datetime, timedelta
import pytz
from telegram import ChatMember, Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from mistralai import Mistral

from operations.common import execute_query, fetch_query, fetch_one_query
from operations.users import get_user
from utils import is_chat_admin

API_KEY = os.getenv("MISTRAL_API_KEY")
mistral = Mistral(API_KEY)

model = 'mistral-small-latest'

# Create table to track random user selections
def create_random_selection_table():
    execute_query("""
    CREATE TABLE IF NOT EXISTS Random_Selections (
        selection_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        chat_id INTEGER,
        selected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES Users(user_id)
    )
    """)

# Check if a random selection has been made for this chat today
def get_last_selection(chat_id):
    prague_tz = pytz.timezone("Europe/Prague")
    today = datetime.now(prague_tz).replace(hour=0, minute=0, second=0, microsecond=0)
    today_str = today.strftime('%Y-%m-%d 00:00:00')
    
    return fetch_one_query("""
    SELECT * FROM Random_Selections 
    WHERE chat_id = ? AND selected_at >= ?
    ORDER BY selected_at DESC LIMIT 1
    """, (chat_id, today_str))

# Record a new random selection
def record_selection(user_id, chat_id):
    return execute_query("""
    INSERT INTO Random_Selections (user_id, chat_id) 
    VALUES (?, ?)
    """, (user_id, chat_id))

# Get stats about how many times each user has been selected
def get_selection_stats(chat_id):
    return fetch_query("""
    SELECT u.nickname, u.name, COUNT(rs.selection_id) as times_selected
    FROM Random_Selections rs
    JOIN Users u ON rs.user_id = u.user_id
    WHERE rs.chat_id = ?
    GROUP BY rs.user_id
    ORDER BY times_selected DESC
    """, (chat_id,))

async def pick_random_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Make sure we have the random selections table
    create_random_selection_table()
    
    tg_chat_id = update.effective_chat.id
    
    # Check if a selection has already been made today
    last_selection = get_last_selection(tg_chat_id)
    
    if last_selection:
        # Calculate time until next available selection
        prague_tz = pytz.timezone("Europe/Prague")
        today = datetime.now(prague_tz).replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        time_left = tomorrow - datetime.now(prague_tz)
        
        hours, remainder = divmod(time_left.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        user = get_user(last_selection['user_id'])
        
        await update.message.reply_text(
            f"A user has already been selected today: @{user['nickname']} ({user['name']})\n"
            f"Next selection will be available in {hours} hours and {minutes} minutes.",
            parse_mode=ParseMode.HTML
        )
        return
    
    # Get registered users from our database
    try:
        from operations.users import get_all_users_from_db
        
        # Get all registered users
        all_users = get_all_users_from_db()
        chat_members = []
        
        # For each user, check if they're in the chat
        for user_record in all_users:
            try:
                # Try to get this user's chat member status
                member = await context.bot.get_chat_member(tg_chat_id, user_record['user_id'])
                if member["status"] in [ChatMember.OWNER, ChatMember.ADMINISTRATOR, ChatMember.MEMBER] and not member.user.is_bot:
                    chat_members.append(member)
            except Exception as e:
                # Skip users that aren't in this chat
                continue
        
        if not chat_members:
            await update.message.reply_text("No registered users found in this chat.")
            return
        
        # Select a random chat member
        selected_member = random.choice(chat_members)
        user_id = selected_member.user.id
        
        # Record the selection
        record_selection(user_id, tg_chat_id)
        
        user = get_user(user_id)
        
        # Get statistics for this user
        user_stats = fetch_one_query("""
        SELECT COUNT(*) as times_selected
        FROM Random_Selections
        WHERE user_id = ? AND chat_id = ?
        """, (user_id, tg_chat_id))
        
        times_selected = user_stats['times_selected'] if user_stats else 1

        chat_response = mistral.chat.complete(
            model= model,
            messages = [
                {
                    "role": "user",
                    "content": f"Придумай веселый стишок для пользователя @{user['nickname']} ({user['name']}) на тему того, что он выбран п*дором дня. Включи в текст стишка его никнейм с символом @ и имя.",
                },
            ]
        )

        await update.message.reply_text(chat_response.choices[0].message.content)
        
        # await update.message.reply_text(
        #     f"🎲 <b>Pidor of the day is selected:</b> @{user['nickname']} ({user['name']})\n"
        #     f"This user has been selected {times_selected} time(s) in total.",
        #     parse_mode=ParseMode.HTML
        # )
    
    except Exception as e:
        await update.message.reply_text(f"Error selecting random user: {str(e)}")

async def get_random_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Make sure we have the random selections table
    create_random_selection_table()
    
    tg_chat_id = update.effective_chat.id
    
    # Get statistics for all users in this chat
    stats = get_selection_stats(tg_chat_id)
    
    if not stats:
        await update.message.reply_text("No pidors in this chat yet.")
        return
    
    message = "<b>Pidor Statistics:</b>\n\n"
    
    for idx, stat in enumerate(stats, start=1):
        message += f"{idx}. @{stat['nickname']} ({stat['name']}): selected {stat['times_selected']} time(s)\n"
    
    await update.message.reply_text(message, parse_mode=ParseMode.HTML)

async def clear_random_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_chat_admin(update, context):
        return
    
    tg_chat_id = update.effective_chat.id
    
    execute_query("DELETE FROM Random_Selections WHERE chat_id = ?", (tg_chat_id,))
    
    await update.message.reply_text("Random selection statistics have been cleared for this chat.")