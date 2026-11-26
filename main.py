#!/usr/bin/env python3
"""THE WORLD IN ONE PAGE - Thursday 26 November 2026, MORNING EDITION.

A newspaper front page drawn entirely in code for the make.fun
news-image-20261126 bounty. Python standard library only: own 5x7 bitmap
font, own PNG encoder, no photos, no network, fully deterministic
(two runs produce byte-identical output).

Run:  python3 main.py        -> writes /output/entry.png (1024x1024)
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
# 5x7 glyphs, '1' = ink. Rendered in ALL CAPS; the normaliser below folds
# accents and punctuation onto glyphs that exist.
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
def illo_tariffs(cv, x, y, w, h):
    """Cargo ship stacked with crates, big % flag."""
    cv.rect(x, y, w, h, (235, 242, 250))
    cv.rect(x, y, w, h, MID, fill=False)
    cv.hline(x + 8, y + h - 22, w - 16, BLUE, 2)
    cv.hline(x + 30, y + h - 14, w - 60, BLUE, 2)
    cv.tri([(x + 30, y + h - 34), (x + w - 30, y + h - 34),
            (x + w - 58, y + h - 20)], RED)
    cv.rect(x + 30, y + h - 48, w - 60, 14, RED)
    cx0 = x + 52
    for i in range(3):
        cv.rect(cx0 + i * 52, y + h - 48 - 34, 46, 30, GOLD, fill=False)
        cv.line(cx0 + i * 52, y + h - 48 - 34, cx0 + i * 52 + 46,
                y + h - 48 - 4, GOLD)
        cv.line(cx0 + i * 52 + 46, y + h - 48 - 34, cx0 + i * 52,
                y + h - 48 - 4, GOLD)
    cv.rect(x + w - 92, y + 16, 34, 34, INK)
    draw_text(cv, x + w - 88, y + 22, "%", 2, PAPER)
    draw_text(cv, x + 14, y + 10, "14 PARTNERS", 1, BLUE)


def illo_gulf(cv, x, y, w, h):
    """Refinery towers, flame and smoke plume, missile streak."""
    cv.rect(x, y, w, h, (250, 238, 226))
    cv.rect(x, y, w, h, MID, fill=False)
    # ground
    cv.hline(x + 8, y + h - 20, w - 16, INK, 2)
    # refinery towers
    for tx in (x + 22, x + 52, x + 82):
        cv.rect(tx, y + h - 62, 22, 42, INK, fill=False)
        cv.line(tx + 4, y + h - 62, tx + 11, y + h - 78, INK)
        cv.line(tx + 18, y + h - 62, tx + 11, y + h - 78, INK)
    # flame on middle tower
    fx, fy = x + 63, y + h - 92
    cv.tri([(fx, fy), (fx - 8, fy + 18), (fx + 8, fy + 18)], RED)
    cv.tri([(fx, fy + 6), (fx - 5, fy + 18), (fx + 5, fy + 18)], GOLD)
    # smoke plume drifting right
    for (px, py, pr) in [(x + 150, y + 30, 8), (x + 168, y + 44, 11),
                         (x + 186, y + 60, 13), (x + 200, y + 78, 10)]:
        cv.circle(px, py, pr, GREY)
    # missile streak
    mx, my = x + w - 66, y + 18
    cv.line(mx, my, mx + 34, my + 20, RED)
    cv.tri([(mx + 34, my + 20), (mx + 22, my + 14), (mx + 24, my + 26)], RED)
    draw_text(cv, x + 14, y + 8, "RAS TANURA", 2, RED)


def illo_ukraine(cv, x, y, w, h):
    """City building under a burst, shield below."""
    cv.rect(x, y, w, h, (236, 238, 244))
    cv.rect(x, y, w, h, MID, fill=False)
    # building
    bx, by = x + 34, y + h - 66
    cv.rect(bx, by, 66, 46, INK, fill=False)
    for wy in (by + 8, by + 24):
        for wx in (bx + 8, bx + 26, bx + 44):
            cv.rect(wx, wy, 12, 10, BLUE, fill=False)
    # burst above the roof
    cx, cy = bx + 33, y + 26
    for k in range(8):
        ang = k * math.pi / 4.0
        ex = int(cx + 26 * math.cos(ang))
        ey = int(cy + 26 * math.sin(ang))
        cv.line(cx, cy, ex, ey, GOLD)
    cv.circle(cx, cy, 6, RED)
    # shield
    sx, sy = x + w - 74, y + h - 56
    cv.tri([(sx, sy), (sx + 40, sy), (sx + 20, sy + 40)], BLUE)
    draw_text(cv, sx + 14, sy + 12, "?", 2, PAPER)
    draw_text(cv, x + 14, y + 8, "KYIV", 2, BLUE)


# -------------------------------------------------------------------- data --
MASTHEAD = "THE WORLD IN ONE PAGE"
SUBTITLE = "THURSDAY 26 NOVEMBER 2026 - MORNING EDITION - VERIFIED TO 08:00 CST"
STRIP = "27 STORIES - 3 LEADS - 10 SECONDARIES - 14 IN BRIEF - 8 PINS ON MAP"

TIMELINE = [
    ("THU 26 NOV 00:12 GMT", "WASHINGTON POST FIRST REPORTS TRUMP TARIFFS"),
    ("WED 25 NOV 10:15 LOCAL", "ARMY DETONATES 4,500 KG OF LEAD AZIDE IN IOWA"),
    ("WED 25 NOV", "RUSSIAN MISSILE HITS KYIV SHOPPING MALL"),
    ("WED 25 NOV OVERNIGHT", "HOUTHI MISSILE INTERCEPTED OVER RIYADH"),
    ("WED 25 NOV 00:18 GMT", "SHENZHOU-24 LIFTS OFF WITH PAKISTAN'S FIRST ASTRONAUT"),
    ("THU 26 NOV 01:05 KYIV", "ZELENSKY: NO GOOD NEWS ON INTERCEPTORS"),
]

LEADS = [
    dict(kicker="LEAD 1 - WASHINGTON - ANNOUNCED 25 NOV",
         illo=illo_tariffs,
         head="TRUMP UNVEILS NEW TARIFFS ON 14 PARTNERS",
         sub=("Announced 25 Nov; China up to 40%, Vietnam up to 35%, others "
              "20-25%; tariffs take effect in 2027 - not today"),
         facts=[
             "Announced Wednesday in Washington, first reported 00:12 GMT. "
             "14 partners including the EU, Japan, India, Taiwan and South Korea.",
             "Legal basis: a March 2026 White House 'overcapacity' probe. It "
             "follows a Supreme Court ruling that 'Liberation Day' tariffs were "
             "illegal; about $100B was refunded.",
             "The EU is opposed and says the agreed cap was 15%. The "
             "US-China trade-war ceasefire expires on 10 Jan 2027.",
         ],
         tag="ANNOUNCED 25 NOV - IN FORCE 2027",
         src="Sources: BBC - Washington Post - CNBC - NPR - Al Jazeera"),
    dict(kicker="LEAD 2 - THE GULF - ATTACKS CONFIRMED",
         illo=illo_gulf,
         head="GULF WAR WIDENS: HOUTHIS HIT RIYADH AND RAS TANURA",
         sub=("Missile intercepted over Riyadh; tanker mined in Hormuz; "
              "UK sends Typhoon jets to Saudi Arabia"),
         facts=[
             "Overnight explosions in Sanaa; the Saudi-led coalition "
             "intercepted a Houthi ballistic missile heading for Riyadh.",
             "The Houthis CLAIM a strike on the Ras Tanura refinery; "
             "satellite images show a large smoke plume. The claim is not "
             "independently verified.",
             "A tanker hit a mine in the Strait of Hormuz and caught fire; "
             "Iran says 3 ships hit mines. The PIF Tower was hit, 11 injured.",
         ],
         tag="DAMAGE CLAIMS UNVERIFIED",
         src="Sources: Al Jazeera live - Reuters / Planet Labs - UKMTO"),
    dict(kicker="LEAD 3 - UKRAINE - LEAK PUBLISHED",
         illo=illo_ukraine,
         head="LEAK PUTS RUSSIAN WAR DEAD NEAR 500,000",
         sub=("Registry data published; Kyiv mall hit; US said to rule out "
              "troops in any postwar guarantee"),
         facts=[
             "Leaked Russian registry data puts Russian soldiers dead at about "
             "490,000-500,000. Western estimates top 700,000 - a different "
             "method; do not mix the figures.",
             "A Russian ballistic missile hit a Kyiv shopping mall, at least "
             "3-4 injured; blackouts in 5 regions; the Zaporizhzhia plant "
             "lost external power a 17th time.",
             "A US envoy privately said postwar guarantees exclude US troops "
             "and bases - reported, not formally announced. Zelensky: "
             "'not yet on paper'.",
         ],
         tag="US POSITION REPORTED, NOT ANNOUNCED",
         src="Sources: CBS - BBC - The Guardian - Le Monde - Kyiv Independent"),
]

SECONDARIES = [
    ("AI SELL-OFF DEEPENS",
     "Nasdaq -0.6%, Nvidia -3.4% after an 8% intraday slide; Anthropic falls "
     "below its $83 IPO price; Amazon down over 3%."),
    ("NETANYAHU CASE IN DOUBT",
     "Judge asks the attorney general to reconsider the bribery case; formal "
     "dismissal or a plea deal now expected."),
    ("XI PURGE REACHES SHANGHAI",
     "Politburo member Chen Jining under investigation - the 4th sitting "
     "member probed; plenum expelled a record 33."),
    ("IOWA BLAST 'EXTREMELY SUCCESSFUL'",
     "Army says 4,500 kg of lead azide went up cleanly at 10:15 local; no "
     "damage, EPA monitors recorded zero detections."),
    ("MACY'S PARADE POSTPONED",
     "100th Thanksgiving parade moves to Saturday after a storm brings 60 "
     "mph gusts; first weather delay in its history."),
    ("KING TIDES BATTER CALIFORNIA",
     "Strongest El Nino on record drives coastal flooding into 'uncharted "
     "territory'; Pacifica pier partly collapses."),
    ("CAIRO TANKER FIRE KILLS 31",
     "Fuel tanker overturns and catches fire in Imbaba, Giza; at least 31 "
     "dead, 21 hurt, 27 vehicles burned."),
    ("76 HOSTAGES FREED IN CARTAGENA",
     "Police storm an Exito supermarket after a 17-hour standoff; one "
     "gunman killed; Petro calls it a failed robbery."),
    ("N. KOREA EXPELS SWISS ENVOY",
     "Top Swiss diplomat ordered out within 48 hours; trigger was Swiss "
     "sanctions on a children's camp in Wonsan."),
    ("COP31 REBOUNDS AFTER COLLAPSE",
     "Longest-ever UN climate summit ended 22 Nov in Antalya with no deal - "
     "the first since Copenhagen 2009; talks resume."),
]

ALSO_ON = [
    "ABREGO GARCIA ARRIVES IN SPAIN",
    "SPAIN VOTES SUNDAY 29 NOV",
    "SOLOMONS END CHINA PACT",
    "RAMAPHOSA SURVIVES VOTE",
    "HAMAS SECURITY CHIEF KILLED",
    "SHENZHOU-24 LAUNCHES",
    "PLANE CRASH KILLS 6 IN US",
    "SPACEX STARMIND APPROVED",
    "HUAWEI GUILTY OF THEFT",
    "US TO BLACKLIST MEGASPEED",
    "RECORD MIGRANT DAY IN CANARIES",
    "2 LIBYAN OFFICERS KILLED",
    "BAGHDAD TAKES KURD FIELDS",
    "UK SANCTIONS MYANMAR GENERALS",
]

DATE_CHECK = [
    "DATE CHECK - 26 NOVEMBER 2026 IS A THURSDAY. STORIES THAT BROKE ON "
    "OTHER DAYS ARE NOT IN THIS EDITION.",
    "TARIFFS WERE ANNOUNCED 25 NOV AND TAKE EFFECT IN 2027. HOUTHI DAMAGE "
    "CLAIMS ARE UNVERIFIED. US 'NO TROOPS' POSITION IS REPORTED, NOT ANNOUNCED.",
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
    (2, 47, 25, "RIYADH", -2, 8),
    (3, 56, 26, "HORMUZ", 10, -4),
    (4, 30, 50, "KYIV", 0, -6),
    (5, 35, 31, "GAZA", -10, -6),
    (6, 121, 31, "SHANGHAI", 0, 0),
    (7, -91, 41, "IOWA", 0, 0),
    (8, 31, 30, "CAIRO", 4, 8),
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
    # pins (dx, dy nudge apart the clustered Middle East pins)
    for num, lon, lat, _name, dx, dy in PINS:
        px, py = proj(lon, lat)
        px += dx
        py += dy
        cv.circle(px, py, 6, RED)
        cv.circle(px, py, 6, PAPER, fill=False)
        draw_text(cv, px - 2, py - 3, str(num), 1, PAPER)
    # legend
    legend = "1 WASHINGTON  2 RIYADH  3 HORMUZ  4 KYIV  5 GAZA  6 SHANGHAI  7 IOWA  8 CAIRO"
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

    os.makedirs("/output", exist_ok=True)
    size = write_png(cv, "/output/entry.png")
    print("wrote /output/entry.png  %d bytes  %dx%d" % (size, W, H))


if __name__ == "__main__":
    main()
