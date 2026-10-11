import math

import pygame

import config
from core import save
from core.numfmt import fmt_num
from effects import glow
from scenes.base import Scene
from ui.widgets import GlowButton, draw_coin, draw_panel


class TitleScene(Scene):
    music = "lobby"
    """Main menu: a left-hand menu panel over an animated mountain panorama."""
    bg_mode = "title"

    def enter(self):
        self.t = 0.0
        x, w, h = 101, 367, 56
        self.saved = save.load_run()
        self.records = save.load_records()
        keys = (["continue"] if self.saved else []) + ["play", "howto", "collection", "settings", "quit"]
        labels = dict(play="NEW RUN", howto="HOW TO PLAY", collection="COLLECTION", settings="SETTINGS", quit="QUIT")
        self.btns = {}
        for i, k in enumerate(keys):
            if k == "continue":
                text = f"CONTINUE  (ROUND {self.saved.round_idx + 1})"
            else:
                text = labels[k]
            primary = k == ("continue" if self.saved else "play")
            self.btns[k] = GlowButton((x, 143 + i * 68, w, h), text, None, 22 if primary else 20,
                                      style="primary" if primary else "secondary")
        self.confirm = 0.0                    # NEW RUN over a saved run asks to click twice

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.resume() if self.saved else self.start()
        for k, b in self.btns.items():
            if b.handle_event(e, self.g.sfx):
                if k == "continue":
                    self.resume()
                elif k == "play":
                    self.start()
                elif k == "howto":
                    self.g.scenes.goto("howto")
                elif k == "collection":
                    self.g.scenes.goto("collection", tab=0)
                elif k == "settings":
                    self.g.scenes.goto("settings")
                else:
                    self.g.running = False

    def start(self):
        if self.saved and self.confirm <= 0:               # don't wipe a saved run on a single click
            self.confirm = 2.5
            self.g.sfx.play("error")
            return
        save.delete_save()
        self.g.new_run()
        self.g.sfx.play("reveal")
        self.g.scenes.goto("round_select" if self.records["tutorial_done"] else "howto",
                           **({} if self.records["tutorial_done"] else {"then": "round_select"}))

    def resume(self):
        self.g.new_run()
        self.g.run = self.saved
        self.g.apply_demo()
        self.g.sfx.play("reveal")
        self.g.scenes.goto("round_select")

    def update(self, dt):
        self.t += dt
        self.confirm = max(0.0, self.confirm - dt)
        for b in self.btns.values():
            b.update(dt)

    def draw(self, surf):
        t, run = self.t, self.g.run
        panel = pygame.Rect(56, 24, 444, 680)                     # the menu panel (double frame)
        draw_panel(surf, panel, config.NAVY_LINE, 250, radius=4)
        pygame.draw.rect(surf, (150, 170, 220), panel.inflate(-12, -12), 2)
        title = pygame.Rect(91, 51, 382, 69)
        pygame.draw.rect(surf, (30, 40, 92), title)
        pygame.draw.rect(surf, (150, 170, 220), title, 2)
        glow.draw_glow_text(surf, "POKE'R", 64, config.CREAM, (title.centerx, title.centery - 2 + math.sin(t * 2.0) * 2))
        for i in range(3):                                        # little twinkles around the logo
            k = (t * 0.8 + i * 0.33) % 1.0
            r = int(6 * math.sin(k * math.pi))
            sx, sy = title.x + 24 + i * 150 + (i * 37) % 40, title.y + 12 + (i * 23) % 40
            if r > 0:
                pygame.draw.line(surf, config.CREAM, (sx - r, sy), (sx + r, sy), 2)
                pygame.draw.line(surf, config.CREAM, (sx, sy - r), (sx, sy + r), 2)
        for k, b in self.btns.items():
            text = "CLICK AGAIN: ABANDON SAVED RUN" if k == "play" and self.confirm > 0 else None
            b.draw(surf, t, text, icon="play" if k in ("play", "continue") else None)
        glow.draw_text(surf, "SMALL STEPS, BIG REWARDS.", 14, (96, 116, 168), (panel.centerx, 636), kind="ui")
        rec = self.records                                         # lifetime records, top right
        pill = pygame.Rect(880, 8, 387, 92)
        draw_panel(surf, pill, config.NAVY_LINE, 250, radius=4)
        glow.draw_text(surf, "RECORDS", 14, config.MUTED, (pill.x + 18, pill.y + 18), "midleft", kind="ui")
        best = f"BEST ROUND {rec['best_round']}/{len(config.ROUND_NAMES)}" if rec["runs"] else "NO RUNS YET"
        glow.draw_text(surf, best, 20, config.CREAM,
                       (pill.x + 18, pill.y + 46), "midleft")
        glow.draw_text(surf, f"RUNS {rec['runs']}  WINS {rec['wins']}", 14, config.MUTED, (pill.right - 18, pill.y + 18),
                       "midright", kind="ui")
        glow.draw_text(surf, f"BEST HAND {fmt_num(rec['best_hand'])}", 16, config.GOLD, (pill.x + 18, pill.y + 72), "midleft",
                       kind="ui")
