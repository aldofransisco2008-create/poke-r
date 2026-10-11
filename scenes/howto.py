"""HOW TO PLAY: a short illustrated tutorial. Shown automatically before the very first run, and from the title menu."""
import math

import pygame

import config
from core import save
from core.cards import CARD_COLOR, CardType as C
from core.dice import Die
from effects import glow
from scenes.base import Scene
from ui.dice_view import die_art, draw_kind_icon
from ui.widgets import GlowButton, draw_parchment

PAGES = (
    ("ROLL, PICK, PLAY",
     ["Every round has a TARGET score. Reach it before your PLAYS run out.",
      "Click dice (or keys 1-7) to pick them, then PLAY. Poker combos score:",
      "Pair, Two Pair, Three of a Kind, Straight, Full House, Four and Five of a Kind.",
      "Only the dice that form the combo score. DISCARD swaps dice you don't want."],
     "dice"),
    ("ELEMENTS",
     ["Elements are special dice that sit in your hand every round.",
      "Play them with your combo and they fire: Fire adds, Ice multiplies, Sun boosts the hand...",
      "Their order matters: Elements act left to right. Drag them in the shop to reorder.",
      "Hover any Element (or press I for INFO) to read exactly what it does."],
     "elements"),
    ("FACTIONS",
     ["Every Element belongs to a faction of three: one Common, one Rare and one Super.",
      "Play 2 members of a faction in the SAME hand for its bonus - all 3 for the full bonus.",
      "Factions are where the huge scores come from. The shop favours factions you already own.",
      "Buying an Element you own levels it up: all its numbers grow by 10%."],
     "faction"),
    ("THE SHOP",
     ["Clear a round to get paid: a reward, $3 per unused play, and interest on saved money.",
      "Skills level up a combo (+20% each). Vouchers are permanent upgrades.",
      "Every 2nd act ends with a BOSS that bends the rules - read its rule before you play.",
      "There are 50 rounds. Reaching the end is meant to be a real achievement. Good luck!"],
     "shop"),
)


class HowToScene(Scene):
    music = "lobby"

    def enter(self):
        self.t = 0.0
        self.page = 0
        self.back = GlowButton((360, 600, 200, 52), "< BACK", None, 20)
        self.next = GlowButton((720, 600, 200, 52), "NEXT >", None, 22, style="primary")
        self.skip = GlowButton((1090, 34, 140, 44), "SKIP", None, 18)

    def finish(self):
        rec = save.load_records()
        rec["tutorial_done"] = True
        save.save_records(rec)
        self.g.scenes.goto(self.kw.get("then", "title"))

    def turn(self, d):
        if 0 <= self.page + d < len(PAGES):
            self.page += d
            self.t = 0.0
            self.g.sfx.play("click")
        elif d > 0:
            self.finish()

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_RIGHT, pygame.K_RETURN, pygame.K_SPACE):
                self.turn(1)
            elif e.key == pygame.K_LEFT:
                self.turn(-1)
            elif e.key == pygame.K_ESCAPE:
                self.finish()
        if self.next.handle_event(e, self.g.sfx):
            self.turn(1)
        if self.back.handle_event(e, self.g.sfx):
            self.turn(-1)
        if self.skip.handle_event(e, self.g.sfx):
            self.finish()

    def update(self, dt):
        self.t += dt
        for b in (self.back, self.next, self.skip):
            b.update(dt)

    def draw(self, surf):
        t = self.t
        draw_parchment(surf, (60, 24, 1160, 672), 18, corners=True)
        title, lines, art = PAGES[self.page]
        glow.draw_text(surf, f"HOW TO PLAY  {self.page + 1}/{len(PAGES)}", 16, (120, 96, 64), (640, 64), kind="ui")
        glow.draw_text(surf, title, 46, config.INK, (640, 108))
        self.draw_art(surf, art, t)
        for i, ln in enumerate(lines):
            glow.draw_text(surf, ln, 17, (70, 52, 36), (640, 420 + i * 36), kind="ui")
        for i in range(len(PAGES)):                               # page dots
            pygame.draw.circle(surf, config.RED if i == self.page else (190, 168, 130), (640 + (i - 1.5) * 22, 576), 6)
        if self.page > 0:
            self.back.draw(surf, t)
        self.next.draw(surf, t, "LET'S PLAY!" if self.page == len(PAGES) - 1 else "NEXT >")
        self.skip.draw(surf, t)

    def draw_art(self, surf, art, t):
        cy = 270
        if art == "dice":                                         # a Full House lifting out of the hand
            for i, v in enumerate((5, 5, 5, 2, 2)):
                lift = 26 * max(0.0, math.sin(t * 3 - i * .4))
                img = die_art(Die(v), 96)
                surf.blit(img, img.get_rect(center=(400 + i * 120, cy - lift)))
            glow.draw_glow_text(surf, "FULL HOUSE  +200", 26, config.GOLD, (640, 370))
        elif art == "elements":                                   # three Element dice
            for i, k in enumerate((C.FIRE, C.ICE, C.SUN)):
                img = die_art(Die(4 + i % 2, k), 96)
                x = 460 + i * 180
                surf.blit(img, img.get_rect(center=(x, cy + math.sin(t * 2 + i) * 6)))
                glow.draw_glow_text(surf, k.value.upper(), 18, CARD_COLOR[k], (x, cy + 74))
        elif art == "faction":                                    # the Inferno trio, joined
            xs = (460, 640, 820)
            for i, k in enumerate((C.FIRE, C.DEVIL, C.SUN)):
                r = 46 + 4 * math.sin(t * 4 + i)
                pygame.draw.circle(surf, (40, 24, 30), (xs[i], cy), int(r) + 6)
                pygame.draw.circle(surf, CARD_COLOR[k], (xs[i], cy), int(r))
                draw_kind_icon(surf, k, (xs[i], cy), int(r * .6), (255, 248, 230))
            pygame.draw.line(surf, (255, 140, 60), (xs[0] + 52, cy), (xs[1] - 52, cy), 5)
            pygame.draw.line(surf, (255, 140, 60), (xs[1] + 52, cy), (xs[2] - 52, cy), 5)
            glow.draw_glow_text(surf, "INFERNO 3/3!  HAND x3", 28, (255, 140, 60), (640, 370))
        else:                                                     # coins
            for i in range(7):
                a = t * 2 + i
                x, y = 640 + math.cos(a) * 170, cy + math.sin(a) * 50
                pygame.draw.circle(surf, (230, 170, 40), (int(x), int(y)), 20)
                pygame.draw.circle(surf, (255, 225, 110), (int(x), int(y)), 14)
            glow.draw_glow_text(surf, "+$ INTEREST", 30, config.GOLD, (640, cy))
