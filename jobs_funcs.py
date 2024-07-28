import datetime
from telegram import Update
from telegram.ext import CallbackContext
from utils import is_chat_admin
from date_utils import next_saturday
from constants import reply_markup
from match_files import load_data, save_data


async def get_jobs(update: Update, context: CallbackContext):
    jobs = context.job_queue.jobs()

    s = ""
    for job in jobs:
        s += repr(job)

    await update.message.reply_text("jobs: " + s)


async def start(context: CallbackContext):
    job_data = context.job.data
    chat_id = job_data['chat_id']
    game_date = next_saturday()
    game_id = game_date.strftime("%d.%m.%Y_%H_%M")
    game_time_frmt = game_date.strftime("%d.%m.%Y %H:%M")

    data = load_data()
    if game_id in data:
        await context.bot.send_message(chat_id=chat_id, text="Game already exists!")
        return

    data[game_id] = {
        "datetime": game_date.isoformat(),
        "players": [],
        "waiting_list": [],
        "start_time": datetime.datetime.now().isoformat(),
        "message": ""
    }
    save_data(data)

    sent_message = await context.bot.send_message(chat_id=chat_id, text=f"Registration opened! \n{game_time_frmt}", reply_markup=reply_markup)
    await context.bot.pin_chat_message(chat_id=chat_id, message_id=sent_message.message_id)


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
    next_wednesday = now + \
        datetime.timedelta((2 - now.weekday() + 7) % 7)  # 2 for Wednesday
    next_wednesday = datetime.datetime.combine(
        next_wednesday, datetime.time(10, 0))
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
