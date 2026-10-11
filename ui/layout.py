"""Layout constants and small shared UI helpers."""
import pygame

import config
from core.numfmt import fmt_num  # noqa: F401  (re-exported for the scenes)
from effects import glow
from effects.tween import out_cubic

W, H = config.SCREEN_W, config.SCREEN_H

# gameplay screen
DIE_SIZE, DIE_GAP = 104, 28
HAND_CY = 540
DECK_POS, DISCARD_POS = (150, 540), (1224, 540)
PLAY_CY, PLAY_X, PLAY_GAP = 330, 500, 16


TRAY_PAD, TRAY_MIN, TRAY_MAX = 60, 756, 1100     # room left and right of the dice; the tray grows with the hand


def tray_rect(n=config.HAND_SIZE):
    """The panel the hand rests on: wide enough for n dice with a comfortable gap and padding."""
    w = min(TRAY_MAX, max(TRAY_MIN, n * DIE_SIZE + (n - 1) * DIE_GAP + 2 * TRAY_PAD))
    return pygame.Rect(640 - w // 2, 448, w, 158)


def hand_x(i, n=config.HAND_SIZE):
    step = DIE_SIZE + DIE_GAP if n < 2 else min(DIE_SIZE + DIE_GAP, (tray_rect(n).w - 2 * TRAY_PAD - DIE_SIZE) / (n - 1))
    total = DIE_SIZE + (n - 1) * step
    return 640 - total / 2 + DIE_SIZE / 2 + i * step

# indexed by combo rank (1..10)
COMBO_COLORS = [None, (226, 220, 200), config.TEAL, config.TEAL, config.GREEN, config.GOLD,
                config.EMBER, config.RED, config.VIOLET, (236, 132, 180), None]
COMBO_SHAKE = [0, 0, 0.10, 0.16, 0.22, 0.30, 0.34, 0.42, 0.55, 0.8, 1.0]


def combo_color(rank, t):
    return glow.rainbow(t) if rank >= 10 else COMBO_COLORS[rank]


class FloatText:
    def __init__(self, x, y, text, color, size=36, life=1.1, rise=60):
        self.x, self.y, self.text, self.color, self.size = x, y, text, color, size
        self.life = self.max = life
        self.rise = rise

    def update(self, dt):
        self.life -= dt
        return self.life > 0

    def draw(self, surf):
        k = 1 - self.life / self.max
        y = self.y - self.rise * out_cubic(k)
        fade = min(1.0, self.life / (self.max * 0.4))
        glow.draw_glow_text(surf, self.text, self.size, self.color, (self.x, y), "center", fade)
