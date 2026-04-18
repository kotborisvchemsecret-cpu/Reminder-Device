import tkinter as tk
from events_helper import load_events, save_events
from datetime import datetime

root = tk.Tk()
root.title("Tamagotchi Pet")

mood_label = tk.Label(root, text="😴 No events", font=("Arial", 16))
mood_label.pack(pady=10)

listbox = tk.Listbox(root, width=50, height=10)
listbox.pack(pady=10)

def update_pet_gui():
    today = datetime.now().date()
    events = load_events()
    upcoming = []

    for e in events:
        try:
            event_date = datetime.fromisoformat(e["date"]).date()
            if e.get("yearly", False):
                event_date = event_date.replace(year=today.year)
                if event_date < today:
                    event_date = event_date.replace(year=today.year + 1)
            diff = (event_date - today).days
            if diff >= 0 or e.get("yearly", False):
                upcoming.append((diff, e))
        except:
            continue

    upcoming.sort(key=lambda x: x[0])

    # Update Listbox
    listbox.delete(0, tk.END)
    for diff, e in upcoming:
        yearly = " 🎉" if e.get("yearly") else ""
        listbox.insert(tk.END, f"{e['title']}{yearly} in {diff} days")

    # Update mood
    if upcoming:
        diff, e = upcoming[0]
        if diff > 5:
            mood = "😊 Chill"
        elif diff > 1:
            mood = "😬 Getting close"
        elif diff == 1:
            mood = "😱 TOMORROW"
        else:
            mood = "😢 Today / Missed it"
        mood_label.config(text=f"{mood} | {e['title']}")
    else:
        mood_label.config(text="😴 No upcoming events")

    root.after(5000, update_pet_gui)

update_pet_gui()
root.mainloop()