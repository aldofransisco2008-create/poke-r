import math

import pygame

import config
from core.numfmt import fmt_num
from effects import glow
from scenes.base import Scene
from ui.widgets import GlowButton


class RoundSelectScene(Scene):
    music = "lobby"
    """The 10 acts as columns of 5 stone medallions, joined by a winding trail."""
    bg_mode = "scene"

    def enter(self):
        self.t = 0.0
        # one column per act, Trial ... Guardian top to bottom
        n = config.ROUNDS_PER_ACT
        self.pos = [(80 + (i // n) * 124, 238 + (i % n) * 80) for i in range(len(config.ROUND_NAMES))]
        self.start_btn = GlowButton((470, 636, 340, 60), "", None, 26, style="primary")
        self.back_btn = GlowButton((40, 644, 150, 46), "< BACK", None, 20)

    def go(self):
        self.g.scenes.goto("round_intro")

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.go()
        elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.g.scenes.goto("title")
        if self.start_btn.handle_event(e, self.g.sfx):
            self.go()
        if self.back_btn.handle_event(e, self.g.sfx):
            self.g.scenes.goto("title")

    def update(self, dt):
        self.t += dt
        self.start_btn.update(dt)
        self.back_btn.update(dt)

    def draw(self, surf):
        t, run = self.t, self.g.run
        glow.draw_glow_text(surf, "ROUND SELECT", 60, config.CREAM, (640, 74))
        glow.draw_glow_text(surf, f"{len(config.ACTS)} acts of {config.ROUNDS_PER_ACT} rounds - every 2nd act ends with a BOSS", 18, config.CREAM, (640, 124), kind="ui")
        for a, name in enumerate(config.ACTS):
            cur = a == run.act_idx
            x = 80 + a * 124
            glow.draw_glow_text(surf, f"ACT {a + 1}", 13, config.GOLD if cur else config.MUTED, (x, 176), kind="ui")
            for k, word in enumerate(name.upper().split()):
                glow.draw_glow_text(surf, word, 12, config.CREAM if cur else (172, 190, 204), (x, 194 + k * 14))
        for i in range(len(self.pos) - 1):
            (x1, y1), (x2, y2) = self.pos[i], self.pos[i + 1]
            done = i < run.round_idx
            n = int(math.dist((x1, y1), (x2, y2)) // 16)
            for k in range(n):                                  # dotted trail
                f = (k + .5) / n
                pygame.draw.circle(surf, config.GOLD if done else (210, 226, 232), (x1 + (x2 - x1) * f, y1 + (y2 - y1) * f), 3)
        for i, (x, y) in enumerate(self.pos):
            done, cur = i < run.round_idx, i == run.round_idx
            r = 20 + (3 * math.sin(t * 4) if cur else 0)
            glow.draw_ellipse_shadow(surf, int(x), int(y + r - 4), r * 2, 12, 100)
            boss = i % config.ROUNDS_PER_ACT == config.LAST_STAGE and (i // config.ROUNDS_PER_ACT) in config.BOSSES
            body = (118, 184, 96) if done else (214, 76, 54) if cur else (110, 30, 40) if boss else (58, 78, 96)
            pygame.draw.circle(surf, glow.scale(body, .5), (x, y + 3), int(r))
            pygame.draw.circle(surf, body, (x, y), int(r))
            pygame.draw.circle(surf, glow.mix(body, (255, 255, 255), .3), (x - 6, y - 8), int(r * .45))
            pygame.draw.circle(surf, config.CREAM if (done or cur) else (120, 140, 156), (x, y), int(r), 3)
            if done:
                pygame.draw.lines(surf, config.CREAM, False, [(x - 8, y), (x - 2, y + 6), (x + 9, y - 7)], 4)
            else:
                glow.draw_text(surf, str(i + 1), 18, config.CREAM if cur else (176, 192, 204), (x, y))
            col = config.CREAM if (done or cur) else (172, 190, 204)
            if boss:
                for dx in (-12, 0, 12):                         # a crown over boss medallions
                    pygame.draw.polygon(surf, config.GOLD, [(x + dx - 5, y - r + 3), (x + dx, y - r - 6), (x + dx + 5, y - r + 3)])
                bname = config.BOSSES[i // config.ROUNDS_PER_ACT]["name"].split(",")[0].upper()
                glow.draw_glow_text(surf, bname, 12, config.RED if not done else col, (x, y + 31), kind="ui")
            else:
                glow.draw_glow_text(surf, config.STAGES[i % config.ROUNDS_PER_ACT], 12, col, (x, y + 31), kind="ui")
            glow.draw_glow_text(surf, fmt_num(config.TARGETS[i]), 12, config.GOLD if cur else col, (x, y + 45), kind="ui")
        self.start_btn.draw(surf, t, f"START ROUND {run.round_idx + 1}", icon="play")
        self.back_btn.draw(surf, t)
