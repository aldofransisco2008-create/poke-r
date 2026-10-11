import pygame

import config
from effects import glow
from effects.tween import out_back, out_cubic
from scenes.base import Scene
from ui import layout as L
from ui.widgets import GlowButton, draw_coin, draw_parchment

CONFETTI = [config.GOLD, config.RED, config.TEAL, config.GREEN, config.EMBER]


class RoundResultScene(Scene):
    music = "game"
    def enter(self):
        g = self.g
        self.t = 0.0
        self.pay = g.run.payout()
        self.left_plays, self.left_pay, self.interest = g.run.hand_ins, g.run.leftover_pay(), g.run.interest()
        self.held = g.run.money
        g.sfx.play("win")
        g.particles.confetti(CONFETTI, 150)
        last = g.run.is_last_round
        self.btn = GlowButton((470, 584, 340, 62), "CLAIM VICTORY" if last else "TO THE SHOP", None, 26, style="primary")

    def go(self):
        if self.t < 0.6:
            return
        if self.g.run.is_last_round:
            self.g.scenes.goto("victory")
        else:
            self.g.scenes.goto("shop", payout=self.pay)

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.go()
        if self.btn.handle_event(e, self.g.sfx):
            self.go()

    def update(self, dt):
        self.t += dt
        self.btn.update(dt)
        if int(self.t * 60) % 45 == 0 and self.t < 3:
            self.g.particles.confetti(CONFETTI, 6)

    def draw(self, surf):
        run, t = self.g.run, self.t
        k = out_back(t / 0.5)
        glow.draw_glow_text(surf, "ROUND CLEARED!", int(80 * max(0.05, k)) // 2 * 2, config.CREAM, (640, 110))
        panel = pygame.Rect(340, 170, 600, 392)
        draw_parchment(surf, panel, 16, corners=True)
        glow.draw_text(surf, f"Round {run.round_idx + 1} - {run.round_name}", 24, config.INK, (640, 210), kind="ui")
        shown = run.round_score * out_cubic((t - 0.3) / 0.9)
        glow.draw_text(surf, "SCORE", 15, (120, 96, 64), (640, 262), kind="ui")
        glow.draw_text(surf, L.fmt_num(shown), 68, config.INK, (640, 314))
        glow.draw_text(surf, f"target {L.fmt_num(run.target)}   ({run.round_score / run.target:.0%})", 19, (96, 74, 48), (640, 366), kind="ui")
        pygame.draw.line(surf, (176, 148, 104), (400, 390), (880, 390), 2)
        ink, soft = config.INK, (96, 74, 48)
        rows = (("Round reward", config.ROUND_REWARD),
                (f"{self.left_plays} unused play{'s' if self.left_plays != 1 else ''} x ${config.HAND_LEFTOVER_PAY}", self.left_pay),
                (f"Interest on ${self.held} held", self.interest))
        for k, (label, v) in enumerate(rows):
            glow.draw_text(surf, label, 16, soft, (400, 410 + k * 22), "midleft", kind="ui")
            glow.draw_text(surf, f"+${v}", 18, ink, (880, 410 + k * 22), "midright", kind="ui")
        pygame.draw.line(surf, (176, 148, 104), (400, 474), (880, 474), 2)
        amount = L.fmt_num(self.pay * out_cubic((t - 0.8) / 0.7))
        tw = glow.render_text(f"+{amount}", 46, config.INK).get_width()
        draw_coin(surf, (640 - tw // 2 - 26, 504), 17, t)
        glow.draw_text(surf, f"+{amount}", 46, (150, 100, 20), (640 + 16, 504))
        glow.draw_text(surf, f"best hand: {run.best_hand[0]}  {L.fmt_num(run.best_hand[1])}", 16, soft, (640, 540), kind="ui")
        self.btn.draw(surf, t)
