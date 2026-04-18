import os
import json
from datetime import datetime
from events_helper import load_events, save_events
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EVENTS_FILE = os.path.join(BASE_DIR, "events.json")  # same absolute path as Flask


from datetime import datetime

def get_upcoming_events():
    events = load_events()
    today = datetime.now().date()
    upcoming = []

    for e in events:
        try:
            event_date = datetime.fromisoformat(e["date"]).date()

            # Handle yearly events
            if e.get("yearly", False):
                event_date = event_date.replace(year=today.year)
                if event_date < today:
                    event_date = event_date.replace(year=today.year + 1)

            diff = (event_date - today).days

            # Only future events
            if diff >= 0 or e.get("yearly", False):
                upcoming.append((diff, e))  # store tuple (days, event)

        except Exception as ex:
            print("Skipping bad event:", e, ex)

    # Sort by soonest
    upcoming.sort(key=lambda x: x[0])
    return upcoming

while True:
    upcoming = get_upcoming_events()
    
    if not upcoming:
        print("😴 No upcoming events")
    else:
        for diff, e in upcoming[:5]:  # show next 5 events
            if diff > 5:
                mood = "😊 Chill"
            elif diff > 1:
                mood = "😬 Getting close"
            elif diff == 1:
                mood = "😱 TOMORROW"
            else:
                mood = "😢 Today / Missed it"

            yearly = "🎉" if e.get("yearly") else ""
            print(f"{mood} | {e['title']} {yearly} in {diff} days")

    time.sleep(5)