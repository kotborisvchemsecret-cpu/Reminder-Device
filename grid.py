def draw_icon(lcd, icon, x, y, scale=3):
    if not icon:
        return

    try:
        for row_i, row in enumerate(icon):
            for col_i, color in enumerate(row):
                if scale == 1:
                    lcd.pixel(x + col_i, y + row_i, fix_color(color))
                else:
                    # draw a filled block instead of a single pixel
                    for dy in range(scale):
                        for dx in range(scale):
                            lcd.pixel(
                                x + col_i * scale + dx,
                                y + row_i * scale + dy,
                                fix_color(color)
                            )
    except Exception as e:
        print("ICON ERROR:", e)
        
def fix_color(c):
    # swap bytes (THIS is the real fix in most cases)
    c = ((c & 0xFF) << 8) | ((c >> 8) & 0xFF)
    return c & 0xFFFF