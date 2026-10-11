import math

import pygame

import config
from effects import glow
from scenes.base import Scene
from ui.widgets import GlowButton, Slider, Toggle, draw_parchment


def icon(surf, kind, x, y, c=(56, 44, 34)):
    if kind == "music":
        pygame.draw.circle(surf, c, (x - 6, y + 9), 6)
        pygame.draw.circle(surf, c, (x + 9, y + 6), 6)
        pygame.draw.line(surf, c, (x - 1, y + 8), (x - 1, y - 10), 3)
        pygame.draw.line(surf, c, (x + 14, y + 5), (x + 14, y - 13), 3)
        pygame.draw.line(surf, c, (x - 1, y - 10), (x + 14, y - 13), 4)
    elif kind in ("sfx", "mute"):
        pygame.draw.polygon(surf, c, [(x - 12, y - 5), (x - 5, y - 5), (x + 3, y - 12), (x + 3, y + 12), (x - 5, y + 5), (x - 12, y + 5)])
        if kind == "sfx":
            pygame.draw.arc(surf, c, (x - 2, y - 8, 16, 16), -1, 1, 3)
            pygame.draw.arc(surf, c, (x - 2, y - 14, 26, 28), -1, 1, 3)
        else:
            pygame.draw.line(surf, c, (x + 8, y - 7), (x + 20, y + 7), 3)
            pygame.draw.line(surf, c, (x + 20, y - 7), (x + 8, y + 7), 3)
    elif kind == "full":
        pygame.draw.rect(surf, c, (x - 14, y - 12, 28, 19), 3, border_radius=2)
        pygame.draw.line(surf, c, (x, y + 8), (x, y + 13), 3)
        pygame.draw.line(surf, c, (x - 8, y + 13), (x + 8, y + 13), 3)
    elif kind == "crt":
        pygame.draw.rect(surf, c, (x - 14, y - 11, 28, 20), 3)
        for k in range(3):
            pygame.draw.line(surf, c, (x - 9, y - 6 + k * 5), (x + 9, y - 6 + k * 5), 2)
    elif kind == "color":
        for k, col in enumerate(((200, 70, 70), (80, 170, 90), (70, 110, 210))):
            pygame.draw.rect(surf, col, (x - 14 + k * 10, y - 11 + (k % 2) * 4, 10, 18))
        pygame.draw.rect(surf, c, (x - 14, y - 11, 28, 22), 2)
    else:  # shake
        pygame.draw.lines(surf, c, False, [(x - 14, y), (x - 8, y - 9), (x, y + 9), (x + 8, y - 9), (x + 14, y)], 3)


ROW = dict(music=206, sfx=256, speed=306, full=356, shake=406, flash=456, crt=506, mute=556, color=616)


class SettingsScene(Scene):
    music = "lobby"
    def enter(self):
        g = self.g
        self.t = 0.0
        self.back = GlowButton((44, 38, 130, 44), "< BACK", None, 20)
        x = 830
        self.sliders = [Slider((x - 250, ROW["music"] - 12, 250, 24), g.sfx.music_volume, g.sfx.set_music_volume),
                        Slider((x - 250, ROW["sfx"] - 12, 250, 24), g.sfx.volume, g.sfx.set_sfx_volume)]
        self.swatches = [pygame.Rect(600 + i * 42, ROW["color"] - 17, 34, 34) for i in range(len(config.BOARD_COLORS))]
        tg = lambda key: (x - 70, ROW[key] - 17, 70, 34)
        self.toggles = [Toggle(tg("full"), getattr(g, "fullscreen", False), self.set_full),
                        Toggle(tg("shake"), config.SHAKE, self.set_shake),
                        Toggle(tg("flash"), config.FLASHES, self.set_flashes),
                        Toggle(tg("crt"), config.CRT, self.set_crt),
                        Toggle(tg("mute"), g.sfx.muted, lambda v: g.sfx.toggle_mute() if v != g.sfx.muted else None)]
        self.speed_btn = GlowButton((x - 110, ROW["speed"] - 20, 110, 40), "", None, 20, style="gold")

    def set_full(self, v):
        if v != getattr(self.g, "fullscreen", False):
            self.g.toggle_fullscreen()

    def set_shake(self, v):
        config.SHAKE = v
        self.g.save_settings()

    def set_flashes(self, v):
        config.FLASHES = v
        self.g.save_settings()

    def set_crt(self, v):
        config.CRT = v
        self.g.save_settings()

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.g.scenes.goto("title")
        if self.back.handle_event(e, self.g.sfx):
            self.g.scenes.goto("title")
        for s in self.sliders:
            s.handle_event(e)
        if self.speed_btn.handle_event(e, self.g.sfx):
            self.g.speed_idx = (self.g.speed_idx + 1) % len(config.GAME_SPEEDS)
            self.g.save_settings()
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, r in enumerate(self.swatches):
                if r.collidepoint(e.pos):
                    self.g.set_board(i)
                    self.g.sfx.play("click")
        if e.type == pygame.MOUSEBUTTONUP:
            self.g.save_settings()                                  # volumes are saved when a slider is released
        for tg in self.toggles:
            if tg.handle_event(e):
                self.g.sfx.play("click")

    def update(self, dt):
        self.t += dt
        self.back.update(dt)
        self.speed_btn.update(dt)
        for tg in self.toggles:
            tg.update(dt)

    def draw(self, surf):
        t = self.t
        panel = pygame.Rect(300, 96, 680, 570)
        draw_parchment(surf, panel, 18, corners=True)
        glow.draw_text(surf, "SETTINGS", 40, config.INK, (640, 140))
        self.back.draw(surf, t)
        rows = [("music", "Music"), ("sfx", "Sound effects"), ("speed", "Game speed"), ("full", "Fullscreen"),
                ("shake", "Screen shake & zoom"), ("flash", "Flashing effects"), ("crt", "Scan lines"), ("mute", "Mute all")]
        for k, label in rows:
            y = ROW[k]
            icon(surf, {"speed": "shake", "flash": "crt"}.get(k, k), 352, y)
            glow.draw_text(surf, label, 21, config.INK, (392, y), "midleft", kind="ui")
            if k != "mute":
                pygame.draw.line(surf, (200, 150, 110), (330, y + 25), (950, y + 25), 2)
        self.speed_btn.draw(surf, t, f"{config.GAME_SPEEDS[self.g.speed_idx]:g}x")
        for s in self.sliders:
            s.draw(surf)
        for tg in self.toggles:
            tg.draw(surf)
        # little painted hills along the bottom of the panel
        for i, (col, base, amp) in enumerate((((150, 190, 206), 618, 22), ((92, 150, 150), 626, 16))):
            pts = [(panel.x + 4, panel.bottom - 4)] + [(panel.x + 4 + k * 24, base - amp * (0.5 + 0.5 * math.sin(k * .7 + i * 2))) for k in range(0, 28)] + [(panel.right - 4, panel.bottom - 4)]
            pygame.draw.polygon(surf, col, pts)
        icon(surf, "color", 352, ROW["color"])
        glow.draw_text(surf, "Board color", 21, config.INK, (392, ROW["color"]), "midleft", kind="ui")
        for i, (r, (name, top, bottom)) in enumerate(zip(self.swatches, config.BOARD_COLORS)):
            on = i == self.g.board_idx
            pygame.draw.rect(surf, (56, 44, 34), r.inflate(6, 6), border_radius=6)
            pygame.draw.rect(surf, top, (r.x, r.y, r.w, r.h // 2))
            pygame.draw.rect(surf, bottom, (r.x, r.y + r.h // 2, r.w, r.h - r.h // 2))
            if on:
                pygame.draw.rect(surf, config.GOLD, r.inflate(10, 10), 3, border_radius=8)
        glow.draw_text(surf, config.BOARD_COLORS[self.g.board_idx][0], 14, (96, 74, 48), (790, 656), kind="ui")
