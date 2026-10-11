import math
import random

import pygame

import config
from core.cards import CARD_COLOR, CARD_TIER, CardType
from core.dice import Die
from effects import glow
from effects.tween import approach
from ui.layout import DIE_SIZE, HAND_CY as L_HAND_Y

NORMAL_COLOR = (226, 196, 150)          # ivory: every normal die looks the same, only the pips differ
PIPS = {
    0: [],                     # a face-down die (boss Nyxara)
    1: [(.5, .5)],
    2: [(.3, .3), (.7, .7)],
    3: [(.3, .3), (.5, .5), (.7, .7)],
    4: [(.3, .3), (.7, .3), (.3, .7), (.7, .7)],
    5: [(.3, .3), (.7, .3), (.5, .5), (.3, .7), (.7, .7)],
    6: [(.3, .27), (.7, .27), (.3, .5), (.7, .5), (.3, .73), (.7, .73)],
}


def die_color(die):
    return CARD_COLOR[die.kind] if die.kind else NORMAL_COLOR


def _crescent(n=24):
    """Unit-size crescent: the outer circle's arc outside a shifted inner circle, back along the inner arc."""
    (ox, oy, orr), (ix, iy, ir) = (0, 0, .95), (.42, -.25, .78)
    outside = lambda x, y: math.hypot(x - ix, y - iy) > ir
    inside = lambda x, y: math.hypot(x - ox, y - oy) <= orr
    outer = [(ox + math.cos(a) * orr, oy + math.sin(a) * orr) for a in (k * math.tau / n for k in range(n))]
    inner = [(ix + math.cos(a) * ir, iy + math.sin(a) * ir) for a in (k * math.tau / n for k in range(n))]
    o = [p for p in outer if outside(*p)]
    k0 = next(k for k in range(n) if outside(*outer[k]) and not outside(*outer[k - 1]))
    o = [outer[(k0 + k) % n] for k in range(n) if outside(*outer[(k0 + k) % n])]
    i = [p for p in inner if inside(*p)]
    i.sort(key=lambda p: math.atan2(p[1] - iy, p[0] - ix))
    a_end = math.atan2(o[-1][1] - iy, o[-1][0] - ix)
    i.sort(key=lambda p: (math.atan2(p[1] - iy, p[0] - ix) - a_end) % math.tau)
    return o + i


_CRESCENT = _crescent()


def draw_kind_icon(surf, kind, c, r, color):
    """One small polygon icon per special-die kind."""
    cx, cy = c
    P = lambda pts: [(cx + x * r, cy + y * r) for x, y in pts]
    light = glow.mix(color, (255, 255, 255), .55)
    dark = glow.scale(color, .25)
    if kind is CardType.LIGHTNING:
        pygame.draw.polygon(surf, color, P([(.15, -1), (-.65, .12), (-.08, .12), (-.35, 1), (.65, -.22), (.05, -.22)]))
    elif kind is CardType.ICE:
        for k in range(3):
            a = k * math.pi / 3
            dx, dy = math.cos(a) * r, math.sin(a) * r
            pygame.draw.line(surf, color, (cx - dx, cy - dy), (cx + dx, cy + dy), max(2, int(r * .2)))
        for k in range(6):
            a = k * math.pi / 3
            bx, by = cx + math.cos(a) * r * .62, cy + math.sin(a) * r * .62
            for s in (-1, 1):
                a2 = a + s * 0.9
                pygame.draw.line(surf, color, (bx, by), (bx + math.cos(a2) * r * .32, by + math.sin(a2) * r * .32),
                                 max(1, int(r * .12)))
    elif kind is CardType.FIRE:
        pygame.draw.polygon(surf, color, P([(0, -1), (.5, -.25), (.62, .35), (.28, .92), (-.28, .92), (-.62, .35), (-.5, -.1), (-.2, .15)]))
        pygame.draw.polygon(surf, glow.mix(color, (255, 245, 170), .7), P([(0, -.1), (.28, .35), (.15, .75), (-.15, .75), (-.28, .35)]))
    elif kind is CardType.GRASS:
        for tx, ty in ((-.8, -.45), (-.35, -1.0), (.25, -.9), (.75, -.35)):
            bx = tx * .4
            pygame.draw.polygon(surf, color, P([(bx - .22, .95), (bx + .22, .95), (tx, ty)]))
        pygame.draw.line(surf, light, (cx - r * .9, cy + r * .95), (cx + r * .9, cy + r * .95), max(2, int(r * .15)))
    elif kind is CardType.WIZARD:
        pygame.draw.polygon(surf, color, P([(.05, -1), (-.6, .62), (.6, .62)]))
        pygame.draw.polygon(surf, color, P([(-.95, .62), (.95, .62), (.95, .9), (-.95, .9)]))
        pygame.draw.circle(surf, light, (int(cx + r * .05), int(cy - r * .05)), max(2, int(r * .18)))
    elif kind is CardType.GLASS:
        pygame.draw.polygon(surf, color, P([(0, -1), (.8, -.3), (.5, .95), (-.5, .95), (-.8, -.3)]))
        pygame.draw.polygon(surf, light, P([(0, -1), (.8, -.3), (0, -.25)]))
        pygame.draw.line(surf, dark, (cx, cy - r * .25), (cx + r * .3, cy + r * .95), max(1, int(r * .1)))
    elif kind is CardType.DEVIL:
        pygame.draw.circle(surf, color, (int(cx), int(cy + r * .22)), int(r * .66))
        pygame.draw.polygon(surf, color, P([(-.72, -.15), (-.55, -1), (-.12, -.42)]))
        pygame.draw.polygon(surf, color, P([(.72, -.15), (.55, -1), (.12, -.42)]))
        pygame.draw.circle(surf, dark, (int(cx - r * .25), int(cy + r * .12)), max(1, int(r * .1)))
        pygame.draw.circle(surf, dark, (int(cx + r * .25), int(cy + r * .12)), max(1, int(r * .1)))
    elif kind is CardType.MIDAS:
        pygame.draw.circle(surf, color, (int(cx), int(cy)), max(2, int(r * .95)))
        pygame.draw.circle(surf, dark, (int(cx), int(cy)), max(1, int(r * .68)), max(1, int(r * .16)))
        pygame.draw.rect(surf, dark, (int(cx) - max(1, int(r * .08)), int(cy - r * .5), max(1, int(r * .16)), int(r)))
        pygame.draw.rect(surf, dark, (int(cx - r * .3), int(cy - r * .3), int(r * .6), max(1, int(r * .14))))
        pygame.draw.rect(surf, dark, (int(cx - r * .3), int(cy + r * .16), int(r * .6), max(1, int(r * .14))))
    elif kind is CardType.HOURGLASS:
        pygame.draw.polygon(surf, color, P([(-.7, -.95), (.7, -.95), (0, 0)]))
        pygame.draw.polygon(surf, color, P([(0, 0), (-.7, .95), (.7, .95)]))
        pygame.draw.polygon(surf, light, P([(-.25, .95), (.25, .95), (0, .5)]))
        pygame.draw.line(surf, light, (cx - r * .85, cy - r), (cx + r * .85, cy - r), max(2, int(r * .14)))
        pygame.draw.line(surf, light, (cx - r * .85, cy + r), (cx + r * .85, cy + r), max(2, int(r * .14)))
    elif kind is CardType.WIND:                          # three swirling gust lines
        w = max(2, int(r * .18))
        for k, (y, l) in enumerate(((-.55, 1.5), (0, 1.8), (.55, 1.2))):
            x0 = cx - r * .9
            pygame.draw.line(surf, color, (x0, cy + y * r), (x0 + l * r * .9, cy + y * r), w)
            pygame.draw.circle(surf, color, (int(x0 + l * r * .9), int(cy + (y - .18) * r)), max(2, int(r * .22)), w // 2 + 1)
    elif kind is CardType.WATER:                         # a drop
        pygame.draw.polygon(surf, color, P([(0, -1), (.45, -.2), (.62, .3), (.45, .8), (0, .98), (-.45, .8), (-.62, .3), (-.45, -.2)]))
        pygame.draw.circle(surf, light, (int(cx - r * .22), int(cy + r * .3)), max(1, int(r * .16)))
    elif kind is CardType.STONE:                         # a rough boulder
        pygame.draw.polygon(surf, color, P([(-.9, .8), (-.75, -.2), (-.3, -.75), (.35, -.85), (.85, -.25), (.95, .8)]))
        pygame.draw.line(surf, dark, (cx - r * .3, cy - r * .3), (cx + r * .1, cy + r * .4), max(1, int(r * .12)))
    elif kind is CardType.METAL:                         # an ingot
        pygame.draw.polygon(surf, color, P([(-.95, .7), (-.6, -.35), (.6, -.35), (.95, .7)]))
        pygame.draw.polygon(surf, light, P([(-.6, -.35), (.6, -.35), (.45, -.05), (-.45, -.05)]))
    elif kind is CardType.MOON:                          # a crescent
        pygame.draw.polygon(surf, color, P(_CRESCENT))
    elif kind is CardType.STORM:                         # a cloud with a bolt
        for x, y, rr in ((-.45, -.1, .45), (.1, -.35, .55), (.55, -.05, .4)):
            pygame.draw.circle(surf, color, (int(cx + x * r), int(cy + y * r)), max(2, int(rr * r)))
        pygame.draw.rect(surf, color, (int(cx - r * .85), int(cy - r * .1), int(r * 1.7), int(r * .4)))
        pygame.draw.polygon(surf, light, P([(.1, .2), (-.3, .7), (0, .7), (-.2, 1.05), (.35, .5), (.05, .5)]))
    elif kind is CardType.SUN:                           # disc with rays
        for k in range(8):
            a = k * math.pi / 4
            pygame.draw.line(surf, color, (cx + math.cos(a) * r * .55, cy + math.sin(a) * r * .55),
                             (cx + math.cos(a) * r, cy + math.sin(a) * r), max(2, int(r * .18)))
        pygame.draw.circle(surf, color, (int(cx), int(cy)), max(2, int(r * .5)))
    elif kind is CardType.CRYSTAL:                       # a faceted gem
        pygame.draw.polygon(surf, color, P([(0, -1), (.7, -.35), (.45, .95), (-.45, .95), (-.7, -.35)]))
        pygame.draw.polygon(surf, light, P([(0, -1), (.7, -.35), (0, -.1), (-.7, -.35)]))
        pygame.draw.line(surf, dark, (cx, cy - r * .1), (cx, cy + r * .95), max(1, int(r * .1)))
    elif kind is CardType.STAR:                          # five-point star
        pts = [(math.sin(i * math.pi / 5) * (1 if i % 2 == 0 else .45), -math.cos(i * math.pi / 5) * (1 if i % 2 == 0 else .45))
               for i in range(10)]
        pygame.draw.polygon(surf, color, P(pts))
    elif kind is CardType.THORN:                         # a thorny stem
        w = max(2, int(r * .2))
        pygame.draw.line(surf, color, (cx - r * .2, cy + r), (cx + r * .2, cy - r), w)
        for y, sgn in ((-.5, 1), (0, -1), (.5, 1)):
            x = cx + (-y) * r * .2
            pygame.draw.polygon(surf, color, [(x, cy + y * r - r * .15), (x, cy + y * r + r * .15), (x + sgn * r * .6, cy + y * r - r * .2)])
    elif kind is CardType.TSUNAMI:                       # a curling wave
        pygame.draw.polygon(surf, color, P([(-1, .9), (-1, .2), (-.6, -.5), (0, -.95), (.6, -.8), (.95, -.3), (.5, -.35),
                                            (.2, -.1), (.35, .35), (1, .5), (1, .9)]))
        pygame.draw.line(surf, light, (cx - r * .6, cy - r * .3), (cx, cy - r * .75), max(1, int(r * .14)))
    elif kind is CardType.QUAKE:                         # cracked ground
        pygame.draw.polygon(surf, color, P([(-1, .1), (1, .1), (1, .95), (-1, .95)]))
        pygame.draw.lines(surf, dark, False, P([(-.1, .1), (.15, .4), (-.1, .65), (.1, .95)]), max(1, int(r * .14)))
        for x in (-.7, 0, .7):
            pygame.draw.line(surf, color, (cx + x * r, cy - r * .2), (cx + x * r, cy - r * .9), max(1, int(r * .14)))
    elif kind is CardType.GAIA:                          # a tree
        pygame.draw.rect(surf, color, (int(cx - r * .14), int(cy + r * .1), max(2, int(r * .28)), int(r * .9)))
        for x, y, rr in ((0, -.45, .55), (-.45, -.05, .4), (.45, -.05, .4)):
            pygame.draw.circle(surf, color, (int(cx + x * r), int(cy + y * r)), max(2, int(rr * r)))
        pygame.draw.circle(surf, light, (int(cx - r * .15), int(cy - r * .6)), max(1, int(r * .14)))
    elif kind is CardType.ECLIPSE:                       # a dark disc with a bright ring
        pygame.draw.circle(surf, light, (int(cx), int(cy)), max(3, int(r * .95)))
        pygame.draw.circle(surf, color, (int(cx), int(cy)), max(2, int(r * .72)))
        pygame.draw.circle(surf, dark, (int(cx + r * .2), int(cy - r * .1)), max(2, int(r * .55)))
    elif kind is CardType.GHOST:                         # a sheet ghost
        pygame.draw.circle(surf, color, (int(cx), int(cy - r * .2)), max(2, int(r * .7)))
        pygame.draw.polygon(surf, color, P([(-.7, -.2), (.7, -.2), (.7, .95), (.35, .7), (0, .95), (-.35, .7), (-.7, .95)]))
        for x in (-.25, .25):
            pygame.draw.circle(surf, dark, (int(cx + x * r), int(cy - r * .25)), max(1, int(r * .13)))
    elif kind is CardType.ECHO:                          # a source and its echoes
        pygame.draw.circle(surf, color, (int(cx - r * .55), int(cy)), max(2, int(r * .28)))
        for k, rr in enumerate((.6, 1.0)):
            pygame.draw.arc(surf, color, (cx - r * .55 - rr * r, cy - rr * r, rr * r * 2, rr * r * 2), -1.0, 1.0,
                            max(1, int(r * .16)))
    elif kind is CardType.VOID:                          # a black hole with a swirling rim
        pygame.draw.circle(surf, light, (int(cx), int(cy)), max(3, int(r * .95)), max(1, int(r * .18)))
        pygame.draw.circle(surf, (10, 6, 20), (int(cx), int(cy)), max(2, int(r * .62)))
        pygame.draw.arc(surf, light, (cx - r * .8, cy - r * .8, r * 1.6, r * 1.6), 0.4, 2.6, max(1, int(r * .12)))
    elif kind is CardType.GEAR:                          # a cog
        w = max(2, int(r * .3))
        for k in range(8):
            a = k * math.pi / 4
            pygame.draw.line(surf, color, (cx, cy), (cx + math.cos(a) * r, cy + math.sin(a) * r), w)
        pygame.draw.circle(surf, color, (int(cx), int(cy)), max(2, int(r * .72)))
        pygame.draw.circle(surf, dark, (int(cx), int(cy)), max(1, int(r * .28)))
    elif kind is CardType.PISTON:                        # a cylinder with a rod
        pygame.draw.rect(surf, color, (int(cx - r * .7), int(cy - r), max(2, int(r * 1.4)), max(2, int(r * .9))))
        pygame.draw.rect(surf, color, (int(cx - r * .15), int(cy - r * .1), max(2, int(r * .3)), max(2, int(r * .8))))
        pygame.draw.rect(surf, light, (int(cx - r * .55), int(cy + r * .65), max(2, int(r * 1.1)), max(1, int(r * .3))))
    elif kind is CardType.CHRONO:                        # a clock face
        pygame.draw.circle(surf, color, (int(cx), int(cy)), max(3, int(r * .95)), max(1, int(r * .2)))
        pygame.draw.line(surf, color, (cx, cy), (cx, cy - r * .62), max(1, int(r * .18)))
        pygame.draw.line(surf, color, (cx, cy), (cx + r * .45, cy + r * .2), max(1, int(r * .18)))
    elif kind is CardType.DOUBLOON:                      # a coin with a skull-ish dot face
        pygame.draw.circle(surf, color, (int(cx), int(cy)), max(2, int(r * .95)))
        pygame.draw.circle(surf, dark, (int(cx), int(cy)), max(1, int(r * .7)), max(1, int(r * .12)))
        for x in (-.25, .25):
            pygame.draw.circle(surf, dark, (int(cx + x * r), int(cy - r * .1)), max(1, int(r * .14)))
    elif kind is CardType.CUTLASS:                       # a curved blade
        pygame.draw.polygon(surf, color, P([(-.85, .85), (-.6, .95), (.55, -.4), (.8, -1), (.25, -.6)]))
        pygame.draw.line(surf, light, (cx - r * .95, cy + r * .45), (cx - r * .35, cy + r * .95), max(2, int(r * .2)))
    elif kind is CardType.KRAKEN:                        # a head with curling tentacles
        pygame.draw.circle(surf, color, (int(cx), int(cy - r * .35)), max(2, int(r * .6)))
        for x in (-.75, -.25, .25, .75):
            pygame.draw.line(surf, color, (cx + x * r * .6, cy), (cx + x * r, cy + r * .95), max(1, int(r * .2)))
        for x in (-.2, .2):
            pygame.draw.circle(surf, dark, (int(cx + x * r), int(cy - r * .4)), max(1, int(r * .12)))
    elif kind is CardType.MIRROR:                        # a hand mirror
        pygame.draw.ellipse(surf, color, (cx - r * .6, cy - r, r * 1.2, r * 1.3))
        pygame.draw.ellipse(surf, light, (cx - r * .38, cy - r * .78, r * .76, r * .86))
        pygame.draw.line(surf, color, (cx, cy + r * .3), (cx, cy + r), max(2, int(r * .25)))
    elif kind is CardType.PRISM:                         # a triangle splitting a beam
        pygame.draw.polygon(surf, color, P([(0, -.95), (.85, .75), (-.85, .75)]))
        pygame.draw.polygon(surf, light, P([(0, -.45), (.35, .4), (-.35, .4)]))
        for k, c in enumerate(((255, 90, 90), (255, 230, 90), (90, 200, 255))):
            pygame.draw.line(surf, c, (cx + r * .5, cy + r * .1), (cx + r, cy + r * (-.2 + k * .25)), max(1, int(r * .12)))
    elif kind is CardType.TAIJI:                         # yin-yang
        pygame.draw.circle(surf, (245, 245, 250), (int(cx), int(cy)), max(3, int(r * .95)))
        pygame.draw.polygon(surf, (30, 30, 40), [(cx + math.cos(a) * r * .95, cy + math.sin(a) * r * .95)
                                                  for a in (math.pi / 2 + k * math.pi / 16 for k in range(17))])
        pygame.draw.circle(surf, (30, 30, 40), (int(cx), int(cy - r * .47)), max(1, int(r * .48)))
        pygame.draw.circle(surf, (245, 245, 250), (int(cx), int(cy + r * .47)), max(1, int(r * .48)))
        pygame.draw.circle(surf, (245, 245, 250), (int(cx), int(cy - r * .47)), max(1, int(r * .14)))
        pygame.draw.circle(surf, (30, 30, 40), (int(cx), int(cy + r * .47)), max(1, int(r * .14)))
    elif kind is CardType.WOLF:                          # a wolf head with pointed ears
        pygame.draw.polygon(surf, color, P([(-.8, -.95), (-.3, -.45), (.3, -.45), (.8, -.95), (.75, .1), (0, .95), (-.75, .1)]))
        for x in (-.3, .3):
            pygame.draw.circle(surf, dark, (int(cx + x * r), int(cy - r * .05)), max(1, int(r * .13)))
    elif kind is CardType.HAWK:                          # spread wings
        pygame.draw.polygon(surf, color, P([(-1, -.5), (-.2, .05), (0, -.2), (.2, .05), (1, -.5), (.35, .5), (0, .95), (-.35, .5)]))
        pygame.draw.circle(surf, light, (int(cx), int(cy - r * .3)), max(1, int(r * .2)))
    elif kind is CardType.DRAGON:                        # a horned head breathing flame
        pygame.draw.polygon(surf, color, P([(-.9, -.2), (-.4, -.95), (-.25, -.45), (.45, -.45), (.95, .05), (.4, .25), (-.2, .95), (-.9, .4)]))
        pygame.draw.circle(surf, (255, 230, 90), (int(cx - r * .1), int(cy - r * .15)), max(1, int(r * .14)))
        pygame.draw.polygon(surf, (255, 200, 60), P([(.95, .05), (1, .55), (.55, .3)]))
    elif kind is CardType.COMET:                         # a head with a tail
        pygame.draw.polygon(surf, light, P([(.35, -.35), (-1, .55), (-.6, .9), (.55, .1)]))
        pygame.draw.circle(surf, color, (int(cx + r * .45), int(cy - r * .2)), max(2, int(r * .5)))
    elif kind is CardType.AURORA:                        # rippling curtains of light
        for k, y in enumerate((-.6, -.05, .5)):
            pts = [(cx + (x / 6 - .5) * r * 1.9, cy + y * r + math.sin(x * 1.3 + k) * r * .22) for x in range(7)]
            pygame.draw.lines(surf, color if k != 1 else light, False, pts, max(1, int(r * .22)))
    elif kind is CardType.GALAXY:                        # a spiral
        pts = [(cx + math.cos(a) * r * a / 9.5, cy + math.sin(a) * r * a / 9.5 * .8) for a in (k * .35 for k in range(28))]
        pygame.draw.lines(surf, color, False, pts, max(1, int(r * .2)))
        pygame.draw.circle(surf, light, (int(cx), int(cy)), max(1, int(r * .2)))
    elif kind is CardType.SULFUR:                        # the alchemical triangle-over-cross
        pygame.draw.polygon(surf, color, P([(0, -1), (.6, .05), (-.6, .05)]), max(1, int(r * .2)))
        pygame.draw.line(surf, color, (cx, cy + r * .05), (cx, cy + r), max(1, int(r * .2)))
        pygame.draw.line(surf, color, (cx - r * .45, cy + r * .55), (cx + r * .45, cy + r * .55), max(1, int(r * .2)))
    elif kind is CardType.MERCURY:                       # a flask with liquid metal
        pygame.draw.rect(surf, color, (int(cx - r * .2), int(cy - r), max(2, int(r * .4)), max(2, int(r * .6))))
        pygame.draw.circle(surf, color, (int(cx), int(cy + r * .3)), max(2, int(r * .68)))
        pygame.draw.circle(surf, light, (int(cx), int(cy + r * .42)), max(1, int(r * .42)))
    elif kind is CardType.PHOENIX:                       # a firebird with raised wings
        pygame.draw.polygon(surf, color, P([(-1, -.8), (-.25, -.05), (0, -.6), (.25, -.05), (1, -.8), (.55, .25), (.25, .3),
                                            (.4, .95), (0, .55), (-.4, .95), (-.25, .3), (-.55, .25)]))
        pygame.draw.circle(surf, (255, 240, 150), (int(cx), int(cy - r * .2)), max(1, int(r * .18)))
    elif kind is CardType.KNIGHT:                        # a chess knight
        pygame.draw.polygon(surf, color, P([(-.6, .95), (.65, .95), (.5, .55), (.45, -.1), (.2, -.75), (-.1, -1), (-.25, -.7),
                                            (-.75, -.35), (-.7, -.05), (-.2, -.15), (-.45, .55)]))
        pygame.draw.circle(surf, dark, (int(cx - r * .05), int(cy - r * .55)), max(1, int(r * .12)))
    elif kind is CardType.QUEEN:                         # a tall crown with pearls
        pygame.draw.polygon(surf, color, P([(-.8, .8), (-.95, -.55), (-.45, .05), (0, -.85), (.45, .05), (.95, -.55), (.8, .8)]))
        for x, y in ((-.95, -.55), (0, -.85), (.95, -.55)):
            pygame.draw.circle(surf, light, (int(cx + x * r), int(cy + y * r)), max(1, int(r * .17)))
        pygame.draw.rect(surf, light, (int(cx - r * .8), int(cy + r * .55), max(2, int(r * 1.6)), max(1, int(r * .2))))
    elif kind is CardType.KING:                          # a crown topped by a cross
        pygame.draw.polygon(surf, color, P([(-.9, .9), (-.9, -.2), (-.45, .15), (0, -.35), (.45, .15), (.9, -.2), (.9, .9)]))
        pygame.draw.line(surf, color, (cx, cy - r * .35), (cx, cy - r), max(1, int(r * .2)))
        pygame.draw.line(surf, color, (cx - r * .25, cy - r * .72), (cx + r * .25, cy - r * .72), max(1, int(r * .2)))
        pygame.draw.circle(surf, dark, (int(cx), int(cy + r * .5)), max(1, int(r * .17)))
    else:  # JESTER
        pygame.draw.polygon(surf, color, P([(-.9, .6), (-.9, -.6), (-.45, -.1), (0, -1), (.45, -.1), (.9, -.6), (.9, .6)]))
        for x, y in ((-.9, -.6), (0, -1), (.9, -.6)):
            pygame.draw.circle(surf, light, (int(cx + x * r), int(cy + y * r)), max(2, int(r * .16)))


_art = {}


def die_art(die, size=DIE_SIZE):
    key = (die, size)
    if key not in _art:
        _art[key] = _make_die(die.value, die_color(die), size, die.kind)
    return _art[key]


def _nrect(s, color, x, y, w, h, c):
    """Filled rectangle with the corners notched by c pixels (low-res canvas)."""
    pygame.draw.rect(s, color, (x + c, y, w - 2 * c, h))
    pygame.draw.rect(s, color, (x, y + c, w, h - 2 * c))


def _draw_motif(s, kind, L, col):
    """A small decoration unique to every Element, kept to the die's border band so the pips stay readable."""
    K = CardType
    lt = glow.mix(col, (255, 255, 255), .5)
    dk = glow.scale(col, .55)
    px = lambda c, x, y, w=2, h=2: pygame.draw.rect(s, c, (x, y, w, h))
    lo, hi = 4, L - 6                                      # inner edges of the body
    if kind is K.FIRE:                                     # flame tongues along the bottom
        for x in range(6, L - 8, 6):
            pygame.draw.polygon(s, (255, 220, 90), [(x, hi + 2), (x + 3, hi - 5), (x + 6, hi + 2)])
    elif kind is K.WATER:                                  # a wave along the bottom
        for x in range(4, L - 4, 2):
            px(lt, x, hi - 1 + round(math.sin(x * .5) * 1.5))
    elif kind is K.WIND:                                   # streaks across the top
        for y, x0, w in ((lo + 1, 18, 22), (lo + 4, 24, 16)):
            pygame.draw.line(s, lt, (x0, y), (x0 + w, y), 1)
    elif kind is K.STONE:                                  # speckles
        for x, y in ((40, 6), (44, 14), (6, 40), (14, 45), (42, 44), (24, 5), (5, 24)):
            px(dk, x, y)
    elif kind is K.GRASS:                                  # tufts on the bottom edge
        for x in range(6, L - 6, 5):
            pygame.draw.line(s, (40, 120, 40), (x, hi + 2), (x + 2, hi - 4), 1)
    elif kind is K.MIDAS:                                  # gold rim
        pygame.draw.rect(s, (255, 236, 140), (3, 3, L - 6, L - 6), 1)
        px((255, 255, 220), L - 10, 5, 3, 1)
    elif kind is K.JESTER:                                 # harlequin diamonds in the corners
        for cx, cy in ((L - 9, 8), (8, L - 9), (L - 9, L - 9)):
            pygame.draw.polygon(s, lt, [(cx, cy - 4), (cx + 3, cy), (cx, cy + 4), (cx - 3, cy)])
    elif kind is K.STAR:                                   # tiny twinkles
        for x, y in ((40, 8), (46, 20), (8, 44), (30, 46), (44, 42)):
            pygame.draw.line(s, (255, 255, 220), (x - 2, y), (x + 2, y), 1)
            pygame.draw.line(s, (255, 255, 220), (x, y - 2), (x, y + 2), 1)
    elif kind is K.DEVIL:                                  # little horns on the top edge
        for x in (16, L - 20):
            pygame.draw.polygon(s, (90, 10, 20), [(x, lo + 2), (x + 2, lo - 4), (x + 5, lo + 2)])
    elif kind is K.ICE:                                    # frost in the corners
        for cx, cy, sx, sy in ((L - 5, 4, -1, 1), (4, L - 5, 1, -1), (L - 5, L - 5, -1, -1)):
            for k in range(3):
                pygame.draw.line(s, (235, 250, 255), (cx, cy), (cx + sx * (8 - k * 2), cy + sy * (k * 3)), 1)
    elif kind is K.GLASS:                                  # shine streaks
        for o in (0, 6):
            pygame.draw.line(s, (255, 255, 255), (L - 18 + o, 4), (L - 4, 18 - o), 1)
    elif kind is K.METAL:                                  # rivets
        for x, y in ((L - 8, 6), (6, L - 8), (L - 8, L - 8)):
            pygame.draw.circle(s, dk, (x, y), 2)
            px(lt, x - 1, y - 1, 1, 1)
    elif kind is K.THORN:                                  # thorns along the right edge
        for y in range(8, L - 8, 7):
            pygame.draw.polygon(s, (30, 70, 34), [(L - 4, y), (L - 9, y + 2), (L - 4, y + 4)])
    elif kind is K.HOURGLASS:                              # falling sand
        for x, y in ((L - 10, 8), (L - 10, 12), (L - 10, 16), (L - 12, 44), (L - 9, 44), (L - 6, 44)):
            px((240, 220, 150), x, y, 1, 2)
    elif kind is K.WIZARD:                                 # sparkles
        for x, y in ((42, 7), (7, 42), (44, 44), (26, 46)):
            px((255, 250, 180), x, y, 1, 1)
            px((255, 250, 180, 120), x - 1, y, 3, 1)
    elif kind is K.MOON:                                   # stars of the night sky
        for x, y in ((40, 7), (46, 14), (10, 44), (44, 45)):
            px((240, 240, 255), x, y, 1, 1)
    elif kind is K.SUN:                                    # rays from the corner
        for a in range(0, 90, 15):
            r = math.radians(a)
            pygame.draw.line(s, (255, 230, 120), (L - 4, L - 4), (L - 4 - math.cos(r) * 10, L - 4 - math.sin(r) * 10), 1)
    elif kind is K.TSUNAMI:                                # a curling crest on the bottom
        pygame.draw.arc(s, (190, 220, 255), (L - 22, hi - 8, 16, 14), 0, math.pi, 2)
        pygame.draw.line(s, (190, 220, 255), (4, hi + 1), (L - 22, hi + 1), 1)
    elif kind is K.LIGHTNING:                              # a zigzag
        pygame.draw.lines(s, (255, 250, 170), False, [(L - 8, 4), (L - 13, 12), (L - 8, 12), (L - 13, 20)], 1)
    elif kind is K.QUAKE:                                  # cracks
        pygame.draw.lines(s, dk, False, [(L - 4, 20), (L - 9, 26), (L - 6, 31), (L - 11, 38)], 1)
        pygame.draw.lines(s, dk, False, [(16, L - 4), (20, L - 9), (25, L - 7)], 1)
    elif kind is K.GAIA:                                   # leaves in the corners
        for cx, cy in ((L - 9, 8), (8, L - 9), (L - 9, L - 9)):
            pygame.draw.ellipse(s, (40, 120, 60), (cx - 4, cy - 2, 8, 4))
            px((150, 230, 150), cx - 1, cy - 1, 2, 1)
    elif kind is K.CRYSTAL:                                # facet lines
        for o in (0, 8, 16):
            pygame.draw.line(s, lt, (L - 4 - o, 4), (L - 4, 4 + o), 1)
    elif kind is K.STORM:                                  # rain
        for x in range(8, L - 6, 6):
            pygame.draw.line(s, (190, 200, 240), (x, hi - 3), (x - 2, hi + 1), 1)
    elif kind is K.GHOST:                                  # wisps drifting up the sides
        for x, y in ((L - 7, 30), (L - 9, 22), (L - 7, 14)):
            pygame.draw.circle(s, (240, 250, 255), (x, y), 2, 1)
    elif kind is K.ECHO:                                   # an echoing outline
        pygame.draw.rect(s, lt, (5, 5, L - 10, L - 10), 1)
        pygame.draw.rect(s, glow.mix(col, (255, 255, 255), .25), (8, 8, L - 16, L - 16), 1)
    elif kind is K.VOID:                                   # a swirl in the corner
        pygame.draw.arc(s, (170, 140, 230), (L - 20, L - 20, 16, 16), 0, 4.5, 1)
        pygame.draw.arc(s, (120, 90, 180), (L - 16, L - 16, 8, 8), 1, 5.5, 1)
    elif kind is K.ECLIPSE:                                # a glowing corona ring
        pygame.draw.rect(s, (200, 170, 255), (3, 3, L - 6, L - 6), 1)
        pygame.draw.rect(s, dk, (5, 5, L - 10, L - 10), 1)
    elif kind is K.GEAR:                                   # teeth along the bottom
        for x in range(6, L - 6, 5):
            px(dk, x, hi, 3, 2)
    elif kind is K.PISTON:                                 # a pressure gauge in the corner
        pygame.draw.circle(s, lt, (L - 10, L - 10), 4, 1)
        pygame.draw.line(s, (255, 90, 80), (L - 10, L - 10), (L - 7, L - 12), 1)
    elif kind is K.CHRONO:                                 # hour ticks around the border
        for k in range(12):
            a = k * math.tau / 12
            px(lt, int(L / 2 + math.cos(a) * (L / 2 - 6)), int(L / 2 + math.sin(a) * (L / 2 - 6)), 1, 1)
    elif kind is K.DOUBLOON:                               # a stack of coins
        for k in range(3):
            pygame.draw.ellipse(s, (255, 236, 140), (L - 14, L - 9 - k * 3, 9, 4))
    elif kind is K.CUTLASS:                                # a slash across the corner
        pygame.draw.line(s, (255, 255, 255), (L - 20, 4), (L - 4, 20), 1)
        pygame.draw.line(s, lt, (L - 18, 4), (L - 4, 18), 1)
    elif kind is K.KRAKEN:                                 # a tentacle along the bottom
        pts = [(4 + x, hi - 1 + round(math.sin(x * .4) * 2)) for x in range(0, L - 10, 2)]
        pygame.draw.lines(s, dk, False, pts, 2)
    elif kind is K.MIRROR:                                 # a mirrored reflection line
        pygame.draw.line(s, (255, 255, 255), (4, L // 2), (8, L // 2), 1)
        pygame.draw.line(s, (255, 255, 255), (L - 8, L // 2), (L - 4, L // 2), 1)
    elif kind is K.PRISM:                                  # a rainbow edge
        for k, c in enumerate(((255, 90, 90), (255, 200, 80), (120, 230, 120), (90, 170, 255))):
            pygame.draw.line(s, c, (5, hi - 1 + k), (L - 6, hi - 1 + k), 1)
    elif kind is K.TAIJI:                                  # half-light, half-dark border
        pygame.draw.line(s, (240, 240, 250), (4, 3), (L - 5, 3), 1)
        pygame.draw.line(s, (20, 20, 30), (4, L - 4), (L - 5, L - 4), 1)
    elif kind is K.WOLF:                                   # claw marks
        for o in (0, 4, 8):
            pygame.draw.line(s, dk, (L - 16 + o, 5), (L - 20 + o, 15), 1)
    elif kind is K.HAWK:                                   # feathers on the sides
        for y in (14, 22, 30):
            pygame.draw.line(s, lt, (L - 5, y), (L - 11, y + 4), 1)
    elif kind is K.DRAGON:                                 # scales
        for x, y in ((40, 8), (44, 14), (40, 20), (8, 40), (14, 44), (40, 44)):
            pygame.draw.arc(s, (255, 170, 80), (x - 2, y - 2, 5, 5), math.pi, math.tau, 1)
    elif kind is K.COMET:                                  # a streak across the top
        pygame.draw.line(s, (220, 240, 255), (12, 4), (L - 6, 9), 1)
        px((255, 255, 255), L - 7, 8, 2, 2)
    elif kind is K.AURORA:                                 # green-violet bands on top
        for k, c in enumerate(((120, 255, 180), (170, 130, 255))):
            pts = [(4 + x, 4 + k * 3 + round(math.sin(x * .3 + k) * 1)) for x in range(0, L - 8, 2)]
            pygame.draw.lines(s, c, False, pts, 1)
    elif kind is K.GALAXY:                                 # scattered star dust
        for x, y in ((40, 6), (46, 12), (6, 44), (12, 40), (44, 44), (24, 46), (46, 30)):
            px((230, 220, 255), x, y, 1, 1)
    elif kind is K.SULFUR:                                 # bubbling yellow fumes
        for x, y in ((L - 8, 30), (L - 10, 22), (L - 7, 14)):
            pygame.draw.circle(s, (250, 245, 150), (x, y), 2, 1)
    elif kind is K.MERCURY:                                # a liquid-metal drip
        pygame.draw.line(s, (240, 245, 255), (L - 8, 4), (L - 8, 12), 2)
        pygame.draw.circle(s, (240, 245, 255), (L - 8, 14), 2)
    elif kind is K.KNIGHT:                                 # a checkerboard strip
        for x in range(4, L - 6, 4):
            px((240, 240, 250) if (x // 4) % 2 else (40, 40, 60), x, hi, 4, 2)
    elif kind is K.QUEEN:                                  # pearls along the top
        for x in range(10, L - 8, 6):
            pygame.draw.circle(s, (255, 240, 250), (x, 5), 1)
    elif kind is K.KING:                                   # an ermine-trimmed royal border
        pygame.draw.rect(s, (255, 240, 200), (3, 3, L - 6, L - 6), 1)
        for x, y in ((8, 3), (L - 10, 3), (8, L - 4), (L - 10, L - 4)):
            px((40, 30, 40), x, y, 1, 1)
    elif kind is K.PHOENIX:                                # embers rising
        for x, y in ((40, 40), (44, 32), (8, 42), (12, 34), (42, 24)):
            px((255, 200, 80), x, y, 1, 2)


def _make_die(value, col, S, kind=None):
    """Pixel-art die drawn on a (S/2)x(S/2) canvas and magnified x2 with nearest-neighbour."""
    L = S // 2
    s = pygame.Surface((L, L), pygame.SRCALPHA)
    edge = (30, 18, 44)
    if kind:
        top, mid, bot = glow.mix(col, (255, 255, 255), .30), col, glow.scale(col, .58)
    else:
        top, mid, bot = (255, 250, 236), (240, 228, 200), (196, 178, 146)
    _nrect(s, edge, 0, 0, L, L, 4)
    _nrect(s, mid, 2, 2, L - 4, L - 4, 3)
    pygame.draw.rect(s, top, (5, 2, L - 10, 2))                # light edges (top, left)
    pygame.draw.rect(s, top, (2, 5, 2, L - 10))
    pygame.draw.rect(s, bot, (5, L - 4, L - 10, 2))            # shade (bottom, right)
    pygame.draw.rect(s, bot, (L - 4, 5, 2, L - 10))
    pygame.draw.rect(s, glow.mix(top, (255, 255, 255), .6), (6, 4, 4, 2))
    if kind:
        _draw_motif(s, kind, L, col)
    pr = 4
    for px, py in PIPS[value]:
        c = (int(px * L), int(py * L))
        if kind:
            pygame.draw.circle(s, glow.scale(col, .35), (c[0], c[1] + 1), pr + 1)
            pygame.draw.circle(s, (255, 248, 230), c, pr)
        else:
            pygame.draw.circle(s, (34, 22, 40), c, pr)
            pygame.draw.rect(s, (130, 120, 140), (c[0] - 1, c[1] - 2, 2, 2))
    if kind:
        bc = (7, 7)                                       # element badge in the top-left corner (clear of the pips)
        pygame.draw.circle(s, edge, bc, 6)
        pygame.draw.circle(s, glow.scale(col, .55), bc, 5)
        draw_kind_icon(s, kind, (bc[0] + 1, bc[1] + 1), 4, glow.scale(col, .25))
        draw_kind_icon(s, kind, bc, 4, (255, 248, 230))
    return pygame.transform.scale(s, (S, S))


class DieSprite:
    """One on-screen die. Position is the die centre. mode: hand | played | out."""

    def __init__(self, die, pos, delay=0.0):
        self.die = die
        self.x, self.y = pos
        self.tx, self.ty = pos
        self.selected = False
        self.hover = 0.0
        self.angle = 0.0
        self.spin = 0.0
        self.scale = 1.0
        self.alpha = 255
        self.delay = delay
        self.mode = "hand"
        self.flash = 0.0
        self.seed = (die.value * 7 + id(self) // 16) % 17
        self.shake = 0.0
        self.rate = 13.0
        self.dim = False                         # played but not part of the combo: does not score
        self.roll = 0.6 if die.kind else 0.0     # special dice tumble through faces before landing
        self.hidden = False                      # face-down (boss Nyxara)
        self.level = 1                           # the Element's level (shown above the die)

    @property
    def color(self):
        return die_color(self.die)

    def hit_rect(self):
        return pygame.Rect(self.x - DIE_SIZE / 2, self.y - DIE_SIZE / 2, DIE_SIZE, DIE_SIZE)

    def update(self, dt):
        if self.delay > 0:
            self.delay -= dt
            return
        if self.mode == "out":
            self.x = approach(self.x, self.tx, 5, dt)
            self.y = approach(self.y, self.ty, 5, dt)
            self.angle += self.spin * dt
            self.scale = max(0.0, self.scale - dt * 1.7)
            self.alpha = max(0, self.alpha - 430 * dt)
        else:
            self.x = approach(self.x, self.tx, self.rate, dt)
            self.y = approach(self.y, self.ty, self.rate, dt)
            self.angle = approach(self.angle, 0.0, 9, dt)
            self.scale = approach(self.scale, 1.0, 9, dt)
        if self.roll > 0:
            self.roll -= dt
            self.angle = self.roll * 900
        self.flash = max(0.0, self.flash - dt * 2.4)
        self.shake = max(0.0, self.shake - dt * 3)

    def dead(self):
        return self.mode == "out" and self.alpha <= 0

    def _aura(self, surf, t, rect, col, tier):
        """Rare: pulsing ice-blue frame and orbiting diamonds.  Super: rainbow frame, orbiting stars, rising sparks."""
        cx, cy = rect.center
        ph = self.seed
        if tier == 2:
            ring = glow.mix((110, 180, 255), (255, 255, 255), 0.5 + 0.5 * math.sin(t * 5 + ph))
            pygame.draw.rect(surf, ring, rect.inflate(10 + int(3 * math.sin(t * 4 + ph)) * 2, 10 + int(3 * math.sin(t * 4 + ph)) * 2), 2, border_radius=14)
            n, rad, size = 3, 70, 4
        else:
            pygame.draw.rect(surf, glow.rainbow(t * 2 + ph * .1), rect.inflate(14, 14), 4, border_radius=16)
            pygame.draw.rect(surf, glow.rainbow(t * 2 + ph * .1 + .5), rect.inflate(6, 6), 2, border_radius=14)
            n, rad, size = 5, 74, 5
            for i in range(6):                                   # sparks drifting up off the top edge
                k = (t * 0.7 + i / 6 + ph * .07) % 1.0
                sx = rect.x + 8 + ((i * 41 + ph * 13) % (rect.w - 16))
                glow.draw_glow_circle(surf, (sx, rect.y + 6 - k * 44), 4 * (1 - k) + 2, glow.rainbow(t + i * .2), 1 - k)
        for i in range(n):
            a = t * (2.2 if tier == 2 else 3.0) + i * math.tau / n + ph
            px, py = cx + math.cos(a) * rad, cy + math.sin(a) * rad * .75 + 4
            s = size + 2 * math.sin(t * 9 + i)
            c = glow.mix((170, 210, 255), (255, 255, 255), .5) if tier == 2 else glow.hsv(i / n + t * .4, .45, 1.0)
            pygame.draw.polygon(surf, c, [(px, py - s * 1.5), (px + s * .55, py), (px, py + s * 1.5), (px - s * .55, py)])

    def draw(self, surf, t):
        if self.delay > 0:
            return
        die = self.die
        if self.roll > 0:                        # tumbling: flicker random faces of the same kind
            die = Die(int(t * 12 + self.seed) % 6 + 1, die.kind)
        if self.hidden:
            die = Die(0)
        art = die_art(die)
        bob = (int(math.sin(t * 2.2 + self.seed) * 2.0) // 2 * 2) if self.mode == "hand" else 0
        sc = self.scale
        cx = int(self.x + math.sin(t * 60) * 5 * self.shake) // 2 * 2
        cy = int(self.y + bob - 6 * self.hover) // 2 * 2
        col = self.color
        special = bool(self.die.kind)
        alpha = min(self.alpha, 105) if self.dim else self.alpha
        half = DIE_SIZE // 2
        rect = pygame.Rect(cx - half, cy - half, DIE_SIZE, DIE_SIZE)
        if alpha > 60:
            lift = max(0.0, (L_HAND_Y - cy)) if self.mode == "hand" else 0.0     # raised dice cast a smaller shadow
            glow.draw_ellipse_shadow(surf, cx, rect.bottom + 10 + int(lift * 0.4), DIE_SIZE * (0.9 - lift / 200), 14,
                                     int(110 * alpha / 255))
            if special and not self.dim and int(t * 3 + self.seed) % 2 == 0:
                pygame.draw.rect(surf, glow.mix(col, config.CREAM, 0.35), rect.inflate(8, 8), 2, border_radius=14)
            if special and not self.dim and self.mode != "out" and CARD_TIER[self.die.kind] >= 2:
                self._aura(surf, t, rect, col, CARD_TIER[self.die.kind])
            if self.selected:
                pygame.draw.rect(surf, config.GOLD, rect.inflate(10, 10), 4, border_radius=14)
            elif self.hover > 0.3:
                pygame.draw.rect(surf, config.CREAM, rect.inflate(8, 8), 2, border_radius=14)
        img = art
        if self.angle % 360 != 0 or abs(sc - 1) > 0.01:
            img = pygame.transform.rotozoom(art, int(self.angle / 15) * 15, sc)     # steps of 15 degrees: stop-motion spin
        if alpha < 255 or self.flash > 0:
            img = img.copy()
            if self.flash > 0:
                img.fill((int(170 * (self.flash > 0.4)),) * 3, special_flags=pygame.BLEND_RGB_ADD)
            img.set_alpha(int(alpha))
        surf.blit(img, img.get_rect(center=(cx, cy)))
        if self.hidden:
            glow.draw_text(surf, "?", 48, (90, 70, 110), (cx, cy))
        if special and self.mode != "out" and self.roll <= 0:
            name = self.die.kind.value.upper() + (f" LV{self.level}" if self.level > 1 else "")
            glow.draw_glow_text(surf, name, 14, glow.mix(col, config.CREAM, .45),
                                (cx, cy - half - 14), "center", 1.0)
