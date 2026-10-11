"""Retro pixel UI widgets: notched panels and buttons with flat colour bands, chunky borders and bevels."""
import math

import pygame

import config
from effects import glow

_cache = {}


def _bands(w, h, top, bottom, radius, alpha=255, n=None):
    """Vertical gradient quantised into a few flat colour bands (no smooth shading)."""
    n = n or max(2, min(5, h // 14))
    key = ("b", w, h, top, bottom, radius, alpha, n)
    s = _cache.get(key)
    if s is None:
        if len(_cache) > 600:
            _cache.clear()
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        step = max(2, (h // n) // 2 * 2)
        for i in range(n):
            y0 = i * step
            y1 = h if i == n - 1 else y0 + step
            pygame.draw.rect(s, (*glow.mix(top, bottom, i / max(1, n - 1)), alpha), (0, y0, w, y1 - y0))
        mask = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, w, h), border_radius=radius)
        s.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        _cache[key] = s
    return s


def draw_corners(surf, rect, color=config.BRONZE, size=14):
    """Small square studs plus a short L in each corner."""
    r = pygame.Rect(rect)
    for (x, y, dx, dy) in ((r.left + 6, r.top + 6, 1, 1), (r.right - 8, r.top + 6, -1, 1),
                           (r.left + 6, r.bottom - 8, 1, -1), (r.right - 8, r.bottom - 8, -1, -1)):
        pygame.draw.rect(surf, color, (x, y, 4, 4))
        pygame.draw.rect(surf, glow.mix(color, config.CREAM, .5), (x, y, 2, 2))


def draw_panel(surf, rect, color=None, alpha=235, radius=16, glow_k=0, corners=False):
    """Dark panel with a chunky light border. `color` only tints the border."""
    rect = pygame.Rect(rect)
    glow.draw_shadow(surf, rect, radius, (0, 6), 110)
    surf.blit(_bands(rect.w, rect.h, (40, 52, 104), (26, 34, 76), radius, min(255, alpha + 15)), rect)
    edge = glow.mix(config.NAVY_LINE, color or config.NAVY_LINE, 0.3)
    pygame.draw.rect(surf, (12, 14, 34), rect.inflate(4, 4), 2, border_radius=radius + 2)
    pygame.draw.rect(surf, edge, rect, 2, border_radius=radius)
    pygame.draw.rect(surf, (18, 24, 56), rect.inflate(-8, -8), 2, border_radius=max(2, radius - 4))
    if corners:
        draw_corners(surf, rect)


def draw_parchment(surf, rect, radius=14, corners=False, shadow=True):
    rect = pygame.Rect(rect)
    if shadow:
        glow.draw_shadow(surf, rect, radius, (0, 6), 120)
    surf.blit(_bands(rect.w, rect.h, config.PARCH_TOP, config.PARCH_BOTTOM, radius, 255, 4), rect)
    pygame.draw.rect(surf, (90, 56, 44), rect, 4, border_radius=radius)
    pygame.draw.rect(surf, (190, 140, 100), rect.inflate(-12, -12), 2, border_radius=max(2, radius - 4))
    if corners:
        draw_corners(surf, rect, (170, 100, 60))


def draw_coin(surf, center, r=11, t=0.0):
    cx, cy = int(center[0]) // 2 * 2, int(center[1]) // 2 * 2
    w = max(4, int(r * (0.35 + 0.65 * abs(math.cos(t * 2.4)))) // 2 * 2) if t else r
    pygame.draw.ellipse(surf, (120, 76, 20), (cx - w - 2, cy - r - 2, 2 * w + 4, 2 * r + 4))
    pygame.draw.ellipse(surf, config.GOLD, (cx - w, cy - r, 2 * w, 2 * r))
    if w > 6:
        pygame.draw.rect(surf, (255, 246, 190), (cx - w // 2, cy - r // 2, 2, r // 2 + 2))
        pygame.draw.rect(surf, (200, 140, 30), (cx + 2, cy + 2, max(2, w // 3), max(2, r // 3)))


def draw_money_pill(surf, right, cy, amount_text, t=0.0):
    tw = glow.render_text(amount_text, 22, config.CREAM).get_width()
    r = pygame.Rect(0, 0, tw + 68, 40)
    r.midright = (right, cy)
    glow.draw_shadow(surf, r, 12, (0, 4), 110)
    pygame.draw.rect(surf, (26, 34, 76), r, border_radius=12)
    pygame.draw.rect(surf, config.NAVY_LINE, r, 4, border_radius=12)
    draw_coin(surf, (r.x + 24, r.centery), 10, t)
    glow.draw_text(surf, amount_text, 22, config.CREAM, (r.x + 46, r.centery), "midleft")
    return r


def draw_pill(surf, rect, text, size=18, fill=(26, 34, 76), edge=config.NAVY_LINE, color=config.CREAM):
    r = pygame.Rect(rect)
    pygame.draw.rect(surf, fill, r, border_radius=12)
    pygame.draw.rect(surf, edge, r, 4, border_radius=12)
    glow.draw_text(surf, text, size, color, r.center)


def draw_dots(surf, x, y, full, total, color=config.CREAM, r=7, gap=8, anchor="left", max_w=None):
    """A row of pips; with max_w the pips shrink so the row never gets wider than that."""
    size = 14
    w = total * size + (total - 1) * gap
    if max_w and total and w > max_w:
        k = max_w / w
        size, gap = max(6, int(size * k)), max(2, int(gap * k))
        w = total * size + (total - 1) * gap
    x0 = x if anchor == "left" else x - w
    for i in range(total):
        b = pygame.Rect(x0 + i * (size + gap), y - size // 2, size, size)
        if i < full:
            pygame.draw.rect(surf, (12, 14, 34), b.inflate(4, 4))
            pygame.draw.rect(surf, color, b)
            pygame.draw.rect(surf, (255, 255, 255), (b.x, b.y, 4, 4))
        else:
            pygame.draw.rect(surf, config.NAVY_LINE, b, 2)


_STYLES = {
    "primary": dict(top=(255, 100, 76), bottom=(214, 52, 60), edge=(96, 20, 40), text=config.CREAM, base=(140, 28, 48)),
    "secondary": dict(top=(60, 84, 150), bottom=(38, 52, 110), edge=(16, 20, 50), text=config.CREAM, base=(24, 32, 78)),
    "gold": dict(top=(255, 226, 110), bottom=(230, 170, 50), edge=(110, 66, 24), text=(50, 30, 20), base=(170, 110, 34)),
}


class GlowButton:
    """Chunky retro button. style: primary (red) | secondary (blue) | gold."""

    def __init__(self, rect, text, color=None, size=26, hotkey=None, style="secondary"):
        self.rect = pygame.Rect(rect)
        self.text, self.size, self.hotkey, self.style = text, size, hotkey, style
        self.color = color
        self.enabled = True
        self.hover = 0.0
        self.press = 0.0
        self.visible = True

    def handle_event(self, e, sfx=None):
        if not (self.visible and e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.rect.collidepoint(e.pos)):
            return False
        if not self.enabled:
            if sfx:
                sfx.play("error")
            return False
        self.press = 1.0
        if sfx:
            sfx.play("click")
        return True

    def update(self, dt):
        over = self.enabled and self.rect.collidepoint(pygame.mouse.get_pos())
        self.hover += ((1.0 if over else 0.0) - self.hover) * min(1.0, dt * 14)
        self.press = max(0.0, self.press - dt * 6)

    def draw(self, surf, t, text=None, icon=None):
        if not self.visible:
            return
        text = text or self.text
        st = _STYLES[self.style]
        if self.enabled:
            top, bottom, edge, tcol, base = st["top"], st["bottom"], st["edge"], st["text"], st["base"]
            if self.hover > 0.4:
                top, bottom = glow.mix(top, (255, 255, 255), .22), glow.mix(bottom, (255, 255, 255), .16)
        else:
            top, bottom, edge, tcol, base = (86, 90, 110), (66, 70, 90), (30, 30, 46), (140, 144, 164), (50, 54, 72)
        depth = 6 if self.press < 0.5 else 2                    # pressed buttons sink
        r = pygame.Rect(self.rect.x, self.rect.y + (6 - depth), self.rect.w, self.rect.h - 6)
        pygame.draw.rect(surf, edge, pygame.Rect(r.x, r.y + depth, r.w, r.h), border_radius=12)          # bottom slab
        pygame.draw.rect(surf, base, pygame.Rect(r.x + 2, r.y + depth, r.w - 4, r.h - 2), border_radius=12)
        body = pygame.Rect(r.x, r.y, r.w, r.h)
        pygame.draw.rect(surf, edge, body, border_radius=12)
        inner = body.inflate(-6, -6)
        surf.blit(_bands(inner.w, inner.h, top, bottom, 8, 255, 3), inner)
        pygame.draw.rect(surf, glow.mix(top, (255, 255, 255), .6), (inner.x + 4, inner.y, inner.w - 8, 2))
        cx, cy = body.centerx, body.centery
        if icon == "play":
            x0 = body.x + 24
            for i in range(5):
                pygame.draw.rect(surf, tcol, (x0 + i * 4, cy - 10 + i * 2, 4, 20 - i * 4))
        elif icon == "refresh":
            x0 = body.x + 22
            pygame.draw.rect(surf, tcol, (x0, cy - 8, 14, 4))
            pygame.draw.rect(surf, tcol, (x0, cy - 8, 4, 16))
            pygame.draw.rect(surf, tcol, (x0, cy + 4, 14, 4))
            pygame.draw.rect(surf, tcol, (x0 + 10, cy - 12, 8, 4))
        if self.enabled:
            glow.draw_text(surf, text, self.size, (24, 12, 32) if self.style != "gold" else (255, 244, 200), (cx + 2, cy + 2))
        glow.draw_text(surf, text, self.size, tcol, (cx, cy))


class Slider:
    """Horizontal slider (0..1): blocky track and a square knob."""

    def __init__(self, rect, value, on_change):
        self.rect = pygame.Rect(rect)
        self.value = value
        self.on_change = on_change
        self.drag = False

    def _set(self, x):
        self.value = max(0.0, min(1.0, (x - self.rect.x) / self.rect.w))
        self.on_change(self.value)

    def handle_event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.rect.inflate(20, 30).collidepoint(e.pos):
            self.drag = True
            self._set(e.pos[0])
            return True
        if e.type == pygame.MOUSEMOTION and self.drag:
            self._set(e.pos[0])
        if e.type == pygame.MOUSEBUTTONUP:
            self.drag = False
        return False

    def draw(self, surf):
        r = self.rect
        track = pygame.Rect(r.x, r.centery - 6, r.w, 12)
        pygame.draw.rect(surf, (90, 50, 40), track.inflate(4, 4))
        pygame.draw.rect(surf, (226, 200, 160), track)
        fill = int(r.w * self.value) // 4 * 4
        pygame.draw.rect(surf, config.RED, (r.x, r.centery - 6, fill, 12))
        for x in range(r.x + 4, r.x + fill, 8):
            pygame.draw.rect(surf, (255, 150, 130), (x, r.centery - 6, 2, 4))
        kx = r.x + fill
        pygame.draw.rect(surf, (60, 16, 20), (kx - 10, r.centery - 12, 20, 24))
        pygame.draw.rect(surf, (240, 90, 76), (kx - 8, r.centery - 10, 16, 20))
        pygame.draw.rect(surf, (255, 200, 180), (kx - 8, r.centery - 10, 6, 6))


class Toggle:
    def __init__(self, rect, value, on_change):
        self.rect = pygame.Rect(rect)
        self.value, self.on_change = value, on_change
        self.k = 1.0 if value else 0.0

    def handle_event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.rect.collidepoint(e.pos):
            self.value = not self.value
            self.on_change(self.value)
            return True
        return False

    def update(self, dt):
        self.k += ((1.0 if self.value else 0.0) - self.k) * min(1.0, dt * 16)

    def draw(self, surf):
        r = self.rect
        col = glow.mix((150, 140, 130), config.RED, 1.0 if self.k > 0.5 else 0.0)
        pygame.draw.rect(surf, (60, 30, 30), r.inflate(4, 4), border_radius=8)
        pygame.draw.rect(surf, col, r, border_radius=8)
        kx = r.x + 4 + int((r.w - r.h) * self.k) // 2 * 2
        pygame.draw.rect(surf, (60, 40, 40), (kx, r.y + 2, r.h - 4, r.h - 4))
        pygame.draw.rect(surf, (255, 246, 226), (kx + 2, r.y + 4, r.h - 8, r.h - 8))
