"""In-game INFO book: your combo levels (and run stats) and every Element by faction."""
import pygame

import config
from core.cards import SKILL_DEFS
from core.combos import COMBO_TEXT
from effects import glow
from ui.card_view import SKILL_COLOR, draw_element_list
from ui.widgets import GlowButton, draw_parchment

TABS = ("COMBO LEVELS", "ELEMENTS")


class InfoOverlay:
    def __init__(self):
        self.open = False
        self.tab = 0
        self.t = 0.0
        self.close = GlowButton((1086, 30, 150, 44), "CLOSE", None, 20)
        self.tab_rects = [pygame.Rect(470 + i * 270, 34, 255, 40) for i in range(len(TABS))]

    def toggle(self):
        self.open = not self.open

    def handle_event(self, e, sfx):
        """Call only while open. Returns True when the event was used."""
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_i):
            self.open = False
            return True
        if self.close.handle_event(e, sfx):
            self.open = False
            return True
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, r in enumerate(self.tab_rects):
                if r.collidepoint(e.pos) and i != self.tab:
                    self.tab = i
                    sfx.play("click")
        return True

    def update(self, dt):
        self.t += dt
        self.close.update(dt)

    def draw(self, surf, run):
        ov = pygame.Surface((1280, 720), pygame.SRCALPHA)
        ov.fill((6, 14, 28, 200))
        surf.blit(ov, (0, 0))
        draw_parchment(surf, (20, 16, 1240, 690), 18, corners=True)
        glow.draw_text(surf, "INFO", 40, config.INK, (48, 56), "midleft")
        for i, r in enumerate(self.tab_rects):
            on = i == self.tab
            pygame.draw.rect(surf, config.RED if on else (226, 210, 174), r, border_radius=20)
            pygame.draw.rect(surf, (128, 104, 72) if not on else (110, 30, 22), r, 2, border_radius=20)
            glow.draw_text(surf, TABS[i], 17, config.CREAM if on else config.INK, r.center)
        self.close.draw(surf, self.t)
        pygame.draw.line(surf, (176, 148, 104), (44, 96), (1236, 96), 2)
        if self.tab == 0:
            self.draw_combos(surf, run)
        else:
            draw_element_list(surf, self.t, top=110)

    def draw_combos(self, surf, run):
        ink, soft = config.INK, (96, 74, 48)
        x0 = 60
        cols = (("COMBO", x0), ("NEEDS", x0 + 230), ("BONUS", x0 + 640), ("LEVEL", x0 + 760), ("SCORE", x0 + 880),
                ("NEXT LEVEL", x0 + 1000))
        for name, x in cols:
            glow.draw_text(surf, name, 13, (150, 90, 20), (x, 122), "midleft", kind="ui")
        skill_of = {d.combo: k for k, d in SKILL_DEFS.items()}
        for i, (combo, bonus) in enumerate(reversed(list(config.COMBO_BONUS.items()))):
            y = 152 + i * 50
            r = pygame.Rect(44, y - 20, 1192, 42)
            pygame.draw.rect(surf, (232, 218, 184), r, border_radius=10)
            lv = run.combo_level(combo)
            if lv > 1:
                pygame.draw.rect(surf, SKILL_COLOR[skill_of[combo]], r, 3, border_radius=10)
            glow.draw_text(surf, combo.upper(), 18, ink, (x0, y), "midleft")
            glow.draw_text(surf, COMBO_TEXT[combo], 13, soft, (x0 + 230, y), "midleft", kind="ui")
            glow.draw_text(surf, f"+{bonus}", 18, ink, (x0 + 640, y), "midleft")
            glow.draw_text(surf, f"Lv {lv}", 18, (40, 120, 50) if lv > 1 else ink, (x0 + 760, y), "midleft")
            glow.draw_text(surf, f"x{run.combo_mult(combo):.1f}", 18, ink, (x0 + 880, y), "midleft")
            glow.draw_text(surf, f"{SKILL_DEFS[skill_of[combo]].name}  ->  x{run.combo_mult(combo) + config.COMBO_LEVEL_STEP:.1f}",
                           13, soft, (x0 + 1000, y), "midleft", kind="ui")
        y = 560
        pygame.draw.line(surf, (176, 148, 104), (44, y), (1236, y), 2)
        glow.draw_text(surf, "Each skill raises one combo by a level: +20% to that combo's hand score (after penalties).", 14, soft, (640, y + 22), kind="ui")
        stats = [("HAND", f"{run.hand_size} dice"), ("ELEMENT SLOTS", f"{len(run.slots)} / {run.element_slots}"),
                 ("PLAYS", str(run.max_hand_ins)), ("DISCARDS", str(run.max_discards)),
                 ("INTEREST", f"+${run.interest()} now")]
        for i, (a, b) in enumerate(stats):
            x = 140 + i * 200
            glow.draw_text(surf, a, 13, (150, 90, 20), (x, y + 64), kind="ui")
            glow.draw_text(surf, b, 20, ink, (x, y + 92))
