"""Retro / pixel-art toolkit, all generated in code.

* two bitmap fonts (5x7 and 3x5, upper case) drawn as crisp pixel blocks at even scales,
* `install()` patches pygame so that rounded rects become stepped "notched" pixel corners and every
  smooth scale / rotozoom becomes nearest-neighbour,
* the whole game lives on a 2 px grid (a 640x360 picture magnified x2).
"""
import pygame

PX = 2                                  # logical pixel size in real pixels

# ---------------------------------------------------------------- 5x7 font
_F5 = {
    "A": ".###.|#...#|#...#|#####|#...#|#...#|#...#",
    "B": "####.|#...#|#...#|####.|#...#|#...#|####.",
    "C": ".###.|#...#|#....|#....|#....|#...#|.###.",
    "D": "####.|#...#|#...#|#...#|#...#|#...#|####.",
    "E": "#####|#....|#....|####.|#....|#....|#####",
    "F": "#####|#....|#....|####.|#....|#....|#....",
    "G": ".###.|#...#|#....|#.###|#...#|#...#|.###.",
    "H": "#...#|#...#|#...#|#####|#...#|#...#|#...#",
    "I": ".###.|..#..|..#..|..#..|..#..|..#..|.###.",
    "J": "..###|...#.|...#.|...#.|...#.|#..#.|.##..",
    "K": "#...#|#..#.|#.#..|##...|#.#..|#..#.|#...#",
    "L": "#....|#....|#....|#....|#....|#....|#####",
    "M": "#...#|##.##|#.#.#|#.#.#|#...#|#...#|#...#",
    "N": "#...#|##..#|#.#.#|#..##|#...#|#...#|#...#",
    "O": ".###.|#...#|#...#|#...#|#...#|#...#|.###.",
    "P": "####.|#...#|#...#|####.|#....|#....|#....",
    "Q": ".###.|#...#|#...#|#...#|#.#.#|#..#.|.##.#",
    "R": "####.|#...#|#...#|####.|#.#..|#..#.|#...#",
    "S": ".####|#....|#....|.###.|....#|....#|####.",
    "T": "#####|..#..|..#..|..#..|..#..|..#..|..#..",
    "U": "#...#|#...#|#...#|#...#|#...#|#...#|.###.",
    "V": "#...#|#...#|#...#|#...#|#...#|.#.#.|..#..",
    "W": "#...#|#...#|#...#|#.#.#|#.#.#|##.##|#...#",
    "X": "#...#|#...#|.#.#.|..#..|.#.#.|#...#|#...#",
    "Y": "#...#|#...#|.#.#.|..#..|..#..|..#..|..#..",
    "Z": "#####|....#|...#.|..#..|.#...|#....|#####",
    "0": ".###.|#...#|#..##|#.#.#|##..#|#...#|.###.",
    "1": "..#..|.##..|..#..|..#..|..#..|..#..|.###.",
    "2": ".###.|#...#|....#|...#.|..#..|.#...|#####",
    "3": ".###.|#...#|....#|..##.|....#|#...#|.###.",
    "4": "...#.|..##.|.#.#.|#..#.|#####|...#.|...#.",
    "5": "#####|#....|####.|....#|....#|#...#|.###.",
    "6": "..##.|.#...|#....|####.|#...#|#...#|.###.",
    "7": "#####|....#|...#.|..#..|.#...|.#...|.#...",
    "8": ".###.|#...#|#...#|.###.|#...#|#...#|.###.",
    "9": ".###.|#...#|#...#|.####|....#|...#.|.##..",
    " ": ".....|.....|.....|.....|.....|.....|.....",
    ".": ".....|.....|.....|.....|.....|..##.|..##.",
    ",": ".....|.....|.....|.....|..##.|...#.|..#..",
    ":": ".....|..##.|..##.|.....|..##.|..##.|.....",
    ";": ".....|..##.|..##.|.....|..##.|...#.|..#..",
    "!": "..#..|..#..|..#..|..#..|..#..|.....|..#..",
    "?": ".###.|#...#|....#|...#.|..#..|.....|..#..",
    "'": "..#..|..#..|.#...|.....|.....|.....|.....",
    '"': ".#.#.|.#.#.|.....|.....|.....|.....|.....",
    "-": ".....|.....|.....|#####|.....|.....|.....",
    "+": ".....|..#..|..#..|#####|..#..|..#..|.....",
    "=": ".....|.....|#####|.....|#####|.....|.....",
    "/": "....#|....#|...#.|..#..|.#...|#....|#....",
    "(": "...#.|..#..|.#...|.#...|.#...|..#..|...#.",
    ")": ".#...|..#..|...#.|...#.|...#.|..#..|.#...",
    "[": ".###.|.#...|.#...|.#...|.#...|.#...|.###.",
    "]": ".###.|...#.|...#.|...#.|...#.|...#.|.###.",
    "<": "...#.|..#..|.#...|#....|.#...|..#..|...#.",
    ">": ".#...|..#..|...#.|....#|...#.|..#..|.#...",
    "%": "##..#|##..#|...#.|..#..|.#...|#..##|#..##",
    "$": "..#..|.####|#.#..|.###.|..#.#|####.|..#..",
    "#": ".#.#.|#####|.#.#.|.#.#.|.#.#.|#####|.#.#.",
    "*": ".....|#.#.#|.###.|#####|.###.|#.#.#|.....",
    "&": ".##..|#..#.|#.#..|.#...|#.#.#|#..#.|.##.#",
    "_": ".....|.....|.....|.....|.....|.....|#####",
    "^": "..#..|.#.#.|#...#|.....|.....|.....|.....",
    "|": "..#..|..#..|..#..|..#..|..#..|..#..|..#..",
}
# ---------------------------------------------------------------- 3x5 font
_F3 = {
    "A": ".#.|#.#|###|#.#|#.#", "B": "##.|#.#|##.|#.#|##.", "C": ".##|#..|#..|#..|.##", "D": "##.|#.#|#.#|#.#|##.",
    "E": "###|#..|##.|#..|###", "F": "###|#..|##.|#..|#..", "G": ".##|#..|#.#|#.#|.##", "H": "#.#|#.#|###|#.#|#.#",
    "I": "###|.#.|.#.|.#.|###", "J": "..#|..#|..#|#.#|.#.", "K": "#.#|#.#|##.|#.#|#.#", "L": "#..|#..|#..|#..|###",
    "M": "#.#|###|###|#.#|#.#", "N": "##.|#.#|#.#|#.#|#.#", "O": ".#.|#.#|#.#|#.#|.#.", "P": "##.|#.#|##.|#..|#..",
    "Q": ".#.|#.#|#.#|##.|.##", "R": "##.|#.#|##.|#.#|#.#", "S": ".##|#..|.#.|..#|##.", "T": "###|.#.|.#.|.#.|.#.",
    "U": "#.#|#.#|#.#|#.#|###", "V": "#.#|#.#|#.#|#.#|.#.", "W": "#.#|#.#|###|###|#.#", "X": "#.#|#.#|.#.|#.#|#.#",
    "Y": "#.#|#.#|.#.|.#.|.#.", "Z": "###|..#|.#.|#..|###",
    "0": "###|#.#|#.#|#.#|###", "1": ".#.|##.|.#.|.#.|###", "2": "##.|..#|.#.|#..|###", "3": "##.|..#|.#.|..#|##.",
    "4": "#.#|#.#|###|..#|..#", "5": "###|#..|##.|..#|##.", "6": ".##|#..|###|#.#|###", "7": "###|..#|.#.|.#.|.#.",
    "8": "###|#.#|###|#.#|###", "9": "###|#.#|###|..#|##.",
    " ": "...|...|...|...|...", ".": "...|...|...|...|.#.", ",": "...|...|...|.#.|#..", ":": "...|.#.|...|.#.|...",
    ";": "...|.#.|...|.#.|#..", "!": ".#.|.#.|.#.|...|.#.", "?": "##.|..#|.#.|...|.#.", "'": ".#.|.#.|...|...|...",
    '"': "#.#|#.#|...|...|...", "-": "...|...|###|...|...", "+": "...|.#.|###|.#.|...", "=": "...|###|...|###|...",
    "/": "..#|..#|.#.|#..|#..", "(": ".#.|#..|#..|#..|.#.", ")": ".#.|..#|..#|..#|.#.", "<": "..#|.#.|#..|.#.|..#",
    ">": "#..|.#.|..#|.#.|#..", "%": "#.#|..#|.#.|#..|#.#", "$": ".##|##.|.#.|.##|##.", "|": ".#.|.#.|.#.|.#.|.#.",
    "_": "...|...|...|...|###", "*": "...|#.#|.#.|#.#|...", "#": "#.#|###|#.#|###|#.#", "&": ".#.|#.#|.#.|#.#|.##",
}


def _parse(table, w, h):
    out = {}
    for ch, rows in table.items():
        r = rows.split("|")
        out[ch] = [[c == "#" for c in row] for row in r]
    return out


_G5 = _parse(_F5, 5, 7)
_G3 = _parse(_F3, 3, 5)
_glyph_cache = {}


def font_spec(size):
    """Map a nominal point size onto (glyph table, glyph w, glyph h, integer scale). Scales are even (2 px grid)."""
    if size <= 15:
        return _G3, 3, 5, 2
    if size <= 27:
        return _G5, 5, 7, 2
    if size <= 47:
        return _G5, 5, 7, 4
    if size <= 79:
        return _G5, 5, 7, 6
    if size <= 109:
        return _G5, 5, 7, 8
    return _G5, 5, 7, 12


def _glyph(table, gw, gh, sc, ch, color):
    key = (id(table), sc, ch, color)
    s = _glyph_cache.get(key)
    if s is None:
        rows = table.get(ch) or table.get(ch.upper()) or table["?"]
        s = pygame.Surface((gw * sc, gh * sc), pygame.SRCALPHA)
        for y, row in enumerate(rows):
            for x, on in enumerate(row):
                if on:
                    pygame.draw.rect(s, color, (x * sc, y * sc, sc, sc))
        _glyph_cache[key] = s
    return s


_text_cache = {}


def render(text, size, color):
    """Pixel text surface (transparent background)."""
    key = (text, size, color)
    s = _text_cache.get(key)
    if s is None:
        if len(_text_cache) > 1200:
            _text_cache.clear()
        table, gw, gh, sc = font_spec(size)
        adv = (gw + 1) * sc
        s = pygame.Surface((max(1, len(text) * adv - sc), gh * sc), pygame.SRCALPHA)
        for i, ch in enumerate(text):
            s.blit(_glyph(table, gw, gh, sc, ch, color), (i * adv, 0))
        _text_cache[key] = s
    return s


def outline_px(size):
    return 2 if font_spec(size)[3] <= 4 else 4


# ---------------------------------------------------------------- pygame patches
_orig_rect = pygame.draw.rect
_orig_scale = pygame.transform.scale
_orig_rotate = pygame.transform.rotate
_installed = False


def _notch(br, w, h):
    """Step size (in real pixels) of the notched corner for a requested border radius."""
    if br <= 0 or min(w, h) < 12:
        return 0
    if br < 6:
        return 0
    if br < 12:
        return 2
    if br < 18:
        return 4
    return 6


def pixel_rect(surface, color, rect, width=0, border_radius=0, **kw):
    """pygame.draw.rect replacement: a border radius becomes a stepped (notched) pixel corner."""
    r = pygame.Rect(rect)
    if kw:
        return _orig_rect(surface, color, r, width, border_radius, **kw)
    c = _notch(border_radius, r.w, r.h)
    if c == 0:
        return _orig_rect(surface, color, r, width)
    x, y, w, h = r
    if width == 0:
        _orig_rect(surface, color, (x + c, y, w - 2 * c, h))
        _orig_rect(surface, color, (x, y + c, c, h - 2 * c))
        _orig_rect(surface, color, (x + w - c, y + c, c, h - 2 * c))
        if c > 2:                                        # second step of the staircase
            _orig_rect(surface, color, (x + 2, y + 2, w - 4, h - 4))
        return r
    t = max(1, width)
    _orig_rect(surface, color, (x + c, y, w - 2 * c, t))
    _orig_rect(surface, color, (x + c, y + h - t, w - 2 * c, t))
    _orig_rect(surface, color, (x, y + c, t, h - 2 * c))
    _orig_rect(surface, color, (x + w - t, y + c, t, h - 2 * c))
    for i in range(c // 2):                              # staircase corners, blocks sized like the border
        _orig_rect(surface, color, (x + c - 2 * i - 2, y + 2 * i, t, t))
        _orig_rect(surface, color, (x + w - c + 2 * i + 2 - t, y + 2 * i, t, t))
        _orig_rect(surface, color, (x + c - 2 * i - 2, y + h - 2 * i - t, t, t))
        _orig_rect(surface, color, (x + w - c + 2 * i + 2 - t, y + h - 2 * i - t, t, t))
    return r


def nearest_rotozoom(surf, angle, scale):
    if scale != 1:
        w, h = surf.get_size()
        surf = _orig_scale(surf, (max(1, int(w * scale)), max(1, int(h * scale))))
    if abs(angle) > 0.01:
        surf = _orig_rotate(surf, angle)
    return surf


def install():
    """Route rounded rects to notched pixel corners and smooth scaling to nearest-neighbour."""
    global _installed
    if _installed:
        return
    pygame.draw.rect = pixel_rect
    pygame.transform.smoothscale = lambda surf, size, dest=None: _orig_scale(surf, size, dest) if dest is not None else _orig_scale(surf, size)
    pygame.transform.rotozoom = nearest_rotozoom
    _installed = True


def upscale(surf, factor=PX):
    w, h = surf.get_size()
    return _orig_scale(surf, (w * factor, h * factor))
