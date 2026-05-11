import network
import machine
from machine import Pin, PWM
import socket
import time
import json
import secrets2
import secrets
import ntptime
from lcd import LCD_1inch14
from grid import draw_icon
import ure

# -----------------------
# LCD SETUP
# -----------------------
LCD = LCD_1inch14()

# -----------------------
# GLOBAL SCROLL STATE
# -----------------------
last_scroll = time.ticks_ms()
scroll_pos = 0
event_scroll = 0

# -----------------------
# BUTTONS + NONBLOCKING DEBOUNCE
# -----------------------
btn_up = Pin(2, Pin.IN, Pin.PULL_UP)
btn_down = Pin(3, Pin.IN, Pin.PULL_UP)
last_button = time.ticks_ms()
DEBOUNCE_MS = 150

# -----------------------
# SCROLLING TEXT HELPER
# -----------------------
def draw_scrolling_text(lcd, text, x, y, width, color, offset):
    text_width = len(text) * 8
    if text_width <= width:
        lcd.text(text, x, y, color)
        return

    shift = offset % (text_width + 20)

    start_px = shift
    end_px = shift + width

    px = 0
    for ch in text:
        ch_start = px
        ch_end = px + 8

        if ch_end > start_px and ch_start < end_px:
            draw_x = x + (ch_start - start_px)
            lcd.text(ch, draw_x, y, color)

        px += 8

# -----------------------
# DISPLAY
# -----------------------
def update_display(msg, events=None, ip="0.0.0.0"):
    global event_scroll, scroll_pos

    LCD.fill(LCD.black)
    LCD.rect(0, 0, 240, 135, LCD.blue)

    # Time
    t = time.localtime()
    time_str = "{:02d}:{:02d}".format(t[3], t[4])
    date_str = "{:02d}.{:02d}".format(t[2], t[1])

    # Header
    LCD.text(date_str, 105, 10, LCD.white)
    LCD.text("EVENTS", 10, 10, LCD.green)
    LCD.text(time_str, 185, 10, LCD.white)
    LCD.hline(10, 25, 220, LCD.blue)

    # Events
    if events:
        visible = events[event_scroll:event_scroll + 3]
        y = 40
        for e in visible:
            icon = e.get("icon")

            if icon:
                draw_icon(LCD, icon, 5, y)
                text_x = 25
            else:
                text_x = 15

            title = e["title"]
            draw_scrolling_text(LCD, title, text_x, y+3, 110, LCD.white, scroll_pos)
            LCD.text(e["date"], 150, y, LCD.white)
            y += 22

    # Footer
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
def parse_date(date_str):
    try:
        y, m, d = date_str.split("-")
        return int(y), int(m), int(d)
    except:
        return (2000, 1, 1)

def today():
    t = time.localtime()
    return (t[0], t[1], t[2])

def days_left(event_date, today_date):
    try:
        e = time.mktime((event_date[0], event_date[1], event_date[2], 0,0,0,0,0))
        t = time.mktime((today_date[0], today_date[1], today_date[2], 0,0,0,0,0))
        return int((e - t) / 86400)
    except:
        return "?"

# -----------------------
# BACKLIGHT
# -----------------------
pwm = PWM(Pin(13))
pwm.freq(1000)
pwm.duty_u16(32768)

# -----------------------
# WIFI (NON-BLOCKING)
# -----------------------
ssid = secrets2.WIFI['ssid']
password = secrets2.WIFI['password']

wifi_ok = False
ip = "offline"

update_display("WiFi Init...")

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

# krátký pokus o připojení (NE nekonečný loop)
for _ in range(10):  # cca 10 sekund
    if wlan.isconnected():
        wifi_ok = True
        break
    update_display("Connecting WiFi...")
    time.sleep(1)

if wifi_ok:
    ip = wlan.ifconfig()[0]
    update_display("WiFi OK", ip=ip)

    # -----------------------
    # NTP TIME SYNC (jen pokud WiFi funguje)
    # -----------------------
    try:
        ntptime.settime()
        UTC_OFFSET = 2 * 3600
        t = time.localtime(time.time() + UTC_OFFSET)
        machine.RTC().datetime((t[0], t[1], t[2], t[6], t[3], t[4], t[5], 0))
        update_display("Time Synced!", ip=ip)
    except:
        update_display("NTP Failed", ip=ip)

else:
    update_display("Offline mode", ip=ip)

# -----------------------
# TCP SERVER SETUP
# -----------------------
events = load_events()
update_display("Ready", events, ip)

PORT = 5000
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(("0.0.0.0", PORT))
server.listen(1)
server.settimeout(0.05)

if ip != "offline":
    msg = "TCP Ready"

# -----------------------
# MAIN LOOP
# -----------------------
while True:
    try:
        now = time.ticks_ms()

        # Update scroll positions
        if time.ticks_diff(now, last_scroll) > 40:
            scroll_pos = (scroll_pos + 4) % 2000
            last_scroll = now

        # Handle UP button (non-blocking)
        if not btn_up.value():
            if time.ticks_diff(now, last_button) > DEBOUNCE_MS:
                if event_scroll > 0:
                    event_scroll -= 1
                    msg = "Scroll Up"
                last_button = now

        # Handle DOWN button (non-blocking)
        if not btn_down.value():
            if time.ticks_diff(now, last_button) > DEBOUNCE_MS:
                if event_scroll < max(0, len(events) - 3):
                    event_scroll += 1
                    msg = "Scroll Down"
                last_button = now

        update_display(msg, events, ip)

        # TCP handling
        try:
            conn, addr = server.accept()
            conn.settimeout(1)
        except OSError:
            continue
        buf = b""
        while True:
            try:
                chunk = conn.recv(1024)
                if not chunk:
                    break
                buf += chunk
                if b"\n" in chunk:
                    break
            except OSError:
                break

        print("RECV RAW:", buf)

        if not buf:
            conn.close()
            continue

        try:
            req = json.loads(buf.decode().strip())
        except:
            conn.send(b'{"error":"invalid json"}')
            conn.close()
            continue

        # COMMAND HANDLING
        if req.get("cmd") == "add":
            title = req.get("title", "Task")
            date = req.get("date", "2024-01-01")
            icon = req.get("icon")
            events.append({"title": title, "date": date, "icon": icon})
            save_events(events)
            msg = "Added"
            conn.send(b'{"status":"ok"}')

        elif req.get("cmd") == "delete":
            idx = req.get("index", -1)
            if 0 <= idx < len(events):
                events.pop(idx)
                save_events(events)
                msg = "Deleted"
                conn.send(b'{"status":"ok"}')
            else:
                conn.send(b'{"error":"bad index"}')

        elif req.get("cmd") == "list":
            conn.send(json.dumps(events).encode())

        else:
            conn.send(b'{"error":"unknown cmd"}')

        conn.close()

    except Exception as e:
        print("TCP Error: ", e)
        msg = "TCP Error"
        if 'conn' in locals():
            conn.close()
        time.sleep(0.1)
