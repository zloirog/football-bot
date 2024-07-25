import datetime

def next_saturday():
    today = datetime.datetime.now()
    # Calculate how many days until the next Saturday (Saturday is 5 in Python's weekday())
    days_until_saturday = (5 - today.weekday() + 7) % 7
    if days_until_saturday == 0:
        days_until_saturday = 7  # Ensures we get the next Saturday, not today if today is Saturday
    next_saturday_date = today + datetime.timedelta(days=days_until_saturday)
    next_saturday_date = datetime.datetime.combine(next_saturday_date, datetime.time(9, 30))
    return next_saturday_date