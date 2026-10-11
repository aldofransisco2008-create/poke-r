import math

import pygame

import config
from core import save
from core.numfmt import fmt_num
from effects import glow
from effects.tween import out_back, out_cubic
from scenes.base import Scene


class RoundIntroScene(Scene):
    music = "game"
    """Banner with the round name and target (1.5 s), then the dice are dealt."""

    def enter(self):
        g = self.g
        g.run.start_round()
        g.deck.new_round([c.type for c in g.run.slots], g.run.hand_size)
        g.apply_demo()
        if not g.demo:
            save.save_run(g.run)                      # CONTINUE resumes at the start of this round
        self.t = 0.0
        g.sfx.play("whoosh")

    def handle_event(self, e):
        if self.t > 0.5 and (e.type == pygame.MOUSEBUTTONDOWN or (e.type == pygame.KEYDOWN and e.key != pygame.K_m)):
            self.t = 9.0

    def update(self, dt):
        self.t += dt
        if self.t >= (2.6 if self.g.run.boss else 1.5):          # bosses get a longer entrance
            self.g.scenes.goto("play")

    def draw(self, surf):
        run, t = self.g.run, self.t
        k = out_cubic(t / 0.3)
        band = pygame.Surface((1280, 240), pygame.SRCALPHA)
        band.fill((10, 22, 40, int(232 * k)))
        surf.blit(band, (0, 240))
        pygame.draw.line(surf, config.BRONZE, (0, 240), (1280 * k, 240), 4)
        pygame.draw.line(surf, config.BRONZE, (1280, 480), (1280 - 1280 * k, 480), 4)
        off = (1 - out_back(t / 0.45)) * 700
        glow.draw_text(surf, f"ACT {run.act_idx + 1} / {len(config.ACTS)}    ROUND {run.round_idx + 1} / {len(config.ROUND_NAMES)}",
                       22, config.MUTED, (640 - off, 268), kind="ui")
        boss = run.boss
        if boss:                                              # boss: red band, name, and the rule it imposes
            pulse = 0.5 + 0.5 * math.sin(t * 8)
            red = pygame.Surface((1280, 240), pygame.SRCALPHA)
            red.fill((120, 10, 20, int(90 * k * (0.6 + 0.4 * pulse))))
            surf.blit(red, (0, 240))
            name, title = (boss["name"].split(", ", 1) + [""])[:2]
            glow.draw_glow_text(surf, "BOSS", 22, config.RED, (640 + off, 300), kind="ui")
            glow.draw_glow_text(surf, name.upper(), 76, glow.mix(config.RED, config.CREAM, .3 * pulse), (640 + off, 348))
            glow.draw_glow_text(surf, title.upper(), 24, config.CREAM, (640 - off, 396), kind="ui")
            glow.draw_glow_text(surf, boss["desc"], 20, config.GOLD, (640, 428 + (1 - k) * 40), "center", k, kind="ui")
            if t < 0.05:
                self.g.shake.add(0.8)
        else:
            glow.draw_glow_text(surf, run.act_name.upper(), 80, config.CREAM, (640 + off, 340))
            glow.draw_glow_text(surf, run.stage_name.upper(), 28, config.GOLD if run.stage_name == "Guardian" else config.CREAM,
                                (640 - off, 400), kind="ui")
        glow.draw_glow_text(surf, f"TARGET  {fmt_num(run.target)}", 30, config.GOLD, (640, (462 if boss else 452) + (1 - k) * 40),
                            "center", k, kind="ui")
