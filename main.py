import os
import pytz
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, CallbackContext
from bans import ban, get_all_bans_command, get_my_bans, unban
from date_utils import get_next_weekday
from operations.chats import get_all_chats
from utils import refresh_message, show_registration_message, last_match
from register_funcs import register_himself, register_another_from_chat, register_plus_one, confirm
from remove_funcs import remove, remove_plus_one, remove_other
from jobs_funcs import get_jobs, start_repeating_job, stop_repeating_job, start
from constants import reply_markup


TOKEN = os.getenv("TG_TOKEN")

async def info(update: Update, context: CallbackContext):
    await update.message.reply_text("""Запись проходит автоматически каждую среду в 12 часов дня.
- Что бы зарегистрировать своего другана из чата который, например, занят, нужно написать `/register @druzhok` (druzhok надо заменить на ник своего товарища)
- Твой дружок должен будет в течении следующих трех часов подтвердить запись написав в чат `/confirm` иначе дружок с тобой на футбол не пойдет.
- `/last_match` покажет кто играл в прошлой игре

Остальное не важно, и почитай регламент в файлах.
                              """)


def initiate(application): 
    chats = get_all_chats()

    for chat in chats:
        now = pytz.timezone("Europe/Prague").localize(datetime.datetime.now())
        next_weekday = get_next_weekday(chat['reg_week_day'], chat['reg_time'])
        if next_weekday < now:
            next_weekday += datetime.timedelta(days=7)
        initial_delay = (next_weekday - now).total_seconds()

        weekly_interval = 7 * 24 * 60 * 60  # 7 days in seconds

        job_data = {
        'chat_id': chat['chat_id'],
        }

        application.job_queue.run_repeating(
            start,
            interval=weekly_interval,
            first=initial_delay,
            data=job_data,
            name=chat['chat_id']
        )

# Main function
def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start_repeating_job))
    application.add_handler(CommandHandler("stop", stop_repeating_job))
    application.add_handler(CommandHandler("ban", ban))
    application.add_handler(CommandHandler("unban", unban))
    application.add_handler(CommandHandler("get_my_bans", get_my_bans))
    application.add_handler(CommandHandler("get_all_bans", get_all_bans_command))


    application.add_handler(CommandHandler(
        "show_registration_message", show_registration_message))

    application.add_handler(CommandHandler("register_another_from_chat", register_another_from_chat))
    application.add_handler(CommandHandler("last_match", last_match))
    application.add_handler(CommandHandler("remove_other", remove_other))
    application.add_handler(CommandHandler("confirm", confirm))
    application.add_handler(CommandHandler("get_jobs", get_jobs))

    callback_mapping = {
        'register': register_himself,
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
                [InlineKeyboardButton(
                    "Yes, confirm quit", callback_data='quit_confirm')],
                [InlineKeyboardButton("No, cancel", callback_data='cancel')],
            ]
            confirm_reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_reply_markup(reply_markup=confirm_reply_markup)

        if data == 'remove_plus_one':
            keyboard = [
                [InlineKeyboardButton(
                    "Yes, confirm quit for  ➕ 1️⃣", callback_data='remove_plus_one_confirm')],
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

    initiate(application)

    application.run_polling()
    application.idle()


if __name__ == '__main__':
    main()
