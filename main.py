import json
import datetime
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, CallbackContext
from match_files import load_data, save_data, load_last_match, save_last_match, LAST_MATCH_FILE, DATA_FILE
from date_utils import next_saturday
from register_funcs import register, register_old, register_plus_one, can_user_register
from remove_funcs import remove, remove_plus_one, remove_other
from jobs_funcs import get_jobs, start_repeating_job, stop_repeating_job
from constants import MAX_PLAYERS, PRIORITY_HOURS, DATA_FILE, LAST_MATCH_FILE, CHAT_ID, reply_markup
from utils import get_message, is_chat_admin

async def show_registration_message(update: Update, context: CallbackContext):
    if not await is_chat_admin(update, context):
        return

    chat_id = update.effective_chat.id

    sent_message = await context.bot.send_message(chat_id=chat_id, text=get_message(), reply_markup=reply_markup, parse_mode=ParseMode.HTML)


async def confirm(update: Update, context:ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not data:
        await update.message.reply_text("No games available.")
        return

    game_id = list(data.keys())[-1]
    game = data[game_id]
    user = update.message.from_user.username

    for list_name in ["players", "waiting_list"]:
        for idx, player in enumerate(game[list_name]):
            if player['name'] == user and player['confirmed'] == False:
                player['confirmed'] = True
                save_data(data)
                await update.message.reply_text(f"{user} confirmed his registration.")
                await query.edit_message_text(text=get_message(), reply_markup=reply_markup, parse_mode=ParseMode.HTML)
                return

    await update.message.reply_text(f"{user}, buddy, you don't need to confirm anything.")

async def last_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    last_match_players = load_last_match()

    if not last_match_players:
        await update.message.reply_text("No last match data available.")
        return

    message = "<b>Last Match Players:</b>\n"
    for idx, player in enumerate(last_match_players):
        message += f"{idx + 1}. @{player['name']}\n"

    await update.message.reply_text(message, parse_mode=ParseMode.HTML)


async def info(update: Update, context: CallbackContext):
        await update.message.reply_text("""Запись проходит автоматически каждую среду в 12 часов дня.
- Что бы зарегистрировать своего другана из чата который, например, занят, нужно написать `/register @druzhok` (druzhok надо заменить на ник своего товарища)
- Твой дружок должен будет в течении следующих трех часов подтвердить запись написав в чат `/confirm` иначе дружок с тобой на футбол не пойдет.
- `/last_match` покажет кто играл в прошлой игре

Остальное не важно, и почитай регламент в файлах.
                              """)

async def refresh_message(update: Update, context: CallbackContext):
    query = update.callback_query
    try:
        await query.edit_message_text(text=get_message(), reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    except:
        print("No update")
        return


# Main function
def main():
    application = Application.builder().token(os.getenv('TG_TOKEN')).build()

    application.add_handler(CommandHandler("start", start_repeating_job))
    application.add_handler(CommandHandler("stop", stop_repeating_job))

    application.add_handler(CommandHandler("show_registration_message", show_registration_message))

    application.add_handler(CommandHandler("register", register_old))
    application.add_handler(CommandHandler("quit", remove))
    application.add_handler(CommandHandler("last_match", last_match))
    application.add_handler(CommandHandler("save_last_match", save_last_match))
    application.add_handler(CommandHandler("remove_other", remove_other))
    application.add_handler(CommandHandler("confirm", confirm))
    application.add_handler(CommandHandler("get_jobs", get_jobs))


    callback_mapping = {
        'register': register,
        'register_plus_one': register_plus_one,
        'quit_confirm': remove,
        'refresh_message': refresh_message,
        'remove_plus_one_confirm': remove_plus_one
    }

    async def callback_query_handler(update: Update, context: CallbackContext) -> None:
        query = update.callback_query
        # Get the callback data
        data = query.data
        if data == 'quit':
            keyboard = [
                [InlineKeyboardButton("Yes, confirm quit", callback_data='quit_confirm')],
                [InlineKeyboardButton("No, cancel", callback_data='cancel')],
            ]
            confirm_reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_reply_markup(reply_markup=confirm_reply_markup)
        
        if data == 'remove_plus_one':
            keyboard = [
                [InlineKeyboardButton("Yes, confirm quit for  ➕ 1️⃣", callback_data='remove_plus_one_confirm')],
                [InlineKeyboardButton("No, cancel", callback_data='cancel')],
            ]
            confirm_reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_reply_markup(reply_markup=confirm_reply_markup)
            
        if data == 'cancel':
            await query.edit_message_reply_markup(reply_markup=reply_markup)
            
            
        # Call the corresponding function
        if data in callback_mapping:
           await callback_mapping[data](update, context)

    application.add_handler(CallbackQueryHandler(callback_query_handler))

    now = datetime.datetime.now()
    next_wednesday = now + datetime.timedelta((2 - now.weekday() + 7) % 7)  # 2 for Wednesday
    next_wednesday = datetime.datetime.combine(next_wednesday, datetime.time(10, 0))
    if next_wednesday < now:
        next_wednesday += datetime.timedelta(days=7)
    initial_delay = (next_wednesday - now).total_seconds()

    # Schedule job to run every week
    weekly_interval = 7 * 24 * 60 * 60  # 7 days in seconds

    job_data = {
        'chat_id': CHAT_ID,
    }

    application.job_queue.run_repeating(
        start,
        interval=weekly_interval,
        first=initial_delay,
        data=job_data,
        name=str(CHAT_ID)
    )

    application.run_polling()
    application.idle()

if __name__ == '__main__':
    main()
