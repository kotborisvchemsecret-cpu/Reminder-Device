import network
from machine import Pin, SPI, PWM
import socket
import time
import json
import secrets
import ntptime # Added missing import
from lcd import LCD_1inch14

# Initialize LCD
LCD = LCD_1inch14()

def update_display(msg, events=None, ip="0.0.0.0"):
    LCD.fill(LCD.black)
    LCD.rect(0, 0, 240, 135, LCD.blue)
    
    # Get current time from the Pico
    # (year, month, day, hour, minute, second, weekday, yearday)
    t = time.localtime()
    time_str = "{:02d}:{:02d}".format(t[3], t[4]) # HH:MM format
    date_str = "{:02d}.{:02d}".format(t[2], t[1]) # Day.Month
    
    # 1. Header Area - Title + Clock
    LCD.text(date_str, 105, 10, LCD.white)
    LCD.text("EVENTS", 10, 10, LCD.green) 
    LCD.text(time_str, 185, 10, LCD.white) # Clock in top right
    LCD.hline(10, 25, 220, LCD.blue)
    
    # 2. Main Content Area (Events)
    if events and len(events) > 0:
        y = 40
        for e in events[:3]: # Show 3 events to make room
            LCD.text(f"> {e['title'][:12]}", 15, y, LCD.white)
            LCD.text(f"{e['date']}", 150, y, LCD.white)
            y += 22
    

    # 3. Footer Area - Status and IP
    LCD.hline(10, 110, 220, LCD.blue)
    LCD.text(msg[:12], 15, 118, LCD.white)
    LCD.text(ip, 125, 118, LCD.red)
    
    LCD.show()

# -----------------------
# STORAGE
# -----------------------
EVENTS_FILE = "events.json"

def load_events():
    try:
        with open(EVENTS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_events(events):
    with open(EVENTS_FILE, "w") as f:
        json.dump(events, f)

# -----------------------
# DATE HELPERS
# -----------------------
def today():
    return time.localtime()[:3]  # (year, month, day)

def parse_date(date_str):
    try:
        y, m, d = date_str.split("-")
        return int(y), int(m), int(d)
    except:
        return (2000, 1, 1)

def days_left(event_date, today_date):
    ey, em, ed = event_date
    ty, tm, td = today_date
    return (ey - ty) * 365 + (em - tm) * 30 + (ed - td)

# Backlight
pwm = PWM(Pin(13))
pwm.freq(1000)
pwm.duty_u16(32768)

# -----------------------
# WIFI SETUP
# -----------------------
ssid = secrets.WIFI['ssid']
password = secrets.WIFI['password']

update_display("WiFi Init...")
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

# Wait for WiFi
while not wlan.isconnected():
    update_display("Connecting...")
    time.sleep(1)
   
if wlan.isconnected():
    ip = wlan.ifconfig()[0]
    update_display("Syncing Time...", ip=ip)
    try:
        # Try to sync 3 times
        for _ in range(3):
            try:
                ntptime.settime()
                UTC_OFFSET = 2 * 60 * 60 
                actual_time = time.time() + UTC_OFFSET
                y, m, d, h, mn, s, w, yd = time.localtime(actual_time)
                machine.RTC().datetime((y, m, d, 0, h, mn, s, 0))
                update_display("Time Synced!", ip=ip)
                break 
            except:
                time.sleep(1)
        else:
            update_display("NTP Failed", ip=ip)
    except:
        update_display("Clock Error", ip=ip)
else:
    update_display("WiFi Failed!")
    ip = "No IP"

# -----------------------
# SERVER SETUP
# -----------------------
events = load_events()
update_display("Ready", events, ip) # Initial UI update

addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen(1)
s.settimeout(1.0)

# -----------------------
# MAIN LOOP
# -----------------------
msg = "Send to"
while True:
    try:
        # Every loop (every 1 second), we refresh the display so the clock ticks
        update_display(msg, events, ip)
        
        try:
            conn, addr = s.accept()
        except OSError:
            # This happens if no one connects within the 1-second timeout
            continue 

        request = conn.recv(1024).decode()
        
        if "GET / " in request:
            today_date = today()
            html = f"<html><body><h1>Pico Events</h1><p>IP: {ip}</p><ul>"
            for i, e in enumerate(events):
                try:
                    diff = days_left(parse_date(e["date"]), today_date)
                except: diff = "?"
                html += f"<li>{e['title']} - {e['date']} ({diff} days) <a href='/delete?id={i}'>[Del]</a></li>"
            
            html += '<br><form action="/add">Title: <input name="title"><br>Date: <input name="date" type="date"><button>Add</button></form></body></html>'
            conn.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + html)

        elif "/add" in request:
            try:
                query = request.split("GET /add?")[1].split(" ")[0]

                params = {k: v.replace("+", " ").replace("%20", " ") for k, v in [p.split("=") for p in query.split("&")]}
                events.append({"title": params.get("title", "Task"), "date": params.get("date", "2024-01-01")})
                save_events(events)
                update_display("Event Saved!", events, ip)
            except: pass
            conn.send("HTTP/1.1 303 See Other\r\nLocation: /\r\n\r\n")

        elif "/delete" in request:
            try:
                i_str = request.split("id=")[1].split(" ")[0]
                i = int(i_str)
                if 0 <= i < len(events):
                    events.pop(i)
                    save_events(events)
                    update_display("Deleted!", events, ip) # Fixed typo here
            except: pass
            conn.send("HTTP/1.1 303 See Other\r\nLocation: /\r\n\r\n")

        conn.close()
    except Exception as e:
        msg="Socket Error"
        if 'conn' in locals(): conn.close()
        time.sleep(0.1)