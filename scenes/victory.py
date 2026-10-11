import math
import random

import pygame

import config
from core import save
from effects import glow
from scenes.base import Scene
from ui import layout as L
from ui.widgets import GlowButton, draw_parchment

PALETTE = [config.GOLD, config.RED, config.TEAL, config.GREEN, config.VIOLET, config.EMBER]


class VictoryScene(Scene):
    bg_mode = "scene"

    def enter(self):
        self.t = 0.0
        self.next_fw = 0.0
        self.g.sfx.play("win")
        self.g.particles.confetti(PALETTE, 120)
        save.delete_save()
        save.record_run_end(self.g.run, won=True)
        self.btn = GlowButton((490, 610, 300, 58), "MAIN MENU", None, 24, style="primary")

    def handle_event(self, e):
        if self.btn.handle_event(e, self.g.sfx) or (e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN):
            self.g.scenes.goto("title")

    def update(self, dt):
        self.t += dt
        self.btn.update(dt)
        self.next_fw -= dt
        if self.next_fw <= 0:
            self.next_fw = random.uniform(0.3, 0.7)
            x, y = random.uniform(150, 1130), random.uniform(60, 300)
            self.g.particles.burst(x, y, 60, random.sample(PALETTE, 3), 340, life=(0.8, 1.6), size=(3, 6), grav=160)
        if random.random() < dt * 2:
            self.g.particles.confetti(PALETTE, 4)

    def draw(self, surf):
        run, t = self.g.run, self.t
        glow.draw_glow_text(surf, "VICTORY", 128, config.GOLD, (640, 130 + math.sin(t * 1.8) * 5))
        glow.draw_glow_text(surf, "ULTIMATE CHAMPION", 34, config.CREAM, (640, 226), kind="ui")
        panel = pygame.Rect(410, 290, 460, 280)
        draw_parchment(surf, panel, 16, corners=True)
        rows = [("ROUNDS CLEARED", str(len(config.ROUND_NAMES))), ("TOTAL SCORE", L.fmt_num(run.total_score)),
                ("BEST HAND", f"{run.best_hand[0]}  {L.fmt_num(run.best_hand[1])}")]
        for i, (a, b) in enumerate(rows):
            y = 328 + i * 82
            glow.draw_text(surf, a, 14, (120, 96, 64), (640, y), kind="ui")
            glow.draw_text(surf, b, 34, config.INK, (640, y + 34))
        self.btn.draw(surf, t)
