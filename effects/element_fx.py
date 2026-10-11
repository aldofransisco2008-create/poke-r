"""Signature trigger animations: every Element bursts in its own style when it fires (flames, splashes, bolts,
shards, coins, claws, gears ...), bigger for Rare and Super. Also fireworks, multiplier slams and hype words."""
import math
import random

import pygame

from core.cards import CARD_COLOR, CardType as C
from effects import glow
from effects.tween import out_back, out_cubic
from ui.dice_view import draw_kind_icon

STYLE = {
    C.FIRE: "flame", C.DEVIL: "flame", C.SUN: "flame", C.DRAGON: "flame", C.PHOENIX: "flame",
    C.WATER: "splash", C.TSUNAMI: "splash", C.KRAKEN: "splash", C.MERCURY: "splash",
    C.WIND: "gust", C.HOURGLASS: "gust",
    C.LIGHTNING: "bolt", C.STORM: "bolt",
    C.STONE: "rock", C.QUAKE: "rock", C.METAL: "rock",
    C.GEAR: "gear", C.PISTON: "gear", C.CHRONO: "gear",
    C.GRASS: "leaf", C.THORN: "leaf", C.GAIA: "leaf",
    C.MIDAS: "coin", C.DOUBLOON: "coin", C.CRYSTAL: "shard",
    C.CUTLASS: "slash", C.WOLF: "slash", C.HAWK: "slash",
    C.ICE: "shard", C.GLASS: "shard", C.PRISM: "shard", C.MIRROR: "shard",
    C.STAR: "star", C.MOON: "star", C.ECLIPSE: "star", C.COMET: "star", C.GALAXY: "star", C.AURORA: "star",
    C.GHOST: "void", C.ECHO: "void", C.VOID: "void",
    C.JESTER: "magic", C.WIZARD: "magic", C.TAIJI: "magic",
    C.SULFUR: "bubble",
    C.KNIGHT: "slash", C.QUEEN: "magic", C.KING: "coin",
}
SOUND = {"flame": "fire", "splash": "splash", "gust": "whoosh", "bolt": "lightning", "rock": "boom", "gear": "clank",
         "leaf": "chime", "coin": "coin", "slash": "slash", "shard": "ice", "star": "chime", "void": "boom",
         "magic": "double", "bubble": "splash"}
WHITE = (255, 255, 255)


def _bolt(x0, y0, x1, y1, n=8, jag=30):
    pts = [(x0, y0)]
    for k in range(1, n):
        f = k / n
        pts.append((x0 + (x1 - x0) * f + random.uniform(-jag, jag) * (1 - f * .5), y0 + (y1 - y0) * f))
    pts.append((x1, y1))
    return pts


def _gear(surf, c, r, teeth, a0, col, w=4):
    pts = []
    for k in range(teeth * 2):
        a = a0 + k * math.pi / teeth
        rr = r if k % 2 == 0 else r * .82
        pts += [(c[0] + math.cos(a - .12) * rr, c[1] + math.sin(a - .12) * rr),
                (c[0] + math.cos(a + .12) * rr, c[1] + math.sin(a + .12) * rr)]
    pygame.draw.polygon(surf, col, pts, w)


class ElementFX:
    """One Element's burst at its die. `tier` 1..3 scales the size and length of the show."""

    def __init__(self, kind, tier, pos, particles):
        self.kind, self.tier, self.ps = kind, tier, particles
        self.x, self.y = pos
        self.col = CARD_COLOR[kind]
        self.light = glow.mix(self.col, WHITE, .55)
        self.style = STYLE.get(kind, "magic")
        self.t, self.acc = 0.0, 0.0
        self.life = 0.85 + 0.3 * tier
        self.bolts = []
        self.seed = random.random() * 10
        self._start()

    @property
    def sound(self):
        return SOUND[self.style]

    def dead(self):
        return self.t >= self.life

    # ------------------------------------------------------------ particles
    def _start(self):
        x, y, col, lt, k, ps = self.x, self.y, self.col, self.light, self.tier, self.ps
        cols = [col, lt, WHITE]
        st = self.style
        if st == "splash":
            ps.burst(x, y, 30 * k, [col, lt, (120, 210, 255), WHITE], 520, life=(0.5, 1.1), size=(3, 7), grav=1100,
                     spread=math.radians(140), angle=-math.pi / 2)
        elif st == "rock":
            ps.burst(x, y + 20, 26 * k, [col, glow.scale(col, .6), (120, 100, 80)], 560, "shard", (0.6, 1.2), (5, 10), 1400,
                     spread=math.radians(160), angle=-math.pi / 2)
        elif st == "shard":
            ps.burst(x, y, 30 * k, cols + ([glow.hsv(random.random(), .5, 1) for _ in range(3)] if self.kind is C.PRISM else []),
                     640, "shard", (0.5, 1.1), (4, 9), 200)
        elif st == "coin":
            ps.burst(x, y, 16 * k, [(255, 215, 70), (255, 236, 140)], 620, "coin", (0.8, 1.5), (6, 10), 1300,
                     spread=math.radians(90), angle=-math.pi / 2)
        elif st == "slash":
            ps.burst(x, y, 20 * k, cols, 700, "trail", (0.2, 0.45), (2, 4), 0)
        elif st == "star":
            ps.burst(x, y, 18 * k, cols + [(255, 240, 160)], 420, "star", (0.6, 1.2), (3, 6), 0)
        elif st == "magic":
            ps.burst(x, y, 24 * k, [glow.hsv(i / 6, .55, 1) for i in range(6)], 460, "star", (0.5, 1.0), (3, 6), 60)
        elif st == "leaf":
            ps.burst(x, y, 22 * k, [col, (60, 160, 70), (150, 230, 120)], 380, "confetti", (0.8, 1.5), (4, 7), 120)
        else:
            ps.burst(x, y, 16 * k, cols, 380, life=(0.4, 0.9))
        ps.emit(x, y, 0, 0, 0.5, lt, 8 + 4 * k, "ring")

    def update(self, dt):
        self.t += dt
        self.acc += dt
        x, y, col, lt, ps, k = self.x, self.y, self.col, self.light, self.ps, self.tier
        live = self.t < self.life * 0.75
        step = 0.035 if k == 1 else 0.022
        while self.acc > step:
            self.acc -= step
            if not live:
                continue
            st = self.style
            if st == "flame":
                for _ in range(k):
                    ps.emit(x + random.uniform(-44, 44), y + random.uniform(10, 46), random.uniform(-30, 30),
                            random.uniform(-520, -260), random.uniform(0.35, 0.7),
                            random.choice([(255, 220, 90), (255, 140, 40), col, (255, 70, 30)]), random.uniform(4, 8), "spark", -200)
            elif st == "gust":
                yy = y + random.uniform(-90, 90)
                ps.emit(x - 260, yy, random.uniform(900, 1400), random.uniform(-40, 40), 0.45, random.choice([lt, WHITE]), 3, "trail")
            elif st == "bubble":
                ps.emit(x + random.uniform(-50, 50), y + 40, random.uniform(-30, 30), random.uniform(-260, -120), 0.9,
                        random.choice([col, lt, (250, 245, 150)]), random.uniform(3, 7), "bubble", -60)
            elif st == "void":
                a = random.uniform(0, math.tau)
                r = 150 + 40 * k
                ps.emit(x + math.cos(a) * r, y + math.sin(a) * r, -math.cos(a) * r / 0.45, -math.sin(a) * r / 0.45, 0.45,
                        random.choice([col, lt, (40, 20, 60)]), 3, "trail")
            elif st == "leaf":
                a = self.t * 6 + random.uniform(0, math.tau)
                ps.emit(x + math.cos(a) * 60, y + math.sin(a) * 40, -math.sin(a) * 220, math.cos(a) * 160 - 60, 0.8,
                        random.choice([col, (90, 200, 90)]), 5, "confetti", 40)
            elif st == "star" and random.random() < 0.6:
                ps.emit(x + random.uniform(-120, 120), y + random.uniform(-120, 60), 0, random.uniform(-40, 10), 0.6,
                        random.choice([lt, WHITE, (255, 240, 170)]), random.uniform(3, 6), "star")
            elif st == "magic":
                a = self.t * 9 + random.uniform(-.2, .2)
                ps.emit(x + math.cos(a) * 70, y + math.sin(a) * 70, 0, -60, 0.5, glow.hsv(self.t * 2, .55, 1), 4, "spark")
            elif st == "coin" and random.random() < 0.5:
                ps.emit(x + random.uniform(-20, 20), y, random.uniform(-200, 200), random.uniform(-650, -380), 1.2,
                        (255, 215, 70), random.uniform(6, 9), "coin", 1300)
            elif st == "gear" and random.random() < 0.5:
                a = random.uniform(0, math.tau)
                ps.emit(x + math.cos(a) * 62, y + math.sin(a) * 62, math.cos(a) * 300, math.sin(a) * 300, 0.3,
                        (255, 220, 120), 3, "trail", 600)
        if self.style == "bolt" and live and random.random() < dt * (10 + 8 * k):
            tx = x + random.uniform(-40, 40)
            self.bolts.append([0.0, _bolt(tx + random.uniform(-120, 120), 0, x, y, 9, 34)])
            ps.burst(x, y, 8, [lt, WHITE], 300, life=(0.2, 0.4))
        self.bolts = [[a + dt, p] for a, p in self.bolts if a < 0.16]

    # ------------------------------------------------------------ drawing
    def draw(self, surf):
        t, life, k = self.t, self.life, self.tier
        fade = max(0.0, min(1.0, t / 0.06, (life - t) / 0.35))
        x, y, col, lt = self.x, self.y, self.col, self.light
        lay = pygame.Surface((1280, 720), pygame.SRCALPHA)
        A = lambda a: int(max(0, min(255, a * fade)))
        st = self.style
        if st == "flame":
            n = 7 + 2 * k
            for i in range(n):                                  # licking flame tongues ringing the die
                a = -math.pi / 2 + (i - (n - 1) / 2) * 0.32
                h = (70 + 50 * k) * (0.7 + 0.3 * math.sin(t * 22 + i * 1.7)) * out_cubic(min(1.0, t / 0.2))
                bx, by = x + math.cos(a) * 46, y + 40
                tip = (bx + math.sin(t * 15 + i) * 14, by - h)
                pygame.draw.polygon(lay, (*col, A(170)), [(bx - 16, by), tip, (bx + 16, by)])
                pygame.draw.polygon(lay, (255, 230, 120, A(200)), [(bx - 7, by), (tip[0], tip[1] + h * .4), (bx + 7, by)])
            if k == 3:                                          # a pillar of fire to the sky
                for i, w in enumerate((120, 80, 40)):
                    pygame.draw.rect(lay, (*glow.mix(col, (255, 240, 160), i * .4), A(70 + 40 * i)), (x - w / 2, 0, w, y))
        elif st == "splash":
            for i in range(2 + k):                              # rippling rings on the surface
                rr = (t - i * 0.12) * 380
                if rr > 4:
                    pygame.draw.ellipse(lay, (*lt, A(230 * max(0.0, 1 - rr / 380))), (x - rr, y + 44 - rr * .25, rr * 2, rr * .5), 4)
            if k >= 2:                                          # a wave rolling across the screen
                front = -200 + t / life * 1700
                pts = [(px, 720 - (140 + 60 * k) * math.exp(-((px - front) / 220) ** 2) - 14 * math.sin(px * .03 + t * 8))
                       for px in range(0, 1281, 32)]
                pygame.draw.polygon(lay, (*col, A(150)), [(0, 720)] + pts + [(1280, 720)])
                pygame.draw.lines(lay, (*WHITE, A(220)), False, pts, 4)
        elif st == "gust":
            for i in range(3 + k):                              # spinning wind arcs
                r = 50 + i * 18
                a0 = t * (9 - i) + i
                pygame.draw.arc(lay, (*lt, A(200)), (x - r, y - r * .8, r * 2, r * 1.6), a0, a0 + 2.2, 4)
        elif st == "bolt":
            if self.bolts and k >= 2:
                lay.fill((*lt, A(40)))
            for age, pts in self.bolts:
                pygame.draw.lines(lay, (*col, A(255)), False, pts, 10)
                pygame.draw.lines(lay, (*WHITE, A(255)), False, pts, 4)
                bx, by = pts[len(pts) // 2]                     # a forked branch
                pygame.draw.lines(lay, (*lt, A(200)), False, _bolt(bx, by, bx + random.uniform(-90, 90), by + 80, 4, 14), 3)
        elif st == "rock":
            for i in range(6 + 2 * k):                          # cracks racing across the ground
                a = i * math.tau / (6 + 2 * k) + self.seed
                L = (80 + 60 * k) * out_cubic(min(1.0, t / 0.25))
                rnd = random.Random(int(self.seed * 100) + i)
                pts = [(x, y + 40)]
                for s in range(1, 5):
                    f = s / 4
                    pts.append((x + math.cos(a) * L * f + rnd.uniform(-10, 10), y + 40 + math.sin(a) * L * f * .4 + rnd.uniform(-6, 6)))
                pygame.draw.lines(lay, (40, 26, 20, A(230)), False, pts, 5)
                pygame.draw.lines(lay, (*glow.mix(col, (255, 200, 120), .5), A(200)), False, pts, 2)
        elif st == "gear":
            _gear(lay, (x, y), 74, 10, t * 4, (*col, A(230)), 6)
            _gear(lay, (x + 70, y - 66), 34, 7, -t * 8, (*lt, A(230)), 4)
            if k >= 2:
                _gear(lay, (x - 74, y - 58), 42, 8, -t * 6, (*lt, A(230)), 4)
            if k == 3:
                _gear(lay, (x, y), 130 + 10 * math.sin(t * 6), 18, -t * 2, (*WHITE, A(150)), 3)
        elif st == "slash":
            for i in range(3):                                  # three claw slashes, one after the other
                kk = min(1.0, max(0.0, (t - i * 0.07) / 0.12))
                if kk <= 0:
                    continue
                o = (i - 1) * 30
                x0, y0, x1, y1 = x - 90 + o, y - 90, x + 70 + o, y + 90
                ex, ey = x0 + (x1 - x0) * kk, y0 + (y1 - y0) * kk
                pygame.draw.line(lay, (*col, A(230)), (x0, y0), (ex, ey), 12)
                pygame.draw.line(lay, (*WHITE, A(255)), (x0, y0), (ex, ey), 4)
        elif st == "shard":
            for i in range(2 + k):                              # spinning crystal frames
                r = 50 + i * 26 + 30 * out_back(min(1.0, t / 0.3))
                a0 = t * (3 if i % 2 else -3) + i
                pts = [(x + math.cos(a0 + j * math.tau / 6) * r, y + math.sin(a0 + j * math.tau / 6) * r) for j in range(6)]
                c = glow.hsv(i / 4 + t, .5, 1) if self.kind in (C.PRISM, C.CRYSTAL) else lt
                pygame.draw.polygon(lay, (*c, A(210)), pts, 4)
        elif st == "star":
            n = 5
            r = 60 + 40 * out_back(min(1.0, t / 0.3))
            a0 = t * 2
            pts = [(x + math.sin(a0 + i * math.pi / n) * (r if i % 2 == 0 else r * .45),
                    y - math.cos(a0 + i * math.pi / n) * (r if i % 2 == 0 else r * .45)) for i in range(2 * n)]
            pygame.draw.polygon(lay, (*lt, A(160)), pts, 5)
            if k == 3:                                          # shooting stars across the sky
                for i in range(4):
                    f = (t * 1.3 + i * .25) % 1.0
                    sx, sy = 1300 - f * 1400, 40 + i * 50 + f * 200
                    pygame.draw.line(lay, (*WHITE, A(230)), (sx, sy), (sx + 120, sy - 20), 4)
                    pygame.draw.circle(lay, (*lt, A(255)), (int(sx), int(sy)), 6)
        elif st == "void":
            r = max(4, int(150 * (1 - out_cubic(min(1.0, t / (life * .6))))))
            for i in range(3):                                  # imploding rings
                pygame.draw.circle(lay, (*lt, A(200)), (int(x), int(y)), r + i * 22, 4)
            pygame.draw.circle(lay, (16, 8, 30, A(200)), (int(x), int(y)), int(30 + 30 * math.sin(min(1.0, t / life) * math.pi)))
        elif st == "magic":
            for i in range(6 + 2 * k):                          # orbiting rainbow runes
                a = t * 5 + i * math.tau / (6 + 2 * k)
                px, py = x + math.cos(a) * 84, y + math.sin(a) * 60
                pygame.draw.circle(lay, (*glow.hsv(i / 8 + t, .55, 1), A(230)), (int(px), int(py)), 9, 3)
        elif st == "bubble":
            pygame.draw.circle(lay, (*lt, A(120)), (int(x), int(y)), int(60 + 20 * math.sin(t * 10)), 4)
        surf.blit(lay, (0, 0))
        self._draw_icon(surf, t, fade)

    def _draw_icon(self, surf, t, fade):
        """The Element's emblem pops out of the die and floats up."""
        if t > self.life * .9:
            return
        k = out_back(min(1.0, t / 0.22))
        r = int((20 + 8 * self.tier) * max(0.1, k))
        cx, cy = int(self.x), int(self.y - 96 - 50 * out_cubic(min(1.0, t / self.life)))
        pygame.draw.circle(surf, (20, 12, 34), (cx, cy), r + 5)
        pygame.draw.circle(surf, self.col, (cx, cy), r)
        pygame.draw.circle(surf, glow.mix(self.col, WHITE, .6) if self.tier < 3 else glow.rainbow(t * 4), (cx, cy), r + 5, 3)
        draw_kind_icon(surf, self.kind, (cx, cy), int(r * .62), (255, 248, 230))


class Firework:
    """A rocket that whistles up and bursts into a ring of stars."""

    def __init__(self, x, y_top, colors, particles, delay=0.0, big=False):
        self.x, self.y = x, 720.0
        self.top, self.cols, self.ps, self.delay, self.big = y_top, colors, particles, delay, big
        self.vy = -math.sqrt(2 * 1400 * (720 - y_top))
        self.done = False

    def update(self, dt, sfx=None):
        if self.delay > 0:
            self.delay -= dt
            return
        if self.done:
            return
        self.vy += 1400 * dt
        self.y += self.vy * dt
        self.ps.emit(self.x + random.uniform(-3, 3), self.y, random.uniform(-30, 30), 60, 0.35, (255, 220, 150), 3, "spark")
        if self.vy >= 0:
            self.done = True
            n = 90 if self.big else 55
            col = random.choice(self.cols)
            for i in range(n):
                a = i * math.tau / n
                s = random.uniform(260, 420 if self.big else 330)
                self.ps.emit(self.x, self.y, math.cos(a) * s, math.sin(a) * s, random.uniform(0.8, 1.4),
                             random.choice([col, col, WHITE]), random.uniform(3, 6), "star" if i % 3 == 0 else "spark", 260)
            self.ps.emit(self.x, self.y, 0, 0, 0.5, col, 16, "ring")
            if sfx:
                sfx.play("pop")


class Slam:
    """A huge multiplier ("x3") that slams down on the hand score and cracks into sparks."""

    def __init__(self, text, color, pos):
        self.text, self.col, self.pos = text, color, pos
        self.t, self.life = 0.0, 0.9

    def update(self, dt):
        self.t += dt
        return self.t < self.life

    def draw(self, surf):
        t = self.t
        sc = 3.2 - 2.2 * out_cubic(min(1.0, t / 0.16))
        fade = min(1.0, (self.life - t) / 0.3)
        x, y = self.pos
        jitter = (random.uniform(-4, 4), random.uniform(-4, 4)) if t < 0.3 else (0, 0)
        size = max(8, int(44 * sc) // 2 * 2)
        glow.draw_glow_text(surf, self.text, size, self.col, (x + 150 + jitter[0], y - 34 + jitter[1]), "center", fade)


HYPE = ((3.0, "GODLIKE!!!"), (1.0, "INSANE!!"), (0.5, "MEGA!"), (0.25, "GREAT!"))


def hype_word(final, target):
    """A shout for big hands, measured against the round target."""
    for k, word in HYPE:
        if final >= target * k:
            return word, k
    return None, 0
