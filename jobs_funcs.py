from operations.chats import create_chat, delete_chat, get_chat
from operations.matches import create_match
from utils import is_chat_admin
from date_utils import get_next_weekday, get_current_time
from constants import reply_markup, DATETIME_FORMAT

from telegram import Update
from telegram.ext import CallbackContext

async def get_jobs(update: Update, context: CallbackContext):
    jobs = context.job_queue.jobs()

    job_info = ""
    for job in jobs:
        job_info += repr(job)
        job_info += job.next_t.strftime(DATETIME_FORMAT) + "\n"

    await update.message.reply_text("Current jobs: \n" + job_info)

async def start(context: CallbackContext):
    job_data = context.job.data
    chat_id = job_data['chat_id']

    chat_data = get_chat(chat_id)

    next_match_datetime = get_next_weekday(chat_data['game_week_day'], chat_data['game_time'])
    create_match(next_match_datetime, 130, chat_id)

    formatted_game_time = next_match_datetime.strftime("%d.%m.%Y %H:%M")

    sent_message = await context.bot.send_message(chat_id=chat_id, text=f"Registration is now open! \nGame time: {formatted_game_time}", reply_markup=reply_markup)
    await context.bot.pin_chat_message(chat_id=chat_id, message_id=sent_message.message_id)

async def start_repeating_job(update: Update, context: CallbackContext):
    if not await is_chat_admin(update, context):
        return

    chat_id = update.effective_chat.id

    jobs = context.job_queue.jobs()

    job_exists = any(str(job.name) == str(chat_id) for job in jobs)

    if job_exists:
        await update.message.reply_text('The bot is already running in this chat.')
        return

    chat_name = context.args[0]
    reg_week_day = context.args[1]
    reg_time = context.args[2]
    game_week_day = context.args[3]
    game_time = context.args[4]

    create_chat(chat_id, chat_name, game_time, game_week_day, reg_time, reg_week_day)

    next_reg_time = get_next_weekday(reg_week_day, reg_time)

    now = get_current_time()

    initial_delay = (next_reg_time - now).total_seconds()

    # Schedule job to run every week
    weekly_interval = 7 * 24 * 60 * 60  # 7 days in seconds

    job_data = {
        'chat_id': chat_id,
    }

    job = context.job_queue.run_repeating(
        start,
        interval=weekly_interval,
        first=initial_delay,
        data=job_data,
        name=str(chat_id)  # Using chat_id as job name
    )
    context.chat_data[str(chat_id)] = job
    await update.message.reply_text("The bot has started successfully.")

async def stop_repeating_job(update: Update, context: CallbackContext):
    if not await is_chat_admin(update, context):
        return

    chat_id = update.effective_chat.id

    jobs = context.job_queue.jobs()
    for job in jobs:
        if str(job.name) == str(chat_id):
            job.schedule_removal()
            delete_chat(chat_id)
            await update.message.reply_text("The bot has been stopped.")
            return

    await update.message.reply_text("No recurrent messages are currently scheduled for this chat.")
