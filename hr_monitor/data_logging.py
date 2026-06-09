import time
import numpy as np
from collections import deque
from PIL import Image, ImageDraw, ImageFont
from max30102.max30102 import MAX30102
from my_hrcalc import calculate_hr_and_spo2
import math
import csv
import datetime

#--CSV logging setup------------------
CSV_FILENAME=f"ppg_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
csv_file=open(CSV_FILENAME, 'w', newline='')
csv_writer=csv.writer(csv_file)
csv_writer.writerow(['timestamp', 'ir_raw', 'red_raw', 'hr', 'spo2', 'status'])

#--BITMAP LOGO-----------------------
heart_bmp = bytes([0x01, 0xF0, 0x0F, 0x80, 0x06, 0x1C, 0x38, 0x60, 0x18, 0x06, 0x60, 0x18, 0x10, 0x01, 0x80, 0x08, 0x20, 0x01, 0x80, 0x04, 0x40, 0x00, 0x00, 0x02, 0x40, 0x00, 0x00, 0x02, 0xC0, 0x00, 0x08, 0x03, 0x80, 0x00, 0x08, 0x01, 0x80, 0x00, 0x18, 0x01, 0x80, 0x00, 0x1C, 0x01, 0x80, 0x00, 0x14, 0x00, 0x80, 0x00, 0x14, 0x00, 0x80, 0x00, 0x14, 0x00, 0x40, 0x10, 0x12, 0x00, 0x40, 0x10, 0x12, 0x00, 0x7E, 0x1F, 0x23, 0xFE, 0x03, 0x31, 0xA0, 0x04, 0x01, 0xA0, 0xA0, 0x0C, 0x00, 0xA0, 0x0, 0x08, 0x00, 0x60, 0xE0, 0x10, 0x00, 0x20, 0x60, 0x20, 0x06, 0x00, 0x40, 0x60, 0x03, 0x00, 0x40, 0xC0, 0x01, 0x80, 0x01, 0x80, 0x00, 0xC0, 0x03, 0x00, 0x00, 0x60, 0x06, 0x00, 0x00, 0x30, 0x0, 0x00, 0x00, 0x08, 0x10, 0x00, 0x00, 0x06, 0x60, 0x00, 0x00, 0x03, 0xC0, 0x00, 0x00, 0x01, 0x80, 0x00])

oximeter_bmp=bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x08, 0x00, 0x00, 0x00, 0x14, 0x00, 0x00, 0x00, 0x24, 0x00, 0x00, 0x00, 0x22, 0x00, 0x00, 0x00, 0x42, 0x00, 0x00, 0x00, 0x41, 0x00, 0x00, 0x00, 0x80, 0x80, 0x00, 0x00, 0x80, 0x80, 0x00, 0x01, 0x00, 0x80, 0x00, 0x01, 0x00, 0x40, 0x00, 0x02, 0x00, 0x40, 0x00, 0x02, 0x00, 0x40, 0x00, 0x02, 0x00, 0x00, 0x00, 0x02, 0x40, 0x30, 0x00, 0x01, 0x60, 0x88, 0x00, 0x01, 0x98, 0x85, 0x80, 0x00, 0xC0, 0x04, 0x40, 0x00, 0x3C, 0x04, 0x00, 0x00, 0x00, 0x84, 0x80, 0x00, 0x00, 0xC9, 0x00, 0x00, 0x00, 0x20, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

def render_bitmap(bitmap_bytes, width, height, color, flip_horizontal=False):
    #Convert a 1‑bit monochrome bitmap (MSB first) into a PIL Image
    img=Image.new("RGB", (width, height), (0, 0, 0))
    draw=ImageDraw.Draw(img)
    for y in range(height):
        for x in range(width):
            byte_idx=(y*width+x) // 8
            if byte_idx>=len(bitmap_bytes):
                break
            bit=7-(x%8)
            if flip_horizontal:
                bit=(x%8)
            if (bitmap_bytes[byte_idx]>>bit)&1:
                draw.point((x, y), fill=color)
    return img

#--DISPLAY-----------------------
WIDTH, HEIGHT = 240, 240
FB_PATH = "/dev/fb0"

try:
    txt_font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    small_font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    label_font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    status_font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
except:
    txt_font=small_font = ImageFont.load_default()

logo_h=render_bitmap(heart_bmp,32,32,(252, 86, 83))
logo_o=render_bitmap(oximeter_bmp,32,32,(71, 252, 219))
logo_o=logo_o.resize((50,50),Image.BOX)

_sine_points = [(50 + x, 180 + 10 * math.sin(x * 0.2)) for x in range(140)]

def write_display(hr_str, spo2_str, status_str, pred_hr_str=None, pred_spo2_str=None, ir_history=None):
    img=Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    draw=ImageDraw.Draw(img)
    draw.ellipse([5, 5, 235, 235], fill=(0,0,0))

    #Logos(bmp)
    img.paste(logo_h,(66,42))
    img.paste(logo_o,(62,75))

    #BPM val
    draw.text((111, 47), hr_str, font=small_font, fill=(0, 255, 120))

    #SpO_2 val
    draw.text((112, 85), spo2_str, font=small_font, fill=(80, 180, 255))

    #Waveform
    if ir_history and len(ir_history) > 5:
        samples  = list(ir_history)[-130:]
        min_val, max_val = min(samples), max(samples)
        if max_val > min_val:
            rng    = max_val - min_val
            pts    = [(56 + i, 160 - (s - min_val) / rng * 20)
                      for i, s in enumerate(samples)]
            draw.line(pts, fill=(100, 255, 100), width=2)
        else:
            draw.line([(56, 160), (186, 160)], fill=(100, 255, 100), width=2)
    else:
        draw.line(_sine_points, fill=(100, 255, 100), width=2)

    #Status line
    bb2=draw.textbbox((0,-5), status_str, font=status_font)
    draw.text(((WIDTH-(bb2[2]-bb2[0])) // 2, 210), status_str, font=status_font, fill=(255, 174, 0))

    #Convert to RGB565 and write to framebuffer
    pixels = np.array(img)
    r = (pixels[:,:,0] >> 3).astype(np.uint16)
    g = (pixels[:,:,1] >> 2).astype(np.uint16)
    b = (pixels[:,:,2] >> 3).astype(np.uint16)
    with open(FB_PATH, "wb") as fb:
        fb.write(((r << 11) | (g << 5) | b).tobytes())

#--SENSOR-------------------------
sensor=MAX30102()
sensor.setup()

#--CONFIG--------------------------
FS=50#Hz
WINDOW_SEC=6
WINDOW_SAMPLES=FS*WINDOW_SEC
SLIDE_SAMPLES=10
FINGER_THRESH=25000

ir_buf=deque(maxlen=WINDOW_SAMPLES)
red_buf=deque(maxlen=WINDOW_SAMPLES)
hr_history = deque(maxlen=6)
spo2_history = deque(maxlen=6)
samples_since_calc=0

def get_status(hr, spo2):
    if spo2<94: return "LOW O2"
    if hr>100: return "HIGH HR"
    if hr<60: return "LOW HR"
    return "NORMAL"

def fill_buffer():
    write_display("---", "---", "WARMING UP")
    ir_buf.clear()
    red_buf.clear()
    while len(ir_buf) < WINDOW_SAMPLES:
        t0=time.time()
        red,ir=sensor.read_fifo()
        ir_buf.append(ir)
        red_buf.append(red)
        wait=1.0/FS-(time.time()-t0)
        if wait>0:
            time.sleep(wait)

#--MAIN-------------------------------------
print("NextBeat — place finger on sensor.")
fill_buffer()
print("Buffer ready. Monitoring.")

displayed_hr=displayed_spo2=None

try:
    while True:
        t0=time.time()

        red, ir=sensor.read_fifo()
        ir_buf.append(ir)
        red_buf.append(red)
        samples_since_calc+=1

        #Finger check
        recent=list(ir_buf)[-50:]
        recent_ir=list(ir_buf)[-140:]

        if np.mean(recent)<FINGER_THRESH:
            if displayed_hr is not None:
                write_display("---", "---", "NO FINGER")
                displayed_hr=displayed_spo2=None
                hr_history.clear()
                spo2_history.clear()
                print("\nNo finger — waiting...")
            fill_buffer()
            samples_since_calc=0
            print("Buffer ready. Monitoring.")
            continue

        if samples_since_calc<SLIDE_SAMPLES:
            wait=1.0/FS-(time.time()-t0)
            if wait>0:
                time.sleep(wait)
            continue

        samples_since_calc=0
        hr, hr_v, spo2, spo2_v=calculate_hr_and_spo2(
            list(ir_buf), list(red_buf), fs=FS)

        if hr_v:
            hr_history.append(hr)
        if spo2_v:
            spo2_history.append(spo2)

        if not hr_history or not spo2_history:
            write_display("---", "---", "MEASURING")
            print("\rMeasuring...", end="", flush=True)
        else:
            smooth_hr = int(np.median(hr_history))
            smooth_spo2 = int(np.median(spo2_history))
            status = get_status(smooth_hr, smooth_spo2)

            # Display update
            if smooth_hr != displayed_hr or smooth_spo2 != displayed_spo2:
                write_display(f"{smooth_hr} bpm", f"{smooth_spo2}%", status, recent_ir)
                displayed_hr = smooth_hr
                displayed_spo2 = smooth_spo2

            # CSV logging
            csv_writer.writerow([time.time(), ir, red, smooth_hr, smooth_spo2, status])
            csv_file.flush()

            print(f"\rHR: {smooth_hr:3d} bpm | SpO2: {smooth_spo2:3d}% | [{status}]", end="", flush=True)

        wait = 1.0/FS - (time.time() - t0)
        if wait > 0:
            time.sleep(wait)

except KeyboardInterrupt:
    csv_file.close()
    print("\nStopped. Data saved to", CSV_FILENAME)
