"""Round-score progress drawn as a body of water: it never stops moving (flowing ripples, rising bubbles, foam on the
wavefront), swells while a hand is being scored (a pale golden "pending" tide shows what the hand will add) and
explodes into a surge of splashes when the score lands.  Drawn on a half-size canvas and magnified x2 like the rest of
the pixel art."""
import math
import random

import pygame

import config
from effects import glow
from ui.widgets import draw_panel

WATER_TOP, WATER_BOT = (112, 214, 255), (24, 84, 196)
GOLD_TOP, GOLD_BOT = (255, 240, 150), (232, 140, 36)
PENDING_TOP, PENDING_BOT = (255, 248, 190), (255, 196, 80)

_cache = {}


def _gradient(w, h, top, bot):
    key = ("g", w, h, top, bot)
    s = _cache.get(key)
    if s is None:
        if len(_cache) > 200:
            _cache.clear()
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        for y in range(h):
            pygame.draw.line(s, (*glow.mix(top, bot, y / max(1, h - 1)), 255), (0, y), (w, y))
        _cache[key] = s
    return s


def _round_mask(w, h, radius):
    key = ("m", w, h, radius)
    s = _cache.get(key)
    if s is None:
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(s, (255, 255, 255, 255), (0, 0, w, h), border_radius=radius)
        _cache[key] = s
    return s


class WaterBar:
    def __init__(self):
        self.level = 0.0          # displayed fill 0..1 (a spring chasing the real score)
        self.vel = 0.0
        self.kick = 0.0           # surge energy, decays fast
        self.excite = 0.0         # 0 idle .. 1 while a hand is being scored
        self.flash = 0.0
        self.pop = 0.0
        self.gold = 0.0           # 1 once the target is reached: the water turns to liquid gold
        self.bubbles = []         # [x 0..1, y 0..1 (1 = bottom), speed, size, phase]
        self.rings = []           # [age, strength] shock ripples travelling from the wavefront
        self.t = 0.0
        self._rng = random.Random(5)

    # ------------------------------------------------------------ control
    def surge(self, power=1.0):
        self.kick = min(1.8, self.kick + power)
        self.flash = min(1.0, self.flash + 0.55 * power)
        self.pop = 1.0
        self.vel += 0.12 * power
        self.rings.append([0.0, min(1.0, power)])

    def nudge(self, power=0.25):
        """A small bump (each scoring step)."""
        self.kick = min(1.8, self.kick + power)
        self.pop = max(self.pop, 0.4)

    def update(self, dt, target, active, reached=False):
        self.t += dt
        target = max(0.0, min(1.0, target))
        for _ in range(max(1, int(dt / 0.008) + 1)):                 # spring with a little overshoot, sub-stepped
            h = dt / max(1, int(dt / 0.008) + 1)
            self.vel += (110 * (target - self.level) - 12 * self.vel) * h
            self.level += self.vel * h
        self.level = max(0.0, min(1.04, self.level))
        self.kick = max(0.0, self.kick - dt * 1.5)
        self.flash = max(0.0, self.flash - dt * 2.4)
        self.pop = max(0.0, self.pop - dt * 3.2)
        self.excite += ((1.0 if active else 0.0) - self.excite) * min(1.0, dt * 3.0)
        self.gold += ((1.0 if reached else 0.0) - self.gold) * min(1.0, dt * 3.0)
        self.rings = [[a + dt, s] for a, s in self.rings if a < 1.0]
        energy = 0.12 + 0.5 * self.excite + self.kick
        if self.level > 0.01 and self._rng.random() < dt * (3 + 26 * energy):
            self.bubbles.append([self._rng.uniform(0.0, max(0.02, min(1.0, self.level))), 1.02,
                                 self._rng.uniform(0.35, 0.9), self._rng.choice((1, 1, 2)), self._rng.uniform(0, 6.28)])
        for b in self.bubbles:
            b[1] -= b[2] * dt * (1 + self.kick)
        self.bubbles = [b for b in self.bubbles if b[1] > -0.05][-90:]

    def tip(self, rect):
        """Screen position of the wavefront (for splashes)."""
        inner = pygame.Rect(rect).inflate(-14, -14)
        return inner.x + inner.w * min(1.0, self.level), inner.centery

    # ------------------------------------------------------------ drawing
    def _layer(self, w, h, fx, amp, phase, speed, top, bot, alpha=255):
        """One body of water reaching x=fx with a rippling front edge. Returns (surface, mask)."""
        mask = pygame.Surface((w, h), pygame.SRCALPHA)
        if fx > 0.5:
            pts = [(0, 0)]
            for y in range(0, h + 1):
                pts.append((max(0.0, fx + amp * math.sin(y * 0.55 + phase + self.t * speed)
                                + 0.5 * amp * math.sin(y * 1.3 - self.t * speed * 1.7)), y))
            pts.append((0, h))
            pygame.draw.polygon(mask, (255, 255, 255, alpha), pts)
        img = _gradient(w, h, top, bot).copy()
        img.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        return img, mask

    def draw(self, surf, rect, t, pending=None, reached=False, label="", sub=""):
        rect = pygame.Rect(rect)
        draw_panel(surf, rect, config.GOLD if reached else config.NAVY_LINE, 240, radius=14)
        inner = rect.inflate(-14, -14)
        lw, lh = inner.w // 2, inner.h // 2
        low = pygame.Surface((lw, lh), pygame.SRCALPHA)
        low.blit(_gradient(lw, lh, (14, 22, 58), (8, 12, 36)), (0, 0))
        for i in range(0, lw, 24):                                   # faint tile lines of the empty trough
            pygame.draw.line(low, (26, 36, 84), (i, 0), (i, lh))
        lvl = min(1.0, self.level)
        fx = lvl * lw
        energy = 0.12 + 0.5 * self.excite + self.kick
        amp = 0.9 + 1.6 * self.excite + 3.2 * self.kick + min(2.5, abs(self.vel) * 5)
        k = self.gold
        top, bot = glow.mix(WATER_TOP, GOLD_TOP, k), glow.mix(WATER_BOT, GOLD_BOT, k)

        if pending is not None and pending > lvl + 0.004:            # the hand being scored: a pale tide ahead
            pfx = min(1.0, pending) * lw
            pulse = 0.5 + 0.5 * math.sin(self.t * 9)
            pg, _ = self._layer(lw, lh, pfx, amp * 1.3 + 0.8, 1.7, 5.0, glow.mix(PENDING_TOP, (255, 255, 255), .4 * pulse),
                                glow.mix(PENDING_BOT, (255, 230, 140), .4 * pulse))
            low.blit(pg, (0, 0))
            for i in range(8):                                       # glitter on the pending tide
                gx = lvl * lw + ((i * 37 + self.t * 40) % max(4.0, pfx - lvl * lw + 1))
                gy = (i * 11 + int(self.t * 9)) % lh
                low.set_at((int(gx) % lw, gy), (255, 255, 230))
        back, _ = self._layer(lw, lh, fx + 2.0, amp * 1.15, 2.4, -2.2, glow.scale(top, .7), glow.scale(bot, .7))
        low.blit(back, (0, 0))
        front, mask = self._layer(lw, lh, fx, amp, 0.0, 3.0, top, bot)
        low.blit(front, (0, 0))

        det = pygame.Surface((lw, lh), pygame.SRCALPHA)               # everything that lives inside the water
        if fx > 4:
            xs = range(0, int(fx) + 2, 3)
            for kk in range(4):                                       # flowing ripple ribbons
                y0 = lh * (0.18 + 0.2 * kk)
                pts = [(x, y0 + (1.0 + 1.6 * energy) * math.sin(x * 0.085 - self.t * (1.5 + kk * 0.45 + 2.2 * energy) + kk * 1.9))
                       for x in xs]
                if len(pts) > 1:
                    pygame.draw.lines(det, (*glow.mix(top, (255, 255, 255), .55), 120 + 20 * kk), False, pts, 1)
            for i in range(16):                                       # caustic glints
                gx = (i * 47 + self.t * (9 + i % 5 * 4)) % lw
                gy = int((i * 13 + math.sin(self.t * 1.3 + i) * 3) % lh)
                if gx < fx and int(self.t * 3 + i) % 3:
                    pygame.draw.rect(det, (230, 250, 255, 190), (int(gx), gy, 2 + i % 3, 1))
            for b in self.bubbles:                                    # rising bubbles
                bx, by = b[0] * lw + math.sin(self.t * 3 + b[4]) * 2, b[1] * lh
                if bx < fx - 1:
                    if b[3] > 1:
                        pygame.draw.circle(det, (220, 245, 255, 210), (int(bx), int(by)), 2, 1)
                    else:
                        det.set_at((int(bx), int(by)), (240, 252, 255, 230))
            for y in range(0, lh, 2):                                 # foam clinging to the wavefront
                ex = fx + amp * math.sin(y * 0.55 + self.t * 3.0) + 0.5 * amp * math.sin(y * 1.3 - self.t * 5.1)
                r = 1 + int((math.sin(self.t * 8 + y * 1.7) + 1) * 0.7 + self.kick * 1.6)
                pygame.draw.circle(det, (255, 255, 255, 215), (int(ex) - 1, y), r)
            pygame.draw.line(det, (255, 255, 255, 90), (0, 0), (int(fx), 0))       # meniscus highlight
            pygame.draw.line(det, (255, 255, 255, 40), (0, 1), (int(fx), 1))
            pygame.draw.line(det, (0, 20, 80, 70), (0, lh - 1), (int(fx), lh - 1))
        det.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        low.blit(det, (0, 0))
        for age, power in self.rings:                                 # ripple shock leaving the wavefront
            rr = int(age * 70 * (0.6 + power))
            a = max(0, min(255, int(210 * (1 - age) * min(1.0, power + 0.3))))
            if rr > 1:
                pygame.draw.ellipse(low, (255, 255, 255, a), (int(fx) - rr // 2, lh // 2 - rr // 3, rr, max(2, 2 * rr // 3)), 1)

        big = pygame.transform.scale(low, inner.size)
        big.blit(_round_mask(inner.w, inner.h, 10), (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        surf.blit(big, inner)
        if self.flash > 0.01:                                         # white flash while the surge lands
            ov = pygame.Surface(inner.size, pygame.SRCALPHA)
            pygame.draw.rect(ov, (255, 255, 255, int(120 * self.flash)), ov.get_rect(), border_radius=10)
            surf.blit(ov, inner)
        pygame.draw.rect(surf, config.GOLD if reached else (150, 180, 255), inner, 2, border_radius=10)
        if self.kick > 0.15:                                          # bloom around the whole bar
            pygame.draw.rect(surf, glow.mix(top, (255, 255, 255), .5), rect.inflate(int(8 * self.kick), int(8 * self.kick)),
                             2, border_radius=16)

        size = (24 + int(10 * self.pop)) // 2 * 2
        glow.draw_glow_text(surf, label, size, config.CREAM, (inner.centerx, inner.centery - 2))
        if sub:
            glow.draw_text(surf, sub, 13, glow.mix(config.CREAM, (150, 180, 255), .4), (inner.right - 14, inner.centery), "midright", kind="ui")
        glow.draw_text(surf, "ROUND SCORE", 13, glow.mix(config.CREAM, (150, 180, 255), .4), (inner.x + 14, inner.centery), "midleft", kind="ui")
