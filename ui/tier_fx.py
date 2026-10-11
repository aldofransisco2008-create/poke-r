"""Shows for Rare and Super Elements when they trigger: a light pillar and shock rings for Rare, a full-screen blast
with a giant medallion, rays and lightning for Super."""
import math
import random

import pygame

from core.cards import CARD_COLOR, TIER_COLOR
from effects import glow
from effects.tween import out_back, out_cubic
from ui.dice_view import draw_kind_icon

RARE, SUPER = 2, 3


class TierShow:
    def __init__(self, kind, tier, pos, particles):
        self.kind, self.tier, self.pos, self.ps = kind, tier, pos, particles
        self.col = CARD_COLOR[kind]
        self.life = 1.15 if tier == RARE else 2.1
        self.t = 0.0
        self.acc = 0.0
        self.bolts = []
        self.seed = random.random() * 9

    def dead(self):
        return self.t >= self.life

    # ------------------------------------------------------------ update
    def update(self, dt):
        self.t += dt
        self.acc += dt
        x, y = self.pos
        step = 0.03 if self.tier == SUPER else 0.05
        while self.acc > step:
            self.acc -= step
            cols = [self.col, glow.mix(self.col, (255, 255, 255), .6), (255, 255, 255)]
            if self.tier == SUPER:
                cols.append(glow.hsv(random.random(), .6, 1.0))
            fade = max(0.0, 1 - self.t / self.life)
            if random.random() < fade + 0.2:
                self.ps.emit(x + random.uniform(-36, 36), y + random.uniform(-10, 40), random.uniform(-40, 40),
                             random.uniform(-420, -160), random.uniform(0.5, 1.0), random.choice(cols), 4, "spark", 120)
        if self.tier == SUPER and random.random() < dt * 14 and self.t < self.life * 0.8:     # crackling bolts from the sky
            tx = x + random.uniform(-90, 90)
            pts = [(tx + random.uniform(-40, 40), 0)]
            n = 7
            for k in range(1, n + 1):
                f = k / n
                pts.append((tx + (x - tx) * f + random.uniform(-26, 26) * (1 - f), y * f))
            self.bolts.append([0.0, pts])
        self.bolts = [[a + dt, p] for a, p in self.bolts if a < 0.22]

    # ------------------------------------------------------------ draw
    def draw(self, surf):
        t, life, col = self.t, self.life, self.col
        fade = max(0.0, min(1.0, t / 0.08, (life - t) / 0.4))
        x, y = self.pos
        if self.tier == RARE:
            self._draw_rare(surf, t, fade, col, x, y)
        else:
            self._draw_super(surf, t, fade, col, x, y)

    def _draw_rare(self, surf, t, fade, col, x, y):
        lay = pygame.Surface((1280, 720), pygame.SRCALPHA)
        bright = glow.mix(col, (255, 255, 255), .55)
        for i, w in enumerate((70, 46, 24, 10)):                 # light pillar
            a = int((60 + i * 40) * fade * min(1.0, t / 0.12))
            pygame.draw.rect(lay, (*glow.mix(col, (255, 255, 255), i * .22), a), (x - w // 2, 0, w, y + 30))
        for k in range(3):                                        # shock rings
            rr = (t - k * 0.12) * 520
            if 6 < rr < 400:
                a = int(220 * fade * max(0.0, 1 - rr / 400))
                pygame.draw.ellipse(lay, (*bright, a), (x - rr, y - rr * .55, rr * 2, rr * 1.1), 6 if k == 0 else 3)
        for i in range(6):                                        # spinning diamonds around the die
            a = t * 5 + i * math.tau / 6
            r = 50 + 34 * out_cubic(min(1.0, t / 0.4))
            px, py = x + math.cos(a) * r, y + math.sin(a) * r * .8
            s = 6 + 3 * math.sin(t * 20 + i)
            pygame.draw.polygon(lay, (*bright, int(255 * fade)), [(px, py - s), (px + s * .6, py), (px, py + s), (px - s * .6, py)])
        surf.blit(lay, (0, 0))
        k = out_back(min(1.0, t / 0.3))
        size = max(2, int(22 * k)) // 2 * 2
        glow.draw_glow_text(surf, "RARE!", size, TIER_COLOR[RARE], (x, y - 96 - 30 * out_cubic(min(1.0, t / 0.8))), "center", fade, kind="ui")

    def _draw_super(self, surf, t, fade, col, x, y):
        lay = pygame.Surface((1280, 720), pygame.SRCALPHA)
        lay.fill((10, 6, 30, int(130 * fade)))
        C = (640, 260)
        n = 20
        for i in range(n):                                        # spinning rainbow rays
            a = t * 1.4 + i * math.tau / n
            hue = glow.hsv(i / n + t * .3, .55, 1.0)
            pygame.draw.polygon(lay, (*hue, int(70 * fade)), [C, (C[0] + math.cos(a - .05) * 1200, C[1] + math.sin(a - .05) * 1200),
                                                               (C[0] + math.cos(a + .05) * 1200, C[1] + math.sin(a + .05) * 1200)])
        for k in range(4):                                        # shock rings from the die and from the medallion
            rr = (t - k * 0.16) * 1000
            if 8 < rr < 1300:
                a = int(230 * fade * max(0.0, 1 - rr / 1300))
                pygame.draw.circle(lay, (*glow.hsv(k * .17 + t, .5, 1), a), (int(x), int(y)), int(rr), 10 if k == 0 else 5)
        surf.blit(lay, (0, 0))
        for age, pts in self.bolts:                               # lightning from the sky
            pygame.draw.lines(surf, col, False, pts, 9)
            pygame.draw.lines(surf, (255, 255, 255), False, pts, 3)
        k = out_back(min(1.0, t / 0.4))                           # the medallion
        r = int(78 * max(0.05, k))
        pygame.draw.circle(surf, (20, 12, 40), C, r + 12)
        pygame.draw.circle(surf, glow.hsv(t * 1.2, .5, 1.0), C, r + 8, 6)
        pygame.draw.circle(surf, glow.scale(col, .6), C, r)
        pygame.draw.circle(surf, col, (C[0], C[1] - 3), max(2, r - 10))
        draw_kind_icon(surf, self.kind, C, int(r * .6), (255, 248, 230))
        for i in range(10):                                       # orbiting stars
            a = -t * 3 + i * math.tau / 10
            sx, sy = C[0] + math.cos(a) * (r + 40), C[1] + math.sin(a) * (r + 40)
            s = 5 + 3 * math.sin(t * 12 + i)
            pygame.draw.polygon(surf, glow.hsv(i / 10 + t, .4, 1), [(sx, sy - s * 1.6), (sx + s * .5, sy), (sx, sy + s * 1.6), (sx - s * .5, sy)])
        size = int(104 * max(0.1, k)) // 2 * 2
        glow.draw_glow_text(surf, self.kind.value.upper() + "!", size, glow.rainbow(t * 3), (640, 118), "center", fade)
        glow.draw_glow_text(surf, "SUPER ELEMENT", 28, TIER_COLOR[SUPER], (640, 372), "center", fade, kind="ui")
