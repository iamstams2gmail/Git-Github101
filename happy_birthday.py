"""
Happy Birthday — แอนิเมชันเต็มจอด้วย tkinter (single file, ไม่ต้องติดตั้งอะไรเพิ่ม)

วิธีรัน:   python happy_birthday.py

ควบคุม:
    คลิกตัว "y" ท้ายคำว่า Birthday (ตัว y ใน "day")  -> ปิดโปรแกรม (ปุ่มปิดลับ)
    คลิกที่อื่น                                     -> จุดพลุ
    Space                                           -> เล่นแอนิเมชันใหม่
    Esc                                             -> ทางออกฉุกเฉิน (ปิดได้ที่ ALLOW_ESC)
"""

import colorsys
import math
import random
import time
import tkinter as tk
import tkinter.font as tkfont

# ================================================================ ปรับแต่งได้ตรงนี้
LINE1 = "Happy"
LINE2 = "Birthday"                       # ปุ่มปิดลับ = ตัวอักษรสุดท้ายของบรรทัดนี้ (y)
MESSAGE = "Wishing you a year full of love, laughter & cake!"
ALLOW_ESC = True                         # True = กด Esc ออกได้ด้วย (กันติดเต็มจอ)
FRAME_MS = 16                            # ~60 FPS
BALLOON_COUNT = 14
CONFETTI_COUNT = 150
CANDLES = 5

BG_STOPS = ["#120a2a", "#2e1252", "#4a1a5e", "#2a0f3d"]   # ไล่สีพื้นหลัง บน -> ล่าง
BALLOON_COLORS = ["#ff4d6d", "#ffb703", "#4cc9f0", "#80ed99", "#c77dff",
                  "#ff8fab", "#f15bb5", "#00bbf9", "#fee440"]
CONFETTI_COLORS = ["#ff4d6d", "#ffd166", "#06d6a0", "#4cc9f0", "#c77dff",
                   "#ff9f1c", "#f15bb5", "#ffffff"]
TITLE_FONTS = ["Segoe Print", "Comic Sans MS", "Chalkboard SE", "Georgia", "Helvetica"]
TEXT_FONTS = ["Segoe UI", "Helvetica Neue", "Helvetica", "Arial"]


# ================================================================ helpers
def hex_to_rgb(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(r, g, b):
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"


def lerp(a, b, t):
    return a + (b - a) * t


def clamp01(x):
    return max(0.0, min(1.0, x))


def lerp_color(c1, c2, t):
    t = clamp01(t)
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    return rgb_to_hex(lerp(r1, r2, t), lerp(g1, g2, t), lerp(b1, b2, t))


def hsv(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
    return rgb_to_hex(r * 255, g * 255, b * 255)


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


def pick_font(candidates):
    available = set(tkfont.families())
    for f in candidates:
        if f in available:
            return f
    return "TkDefaultFont"


# ================================================================ app
class BirthdayApp:
    def __init__(self, root):
        self.root = root
        root.title("Happy Birthday!")
        root.attributes("-fullscreen", True)
        root.configure(bg=BG_STOPS[0])
        root.update_idletasks()
        self.W = W = root.winfo_screenwidth()
        self.H = H = root.winfo_screenheight()

        self.c = tk.Canvas(root, width=W, height=H, highlightthickness=0, bg=BG_STOPS[0])
        self.c.pack(fill="both", expand=True)

        self._build_bg_lut()
        self._draw_background()
        self._make_balloons()
        self._make_confetti()
        self._make_title()
        self._make_message()
        self._make_cake()

        self.particles = []
        self.restart()

        self.c.bind("<Button-1>", self.on_click)
        root.bind("<space>", lambda e: self.restart())
        if ALLOW_ESC:
            root.bind("<Escape>", lambda e: root.destroy())
        root.focus_force()

        self.last = time.perf_counter()
        self.tick()

    # ------------------------------------------------------------ background
    def _build_bg_lut(self):
        step = 4
        self.lut_step = step
        self.bg_lut = []
        n = len(BG_STOPS) - 1
        for y in range(0, self.H + step, step):
            t = clamp01(y / self.H) * n
            i = min(int(t), n - 1)
            self.bg_lut.append(lerp_color(BG_STOPS[i], BG_STOPS[i + 1], t - i))

    def bg(self, y):
        i = int(y / self.lut_step)
        return self.bg_lut[max(0, min(len(self.bg_lut) - 1, i))]

    def _draw_background(self):
        s = self.lut_step
        for k, col in enumerate(self.bg_lut):
            self.c.create_rectangle(0, k * s, self.W, k * s + s, fill=col, outline="")

    # ------------------------------------------------------------ balloons
    def _make_balloons(self):
        self.balloons = []
        for _ in range(BALLOON_COUNT):
            b = {
                "string": self.c.create_line(0, 0, 0, 0, smooth=True, width=1.5,
                                             fill="#cfc4ea"),
                "body": self.c.create_oval(0, 0, 0, 0, outline=""),
                "shine": self.c.create_oval(0, 0, 0, 0, outline=""),
                "knot": self.c.create_polygon(0, 0, 0, 0, 0, 0, outline=""),
            }
            self._reset_balloon(b, initial=True)
            self.balloons.append(b)

    def _reset_balloon(self, b, initial=False):
        H, W = self.H, self.W
        b["r"] = random.uniform(0.035, 0.06) * H
        b["x"] = random.uniform(0.03, 0.97) * W
        b["y"] = (random.uniform(0.3, 1.3) * H if initial
                  else H + b["r"] * 1.5 + random.uniform(0, H * 0.4))
        b["speed"] = random.uniform(0.05, 0.11) * H
        b["phase"] = random.uniform(0, math.tau)
        col = random.choice(BALLOON_COLORS)
        self.c.itemconfig(b["body"], fill=col)
        self.c.itemconfig(b["shine"], fill=lerp_color(col, "#ffffff", 0.55))
        self.c.itemconfig(b["knot"], fill=lerp_color(col, "#000000", 0.25))

    def _update_balloons(self, t, dt):
        for b in self.balloons:
            r = b["r"]
            b["y"] -= b["speed"] * dt
            if b["y"] + r * 5 < 0:
                self._reset_balloon(b)
            x = b["x"] + math.sin(t * 0.8 + b["phase"]) * self.H * 0.02
            y = b["y"]
            self.c.coords(b["body"], x - r, y - 1.2 * r, x + r, y + 1.2 * r)
            self.c.coords(b["shine"], x - 0.55 * r, y - 0.85 * r, x - 0.2 * r, y - 0.35 * r)
            ky = y + 1.2 * r
            self.c.coords(b["knot"], x, ky - 2, x - 0.15 * r, ky + 0.18 * r,
                          x + 0.15 * r, ky + 0.18 * r)
            pts = [x, ky + 0.18 * r]
            for k in range(1, 5):
                pts += [x + math.sin(t * 2.2 + b["phase"] + k) * r * 0.18 * k / 4,
                        ky + 0.18 * r + k * 0.8 * r]
            self.c.coords(b["string"], *pts)

    # ------------------------------------------------------------ confetti
    def _make_confetti(self):
        self.confetti = []
        for _ in range(CONFETTI_COUNT):
            f = {"id": self.c.create_polygon(0, 0, 0, 0, 0, 0, 0, 0, outline="")}
            self._reset_confetti(f, initial=True)
            self.confetti.append(f)

    def _reset_confetti(self, f, initial=False):
        H, W = self.H, self.W
        f["x"] = random.uniform(0, W)
        f["y"] = random.uniform(-H, H) if initial else random.uniform(-H * 0.2, -10)
        f["vy"] = random.uniform(0.07, 0.17) * H
        f["amp"] = random.uniform(0.02, 0.06) * H
        f["phase"] = random.uniform(0, math.tau)
        f["ang"] = random.uniform(0, math.tau)
        f["spin"] = random.uniform(-4, 4)
        f["flip"] = random.uniform(0, math.tau)
        f["flip_v"] = random.uniform(3, 8)
        f["w"] = random.uniform(0.006, 0.011) * H
        f["h"] = f["w"] * random.uniform(1.4, 2.2)
        f["col"] = random.choice(CONFETTI_COLORS)

    def _update_confetti(self, t, dt):
        for f in self.confetti:
            f["y"] += f["vy"] * dt
            f["x"] += math.sin(t * 1.6 + f["phase"]) * f["amp"] * dt
            f["ang"] += f["spin"] * dt
            f["flip"] += f["flip_v"] * dt
            if f["y"] > self.H + 20:
                self._reset_confetti(f)
            fl = math.cos(f["flip"])
            hw, hh = f["w"] / 2 * max(0.08, abs(fl)), f["h"] / 2
            ca, sa = math.cos(f["ang"]), math.sin(f["ang"])
            pts = []
            for px, py in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)):
                pts += [f["x"] + px * ca - py * sa, f["y"] + px * sa + py * ca]
            self.c.coords(f["id"], *pts)
            self.c.itemconfig(f["id"], fill=lerp_color(f["col"], "#000000",
                                                       0.4 * (1 - abs(fl))))

    # ------------------------------------------------------------ title letters
    def _make_title(self):
        W, H = self.W, self.H
        family = pick_font(TITLE_FONTS)
        px = int(H * 0.17)
        while True:
            self.font = tkfont.Font(family=family, size=-px, weight="bold")
            widest = max(self.font.measure(LINE1), self.font.measure(LINE2))
            if widest <= W * 0.86 or px < 20:
                break
            px = int(px * 0.92)
        self.font_px = px

        self.letters = []
        lines = [(LINE1, H * 0.25), (LINE2, H * 0.25 + px * 1.15)]
        order = 0
        for li, (text, base_y) in enumerate(lines):
            widths = [self.font.measure(ch) for ch in text]
            x = W / 2 - sum(widths) / 2
            for ch, w in zip(text, widths):
                cx = x + w / 2
                x += w
                if ch == " ":
                    continue
                self.letters.append({"ch": ch, "x": cx, "base_y": base_y,
                                     "k": order, "line": li})
                order += 1

        g = max(2, H * 0.004)
        offsets = [(math.cos(a) * g, math.sin(a) * g)
                   for a in (k * math.tau / 6 for k in range(6))]
        for L in self.letters:
            L["shadow"] = self.c.create_text(0, -500, text=L["ch"], font=self.font)
        for L in self.letters:
            L["glow"] = [(self.c.create_text(0, -500, text=L["ch"], font=self.font), dx, dy)
                         for dx, dy in offsets]
        for L in self.letters:
            L["main"] = self.c.create_text(0, -500, text=L["ch"], font=self.font)

        # ปุ่มปิดลับ: ตัวอักษรสุดท้ายของบรรทัดที่ 2 (ตัว y ใน "day")
        self.close_item = [L for L in self.letters if L["line"] == 1][-1]["main"]

    def _update_title(self, t):
        n = len(self.letters)
        H = self.H
        for L in self.letters:
            k = L["k"]
            delay = 0.3 + k * 0.1
            p = clamp01((t - delay) / 1.0)
            y = lerp(-H * 0.15, L["base_y"], ease_out_bounce(p))
            wave = ease_out_cubic(clamp01((t - delay - 1.0) / 1.2))
            y += math.sin(t * 2.3 - k * 0.5) * H * 0.015 * wave
            x = L["x"]

            if p >= 0.36 and k not in self.landed:
                self.landed.add(k)
                for _ in range(12):
                    self.spawn(x, L["base_y"] + self.font_px * 0.4, k / n,
                               speed=H * 0.18, life=random.uniform(0.4, 0.9),
                               size=H * 0.003)

            hue = t * 0.07 + k / n * 0.8
            fade = clamp01(p * 3)
            bgc = self.bg(y)
            sh = H * 0.006
            self.c.coords(L["shadow"], x + sh, y + sh * 1.4)
            self.c.itemconfig(L["shadow"], fill=lerp_color(bgc, "#07031a", fade * 0.85))

            glow = lerp_color(bgc, hsv(hue, 0.9, 0.6), fade)
            pulse = 1 + 0.4 * math.sin(t * 3 + k)
            for gid, dx, dy in L["glow"]:
                self.c.coords(gid, x + dx * pulse, y + dy * pulse)
                self.c.itemconfig(gid, fill=glow)

            self.c.coords(L["main"], x, y)
            self.c.itemconfig(L["main"], fill=lerp_color(bgc, hsv(hue, 0.3, 1.0), fade))

            if t > 3 and random.random() < 0.01:
                self.spawn(x + random.uniform(-0.3, 0.3) * self.font_px,
                           y + random.uniform(-0.45, 0.3) * self.font_px, hue,
                           speed=H * 0.05, life=random.uniform(0.6, 1.2),
                           size=H * random.uniform(0.002, 0.004), gravity=-H * 0.02)

    # ------------------------------------------------------------ message (typewriter)
    def _make_message(self):
        size = max(12, int(self.H * 0.032))
        self.msg_y = self.H * 0.25 + self.font_px * 1.15 + self.font_px * 0.75
        self.msg = self.c.create_text(self.W / 2, self.msg_y, text="",
                                      font=(pick_font(TEXT_FONTS), -size, "italic"),
                                      fill="#f3e9ff")

    def _update_message(self, t):
        start = 0.3 + len(self.letters) * 0.1 + 1.0
        n = int(clamp01((t - start) / 2.2) * len(MESSAGE))
        cursor = "▏" if (n < len(MESSAGE) and int(t * 3) % 2 == 0) else " "
        self.c.itemconfig(self.msg, text=MESSAGE[:n] + (cursor if n > 0 else ""))
        self.c.itemconfig(self.msg, fill=lerp_color("#f3e9ff", "#ffd6f0",
                                                    0.5 + 0.5 * math.sin(t * 2)))

    # ------------------------------------------------------------ cake
    def _make_cake(self):
        W, H, c = self.W, self.H, self.c
        cx = W / 2
        cw = min(W * 0.22, H * 0.34)
        bottom = H * 0.965
        h1, h2 = cw * 0.32, cw * 0.27
        w2 = cw * 0.72

        c.create_oval(cx - cw * 0.65, bottom - cw * 0.06, cx + cw * 0.65, bottom + cw * 0.06,
                      fill="#e9e4f5", outline="")                                  # plate
        c.create_rectangle(cx - cw / 2, bottom - h1, cx + cw / 2, bottom,
                           fill="#8b4f3a", outline="")                             # tier 1
        c.create_rectangle(cx - cw / 2, bottom - h1 * 0.55, cx + cw / 2, bottom - h1 * 0.45,
                           fill="#ffd6e0", outline="")                             # cream line
        top2 = bottom - h1 - h2
        c.create_rectangle(cx - w2 / 2, top2, cx + w2 / 2, bottom - h1,
                           fill="#f78fb3", outline="")                             # tier 2
        for (lx, rx, ty) in ((cx - cw / 2, cx + cw / 2, bottom - h1),
                             (cx - w2 / 2, cx + w2 / 2, top2)):
            c.create_rectangle(lx, ty - 2, rx, ty + h2 * 0.18, fill="#fff5f8", outline="")
            n = 7
            dw = (rx - lx) / n
            for i in range(n):
                dl = h2 * random.uniform(0.25, 0.45)
                c.create_oval(lx + i * dw, ty + h2 * 0.05, lx + (i + 1) * dw,
                              ty + h2 * 0.18 + dl, fill="#fff5f8", outline="")
        for i in range(9):                                                         # sprinkles
            sx = cx - w2 / 2 + w2 * (i + 0.5) / 9
            sy = top2 + h2 * random.uniform(0.6, 0.85)
            c.create_oval(sx - 3, sy - 3, sx + 3, sy + 3,
                          fill=random.choice(CONFETTI_COLORS), outline="")

        self.flames = []
        cand_h, cand_w = h2 * 0.9, max(4, cw * 0.035)
        for i in range(CANDLES):
            x = cx - w2 / 2 + w2 * (i + 1) / (CANDLES + 1)
            c.create_rectangle(x - cand_w / 2, top2 - cand_h, x + cand_w / 2, top2,
                               fill=random.choice(["#4cc9f0", "#ffd166", "#80ed99", "#c77dff"]),
                               outline="")
            c.create_line(x, top2 - cand_h, x, top2 - cand_h - cand_w * 0.6,
                          fill="#2b2b2b", width=1.5)
            fy = top2 - cand_h - cand_w * 0.6
            self.flames.append({
                "x": x, "y": fy, "s": cand_w * 1.3, "phase": random.uniform(0, 10),
                "halo": c.create_oval(0, 0, 0, 0, outline=""),
                "outer": c.create_polygon(0, 0, 0, 0, 0, 0, smooth=True, outline=""),
                "inner": c.create_polygon(0, 0, 0, 0, 0, 0, smooth=True, outline=""),
            })

    def _update_cake(self, t):
        for f in self.flames:
            x, y, s = f["x"], f["y"], f["s"]
            fl = 1 + 0.15 * math.sin(t * 17 + f["phase"]) + 0.1 * math.sin(t * 29 + f["phase"])
            sway = math.sin(t * 6 + f["phase"]) * s * 0.18
            hr = s * 1.0 * fl
            hy = y - s * 0.9
            self.c.coords(f["halo"], x - hr, hy - hr * 1.2, x + hr, hy + hr * 1.2)
            self.c.itemconfig(f["halo"], fill=lerp_color(self.bg(y), "#ffcf70", 0.35))
            h = s * 1.9 * fl
            self.c.coords(f["outer"], x - s * 0.5, y, x - s * 0.55, y - h * 0.35,
                          x + sway, y - h, x + s * 0.55, y - h * 0.35, x + s * 0.5, y)
            self.c.itemconfig(f["outer"], fill=lerp_color("#ff8c1a", "#ffb000",
                                                          0.5 + 0.5 * math.sin(t * 11)))
            h2 = h * 0.55
            self.c.coords(f["inner"], x - s * 0.25, y, x - s * 0.28, y - h2 * 0.35,
                          x + sway * 0.6, y - h2, x + s * 0.28, y - h2 * 0.35, x + s * 0.25, y)
            self.c.itemconfig(f["inner"], fill="#fff6c2")

    # ------------------------------------------------------------ particles / fireworks
    def spawn(self, x, y, hue, speed, life, size, gravity=None):
        if len(self.particles) > 700:
            return
        a = random.uniform(0, math.tau)
        s = random.uniform(0.3, 1.0) * speed
        pid = self.c.create_oval(x, y, x, y, outline="", fill=hsv(hue, 0.6, 1))
        self.particles.append({
            "id": pid, "x": x, "y": y,
            "vx": math.cos(a) * s, "vy": math.sin(a) * s,
            "life": life, "max": life, "size": size, "hue": hue,
            "g": self.H * 0.2 if gravity is None else gravity,
        })

    def firework(self, x, y, n=80):
        base = random.random()
        for _ in range(n):
            self.spawn(x, y, base + random.uniform(-0.12, 0.12), speed=self.H * 0.38,
                       life=random.uniform(0.9, 1.7), size=self.H * random.uniform(0.002, 0.0045))

    def _update_particles(self, t, dt):
        alive = []
        W, H = self.W, self.H
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
            self.c.itemconfig(p["id"], fill=lerp_color(self.bg(p["y"]), col, k))
            alive.append(p)
        self.particles = alive

    # ------------------------------------------------------------ interaction
    def restart(self):
        self.t0 = time.perf_counter()
        for p in self.particles:
            self.c.delete(p["id"])
        self.particles = []
        self.landed = set()
        self.next_fw = 3.0

    def on_click(self, e):
        box = self.c.bbox(self.close_item)
        if box and box[0] <= e.x <= box[2] and box[1] <= e.y <= box[3]:
            self.root.destroy()          # ปุ่มปิดลับ
            return
        self.firework(e.x, e.y, 90)

    # ------------------------------------------------------------ main loop
    def tick(self):
        now = time.perf_counter()
        dt = min(now - self.last, 0.05)
        self.last = now
        t = now - self.t0

        if t >= self.next_fw:
            self.firework(random.uniform(0.1, 0.9) * self.W,
                          random.uniform(0.06, 0.3) * self.H)
            self.next_fw = t + random.uniform(0.9, 2.0)

        self._update_balloons(t, dt)
        self._update_confetti(t, dt)
        self._update_title(t)
        self._update_message(t)
        self._update_cake(t)
        self._update_particles(t, dt)

        self.root.after(FRAME_MS, self.tick)


if __name__ == "__main__":
    root = tk.Tk()
    BirthdayApp(root)
    root.mainloop()
