"""
Hello, World! — แอนิเมชันสวยๆ ด้วย tkinter (single file, ไม่ต้องติดตั้งอะไรเพิ่ม)

วิธีรัน:   python hello_world.py
ควบคุม:
    คลิกเมาส์  -> ระเบิดพลุสีรุ้ง
    Space      -> เล่นแอนิเมชันใหม่
    Esc        -> ออกจากโปรแกรม

    By Stams  eng
"""

import colorsys
import math
import random
import time
import tkinter as tk
import tkinter.font as tkfont

# ---------------------------------------------------------------- settings
W, H = 900, 520
TEXT = "Hello, World!"
SUBTITLE = "—  made with Python & tkinter  —"
FRAME_MS = 16                      # ~60 FPS
BG_STOPS = ["#0f0c29", "#302b63", "#24243e"]   # ไล่สีพื้นหลัง บน -> กลาง -> ล่าง
STAR_COUNT = 140
FONT_FAMILY = "Helvetica"


# ---------------------------------------------------------------- helpers
def hex_to_rgb(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(r, g, b):
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    return rgb_to_hex(lerp(r1, r2, t), lerp(g1, g2, t), lerp(b1, b2, t))


def hsv(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
    return rgb_to_hex(r * 255, g * 255, b * 255)


def clamp01(x):
    return max(0.0, min(1.0, x))


def ease_out_bounce(x):
    n1, d1 = 7.5625, 2.75
    if x < 1 / d1:
        return n1 * x * x
    if x < 2 / d1:
        x -= 1.5 / d1
        return n1 * x * x + 0.75
    if x < 2.5 / d1:
        x -= 2.25 / d1
        return n1 * x * x + 0.9375
    x -= 2.625 / d1
    return n1 * x * x + 0.984375


def ease_out_cubic(x):
    return 1 - (1 - x) ** 3


def bg_color_at(y):
    """สีพื้นหลังที่ระดับความสูง y (ใช้ให้ของที่จางหายกลืนกับพื้น)"""
    t = clamp01(y / H) * (len(BG_STOPS) - 1)
    i = min(int(t), len(BG_STOPS) - 2)
    return lerp_color(BG_STOPS[i], BG_STOPS[i + 1], t - i)


# ---------------------------------------------------------------- app
class HelloWorldApp:
    def __init__(self, root):
        self.root = root
        root.title("Hello, World!")
        root.resizable(False, False)

        self.c = tk.Canvas(root, width=W, height=H, highlightthickness=0,
                           bg=BG_STOPS[0])
        self.c.pack()

        self.font = tkfont.Font(family=FONT_FAMILY, size=66, weight="bold")
        self.base_y = H / 2 - 20

        self._draw_background()
        self._make_stars()
        self._make_letters()
        self.subtitle = self.c.create_text(
            W / 2, H / 2 + 75, text=SUBTITLE,
            font=(FONT_FAMILY, 15, "italic"), fill=bg_color_at(H / 2 + 75))
        self.hint = self.c.create_text(
            W / 2, H - 22, text="click = fireworks   ·   space = replay   ·   esc = quit",
            font=(FONT_FAMILY, 10), fill=bg_color_at(H - 22))

        self.particles = []
        self.restart()

        root.bind("<Button-1>", lambda e: self.burst(e.x, e.y, 70))
        root.bind("<space>", lambda e: self.restart())
        root.bind("<Escape>", lambda e: root.destroy())

        self.last = time.perf_counter()
        self.tick()

    # ---------------- scene setup
    def _draw_background(self):
        for y in range(H):
            self.c.create_line(0, y, W, y, fill=bg_color_at(y))

    def _make_stars(self):
        self.stars = []
        for _ in range(STAR_COUNT):
            x, y = random.uniform(0, W), random.uniform(0, H)
            r = random.choice([0.8, 1, 1, 1.4, 2])
            sid = self.c.create_oval(x - r, y - r, x + r, y + r, outline="", fill="#ffffff")
            self.stars.append({
                "id": sid, "x": x, "y": y, "r": r,
                "phase": random.uniform(0, math.tau),
                "speed": random.uniform(1.0, 3.5),
                "drift": random.uniform(4, 14),     # ความเร็วลอยไปทางซ้าย (px/s)
            })

    def _make_letters(self):
        widths = [self.font.measure(ch) for ch in TEXT]
        x = W / 2 - sum(widths) / 2
        self.letters = []
        for i, (ch, w) in enumerate(zip(TEXT, widths)):
            cx = x + w / 2
            x += w
            if ch == " ":
                continue
            self.letters.append({"ch": ch, "x": cx, "i": i})

        # สร้างเป็นชั้นๆ: เงา -> แสงเรือง -> ตัวอักษรจริง
        offsets = [(math.cos(a) * 3, math.sin(a) * 3)
                   for a in (k * math.tau / 8 for k in range(8))]
        for L in self.letters:
            L["shadow"] = self.c.create_text(0, -200, text=L["ch"], font=self.font,
                                             fill="#05040f")
        for L in self.letters:
            L["glow"] = [(self.c.create_text(0, -200, text=L["ch"], font=self.font), dx, dy)
                         for dx, dy in offsets]
        for L in self.letters:
            L["main"] = self.c.create_text(0, -200, text=L["ch"], font=self.font)

    # ---------------- interaction
    def restart(self):
        self.t0 = time.perf_counter()
        for p in self.particles:
            self.c.delete(p["id"])
        self.particles = []
        self.landed = set()

    def spawn(self, x, y, hue, speed, life, size, gravity=180):
        a = random.uniform(0, math.tau)
        s = random.uniform(0.3, 1.0) * speed
        pid = self.c.create_oval(x, y, x, y, outline="", fill=hsv(hue, 0.6, 1))
        self.particles.append({
            "id": pid, "x": x, "y": y,
            "vx": math.cos(a) * s, "vy": math.sin(a) * s,
            "life": life, "max": life, "size": size,
            "hue": hue, "g": gravity,
        })

    def burst(self, x, y, n):
        base = random.random()
        for _ in range(n):
            self.spawn(x, y, base + random.uniform(-0.15, 0.15),
                       speed=360, life=random.uniform(0.8, 1.6),
                       size=random.uniform(2, 4.5))

    # ---------------- main loop
    def tick(self):
        now = time.perf_counter()
        dt = min(now - self.last, 0.05)
        self.last = now
        t = now - self.t0

        self._update_stars(now, dt)
        self._update_letters(t)
        self._update_subtitle(t)
        self._update_particles(t, dt)

        self.root.after(FRAME_MS, self.tick)

    def _update_stars(self, now, dt):
        for s in self.stars:
            s["x"] -= s["drift"] * dt
            if s["x"] < -3:
                s["x"] = W + 3
                s["y"] = random.uniform(0, H)
            tw = 0.5 + 0.5 * math.sin(now * s["speed"] + s["phase"])
            r = s["r"] * (0.7 + 0.5 * tw)
            self.c.coords(s["id"], s["x"] - r, s["y"] - r, s["x"] + r, s["y"] + r)
            self.c.itemconfig(s["id"], fill=lerp_color(bg_color_at(s["y"]), "#ffffff",
                                                       0.25 + 0.75 * tw))

    def _update_letters(self, t):
        n = len(self.letters)
        for k, L in enumerate(self.letters):
            delay = k * 0.09
            p = clamp01((t - delay) / 1.0)
            # ตกลงมาแบบเด้ง
            y = lerp(-90, self.base_y, ease_out_bounce(p))
            # หลังลงจอดแล้วค่อยๆ เริ่มลอยเป็นคลื่น
            wave_amt = ease_out_cubic(clamp01((t - delay - 1.0) / 1.2))
            y += math.sin(t * 2.4 - k * 0.55) * 12 * wave_amt
            x = L["x"]

            # ตอนแตะพื้นครั้งแรก ปล่อยประกายเล็กๆ
            if p >= 0.36 and k not in self.landed:
                self.landed.add(k)
                for _ in range(10):
                    self.spawn(x, self.base_y + 30, k / n, speed=160,
                               life=random.uniform(0.4, 0.9), size=2)

            hue = t * 0.08 + k / n * 0.6
            fade = clamp01(p * 3)
            bg = bg_color_at(y)

            self.c.coords(L["shadow"], x + 5, y + 7)
            self.c.itemconfig(L["shadow"], fill=lerp_color(bg, "#05040f", fade * 0.8))

            glow_col = lerp_color(bg, hsv(hue, 0.85, 0.55), fade)
            pulse = 1 + 0.35 * math.sin(t * 3 + k)
            for gid, dx, dy in L["glow"]:
                self.c.coords(gid, x + dx * pulse, y + dy * pulse)
                self.c.itemconfig(gid, fill=glow_col)

            self.c.coords(L["main"], x, y)
            self.c.itemconfig(L["main"], fill=lerp_color(bg, hsv(hue, 0.35, 1.0), fade))

            # ประกายวิบวับสุ่มหลังอินโทรจบ
            if t > 2.5 and random.random() < 0.012:
                self.spawn(x + random.uniform(-20, 20), y + random.uniform(-35, 25),
                           hue, speed=60, life=random.uniform(0.6, 1.2),
                           size=random.uniform(1.5, 3), gravity=-20)

    def _update_subtitle(self, t):
        p = clamp01((t - 2.2) / 1.2)
        y = H / 2 + 75 + (1 - ease_out_cubic(p)) * 20
        self.c.coords(self.subtitle, W / 2, y)
        self.c.itemconfig(self.subtitle, fill=lerp_color(bg_color_at(y), "#cfc9ff", p))
        hp = clamp01((t - 3.5) / 1.0) * (0.55 + 0.15 * math.sin(t * 2))
        self.c.itemconfig(self.hint, fill=lerp_color(bg_color_at(H - 22), "#8f89c9", hp))

    def _update_particles(self, t, dt):
        alive = []
        for p in self.particles:
            p["life"] -= dt
            if p["life"] <= 0 or not (-50 < p["x"] < W + 50 and -50 < p["y"] < H + 50):
                self.c.delete(p["id"])
                continue
            p["vy"] += p["g"] * dt
            p["vx"] *= 0.985
            p["vy"] *= 0.985
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            k = p["life"] / p["max"]
            r = p["size"] * (0.4 + 0.6 * k)
            self.c.coords(p["id"], p["x"] - r, p["y"] - r, p["x"] + r, p["y"] + r)
            col = hsv(p["hue"] + t * 0.1, 0.55, 1.0)
            self.c.itemconfig(p["id"], fill=lerp_color(bg_color_at(p["y"]), col, k))
            alive.append(p)
        self.particles = alive


if __name__ == "__main__":
    root = tk.Tk()
    HelloWorldApp(root)
    root.mainloop()