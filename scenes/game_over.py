import math

import pygame

import config
from core import save
from core.dice import Die
from effects import glow
from scenes.base import Scene
from ui import layout as L
from ui.dice_view import die_art
from ui.widgets import GlowButton


def draw_flames(surf, cx, cy, t):
    """Animated elemental flames (fire, water, leaves, stone) rising behind the die."""
    specs = [(-150, (232, 92, 44), 1.0, 0.0), (-80, (246, 150, 56), 1.25, 1.3), (-10, (214, 60, 40), 1.1, 2.1),
             (70, (70, 150, 220), 1.2, 3.0), (140, (96, 178, 92), 1.0, 4.2), (190, (74, 128, 214), 0.85, 5.0)]
    for dx, col, sc, ph in specs:
        h = (150 + 34 * math.sin(t * 3.2 + ph)) * sc
        w = 46 * sc
        x = cx + dx
        for layer, k in ((0, 1.0), (1, .62)):
            c = glow.mix(col, (255, 240, 190), .5) if layer else col
            ww, hh = w * (1 - .4 * layer), h * (1 - .38 * layer)
            sway = math.sin(t * 2.4 + ph) * 12
            pts = [(x - ww, cy + 40), (x - ww * .7, cy - hh * .35), (x + sway * .6, cy - hh),
                   (x + ww * .7, cy - hh * .3), (x + ww, cy + 40)]
            pygame.draw.polygon(surf, c, pts)
    pygame.draw.polygon(surf, (110, 82, 58), [(cx - 200, cy + 60), (cx - 90, cy - 30), (cx - 10, cy + 60)])
    pygame.draw.polygon(surf, (142, 108, 74), [(cx - 10, cy + 60), (cx + 100, cy - 44), (cx + 210, cy + 60)])


class GameOverScene(Scene):
    def enter(self):
        self.t = 0.0
        self.g.sfx.play("over")
        self.g.shake.add(0.5)
        save.delete_save()
        self.records, self.new = save.record_run_end(self.g.run, won=False)
        self.btns = {"retry": GlowButton((470, 566, 340, 58), "PLAY AGAIN", None, 26, style="primary"),
                     "title": GlowButton((470, 634, 340, 52), "MAIN MENU", None, 22)}

    def act(self, k):
        if self.t < 0.5:
            return
        if k == "retry":
            self.g.new_run()
            self.g.scenes.goto("round_select")
        else:
            self.g.scenes.goto("title")

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN:
            self.act("retry")
        for k, b in self.btns.items():
            if b.handle_event(e, self.g.sfx):
                self.act(k)

    def update(self, dt):
        self.t += dt
        for b in self.btns.values():
            b.update(dt)

    def draw(self, surf):
        run, t = self.g.run, self.t
        ov = pygame.Surface((1280, 720), pygame.SRCALPHA)
        ov.fill((6, 12, 24, min(150, int(t * 300))))
        surf.blit(ov, (0, 0))
        draw_flames(surf, 640, 190, t)
        img = pygame.transform.rotozoom(die_art(Die(6), 120), math.sin(t * 1.5) * 6, 1.0)
        glow.draw_ellipse_shadow(surf, 640, 268, 130, 20, 120)
        surf.blit(img, img.get_rect(center=(640, 200 + math.sin(t * 2) * 5)))
        glow.draw_glow_text(surf, "GAME OVER", 88, config.CREAM, (640, 330))
        glow.draw_text(surf, f"reached round {run.round_idx + 1} - {run.round_name}   (short by {L.fmt_num(max(0, run.target - run.round_score))})",
                       17, config.MUTED, (640, 385), kind="ui")
        glow.draw_text(surf, "SCORE", 16, config.MUTED, (640, 424), kind="ui")
        glow.draw_text(surf, L.fmt_num(run.total_score), 52, config.CREAM, (640, 462))
        glow.draw_text(surf, "BEST HAND", 16, config.MUTED, (640, 504), kind="ui")
        glow.draw_text(surf, f"{run.best_hand[0]}  {L.fmt_num(run.best_hand[1])}", 28, config.GOLD, (640, 532), kind="ui")
        if self.new and int(t * 3) % 2 == 0:                  # a new lifetime record blinks
            glow.draw_glow_text(surf, "NEW RECORD: " + " & ".join("best " + n for n in self.new).upper(), 18,
                                config.GOLD, (640, 40), kind="ui")
        glow.draw_text(surf, f"BEST EVER: ROUND {self.records['best_round']}/{len(config.ROUND_NAMES)}   "
                             f"RUNS {self.records['runs']}   WINS {self.records['wins']}", 14, config.MUTED, (640, 700), kind="ui")
        for b in self.btns.values():
            b.draw(surf, t)
