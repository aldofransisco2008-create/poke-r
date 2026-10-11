"""Text and shape helpers for the retro pixel look: bitmap-font text with pixel outlines, square "dots",
blocky shadows and highlight rings. (The module keeps its old name; nothing glows any more.)
"""
import colorsys

import pygame

import config
from effects import retro

_cache = {}
OUTLINE = (24, 16, 40)


# ------------------------------------------------------------------ colors
def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def scale(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


def hsv(h, s=1.0, v=1.0):
    return tuple(int(x * 255) for x in colorsys.hsv_to_rgb(h % 1.0, s, v))


def rainbow(t, speed=0.6, steps=12):
    """Quantised hue: it steps like an old palette cycle."""
    return hsv(int(t * speed * steps) / steps, 0.6, 1.0)


# ------------------------------------------------------------------ text (bitmap font)
def render_text(text, size, color, kind=None):
    return retro.render(text.upper(), size, color)


def _anchor(rect, anchor, pos):
    setattr(rect, anchor, pos)
    return rect


def draw_text(surf, text, size, color, pos, anchor="center", kind=None):
    s = render_text(text, size, color)
    r = _anchor(s.get_rect(), anchor, (int(pos[0]), int(pos[1])))
    surf.blit(s, r)
    return r


def _outlined(text, size, color):
    key = ("o", text, size, color)
    s = _cache.get(key)
    if s is None:
        if len(_cache) > 900:
            _cache.clear()
        w = retro.outline_px(size)
        fill = render_text(text, size, color)
        edge = render_text(text, size, OUTLINE)
        s = pygame.Surface((fill.get_width() + 2 * w, fill.get_height() + 2 * w + (w if retro.font_spec(size)[3] >= 4 else 0)),
                           pygame.SRCALPHA)
        for dx in (-w, 0, w):
            for dy in (-w, 0, w):
                s.blit(edge, (w + dx, w + dy))
        if retro.font_spec(size)[3] >= 4:               # chunky drop shadow under big text
            s.blit(edge, (w, 2 * w))
            s.blit(edge, (w + w, 2 * w))
        s.blit(fill, (w, w))
        _cache[key] = s
    return s


def draw_glow_text(surf, text, size, color, pos, anchor="center", intensity=1.0, spread=0, kind=None):
    """Pixel text with a dark pixel outline (the name is legacy). `intensity` < 1 fades it out."""
    base = _outlined(text.upper(), size, mix(color, config.CREAM, 0.25))
    r = _anchor(base.get_rect(), anchor, (int(pos[0]), int(pos[1])))
    if intensity < 0.97:
        base = base.copy()
        base.set_alpha(int(255 * max(0.0, intensity)))
    surf.blit(base, r)
    return r


# ------------------------------------------------------------------ shapes
def draw_shadow(surf, rect, radius=12, offset=(0, 5), alpha=90, grow=0):
    rect = pygame.Rect(rect).inflate(grow, grow)
    key = ("sh", rect.w, rect.h, radius, alpha)
    s = _cache.get(key)
    if s is None:
        s = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(s, (8, 6, 24, alpha), (0, 0, *rect.size), border_radius=radius)
        _cache[key] = s
    surf.blit(s, (rect.x + (offset[0] // 2) * 2, rect.y + (offset[1] // 2) * 2))


def draw_ellipse_shadow(surf, cx, cy, w, h, alpha=90):
    """Blocky oval shadow: three stacked slabs instead of a smooth ellipse."""
    key = ("es", int(w) // 2, int(h) // 2, alpha)
    s = _cache.get(key)
    if s is None:
        W, H = int(w) // 2 * 2, max(6, int(h) // 2 * 2)
        s = pygame.Surface((W, H), pygame.SRCALPHA)
        col = (8, 6, 24, alpha)
        third = H // 3 // 2 * 2 or 2
        pygame.draw.rect(s, col, (W // 6 // 2 * 2, 0, W - W // 3 // 2 * 2, third))
        pygame.draw.rect(s, col, (0, third, W, H - 2 * third))
        pygame.draw.rect(s, col, (W // 6 // 2 * 2, H - third, W - W // 3 // 2 * 2, third))
        _cache[key] = s
    surf.blit(s, (int(cx) - s.get_width() // 2, int(cy) - s.get_height() // 2))


def disc(radius, color, alpha=255):
    """A square 'dot' with a lighter centre pixel (particles, motes)."""
    radius = max(2, int(radius))
    key = ("dot", radius, color, alpha)
    s = _cache.get(key)
    if s is None:
        d = max(2, (radius // 2) * 2)
        s = pygame.Surface((d, d), pygame.SRCALPHA)
        pygame.draw.rect(s, (*color, alpha), (0, 0, d, d))
        pygame.draw.rect(s, (*mix(color, (255, 255, 255), .5), alpha), (0, 0, max(2, d // 2), max(2, d // 2)))
        _cache[key] = s
    return s


def draw_glow_circle(surf, center, radius, color, intensity=1.0):
    """Square pixel dot (name is legacy)."""
    g = disc(max(2, int(radius)), color, int(255 * min(1.0, max(0.1, intensity))))
    surf.blit(g, (int(center[0]) // 2 * 2 - g.get_width() // 2, int(center[1]) // 2 * 2 - g.get_height() // 2))


def bloom(frame, strength=0.4):
    return
