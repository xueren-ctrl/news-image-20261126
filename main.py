#!/usr/bin/env python3
"""THE WORLD IN ONE PAGE - Thursday 26 November 2026, FULL-DAY EDITION.

A newspaper front page drawn entirely in code for the make.fun
news-image-20261126 bounty. Python standard library only: own 5x7 bitmap
font, own PNG encoder, no photos, no network, fully deterministic
(two runs produce byte-identical output).

All facts come from the full-day research file
(news26-fullday-research.md), verified to the 08:00 UTC cut-off.
Weekdays verified with `date`: 26 Nov 2026 is a Thursday,
25 Nov a Wednesday, 28 Nov a Saturday, 29 Nov a Sunday.

Run:  python3 main.py        -> writes entry.png (1024x1024) next to main.py
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette ---
PAPER = (247, 243, 234)
INK = (26, 26, 26)
RED = (178, 34, 34)
BLUE = (28, 68, 128)
GREY = (110, 108, 100)
DGREY = (70, 68, 60)
LIGHT = (232, 226, 212)
MID = (200, 192, 172)
GOLD = (176, 132, 30)
GREEN = (34, 110, 60)
SEA = (214, 228, 238)
LAND = (226, 214, 180)

# ------------------------------------------------------------- bitmap font --
# 5x7 glyphs, '1' = ink. Text is rendered in ALL CAPS; the normaliser
# below folds accents and punctuation onto glyphs that exist.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ';': ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '$': ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '*': ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    '~': ("00000", "00000", "01001", "10110", "00000", "00000", "00000"),
    '<': ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    '>': ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    '_': ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    '#': ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    '|': ("00100", "00100", "00100", "00100", "00100", "00100", "00100"),
}
FONT['\u2014'] = ("00000", "00000", "00000", "11111", "00000", "00000", "00000")
FONT['\u2013'] = ("00000", "00000", "00000", "01110", "00000", "00000", "00000")
FONT['\u00b7'] = ("00000", "00000", "00000", "00000", "01100", "01100", "00000")
FONT['\u00a3'] = ("00110", "01001", "01000", "11110", "01000", "01001", "11111")

FOLD = {
    '\u00c1': 'A', '\u00c0': 'A', '\u00c4': 'A', '\u00c2': 'A', '\u00c3': 'A', '\u00c5': 'A',
    '\u00c9': 'E', '\u00c8': 'E', '\u00ca': 'E', '\u00cb': 'E',
    '\u00cd': 'I', '\u00cc': 'I', '\u00ce': 'I', '\u00cf': 'I',
    '\u00d3': 'O', '\u00d2': 'O', '\u00d4': 'O', '\u00d6': 'O', '\u00d5': 'O',
    '\u00da': 'U', '\u00d9': 'U', '\u00db': 'U', '\u00dc': 'U',
    '\u00dd': 'Y', '\u00d1': 'N', '\u00c7': 'C', '\u0160': 'S', '\u017d': 'Z',
    '\u00e1': 'A', '\u00e0': 'A', '\u00e4': 'A', '\u00e2': 'A', '\u00e3': 'A', '\u00e5': 'A',
    '\u00e9': 'E', '\u00e8': 'E', '\u00ea': 'E', '\u00eb': 'E',
    '\u00ed': 'I', '\u00ec': 'I', '\u00ee': 'I', '\u00ef': 'I',
    '\u00f3': 'O', '\u00f2': 'O', '\u00f4': 'O', '\u00f6': 'O', '\u00f5': 'O',
    '\u00fa': 'U', '\u00f9': 'U', '\u00fb': 'U', '\u00fc': 'U',
    '\u00fd': 'Y', '\u00f1': 'N', '\u00e7': 'C', '\u0161': 'S', '\u017e': 'Z',
    '\u2019': "'", '\u2018': "'", '\u201c': '"', '\u201d': '"',
    '\u00ab': '"', '\u00bb': '"', '\u2026': '.', '\u2022': '\u00b7',
    '\u2212': '-', '\u00d7': 'X',
}


def norm(text):
    out = []
    for ch in text:
        if ch in FOLD:
            out.append(FOLD[ch])
        elif ch in FONT:
            out.append(ch)
        elif ch.isalpha():
            out.append(ch.upper())
        else:
            out.append(' ')
    return ''.join(out)


# ---------------------------------------------------------------- canvas ----
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bytes(bg) * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(c)

    def rect(self, x, y, w, h, c, fill=True):
        if w <= 0 or h <= 0:
            return
        if fill:
            row = bytes(c) * w
            for yy in range(y, y + h):
                if 0 <= yy < self.h:
                    x0 = max(x, 0)
                    x1 = min(x + w, self.w)
                    if x1 > x0:
                        i = (yy * self.w + x0) * 3
                        self.px[i:i + (x1 - x0) * 3] = row[(x0 - x) * 3:(x1 - x) * 3]
        else:
            for xx in range(x, x + w):
                self.set(xx, y, c)
                self.set(xx, y + h - 1, c)
            for yy in range(y, y + h):
                self.set(x, yy, c)
                self.set(x + w - 1, yy, c)

    def hline(self, x, y, w, c, t=1):
        for yy in range(y, y + t):
            for xx in range(x, x + w):
                self.set(xx, yy, c)

    def vline(self, x, y, h, c, t=1):
        for xx in range(x, x + t):
            for yy in range(y, y + h):
                self.set(xx, yy, c)

    def line(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c, fill=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill:
                    if d <= r * r:
                        self.set(xx, yy, c)
                else:
                    if r * r - 2 * r <= d <= r * r:
                        self.set(xx, yy, c)

    def tri(self, pts, c):
        (x0, y0), (x1, y1), (x2, y2) = pts
        minx, maxx = min(x0, x1, x2), max(x0, x1, x2)
        miny, maxy = min(y0, y1, y2), max(y0, y1, y2)
        den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if den == 0:
            return
        for yy in range(miny, maxy + 1):
            for xx in range(minx, maxx + 1):
                a = ((y1 - y2) * (xx - x2) + (x2 - x1) * (yy - y2)) / den
                b = ((y2 - y0) * (xx - x2) + (x0 - x2) * (yy - y2)) / den
                cc = 1 - a - b
                if a >= 0 and b >= 0 and cc >= 0:
                    self.set(xx, yy, c)


def text_w(s, scale):
    return len(norm(s)) * 6 * scale


def draw_text(cv, x, y, s, scale, color):
    s = norm(s)
    cx = x
    for ch in s:
        g = FONT.get(ch)
        if g is None:
            cx += 6 * scale
            continue
        for row in range(7):
            bits = g[row]
            for col in range(5):
                if bits[col] == '1':
                    for dy in range(scale):
                        for dx in range(scale):
                            cv.set(cx + col * scale + dx, y + row * scale + dy, color)
        cx += 6 * scale
    return cx


def draw_centered(cv, cx, y, s, scale, color):
    draw_text(cv, cx - text_w(s, scale) // 2, y, s, scale, color)


def wrap(s, scale, max_w):
    """Greedy word wrap on the normalised text; returns list of lines."""
    s = norm(s)
    words = s.split(' ')
    lines, cur = [], ''
    for wd in words:
        trial = (cur + ' ' + wd).strip()
        if text_w(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def draw_para(cv, x, y, s, scale, max_w, color, leading=None):
    lh = leading if leading is not None else 9 * scale
    for ln in wrap(s, scale, max_w):
        draw_text(cv, x, y, ln, scale, color)
        y += lh
    return y


# -------------------------------------------------------------- PNG write ---
def write_png(cv, path):
    raw = bytearray()
    for yy in range(cv.h):
        raw.append(0)
        raw.extend(cv.px[yy * cv.w * 3:(yy + 1) * cv.w * 3])
    comp = zlib.compress(bytes(raw), 9)

    def chunk(kind, data):
        c = struct.pack('>I', len(data)) + kind + data
        return c + struct.pack('>I', zlib.crc32(kind + data) & 0xFFFFFFFF)

    ihdr = struct.pack('>IIBBBBB', cv.w, cv.h, 8, 2, 0, 0, 0)
    png = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr)
           + chunk(b'IDAT', comp) + chunk(b'IEND', b''))
    with open(path, 'wb') as f:
        f.write(png)
    return len(png)


# ----------------------------------------------------------- illustrations --
def illo_ukraine(cv, x, y, w, h):
    """Two tower blocks under a night burst, shield with a question mark."""
    cv.rect(x, y, w, h, (236, 238, 244))
    cv.rect(x, y, w, h, MID, fill=False)
    # burst of rays over the roofs
    cx, cy = x + 62, y + 24
    for k in range(8):
        ang = k * math.pi / 4.0 + math.pi / 8.0
        ex = int(cx + 24 * math.cos(ang))
        ey = int(cy + 24 * math.sin(ang))
        cv.line(cx, cy, ex, ey, GOLD)
    cv.circle(cx, cy, 6, RED)
    # left tower block
    bx, by = x + 18, y + h - 64
    cv.rect(bx, by, 52, 44, INK, fill=False)
    for wy in (by + 8, by + 22):
        for wx in (bx + 7, bx + 22, bx + 36):
            cv.rect(wx, wy, 9, 8, BLUE, fill=False)
    # right tower block, shorter
    bx2, by2 = x + 82, y + h - 52
    cv.rect(bx2, by2, 46, 32, INK, fill=False)
    for wy in (by2 + 7,):
        for wx in (bx2 + 7, bx2 + 22):
            cv.rect(wx, wy, 9, 8, BLUE, fill=False)
    # shield, lower right
    sx, sy = x + w - 62, y + h - 48
    cv.tri([(sx, sy), (sx + 34, sy), (sx + 17, sy + 34)], BLUE)
    draw_text(cv, sx + 11, sy + 10, "?", 2, PAPER)
    draw_text(cv, x + 12, y + 8, "KYIV - KHARKIV", 1, BLUE)


def illo_gulf(cv, x, y, w, h):
    """Refinery flare stacks, a flame, drifting smoke, a missile streak."""
    cv.rect(x, y, w, h, (250, 238, 226))
    cv.rect(x, y, w, h, MID, fill=False)
    # ground line
    cv.hline(x + 8, y + h - 18, w - 16, INK, 2)
    # two flare stacks with cross braces
    for tx in (x + 26, x + 62):
        cv.rect(tx, y + h - 58, 20, 40, INK, fill=False)
        cv.line(tx + 2, y + h - 58, tx + 18, y + h - 18, INK)
        cv.line(tx + 18, y + h - 58, tx + 2, y + h - 18, INK)
    # flame on the left stack
    fx, fy = x + 36, y + h - 76
    cv.tri([(fx, fy), (fx - 8, fy + 18), (fx + 8, fy + 18)], RED)
    cv.tri([(fx, fy + 6), (fx - 4, fy + 18), (fx + 4, fy + 18)], GOLD)
    # storage tank, right side
    tx, ty = x + 108, y + h - 48
    cv.rect(tx, ty, 52, 30, INK, fill=False)
    cv.line(tx, ty, tx + 52, ty, INK)
    # smoke plume drifting up-right
    for (px, py, pr) in [(x + 132, y + 26, 7), (x + 148, y + 38, 10),
                         (x + 164, y + 52, 12), (x + 176, y + 68, 9)]:
        cv.circle(px, py, pr, GREY)
    # missile streak, top right
    mx, my = x + w - 58, y + 14
    cv.line(mx, my, mx + 30, my + 18, RED)
    cv.tri([(mx + 30, my + 18), (mx + 19, my + 12), (mx + 21, my + 24)], RED)
    draw_text(cv, x + 12, y + 8, "RIYADH", 2, RED)


def illo_cairo(cv, x, y, w, h):
    """A fuel tanker on a ring road, flames above the tank, black smoke."""
    cv.rect(x, y, w, h, (250, 240, 228))
    cv.rect(x, y, w, h, MID, fill=False)
    # road
    cv.hline(x + 8, y + h - 26, w - 16, INK, 2)
    for dx in range(0, w - 24, 22):
        cv.hline(x + 12 + dx, y + h - 20, 12, GOLD, 2)
    # tanker body: long cylinder tank + cab
    tx, ty = x + 22, y + h - 62
    cv.rect(tx, ty, 104, 26, INK, fill=False)
    cv.circle(tx + 52, ty + 13, 13, INK, fill=False)
    cv.rect(tx + 108, ty + 4, 30, 22, RED)
    cv.rect(tx + 116, ty + 10, 14, 8, PAPER)
    # wheels
    for wx in (tx + 22, tx + 62, tx + 96, tx + 122):
        cv.circle(wx, y + h - 30, 6, INK)
        cv.circle(wx, y + h - 30, 2, PAPER)
    # flames above the tank
    for (fx, fy, fs) in [(tx + 34, ty - 22, 12), (tx + 58, ty - 30, 14),
                         (tx + 84, ty - 20, 11)]:
        cv.tri([(fx, fy - fs), (fx - 7, fy + 6), (fx + 7, fy + 6)], RED)
        cv.tri([(fx, fy - fs + 5), (fx - 4, fy + 6), (fx + 4, fy + 6)], GOLD)
    # smoke
    for (px, py, pr) in [(x + 150, y + 18, 8), (x + 164, y + 30, 11),
                         (x + 176, y + 46, 10)]:
        cv.circle(px, py, pr, DGREY)
    draw_text(cv, x + 12, y + 8, "CAIRO RING ROAD", 1, RED)


# -------------------------------------------------------------------- data --
MASTHEAD = "THE WORLD IN ONE PAGE"
SUBTITLE = "THURSDAY 26 NOVEMBER 2026 - FULL-DAY EDITION - VERIFIED TO 08:00 UTC"
STRIP = "27 STORIES - 3 LEADS - 10 SECONDARIES - 14 IN BRIEF - 8 PINS ON MAP"

TIMELINE = [
    ("THU 26 NOV OVERNIGHT", "RUSSIA LAUNCHES 113 DRONES AT UKRAINE"),
    ("THU 26 NOV", "SAUDI ARABIA INTERCEPTS MISSILES OVER RIYADH"),
    ("WED 25 NOV LATE", "CAIRO TANKER FIRE KILLS AT LEAST 30"),
    ("WED 25 NOV", "USTR PROPOSES TARIFFS ON 14 ECONOMIES"),
    ("SAT 28 NOV 08:30 ET", "MACY'S 100TH PARADE MOVES TO SATURDAY"),
    ("SUN 29 NOV", "SPAIN HOLDS SNAP GENERAL ELECTION"),
]

LEADS = [
    dict(kicker="LEAD 1 - UKRAINE - OVERNIGHT ASSAULT CONFIRMED",
         illo=illo_ukraine,
         head="RUSSIA HITS UKRAINE WITH MISSILES AND 113 DRONES",
         sub=("Kyiv mall hit, 7 injured; Kharkiv high-rise struck, "
              "2 dead and 3 hurt"),
         facts=[
             "Russian forces launched ballistic missiles and 113 strike "
             "drones overnight; air defences destroyed or suppressed 87 "
             "by 08:00 Kyiv time.",
             "Hits at 20 locations, debris at six. In Kyiv a ballistic "
             "missile hit a shopping mall in the Desnianskyi district, "
             "injuring seven people.",
             "In Kharkiv a Shahed drone struck a high-rise in the "
             "Novobavarskyi district, killing two and injuring three; "
             "a fire burned on the 15th floor.",
         ],
         tag="CONFIRMED - UKRAINIAN AIR FORCE",
         src="Sources: Ukrainian Air Force - Kyiv city administration"),
    dict(kicker="LEAD 2 - THE GULF - INTERCEPTS CONFIRMED",
         illo=illo_gulf,
         head="SAUDI ARABIA INTERCEPTS MISSILES AIMED AT RIYADH",
         sub=("Jazan port hit; Ras Tanura refinery damage still only "
              "a Houthi claim"),
         facts=[
             "Saudi air defences intercepted two ballistic missiles fired "
             "towards Riyadh and two drones over the Eastern Province, "
             "the coalition said.",
             "A projectile struck Jazan port, minor damage and no civilian "
             "casualties. A cruise missile aimed at the west and a drone "
             "near Jeddah were also intercepted.",
             "The Houthis CLAIM a strike on the Ras Tanura refinery and "
             "'significant damage' in Riyadh's financial district. "
             "Neither is independently verified.",
         ],
         tag="REFINERY DAMAGE CLAIMED, NOT CONFIRMED",
         src="Sources: Saudi-led coalition - Reuters"),
    dict(kicker="LEAD 3 - CAIRO - TANKER FIRE CONFIRMED",
         illo=illo_cairo,
         head="CAIRO TANKER FIRE KILLS AT LEAST 30",
         sub=("Tanker overturns on ring road; 27 vehicles burned, "
              "39 ambulances sent"),
         facts=[
             "At least 30 people were killed and 25 injured when a fuel "
             "tanker overturned and caught fire on Cairo's ring road "
             "late on 25 November.",
             "A later count put the toll at 31. The tanker crashed above "
             "a tunnel in Al Warraq, Giza; 27 vehicles burned and DNA "
             "testing was ordered.",
             "President El Sisi offered condolences and ordered support "
             "for the injured and victims' families. 39 ambulances "
             "responded.",
         ],
         tag="DEATH TOLL 30, LATER COUNT 31",
         src="Sources: AP - Egypt public prosecutor - The National"),
]

SECONDARIES = [
    ("TRUMP MEETS RUTTE",
     "Trump and NATO chief Mark Rutte met at Mar-a-Lago; Russia's war and "
     "Iran topped the agenda; defence spending must expand."),
    ("US TARIFFS PROPOSED",
     "USTR proposes Section 301 tariffs on 14 economies incl. China, EU, "
     "Vietnam; not in effect; comments due 5 Jan, hearings from 25 Jan 2027."),
    ("MUSK GIVES SPACEX SHARES",
     "Every US child to get two SpaceX shares, one from the firm and one "
     "from Musk; Reuters values the gift at about $18bn."),
    ("CHEN JINING PROBED",
     "China's anti-graft bodies investigate Politburo member and Shanghai "
     "party chief Chen Jining for suspected severe violations."),
    ("HUAWEI CONVICTED",
     "Brooklyn jury convicts Huawei and 3 units on 10 of 12 counts incl. "
     "sanctions violations and fraud; sentencing 14 Sep 2027."),
    ("KIM INSPECTS NUCLEAR SITES",
     "Kim Jong Un inspects nuclear material production and calls for wider "
     "deployment of tactical nuclear weapons."),
    ("UNRWA RULING",
     "UN tribunal says UNRWA relied on unproven Israeli claims to sack nine "
     "staff in 2024; one dismissal rescinded."),
    ("EU SUMMIT ON BUDGET",
     "EU leaders meet Thu-Fri seeking a December deal on a nearly 1.6tn "
     "euro 2028-34 budget and up to 100bn euro for Ukraine."),
    ("SPAIN VOTES SUNDAY",
     "Spain holds a snap general election on Sunday 29 Nov; People's Party "
     "ahead in polls, may need Vox for a majority."),
    ("UN WARNS OF ATROCITIES",
     "UN rights chief Volker Turk warns Israeli attacks and policies point "
     "to a widening risk of further atrocity crimes."),
]

ALSO_ON = [
    "OIL BRENT $94.61, UP 3.5%",
    "IOWA BLAST: ZERO LEAD FOUND",
    "MACY'S PARADE MOVES TO SAT",
    "795 FLEE IN SUDAN IN ONE DAY",
    "POPE URGES LEADERS: BREAK CHAINS",
    "TIDAL TO BAN AI MUSIC 9 DEC",
    "NEW YORK BANS AI TOYS 5 YEARS",
    "FCC APPROVES 1M SATELLITES",
    "POLAND PLANS NO-FLY ZONE",
    "PUTIN SACKS MURMANSK GOVERNOR",
    "US OKAYS $621.9M F-16 SALE",
    "BBC STAFF VOTE TO STRIKE",
    "IRAQ DIALOGUE SET FOR 1 DEC",
    "NVIDIA RATING ON WATCH",
]

DATE_CHECK = [
    "DATE CHECK - 26 NOVEMBER 2026 IS A THURSDAY. STORIES THAT BROKE ON "
    "OTHER DAYS ARE NOT IN THIS EDITION.",
    "TARIFFS WERE PROPOSED 25 NOV AND ARE NOT IN EFFECT. RAS TANURA DAMAGE "
    "IS A CLAIM, NOT CONFIRMED. CAIRO TOLL: 30, LATER COUNT 31.",
]


# --------------------------------------------------------------------- map --
# Rough equirectangular land outlines (lon, lat). Schematic, not survey-grade.
NORTH_AMERICA = [(-168, 66), (-160, 58), (-152, 60), (-145, 60), (-140, 70),
                 (-130, 71), (-125, 72), (-120, 73), (-110, 73), (-100, 73),
                 (-95, 80), (-90, 74), (-85, 66), (-80, 70), (-75, 72),
                 (-70, 62), (-65, 60), (-60, 52), (-55, 47), (-60, 45),
                 (-65, 44), (-70, 42), (-75, 38), (-76, 35), (-80, 32),
                 (-81, 26), (-84, 30), (-90, 21), (-97, 26), (-105, 20),
                 (-110, 23), (-115, 28), (-120, 34), (-124, 40), (-124, 48),
                 (-130, 54), (-140, 60), (-150, 59), (-158, 58), (-165, 60),
                 (-168, 66)]
GREENLAND = [(-58, 64), (-52, 60), (-43, 60), (-40, 65), (-45, 70),
             (-55, 76), (-65, 76), (-60, 70), (-58, 64)]
SOUTH_AMERICA = [(-80, 10), (-77, 7), (-72, 12), (-64, 10), (-60, 8),
                 (-52, 5), (-50, 0), (-44, -3), (-35, -8), (-37, -13),
                 (-40, -20), (-48, -27), (-52, -33), (-58, -38), (-65, -41),
                 (-68, -50), (-70, -54), (-73, -50), (-73, -40), (-71, -30),
                 (-70, -20), (-75, -15), (-80, -5), (-81, 0), (-80, 6)]
EURASIA = [(-10, 36), (-9, 43), (-2, 48), (-1, 50), (3, 53), (8, 57),
           (10, 59), (18, 56), (21, 55), (24, 58), (28, 60), (30, 62),
           (32, 70), (40, 68), (50, 69), (60, 70), (70, 72), (80, 73),
           (90, 75), (100, 77), (110, 76), (120, 73), (130, 72), (140, 72),
           (150, 70), (158, 69), (162, 66), (170, 66), (178, 65), (178, 62),
           (170, 60), (162, 58), (158, 52), (156, 50), (150, 45), (142, 42),
           (140, 38), (135, 34), (130, 33), (127, 35), (126, 38), (122, 39),
           (120, 34), (122, 30), (118, 25), (110, 20), (108, 18), (105, 10),
           (103, 8), (100, 7), (98, 10), (97, 15), (94, 17), (92, 21),
           (89, 22), (86, 20), (80, 15), (80, 8), (77, 8), (75, 15),
           (72, 20), (68, 23), (66, 25), (61, 25), (58, 26), (56, 27),
           (52, 28), (50, 29), (48, 30), (44, 29), (40, 31), (36, 36),
           (33, 36), (30, 36), (27, 37), (26, 38), (23, 36), (22, 40),
           (19, 42), (15, 44), (12, 44), (8, 44), (6, 43), (3, 43),
           (0, 40), (-2, 37), (-6, 36), (-9, 37), (-10, 36)]
AFRICA = [(-17, 15), (-16, 20), (-12, 25), (-10, 30), (-6, 33), (0, 36),
          (10, 37), (15, 32), (20, 32), (25, 31), (30, 31), (32, 31),
          (35, 28), (37, 22), (39, 18), (43, 12), (46, 11), (51, 11),
          (51, 5), (48, 0), (44, -5), (40, -10), (38, -15), (35, -20),
          (33, -26), (30, -30), (26, -34), (20, -35), (16, -32), (14, -27),
          (12, -20), (13, -12), (12, -6), (9, -1), (9, 4), (4, 6), (-3, 5),
          (-8, 5), (-13, 8), (-17, 12), (-17, 15)]
AUSTRALIA = [(113, -22), (114, -28), (115, -33), (118, -35), (124, -33),
             (129, -32), (132, -32), (135, -35), (138, -35), (140, -38),
             (144, -38), (147, -39), (150, -37), (153, -32), (153, -27),
             (151, -24), (149, -20), (146, -19), (143, -17), (142, -14),
             (142, -11), (139, -15), (136, -12), (135, -15), (132, -12),
             (130, -13), (126, -14), (124, -18), (120, -20), (116, -20),
             (113, -22)]
UK = [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53), (1, 51),
      (-3, 50)]

LAND_POLYS = [NORTH_AMERICA, GREENLAND, SOUTH_AMERICA, EURASIA, AFRICA,
              AUSTRALIA, UK]

PINS = [
    (1, -77, 39, "WASHINGTON", 0, 0),
    (2, 47, 25, "RIYADH", -4, 6),
    (3, 42, 17, "JAZAN", 8, -2),
    (4, 30, 50, "KYIV", -2, -8),
    (5, 36, 50, "KHARKIV", 8, 6),
    (6, 31, 30, "CAIRO", 4, 6),
    (7, 121, 31, "SHANGHAI", 0, 0),
    (8, -91, 41, "IOWA", 0, 0),
]


def fill_poly(cv, pts, c):
    """Scanline fill for a polygon given as (x, y) pixel points."""
    if len(pts) < 3:
        return
    miny = min(p[1] for p in pts)
    maxy = max(p[1] for p in pts)
    n = len(pts)
    for yy in range(miny, maxy + 1):
        xs = []
        for i in range(n):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % n]
            if (y0 <= yy < y1) or (y1 <= yy < y0):
                t = (yy - y0) / (y1 - y0)
                xs.append(int(x0 + t * (x1 - x0)))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            for xx in range(xs[k], xs[k + 1] + 1):
                cv.set(xx, yy, c)


def draw_map(cv, x, y, w, h):
    cv.rect(x, y, w, h, SEA)
    cv.rect(x, y, w, h, MID, fill=False)

    def proj(lon, lat):
        px = x + int((lon + 170) / 360.0 * w)
        py = y + int((85 - lat) / 145.0 * h)
        return px, py

    # graticule every 30 degrees
    for lon in range(-150, 181, 30):
        px, _ = proj(lon, 0)
        cv.vline(px, y, h, (190, 205, 218), 1)
    for lat in range(-60, 86, 30):
        _, py = proj(0, lat)
        cv.hline(x, py, w, (190, 205, 218), 1)
    # land
    for poly in LAND_POLYS:
        fill_poly(cv, [proj(lon, lat) for lon, lat in poly], LAND)
    # pins (dx, dy nudge apart the clustered Middle East / Ukraine pins)
    for num, lon, lat, _name, dx, dy in PINS:
        px, py = proj(lon, lat)
        px += dx
        py += dy
        cv.circle(px, py, 6, RED)
        cv.circle(px, py, 6, PAPER, fill=False)
        draw_text(cv, px - 2, py - 3, str(num), 1, PAPER)
    # legend
    legend = "1 WASHINGTON  2 RIYADH  3 JAZAN  4 KYIV  5 KHARKIV  6 CAIRO  7 SHANGHAI  8 IOWA"
    draw_text(cv, x, y + h + 4, legend, 1, DGREY)


# -------------------------------------------------------------------- main --
def main():
    cv = Canvas(W, H, PAPER)
    M = 24                      # margin
    CW = W - 2 * M              # content width = 976

    # ---- masthead ----
    cv.hline(M, 12, CW, INK, 3)
    draw_centered(cv, W // 2, 22, MASTHEAD, 6, INK)
    draw_centered(cv, W // 2, 70, SUBTITLE, 2, DGREY)
    cv.hline(M, 90, CW, INK, 2)
    draw_centered(cv, W // 2, 96, STRIP, 1, GREY)
    cv.hline(M, 108, CW, INK, 1)

    # ---- timeline strip: 2 rows x 3 cols ----
    col_w = CW // 3
    ty = 114
    for idx, (when, what) in enumerate(TIMELINE):
        cx = M + (idx % 3) * col_w
        cy = ty + (idx // 3) * 27
        draw_text(cv, cx, cy, when, 1, BLUE)
        draw_para(cv, cx, cy + 9, what, 1, col_w - 12, INK, leading=9)
    cv.hline(M, 174, CW, INK, 1)

    # ---- 3 leads ----
    ly = 182
    lead_h = 142
    illo_w = 190
    for li, lead in enumerate(LEADS):
        y0 = ly + li * (lead_h + 6)
        lead["illo"](cv, M, y0, illo_w, lead_h - 10)
        tx = M + illo_w + 16
        tw = CW - illo_w - 16
        draw_text(cv, tx, y0, lead["kicker"], 1, RED)
        draw_text(cv, tx, y0 + 11, lead["head"], 2, INK)
        draw_text(cv, tx, y0 + 29, lead["sub"], 1, GREY)
        fy = y0 + 42
        for fact in lead["facts"]:
            yb = fy
            fy = draw_para(cv, tx + 10, fy, fact, 1, tw - 10, INK, leading=10)
            cv.circle(tx + 3, yb + 3, 2, RED)
        draw_text(cv, tx, y0 + lead_h - 16, lead["tag"], 1, RED)
        draw_text(cv, tx + text_w(lead["tag"], 1) + 18, y0 + lead_h - 16,
                  lead["src"], 1, GREY)
        if li < 2:
            cv.hline(M, y0 + lead_h - 2, CW, MID, 1)
    cv.hline(M, 626, CW, INK, 2)

    # ---- secondaries: 2 cols x 5 rows ----
    draw_text(cv, M, 634, "MORE NEWS", 2, INK)
    draw_text(cv, M + text_w("MORE NEWS", 2) + 16, 634,
              "TEN MORE STORIES FROM AROUND THE WORLD", 1, GREY)
    col_w2 = CW // 2
    sy = 654
    for idx, (head, body) in enumerate(SECONDARIES):
        cx = M + (idx % 2) * col_w2
        cy = sy + (idx // 2) * 28
        draw_text(cv, cx, cy, head, 1, RED)
        draw_para(cv, cx, cy + 9, body, 1, col_w2 - 14, DGREY, leading=9)
    cv.hline(M, 796, CW, INK, 2)

    # ---- map (left) + ALSO ON (right) ----
    draw_text(cv, M, 804, "WHERE IT HAPPENED", 2, INK)
    draw_map(cv, M, 824, 500, 118)
    ax = M + 524
    draw_text(cv, ax, 804, "ALSO ON", 2, INK)
    ay = 824
    for i, item in enumerate(ALSO_ON):
        col = i // 7
        row = i % 7
        ix = ax + col * 228
        iy = ay + row * 19
        draw_text(cv, ix, iy, "- " + item, 1, INK)
    cv.hline(M, 978, CW, INK, 2)

    # ---- DATE CHECK footer ----
    fy = 986
    for ln in DATE_CHECK:
        draw_centered(cv, W // 2, fy, ln, 1, DGREY)
        fy += 10
    cv.hline(M, 1010, CW, INK, 3)

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
    size = write_png(cv, out)
    print("wrote %s  %d bytes  %dx%d" % (out, size, W, H))


if __name__ == "__main__":
    main()
