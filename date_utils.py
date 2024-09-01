from datetime import datetime, timedelta
import pytz

def get_next_weekday(weekday_name, time_str):
    # Dictionary to convert weekday name to a weekday number (0=Monday, 6=Sunday)
    weekdays = {
        'monday': 0,
        'tuesday': 1,
        'wednesday': 2,
        'thursday': 3,
        'friday': 4,
        'saturday': 5,
        'sunday': 6
    }
    
    # Parse the time string
    target_time = datetime.strptime(time_str, '%H:%M').time()
    
    # Get the current date and time
    now = datetime.now()
    
    # Find the target weekday number
    target_weekday = weekdays[weekday_name.lower()]
    
    # Calculate days until the next occurrence of the target weekday
    days_ahead = target_weekday - now.weekday()
    if days_ahead <= 0:
        days_ahead += 7

    # Create the next weekday datetime
    next_weekday = datetime(now.year, now.month, now.day) + timedelta(days=days_ahead)
    next_weekday = datetime.combine(next_weekday, target_time)

    # Check if the target weekday is today and before the target time
    if now.weekday() == target_weekday and now.time() < target_time:
        next_weekday = datetime.combine(now, target_time)
    
    return pytz.timezone('Europe/Prague').localize(next_weekday)