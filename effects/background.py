"""Pixel-art backdrops, generated in code and drawn on a 640x360 canvas magnified x2:
  "scene"  sunset landscape (dithered sky, mountains, sea, pines) with drifting clouds, birds, petals and water sparkles
  "title"  the main-menu panorama (effects/title_bg.py)
  "board"  dark table with a pixel diamond lattice and slowly rising motes (for playing / shop)
"""
import math
import random

import pygame

import config
from effects import glow, retro
from effects.title_bg import TitleBackdrop

LW, LH = config.SCREEN_W // 2, config.SCREEN_H // 2
HZ = 220                                   # horizon row on the low-res canvas

SKY = [(20, 24, 64), (32, 40, 96), (46, 66, 130), (70, 104, 160), (110, 146, 184), (168, 184, 196), (232, 200, 168)]
MOUNT_FAR = (86, 100, 150)
MOUNT_MID = (58, 74, 122)
MOUNT_NEAR = (38, 52, 96)


def _dither_bands(surf, y0, y1, colors):
    """Flat horizontal colour bands with a stepped checkerboard dither on every seam."""
    n = len(colors)
    h = (y1 - y0) / n
    for i, c in enumerate(colors):
        top = int(y0 + i * h)
        bot = int(y0 + (i + 1) * h) if i < n - 1 else y1
        pygame.draw.rect(surf, c, (0, top, LW, bot - top))
    for i in range(n - 1):
        seam = int(y0 + (i + 1) * h)
        a, b = colors[i], colors[i + 1]
        for dy in range(-4, 4):
            y = seam + dy
            for x in range(LW):
                p = (x + y) % 4 == 0 if dy in (-4, -3) else (x + y) % 2 == 0 if dy in (-2, -1) else \
                    (x + y) % 2 != 0 if dy in (0, 1) else (x + y) % 4 != 0
                surf.set_at((x, y), b if p else a)


def _ridge(rng, base, amp, step, phase):
    pts = [(0, LH)]
    x = 0
    while x <= LW + step:
        pts.append((x, int(base - amp * (0.5 + 0.5 * math.sin(x / 47.0 + phase)) - rng.randint(0, 8))))
        x += step
    pts.append((LW, LH))
    return pts


def _pine(s, x, y, h, dark, light):
    for k in range(4):
        w = int(h * (0.34 - k * 0.06))
        yy = y - int(h * (0.16 + k * 0.2))
        pygame.draw.polygon(s, dark, [(x - w, yy), (x + w, yy), (x, yy - int(h * 0.34))])
        pygame.draw.polygon(s, light, [(x, yy - int(h * 0.34)), (x + w, yy), (x + w // 4, yy)])
    pygame.draw.rect(s, (66, 40, 34), (x - 1, y - int(h * .12), 3, int(h * .14)))


def _cloud(seed):
    rng = random.Random(seed)
    w, h = rng.randint(60, 110), rng.randint(14, 22)
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    for _ in range(6):
        rw, rh = rng.randint(w // 4, w // 2), rng.randint(h // 3, h // 2)
        x, y = rng.randint(0, w - rw), rng.randint(h // 3, h - rh)
        pygame.draw.ellipse(s, (236, 226, 232), (x, y, rw, rh))
    pygame.draw.rect(s, (200, 196, 214), (0, h - 4, w, 4))
    mask = pygame.mask.from_surface(s)
    out = pygame.Surface((w, h), pygame.SRCALPHA)
    for (x, y) in mask.outline():
        out.set_at((x, y), (170, 170, 200))
    s.blit(out, (0, 0))
    return s


class Background:
    def __init__(self):
        rng = random.Random(11)
        # ---------- scene: static low-res layers
        sky = pygame.Surface((LW, LH))
        _dither_bands(sky, 0, HZ, SKY)
        pygame.draw.circle(sky, (255, 232, 180), (LW // 2 + 80, HZ - 34), 22)          # low sun
        pygame.draw.circle(sky, (255, 250, 220), (LW // 2 + 80, HZ - 34), 14)
        pygame.draw.polygon(sky, MOUNT_FAR, _ridge(rng, HZ - 4, 60, 20, 0.4))
        pygame.draw.polygon(sky, MOUNT_MID, _ridge(rng, HZ + 6, 44, 16, 2.0))
        peak = [(LW // 2 - 120, HZ + 6), (LW // 2 - 20, HZ - 110), (LW // 2 + 14, HZ - 120), (LW // 2 + 130, HZ + 6)]
        pygame.draw.polygon(sky, MOUNT_NEAR, peak)
        pygame.draw.polygon(sky, (236, 240, 250), [(LW // 2 - 32, HZ - 88), peak[1], peak[2], (LW // 2 + 28, HZ - 92), (LW // 2 + 6, HZ - 80),
                                                    (LW // 2 - 10, HZ - 90)])
        for y in range(HZ, LH):                                                          # sea in dithered bands
            k = (y - HZ) / (LH - HZ)
            band = [(52, 120, 150), (40, 96, 132), (30, 74, 112), (24, 56, 92)][min(3, int(k * 4))]
            pygame.draw.line(sky, band, (0, y), (LW, y))
        for y in range(HZ, LH, 2):
            for x in range((y // 2) % 2, LW, 2):
                if rng.random() < 0.06:
                    sky.set_at((x, y), (70, 150, 176))
        self.sky = sky
        fg = pygame.Surface((LW, LH), pygame.SRCALPHA)
        pygame.draw.polygon(fg, (30, 60, 66), [(0, 150), (75, 180), (125, 235), (165, 280), (165, LH), (0, LH)])
        pygame.draw.polygon(fg, (48, 96, 78), [(0, 170), (60, 192), (105, 235), (0, 235)])
        for x, y, h in ((15, 235, 125), (55, 235, 100), (95, 250, 85), (30, 280, 110), (125, 280, 60)):
            _pine(fg, x, y, h, (26, 66, 62), (44, 100, 78))
        pygame.draw.polygon(fg, (66, 62, 90), [(LW, 260), (LW - 75, 280), (LW - 130, 330), (LW - 150, LH), (LW, LH)])
        pygame.draw.polygon(fg, (98, 92, 120), [(LW, 270), (LW - 60, 287), (LW - 100, 320), (LW, 320)])
        for x, y, h in ((LW - 20, 270, 80), (LW - 55, 285, 60)):
            _pine(fg, x, y, h, (28, 70, 64), (46, 104, 80))
        self.fg = fg
        self.clouds = [[rng.uniform(0, LW), rng.randint(20, 120), _cloud(i), rng.uniform(3, 8)] for i in range(5)]
        self.birds = [[rng.uniform(0, LW), rng.randint(50, 120), rng.uniform(13, 22), rng.uniform(0, 6)] for _ in range(4)]
        self.petals = [[rng.uniform(0, LW), rng.uniform(0, LH), rng.uniform(10, 24), rng.uniform(0, 6.28),
                        rng.choice([(255, 214, 96), (255, 140, 70), (120, 210, 110)])] for _ in range(14)]
        self.set_board_color(config.BACKGROUND_TOP, config.BACKGROUND_BOTTOM)
        self.title = TitleBackdrop()
        self.motes = [[rng.uniform(0, config.SCREEN_W), rng.uniform(0, config.SCREEN_H), rng.uniform(8, 20), rng.uniform(0, 6.28)]
                      for _ in range(22)]

    def set_board_color(self, top, bottom):
        """(Re)paint the in-game backdrop (playing, shop ...): a vertical gradient in flat bands, a diamond lattice and a
        frame, all derived from the two colours."""
        board = pygame.Surface((LW, LH))
        for y in range(0, LH, 1):
            pygame.draw.line(board, glow.mix(top, bottom, y / LH), (0, y), (LW, y))
        board = self._band_quantise(board)
        dot, dot2 = glow.scale(top, 1.55), glow.scale(top, 1.95)
        for x in range(-8, LW + 8, 32):
            for y in range(-8, LH + 8, 32):
                for (dx, dy) in ((0, -7), (7, 0), (0, 7), (-7, 0)):
                    board.set_at((x + dx, y + dy), dot)
                board.set_at((x, y), dot2)
        for i in range(6):
            pygame.draw.rect(board, glow.scale(bottom, 0.55 + 0.09 * i), (i * 2, i * 2, LW - i * 4, LH - i * 4), 2)
        self.board = retro.upscale(board)

    @staticmethod
    def _band_quantise(surf, step=10):
        """Collapse the smooth gradient into flat bands."""
        out = pygame.Surface(surf.get_size())
        for y in range(0, surf.get_height(), step):
            pygame.draw.rect(out, surf.get_at((0, y)), (0, y, surf.get_width(), step))
        return out

    def update(self, dt):
        for c in self.clouds:
            c[0] += c[3] * dt
            if c[0] > LW + 10:
                c[0] = -c[2].get_width()
        for b in self.birds:
            b[0] += b[2] * dt
            if b[0] > LW + 20:
                b[0], b[1] = -20, random.randint(50, 120)
        for p in self.petals:
            p[0] += p[2] * dt
            p[1] += (7 + 5 * math.sin(p[3])) * dt
            p[3] += dt * 1.4
            if p[0] > LW + 10 or p[1] > LH + 10:
                p[0], p[1] = random.uniform(-100, 0), random.uniform(-10, LH * .6)
        for m in self.motes:
            m[1] -= m[2] * dt
            m[3] += dt
            if m[1] < -10:
                m[0], m[1] = random.uniform(0, config.SCREEN_W), config.SCREEN_H + 10

    def draw(self, surf, t, mode="board"):
        if mode == "scene":
            self._scene(surf, t)
        elif mode == "title":
            self.title.draw(surf, t)
        else:
            self._board(surf, t)

    def _board(self, surf, t):
        surf.blit(self.board, (0, 0))
        for x, y, r, ph in self.motes:
            if int(t * 2 + ph) % 3:
                glow.draw_glow_circle(surf, (int(x + math.sin(t * .4 + ph) * 16) // 4 * 4, int(y) // 4 * 4), 4, (96, 120, 200), 0.6)

    def _scene(self, surf, t):
        low = self.sky.copy()
        for x, y, img, sp in self.clouds:
            low.blit(img, (int(x), int(y + math.sin(t * 0.2 + x) * 1.5)))
        for x, y, sp, ph in self.birds:
            f = 2 if int(t * 5 + ph) % 2 else -2
            yy = int(y + math.sin(t + ph) * 5)
            bx = int(x)
            pygame.draw.line(low, (28, 24, 60), (bx - 4, yy + f), (bx, yy), 1)
            pygame.draw.line(low, (28, 24, 60), (bx, yy), (bx + 4, yy + f), 1)
        for i in range(26):                                     # sparkling sea
            y = HZ + 6 + (i * 23) % (LH - HZ - 10)
            x = int((i * 89 + t * (6 + i % 5 * 2)) % (LW + 60)) - 30
            if int(t * 2 + i) % 3:
                pygame.draw.rect(low, (170, 226, 232), (x, y, 8 + (i * 7) % 16, 1))
        low.blit(self.fg, (1 if math.sin(t * 0.9) > 0.5 else 0, 0))
        for x, y, sp, ph, col in self.petals:
            low.set_at((int(x) % LW, int(y) % LH), col)
            low.set_at((int(x + 1) % LW, int(y) % LH), col)
        surf.blit(retro.upscale(low), (0, 0))
