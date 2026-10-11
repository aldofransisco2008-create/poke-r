import pygame

import config
from core.combos import COMBO_TEXT
from effects import glow
from scenes.base import Scene
from ui.card_view import SKILL_COLOR, draw_element_list
from ui.widgets import GlowButton, draw_coin, draw_parchment

TABS = ("ELEMENTS", "SKILLS", "COMBOS", "VOUCHERS")


class CollectionScene(Scene):
    music = "lobby"
    """Parchment reference book: every special die, skill and combo in the game."""

    def enter(self):
        self.t = 0.0
        self.tab = self.kw.get("tab", 0)
        self.back = GlowButton((44, 38, 130, 44), "< BACK", None, 20)
        self.tab_rects = [pygame.Rect(440 + i * 200, 44, 190, 40) for i in range(len(TABS))]

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.g.scenes.goto("title")
        if self.back.handle_event(e, self.g.sfx):
            self.g.scenes.goto("title")
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, r in enumerate(self.tab_rects):
                if r.collidepoint(e.pos) and i != self.tab:
                    self.tab = i
                    self.g.sfx.play("click")

    def update(self, dt):
        self.t += dt
        self.back.update(dt)

    def draw(self, surf):
        t = self.t
        draw_parchment(surf, (20, 16, 1240, 690), 18, corners=True)
        self.back.draw(surf, t)
        glow.draw_text(surf, "COLLECTION", 40, config.INK, (196, 62), "midleft")
        for i, r in enumerate(self.tab_rects):
            on = i == self.tab
            pygame.draw.rect(surf, config.RED if on else (226, 210, 174), r, border_radius=20)
            pygame.draw.rect(surf, (128, 104, 72) if not on else (110, 30, 22), r, 2, border_radius=20)
            glow.draw_text(surf, TABS[i], 17, config.CREAM if on else config.INK, r.center)
        pygame.draw.line(surf, (176, 148, 104), (44, 104), (1236, 104), 2)
        if self.tab == 0:
            draw_element_list(surf, t)
        elif self.tab == 1:
            self.draw_skills(surf)
        elif self.tab == 2:
            self.draw_combos(surf)
        else:
            self.draw_vouchers(surf)


    def draw_skills(self, surf):
        for i, s in enumerate(config.SKILLS):
            col = SKILL_COLOR[s["key"]]
            r = pygame.Rect(48 + (i // 6) * 600, 124 + (i % 6) * 88, 580, 78)
            pygame.draw.rect(surf, (232, 218, 184), r, border_radius=12)
            pygame.draw.rect(surf, (150, 122, 84), r, 2, border_radius=12)
            pygame.draw.rect(surf, col, (r.x, r.y, 12, r.h), border_top_left_radius=12, border_bottom_left_radius=12)
            glow.draw_text(surf, s["name"].upper(), 21, config.INK, (r.x + 32, r.y + 25), "midleft")
            glow.draw_text(surf, s["desc"], 15, (96, 74, 48), (r.x + 32, r.y + 54), "midleft", kind="ui")
            draw_coin(surf, (r.right - 78, r.centery), 10)
            glow.draw_text(surf, str(config.SKILL_PRICE), 20, config.INK, (r.right - 60, r.centery), "midleft")

    def draw_combos(self, surf):
        for i, (name, bonus) in enumerate(config.COMBO_BONUS.items()):
            r = pygame.Rect(48 + (i // 5) * 600, 124 + (i % 5) * 108, 580, 94)
            pygame.draw.rect(surf, (232, 218, 184), r, border_radius=12)
            pygame.draw.rect(surf, (150, 122, 84), r, 2, border_radius=12)
            glow.draw_text(surf, name.upper(), 21, config.INK, (r.x + 22, r.y + 30), "midleft")
            glow.draw_text(surf, COMBO_TEXT[name], 15, (96, 74, 48), (r.x + 22, r.y + 62), "midleft", kind="ui")
            glow.draw_text(surf, f"+{bonus}", 30, (168, 52, 36), (r.right - 24, r.centery), "midright")

    def draw_vouchers(self, surf):
        glow.draw_text(surf, "PERMANENT UPGRADES - the shop stocks one voucher at a time", 15, (96, 74, 48), (48, 128), "midleft", kind="ui")
        for i, v in enumerate(config.VOUCHERS):
            r = pygame.Rect(48, 156 + i * 96, 1180, 84)
            pygame.draw.rect(surf, (232, 218, 184), r, border_radius=12)
            pygame.draw.rect(surf, (150, 122, 84), r, 2, border_radius=12)
            pygame.draw.rect(surf, config.GOLD, (r.x, r.y, 12, r.h), border_top_left_radius=12, border_bottom_left_radius=12)
            glow.draw_text(surf, v["name"].upper(), 22, config.INK, (r.x + 32, r.y + 28), "midleft")
            glow.draw_text(surf, v["desc"], 15, (96, 74, 48), (r.x + 32, r.y + 58), "midleft", kind="ui")
            glow.draw_text(surf, f"max level {v['max_level']}", 16, (96, 74, 48), (r.right - 150, r.centery), "midright", kind="ui")
            draw_coin(surf, (r.right - 78, r.centery), 10)
            glow.draw_text(surf, str(config.VOUCHER_PRICE), 20, config.INK, (r.right - 60, r.centery), "midleft")
