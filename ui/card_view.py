"""Parchment cards for the special dice, the slot bar, skill chips/offers and tooltips."""
import math

import pygame

import config
from core.cards import (CARD_COLOR, CARD_DESC, CARD_LONG, CARD_TIER, FACTION_COLOR, FACTION_OF, TIER_COLOR, TIER_NAME,
                        element_price, level_scale)
from effects import glow
from ui.dice_view import draw_kind_icon
from ui.widgets import draw_coin, draw_panel, draw_parchment

CARD_W, CARD_H = 100, 140
_SKILL_COLORS = [config.RED, config.TEAL, config.GOLD, config.GREEN, config.VIOLET, config.EMBER]
SKILL_COLOR = {s["key"]: _SKILL_COLORS[i % 6] for i, s in enumerate(config.SKILLS)}
EDGE = (34, 20, 44)


def _nrect(s, color, x, y, w, h, c):
    pygame.draw.rect(s, color, (x + c, y, w - 2 * c, h))
    pygame.draw.rect(s, color, (x, y + c, w, h - 2 * c))


def _foil(img, tier, t, uid, w, h):
    """Rare: a silver-blue shine sweeps across and the frame breathes.  Super: a rainbow foil sweep, a cycling frame and
    twinkling stars."""
    ph = uid * 0.37
    fx = pygame.Surface((w, h))
    sweep = ((t * (0.5 if tier == 2 else 0.8) + ph) % 1.7) * (w + h) - h * 0.7
    for k in range(18):                                     # a skewed band, brightest in the middle
        a = 1 - abs(k - 9) / 9
        col = glow.scale((120, 150, 210) if tier == 2 else glow.hsv(k / 18 + t * .5, .7, 1.0), .55 * a)
        pygame.draw.line(fx, col, (sweep + k * 3, 0), (sweep + k * 3 - h * 0.7, h), 3)
    img.blit(fx, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    edge = glow.mix((110, 180, 255), (255, 255, 255), .5 + .5 * math.sin(t * 4 + ph)) if tier == 2 else glow.rainbow(t * 2 + ph)
    pygame.draw.rect(img, edge, (3, 3, w - 6, h - 6), 2, border_radius=6)
    for i in range(3 if tier == 2 else 6):                  # twinkles
        k = (t * 0.9 + i * 0.37 + ph) % 1.0
        sx, sy = 10 + (i * 53 + int(ph * 100)) % (w - 20), 10 + (i * 37 + int(ph * 70)) % (h - 20)
        r = int(5 * math.sin(k * math.pi))
        if r > 0:
            c = (255, 255, 255)
            pygame.draw.line(img, c, (sx - r, sy), (sx + r, sy), 2)
            pygame.draw.line(img, c, (sx, sy - r), (sx, sy + r), 2)


def render_card(card, t, anim=None, w=CARD_W, h=CARD_H):
    """Pixel-art parchment card (drawn on a half-size canvas, magnified x2): medallion with turning rays."""
    ctype, col = card.type, CARD_COLOR[card.type]
    lw, lh = w // 2, h // 2
    s = pygame.Surface((lw, lh), pygame.SRCALPHA)
    tier = CARD_TIER[ctype]
    _nrect(s, EDGE if tier == 1 else glow.scale(TIER_COLOR[tier], .8), 0, 0, lw, lh, 3)    # rare / super: coloured frame
    _nrect(s, config.PARCH_TOP, 2, 2, lw - 4, lh - 4, 2)
    pygame.draw.rect(s, config.PARCH_BOTTOM, (4, lh // 2, lw - 8, lh // 2 - 4))
    pygame.draw.rect(s, (200, 150, 110), (4, 4, lw - 8, lh - 8), 1)
    cx, cy, R = lw // 2, 32, 13
    a0 = t * 0.6 + card.uid
    for i in range(8):                                    # rotating rays behind the medallion
        a = a0 + i * math.tau / 8
        pygame.draw.line(s, glow.mix(config.PARCH_BOTTOM, col, .5), (cx, cy),
                         (cx + math.cos(a) * (R + 9), cy + math.sin(a) * (R + 9)), 2)
    pygame.draw.circle(s, EDGE, (cx, cy), R + 2)
    pygame.draw.circle(s, glow.scale(col, .62), (cx, cy), R)
    pygame.draw.circle(s, col, (cx, cy - 1), R - 2)
    pygame.draw.rect(s, glow.mix(col, (255, 255, 255), .5), (cx - 8, cy - 8, 4, 2))
    bob = int(math.sin(t * 2.4 + card.uid) * 1.4)
    draw_kind_icon(s, ctype, (cx + 1, cy + 1 + bob), 8, glow.scale(col, .3))
    draw_kind_icon(s, ctype, (cx, cy + bob), 8, (255, 248, 230))
    for i in range(3):                                    # motes orbiting the medallion
        a = t * 1.5 + i * 2.1 + card.uid
        pygame.draw.rect(s, glow.mix(col, (255, 255, 255), .4), (int(cx + math.cos(a) * (R + 5)) // 1, int(cy + math.sin(a) * (R + 5) * .8), 2, 2))
    pygame.draw.rect(s, (222, 190, 150), (5, lh - 16, lw - 10, 11))
    pygame.draw.rect(s, (150, 100, 76), (5, lh - 16, lw - 10, 11), 1)
    img = pygame.transform.scale(s, (w, h))
    glow.draw_text(img, ctype.value, 12, config.INK, (w // 2, 13))
    glow.draw_text(img, FACTION_OF[ctype].name.upper(), 9, glow.scale(TIER_COLOR[tier], .7) if tier > 1 else (130, 100, 70),
                   (w // 2, 25))
    glow.draw_text(img, CARD_DESC[ctype], 11, glow.scale(col, .55), (w // 2, h - 21))
    if tier > 1:
        _foil(img, tier, t, card.uid, w, h)
    lv = getattr(card, "level", 1)
    if lv > 1:                                            # level badge, top-right
        b = pygame.Rect(w - 34, 34, 30, 18)
        pygame.draw.rect(img, (40, 24, 50), b, border_radius=6)
        pygame.draw.rect(img, config.GOLD, b, 2, border_radius=6)
        glow.draw_text(img, f"L{lv}", 12, config.GOLD, b.center)
    return img


def new_anim():
    return dict(roll=0.0, dur=0.6, val=None, shown=None, trig=0.0, land=0.0, acc=0.0)


class SlotBar:
    """The special-dice inventory: click to select (and sell), drag to reorder."""

    def __init__(self, run, x0=24, y0=82, gap=8, draggable=True):
        self.run, self.x0, self.y0, self.gap = run, x0, y0, gap
        self.draggable = draggable
        self.anims = {}
        self.selected = None
        self.hover = None
        self.press = None
        self.dragging = None
        self.drag_pos = (0, 0)

    def slot_rect(self, i):
        return pygame.Rect(self.x0 + i * (CARD_W + self.gap), self.y0, CARD_W, CARD_H)

    def anim(self, card):
        return self.anims.setdefault(card.uid, new_anim())

    def index_at(self, pos):
        for i in range(len(self.run.slots)):
            if self.slot_rect(i).collidepoint(pos):
                return i
        return None

    def handle_event(self, e):
        """Returns 'select' when a slot was clicked, 'reorder' after a drop."""
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            i = self.index_at(e.pos)
            self.press = (i, e.pos) if i is not None else None
        elif e.type == pygame.MOUSEMOTION and self.press and self.draggable and self.dragging is None:
            if math.dist(e.pos, self.press[1]) > 8:
                self.dragging = self.press[0]
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1 and self.press:
            i, _ = self.press
            if self.dragging is not None:
                n = len(self.run.slots)
                j = max(0, min(n - 1, int((e.pos[0] - self.x0 + self.gap / 2) // (CARD_W + self.gap))))
                self.run.slots.insert(j, self.run.slots.pop(i))
                self.selected = j
                res = "reorder"
            else:
                self.selected = None if self.selected == i else i
                res = "select"
            self.press = self.dragging = None
            return res
        return None

    def update(self, dt):
        self.hover = self.index_at(pygame.mouse.get_pos())
        if self.dragging is not None:
            self.drag_pos = pygame.mouse.get_pos()
        if self.selected is not None and self.selected >= len(self.run.slots):
            self.selected = None

    def _blit(self, surf, card, rect, t, lift=0, alpha=255, extra=1.0):
        img = render_card(card, t)
        if extra != 1:
            img = pygame.transform.rotozoom(img, 0, extra)
        if alpha < 255:
            img.set_alpha(alpha)
        surf.blit(img, img.get_rect(center=(rect.centerx, rect.centery - lift)))

    def draw(self, surf, t):
        for i in range(self.run.element_slots):
            r = self.slot_rect(i)
            if i >= len(self.run.slots) or i == self.dragging:
                pygame.draw.rect(surf, (44, 52, 62), r, border_radius=10)
                pygame.draw.rect(surf, (28, 34, 44), r, 3, border_radius=10)
                glow.draw_text(surf, "?", 52, (86, 96, 108), r.center)
                continue
            card = self.run.slots[i]
            hov = (i == self.hover and self.dragging is None)
            sel = (i == self.selected)
            lift = 6 if (hov or sel) else 0
            rr = r.move(0, -lift)
            glow.draw_shadow(surf, rr, 10, (0, 6 + lift // 2), 100)
            self._blit(surf, card, r, t, lift)
            if sel:
                pygame.draw.rect(surf, config.GOLD, rr.inflate(6, 6), 3, border_radius=12)
        if self.dragging is not None and self.dragging < len(self.run.slots):
            card = self.run.slots[self.dragging]
            r = pygame.Rect(0, 0, CARD_W, CARD_H)
            r.center = self.drag_pos
            glow.draw_shadow(surf, r, 10, (6, 12), 120)
            self._blit(surf, card, r, t, 0, 240, 1.08)


def wrap_lines(text, size, maxw):
    lines, line = [], ""
    for w in text.split():
        if glow.render_text((line + " " + w).strip(), size, (255, 255, 255)).get_width() > maxw and line:
            lines.append(line)
            line = w
        else:
            line = (line + " " + w).strip()
    return lines + [line]


def _price_pill(surf, center, price, col, w=64, h=24):
    small = h <= 18
    p = pygame.Rect(0, 0, w, h)
    p.center = center
    pygame.draw.rect(surf, glow.scale(col, .55), p.move(0, 2), border_radius=h // 2)
    pygame.draw.rect(surf, col, p, border_radius=h // 2)
    draw_coin(surf, (p.x + (11 if small else 14), p.centery), 5 if small else 7)
    glow.draw_text(surf, str(price), 14 if small else 16, config.CREAM, (p.x + (20 if small else 26), p.centery), "midleft")


def _sold(surf, rect, radius=10):
    pygame.draw.rect(surf, (36, 46, 58), rect, border_radius=radius)
    pygame.draw.rect(surf, (70, 84, 98), rect, 2, border_radius=radius)
    glow.draw_text(surf, "SOLD", 22, (110, 124, 138), rect.center)


def draw_skill_tile(surf, rect, sdef, level, hover, affordable, full=False, sold=False, price=None):
    """Tall parchment card for one skill on sale: name, the combo it levels, level and score change, price."""
    rect = pygame.Rect(rect)
    if sold:
        _sold(surf, rect)
        return
    rect = rect.move(0, -int(4 * hover))
    col = SKILL_COLOR[sdef.key]
    draw_parchment(surf, rect, 10)
    pygame.draw.rect(surf, col, (rect.x + 8, rect.y + 8, rect.w - 16, 6), border_radius=3)
    y = rect.y + 40
    for ln in wrap_lines(sdef.name.upper(), 16, rect.w - 16):
        glow.draw_text(surf, ln, 16, config.INK, (rect.centerx, y))
        y += 20
    y += 8
    for ln in wrap_lines(sdef.desc, 13, rect.w - 20)[:3]:
        glow.draw_text(surf, ln, 13, (84, 66, 46), (rect.centerx, y), kind="ui")
        y += 17
    step = config.COMBO_LEVEL_STEP
    glow.draw_text(surf, f"Lv{level} -> Lv{level + 1}", 14, (56, 120, 60), (rect.centerx, rect.bottom - 72), kind="ui")
    glow.draw_text(surf, f"x{1 + step * (level - 1):.1f} -> x{1 + step * level:.1f}", 14, (56, 120, 60),
                   (rect.centerx, rect.bottom - 52), kind="ui")
    if full:
        glow.draw_text(surf, "MAX", 18, (120, 116, 108), (rect.centerx, rect.bottom - 22))
    else:
        _price_pill(surf, (rect.centerx, rect.bottom - 22), sdef.price if price is None else price,
                    col if affordable else (120, 116, 108), 76, 26)


def draw_voucher_tile(surf, rect, vdef, level, hover, affordable, price, maxed, sold=False):
    """Wide tile for a voucher: name, effect, level pips, price."""
    rect = pygame.Rect(rect)
    if sold:
        _sold(surf, rect)
        return
    rect = rect.move(0, -int(3 * hover))
    col = config.VIOLET
    draw_parchment(surf, rect, 10)
    pygame.draw.rect(surf, col, (rect.x, rect.y + 8, 6, rect.h - 16), border_radius=3)
    glow.draw_text(surf, vdef.name.upper(), 15, config.INK, (rect.x + 18, rect.y + 20), "midleft")
    glow.draw_text(surf, vdef.desc, 12, (84, 66, 46), (rect.x + 18, rect.y + 41), "midleft", kind="ui")
    for i in range(vdef.max_level):                       # level pips
        c = (rect.x + 24 + i * 16, rect.bottom - 10)
        pygame.draw.circle(surf, col if i < level else (200, 180, 140), c, 5)
        pygame.draw.circle(surf, glow.scale(col, .6), c, 5, 1)
    if maxed:
        glow.draw_text(surf, "MAX", 17, (120, 116, 108), (rect.right - 14, rect.y + 20), "midright")
    else:
        _price_pill(surf, (rect.right - 42, rect.y + 20), price, col if affordable else (120, 116, 108), 66, 22)


def draw_element_offer(surf, rect, card, t, hover, ok, price, sold=False, owned_level=0, synergy=None):
    """One Element on sale: tier (LEVEL UP if you own it, the faction count if it grows one of yours), card art, price."""
    rect = pygame.Rect(rect)
    tier = CARD_TIER[card.type]
    if owned_level and not sold:
        glow.draw_text(surf, f"LEVEL UP {owned_level}>{owned_level + 1}", 12, config.GOLD, (rect.centerx, rect.y - 10))
    elif synergy and not sold:                            # pulses: this completes more of a faction you own
        col = glow.mix(FACTION_COLOR[FACTION_OF[card.type].key], (255, 255, 255), .3 + .3 * math.sin(t * 6))
        glow.draw_text(surf, synergy, 12, col, (rect.centerx, rect.y - 10))
    else:
        glow.draw_text(surf, TIER_NAME[tier].upper(), 12, glow.mix(TIER_COLOR[tier], config.CREAM, .25), (rect.centerx, rect.y - 10))
    if sold:
        _sold(surf, rect.inflate(0, 0), 12)
        return
    lift = int(6 * hover)
    art = rect.move(0, -lift)
    glow.draw_shadow(surf, art, 12, (0, 6 + lift // 2), 100)
    surf.blit(render_card(card, t, None, rect.w, rect.h), art)
    if hover:
        pygame.draw.rect(surf, config.GOLD, art.inflate(6, 6), 3, border_radius=12)
    _price_pill(surf, (rect.centerx, rect.bottom + 26), price, CARD_COLOR[card.type] if ok else (120, 116, 108), 80, 26)


def faction_lines(ctype):
    """'Faction: A, B, C' and the 2- and 3-member bonuses."""
    f = FACTION_OF[ctype]
    return (f"{f.name.upper()}: " + ", ".join(m.value for m in f.members),
            f"2 played: {f.two}", f"3 played: {f.three}")


def draw_tooltip(surf, pos, ctype, maxw=320, level=1):
    """Panel with the name, tier, full description and synergy of an Element, bottom-centred on pos."""
    col = CARD_COLOR[ctype]
    tier = CARD_TIER[ctype]
    lines = wrap_lines(CARD_LONG[ctype], 15, maxw - 28)
    syn = [ln for part in faction_lines(ctype) for ln in wrap_lines(part, 14, maxw - 28)]
    if level > 1:
        lines = lines + [f"Level {level}: numbers x{level_scale(level):.2f}"]
    h = 56 + 20 * len(lines) + 18 * len(syn)
    r = pygame.Rect(0, 0, maxw, h)
    r.midbottom = pos
    r.clamp_ip(pygame.Rect(8, 8, 1264, 704))
    draw_panel(surf, r, col, 245)
    glow.draw_text(surf, ctype.value.upper(), 17, glow.mix(col, config.CREAM, .35), (r.x + 16, r.y + 22), "midleft")
    glow.draw_text(surf, TIER_NAME[tier].upper(), 13, glow.mix(TIER_COLOR[tier], config.CREAM, .3), (r.right - 16, r.y + 22),
                   "midright")
    for i, ln in enumerate(lines):
        glow.draw_text(surf, ln, 15, config.CREAM, (r.x + 16, r.y + 48 + i * 20), "midleft")
    y = r.y + 50 + 20 * len(lines)
    for i, ln in enumerate(syn):
        glow.draw_text(surf, ln, 14, config.GOLD, (r.x + 16, y + i * 18), "midleft", kind="ui")


_list_cards = {}


def draw_element_list(surf, t, top=114, mouse=None):
    """All Elements: one row per faction (common, rare, super side by side), factions in two columns - collection
    screen and INFO book. Hover an Element for its full text."""
    from core.cards import FACTIONS, MultiplierCard
    mouse = mouse or pygame.mouse.get_pos()
    hovered = None
    per_col = (len(FACTIONS) + 1) // 2
    row_h = min(64, (684 - top) // per_col)
    for n, f in enumerate(FACTIONS):
        x0, y = 40 + (n // per_col) * 604, top + (n % per_col) * row_h
        fc = glow.scale(FACTION_COLOR[f.key], .6)
        pygame.draw.rect(surf, fc, (x0, y + 4, 6, row_h - 10), border_radius=3)
        glow.draw_text(surf, f.name.upper(), 13, (120, 60, 20), (x0 + 12, y + row_h // 2 - 2), "midleft")
        for tier, ct in enumerate(f.members, 1):
            r = pygame.Rect(x0 + 104 + (tier - 1) * 166, y + 2, 160, row_h - 6)
            hov = r.collidepoint(mouse)
            if hov:
                hovered = (ct, r)
            pygame.draw.rect(surf, (240, 226, 192) if hov else (232, 218, 184), r, border_radius=9)
            pygame.draw.rect(surf, TIER_COLOR[tier] if tier > 1 else (150, 122, 84), r, 2, border_radius=9)
            card = _list_cards.setdefault(ct, MultiplierCard(ct))
            ch = r.h - 8
            surf.blit(pygame.transform.smoothscale(render_card(card, t), (int(ch * .72), ch)), (r.x + 5, r.y + 4))
            tx = r.x + 10 + int(ch * .72)
            glow.draw_text(surf, ct.value.upper(), 14, config.INK, (tx, r.y + 13), "midleft")
            glow.draw_text(surf, f"${element_price(ct)}", 12, glow.scale(TIER_COLOR[tier], .75), (r.right - 8, r.y + 13),
                           "midright")
            glow.draw_text(surf, CARD_DESC[ct], 12, (84, 66, 46), (tx, r.y + 33), "midleft", kind="ui")
    glow.draw_text(surf, "play 2 Elements of one faction in the same hand for its bonus - all 3 for the full bonus  "
                   "(hover an Element)", 13, (120, 96, 64), (640, 696), kind="ui")
    if hovered:
        ct, r = hovered
        draw_tooltip(surf, (r.centerx, r.y - 4) if r.y > 330 else (r.centerx, r.bottom + 240), ct)
