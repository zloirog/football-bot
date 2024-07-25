import json
import datetime
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, CallbackContext

async def get_jobs(update: Update, context: CallbackContext):
    jobs = context.job_queue.jobs()

    s = ""
    for job in jobs:
      s += repr(job)

    await update.message.reply_text("jobs: " + s)

async def start_repeating_job(update: Update, context: CallbackContext):
    if not await is_chat_admin(update, context):
        return

    chat_id = update.effective_chat.id

    jobs = context.job_queue.jobs()

    if len(jobs) != 0:
        await update.message.reply_text('Already started in that chat.')
        return


    # Calculate time to next Wednesday at 12:00
    now = datetime.datetime.now()
    next_wednesday = now + datetime.timedelta((2 - now.weekday() + 7) % 7)  # 2 for Wednesday
    next_wednesday = datetime.datetime.combine(next_wednesday, datetime.time(10, 0))
    if next_wednesday < now:
        next_wednesday += datetime.timedelta(days=7)
    initial_delay = (next_wednesday - now).total_seconds()

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
    context.chat_data['job'] = job

async def stop_repeating_job(update: Update, context: CallbackContext):
    if not await is_chat_admin(update, context):
        return
    job = context.chat_data.get('job')
    if job:
        job.schedule_removal()
        await update.message.reply_text("Bot stopped.")
    else:
        await update.message.reply_text("No recurrent messages are currently scheduled.")
