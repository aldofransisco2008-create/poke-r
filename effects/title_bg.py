"""The main-menu panorama (640x360 canvas magnified x2): layered blue mountain ranges that drift and breathe, a big
snow-capped peak with glinting ice and blowing snow, glowing lava streaks that pulse, mist, and a lake with sliding
ripples and a wobbling reflection."""
import math
import random

import pygame

import config
from effects import glow, retro

LW, LH = config.SCREEN_W // 2, config.SCREEN_H // 2
BASE = 230                                     # shoreline row


class TitleBackdrop:
    def __init__(self):
        rng = random.Random(21)
        self.prof = []
        for seed in range(3):
            r = random.Random(40 + seed * 7)
            self.prof.append([(k, r.uniform(0, 6.28), a) for k, a in ((1, 1.0), (2, .65), (3, .45), (5, .3), (8, .16), (13, .08))])
        self.sky = pygame.Surface((LW, LH))
        for y in range(LH):
            self.sky.fill(glow.mix((16, 24, 66), (74, 112, 178), min(1.0, y / 190) ** 1.1), (0, y, LW, 1))
        self.snow = [[rng.uniform(0, LW), rng.uniform(70, 190), rng.uniform(10, 34), rng.uniform(0, 6.28)] for _ in range(46)]
        self.ember = [[rng.uniform(0, LW), rng.uniform(120, 240), rng.uniform(6, 16), rng.uniform(0, 6.28)] for _ in range(30)]

    def _ridge(self, layer, base, amp, t, speed, breathe):
        comps = self.prof[layer]
        norm = sum(a for _, _, a in comps)
        P = LW * 2.0
        shift = t * speed
        pts = [(0, LH)]
        for x in range(0, LW + 5, 4):
            v = sum(a * math.sin(math.tau * k * (x + shift) / P + ph) for k, ph, a in comps) / norm
            pts.append((x, int(base - amp * (0.5 + 0.5 * v) + breathe * math.sin(t * 0.5 + x * 0.013 + layer))))
        pts.append((LW, LH))
        return pts

    @staticmethod
    def _streak(low, cx, cy, w, h, t, ph, col, core):
        """A glowing lava / sunset streak: a lens shape with a living, jagged top edge."""
        n = 22
        top, bot = [], []
        for i in range(n + 1):
            u = i / n
            env = math.sin(math.pi * u) ** 0.8
            x = cx - w / 2 + u * w
            top.append((x, cy - h * env * (0.65 + 0.35 * math.sin(u * 9 + ph + t * 0.9))))
            bot.append((x, cy + h * 0.32 * env * (0.7 + 0.3 * math.sin(u * 6 - ph + t * 0.7))))
        pulse = 0.5 + 0.5 * math.sin(t * 1.3 + ph)
        pygame.draw.polygon(low, glow.mix(col, (255, 150, 110), 0.25 * pulse), top + bot[::-1])
        top2 = [(x, cy - (cy - y) * 0.55) for x, y in top]
        bot2 = [(x, cy + (y - cy) * 0.5) for x, y in bot]
        pygame.draw.polygon(low, glow.mix(core, (255, 240, 200), 0.4 * pulse), top2 + bot2[::-1])

    def draw(self, surf, t):
        low = self.sky.copy()
        for i in range(34):                                         # stars twinkling in the dark top
            if int(t * 1.6 + i * 1.7) % 4:
                low.set_at(((i * 97 + 13) % LW, (i * 53 + 7) % 90), (170, 190, 240))
        pygame.draw.polygon(low, (94, 136, 204), self._ridge(0, 190, 96, t, 2.0, 2.0))        # far haze range (drifts)
        pygame.draw.polygon(low, (70, 108, 182), self._ridge(1, 206, 74, t, 3.5, 1.6))
        coral, peach = (236, 100, 84), (255, 196, 124)
        self._streak(low, 470 + 8 * math.sin(t * 0.3), 150, 200, 13, t, 0.4, coral, peach)
        self._streak(low, 585 + 6 * math.sin(t * 0.4 + 1), 140, 110, 11, t, 2.1, coral, peach)
        self._streak(low, 20, 152, 100, 16, t, 3.3, coral, peach)
        # the big peak
        peak = [(250, 236), (330, 196), (392, 160), (440, 130), (490, 96), (524, 72), (548, 58), (570, 80), (588, 110),
                (612, 128), (640, 138), (640, 236)]
        pygame.draw.polygon(low, (34, 52, 108), peak)
        pygame.draw.polygon(low, (46, 70, 130), [(548, 58), (524, 72), (490, 96), (470, 124), (500, 150), (534, 108), (542, 78)])
        pygame.draw.polygon(low, (26, 40, 90), [(548, 58), (570, 80), (588, 110), (612, 128), (640, 138), (640, 236), (580, 236), (560, 150)])
        rim = [(548, 58), (524, 72), (490, 96), (440, 130), (392, 160)]                    # ice glinting down the ridge
        for i in range(34):
            k = i / 33
            seg = min(3, int(k * 4))
            a, b = rim[seg], rim[seg + 1]
            f = k * 4 - seg
            px, py = int(a[0] + (b[0] - a[0]) * f), int(a[1] + (b[1] - a[1]) * f)
            if math.sin(t * 2.6 - i * 0.7) > -0.2:
                low.set_at((px, py), (150, 220, 255))
                low.set_at((px + 1, py), (110, 190, 245))
                if math.sin(t * 3.1 + i) > 0.85:
                    pygame.draw.rect(low, (255, 255, 255), (px - 1, py - 1, 3, 3))
        for x, y, sp, ph in self.snow:                                                       # snow streaming off the slopes
            px = (x - t * sp) % LW
            py = y + math.sin(t * 0.8 + ph) * 6 + (t * 3) % 6
            if (int(px) + int(py)) % 2 == 0 and 60 < py < 210:
                low.set_at((int(px) % LW, int(py)), (226, 240, 255))
        for i in range(16):                                                                  # plume off the summit
            px = 548 - (i * 5 + t * 22) % 90
            low.set_at((int(px), int(60 + (i * 3) % 14 + i * 0.35)), (236, 246, 255) if i % 2 else (180, 210, 245))
        pygame.draw.polygon(low, (52, 84, 156), self._ridge(2, 224, 44, t, 5.5, 1.0))        # mid range
        for k in range(3):                                                                   # mist drifting between ranges
            m = pygame.Surface((240, 14), pygame.SRCALPHA)
            pygame.draw.ellipse(m, (176, 206, 244, 46), (0, 0, 240, 14))
            low.blit(m, (int((t * (6 + k * 3) + k * 210) % (LW + 240) - 120), 174 + k * 18))
        pygame.draw.rect(low, (60, 96, 168), (0, BASE - 6, LW, 8))
        self._streak(low, 150 + 10 * math.sin(t * 0.35), 221, 420, 9, t, 0.9, coral, peach)  # lava on the shore
        self._streak(low, 470 + 10 * math.sin(t * 0.3 + 2), 224, 330, 8, t, 2.4, coral, (255, 206, 140))
        for y in range(BASE, LH):                                                            # the lake
            pygame.draw.line(low, glow.mix((88, 140, 206), (36, 70, 144), min(1.0, (y - BASE) / (LH - BASE) * 1.3)), (0, y), (LW, y))
        for i in range(30):                                                                  # ripples sliding across
            y = BASE + 6 + (i * 11) % 86
            x = (i * 71 + t * (7 + i % 5 * 3) * (1 if i % 2 else -1)) % (LW + 40) - 20
            if int(t * 1.5 + i) % 3:
                pygame.draw.line(low, (150, 190, 236) if i % 3 else (190, 220, 250), (x, y), (x + 8 + i % 14, y))
        for i in range(10):                                                                  # wobbling lava reflection
            y = BASE + 4 + i * 3
            wob = math.sin(t * 2.2 + i * 0.9) * 4
            col = glow.mix((255, 190, 120), coral, i / 10)
            for sx, sw in ((60, 160), (330, 220), (520, 90)):
                pygame.draw.line(low, col, (sx + wob, y), (sx + sw + wob * 1.4, y))
        for x, y, sp, ph in self.ember:                                                      # embers floating up
            if int(t * 3 + ph) % 3:
                low.set_at((int((x + math.sin(t * 0.7 + ph) * 8) % LW), int((y - t * sp) % 150 + 100)), (255, 170, 90))
        pygame.draw.polygon(low, (20, 32, 76), [(0, LH)] + [(x, 322 + int(4 * math.sin(x * 0.02 + t * 0.4) + 3 * math.sin(x * 0.05)))
                                                          for x in range(0, LW + 8, 8)] + [(LW, LH)])
        pygame.draw.polygon(low, (13, 22, 56), [(0, LH)] + [(x, 342 + int(3 * math.sin(x * 0.03 - t * 0.3)))
                                                          for x in range(0, LW + 8, 8)] + [(LW, LH)])
        surf.blit(retro.upscale(low), (0, 0))
