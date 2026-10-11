import json
import os

import pygame

import config
from audio.synth import Sfx
from core.cards import SKILL_DEFS, VOUCHER_DEFS, CardType, MultiplierCard
from core.deck import DeckManager
from core.run_state import RunState
from effects.background import Background
from effects.particles import ParticleSystem
from effects.shake import Shake
from scenes.base import SceneManager


SETTINGS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")


class Game:
    """Shared context handed to every scene."""

    def __init__(self, screen, registry):
        self.screen = screen
        self.frame = pygame.Surface((config.SCREEN_W, config.SCREEN_H)).convert()
        self.sfx = Sfx()
        self.bg = Background()
        self.particles = ParticleSystem()
        self.shake = Shake()
        self.run = RunState()
        self.deck = DeckManager()
        self.time = 0.0
        self.hitstop = 0.0
        self.flash = 0.0
        self.flash_col = (255, 246, 224)  # tint of the screen flash (punch() sets it, it drifts back to cream)
        self.zoom = 0.0                  # zoom punch: the picture kicks in for a moment
        self.aberr = 0.0                 # chromatic split: red and blue drift apart on big hits
        self.running = True
        self.demo = False                # hidden developer demo mode (F9)
        self.scenes = SceneManager(self, registry)
        self.board_idx = 0
        self.speed_idx = 0                # index into config.GAME_SPEEDS
        self.load_settings()
        self.scan = pygame.Surface((config.SCREEN_W, config.SCREEN_H), pygame.SRCALPHA)
        for y in range(0, config.SCREEN_H, 4):                 # faint CRT scan-lines on the 2 px grid
            pygame.draw.rect(self.scan, (0, 0, 20, 34), (0, y + 2, config.SCREEN_W, 2))

    # ------------------------------------------------------------ settings (kept in settings.json)
    def load_settings(self):
        try:
            with open(SETTINGS_PATH, encoding="utf-8") as f:
                d = json.load(f)
            self.set_board(int(d.get("board", 0)), save=False)
            self.speed_idx = int(d.get("speed", 0)) % len(config.GAME_SPEEDS)
            config.SHAKE = bool(d.get("shake", config.SHAKE))
            config.FLASHES = bool(d.get("flashes", config.FLASHES))
            config.CRT = bool(d.get("crt", config.CRT))
            self.sfx.set_music_volume(float(d.get("music", self.sfx.music_volume)))
            self.sfx.set_sfx_volume(float(d.get("sfx", self.sfx.volume)))
        except (OSError, ValueError, TypeError):
            pass

    def save_settings(self):
        try:
            with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump(dict(board=self.board_idx, music=self.sfx.music_volume, sfx=self.sfx.volume, speed=self.speed_idx,
                               shake=config.SHAKE, flashes=config.FLASHES, crt=config.CRT), f)
        except OSError:
            pass

    @property
    def game_speed(self):
        return config.GAME_SPEEDS[self.speed_idx]

    def set_board(self, i, save=True):
        """Pick the colour of the in-game backdrop."""
        self.board_idx = i % len(config.BOARD_COLORS)
        _, top, bottom = config.BOARD_COLORS[self.board_idx]
        self.bg.set_board_color(top, bottom)
        if save:
            self.save_settings()

    def new_run(self):
        self.run = RunState()
        self.deck = DeckManager()
        self.apply_demo()

    def apply_demo(self):
        self.run.demo = self.demo
        self.deck.cheat = self.demo

    def skip_to_endgame(self):
        """Fresh run on the last SKIP_ROUNDS_LEFT rounds with maxed vouchers, levelled skills and strong Elements."""
        self.new_run()
        run = self.run
        run.round_idx = len(config.ROUND_NAMES) - config.SKIP_ROUNDS_LEFT
        run.money = config.SKIP_MONEY
        run.vouchers = {k: v.max_level for k, v in VOUCHER_DEFS.items()}
        run.skills = {k: config.SKIP_SKILL_LEVEL - 1 for k in SKILL_DEFS}     # combo level = 1 + stacks
        run.slots = [MultiplierCard(CardType[n], level=config.SKIP_ELEMENT_LEVEL)
                     for n in config.SKIP_ELEMENTS][:run.element_slots]
        self.sfx.play("reveal")
        self.scenes.goto("round_select")

    def punch(self, flash=0.0, col=None, zoom=0.0, aberr=0.0, shake=0.0):
        """One call for a big hit: tinted flash, zoom kick, colour split and screen shake."""
        self.flash = max(self.flash, flash)
        if col and flash > 0:
            self.flash_col = col
        self.zoom = max(self.zoom, zoom)
        self.aberr = max(self.aberr, aberr)
        if shake:
            self.shake.add(shake)

    def toggle_fullscreen(self):
        """Fullscreen on/off; some video drivers refuse, which must never crash the game."""
        try:
            pygame.display.toggle_fullscreen()
            self.fullscreen = not getattr(self, "fullscreen", False)
        except pygame.error:
            pass
        return getattr(self, "fullscreen", False)

    # ------------------------------------------------------------ frame
    def handle_event(self, e):
        if e.type == pygame.QUIT:
            self.running = False
        elif e.type == pygame.KEYDOWN and e.key == pygame.K_m:
            self.sfx.toggle_mute()
        elif e.type == pygame.KEYDOWN and e.key == pygame.K_F12:
            self.toggle_fullscreen()
        elif e.type == pygame.KEYDOWN and e.key == pygame.K_F11 and config.DEV_MODE:     # dev: skip to the endgame
            self.skip_to_endgame()
        elif e.type == pygame.KEYDOWN and e.key == pygame.K_F9 and config.DEV_MODE:      # dev: demo mode
            self.demo = not self.demo
            self.apply_demo()
        elif e.type == pygame.KEYDOWN and e.key == pygame.K_F10 and self.demo and config.DEV_MODE:
            self.run.money += config.DEMO_CASH_KEY
            self.sfx.play("coin")
        else:
            self.scenes.handle_event(e)

    def update(self, real_dt, fps):
        dt = real_dt
        if self.hitstop > 0:
            self.hitstop -= real_dt
            dt = 0.0
        self.time += dt
        self.flash = max(0.0, self.flash - real_dt * 2.2)
        if self.flash <= 0.01:
            self.flash_col = (255, 246, 224)
        self.zoom = max(0.0, self.zoom - real_dt * 3.5)
        self.aberr = max(0.0, self.aberr - real_dt * 2.5)
        self.shake.update(real_dt)
        self.bg.update(dt)
        self.particles.update(dt)
        self.scenes.update(dt)

    def draw(self):
        f = self.frame
        self.bg.draw(f, self.time, getattr(self.scenes.current, "bg_mode", "board"))
        self.scenes.draw(f)
        self.particles.draw(f)
        if self.flash > 0.01:
            ov = pygame.Surface(f.get_size())
            ov.fill(self.flash_col)
            ov.set_alpha(int((110 if config.FLASHES else 35) * self.flash))
            f.blit(ov, (0, 0))
        self.scenes.draw_fade(f)
        if config.CRT:
            f.blit(self.scan, (0, 0))
        if config.SHAKE and config.FLASHES and self.aberr > 0.03:              # chromatic split: red one way, blue the other
            d = max(2, int(10 * self.aberr)) // 2 * 2
            out = f.copy()
            out.fill((0, 255, 0), special_flags=pygame.BLEND_RGB_MULT)
            for col, dx in (((255, 0, 0), d), ((0, 0, 255), -d)):
                ch = f.copy()
                ch.fill(col, special_flags=pygame.BLEND_RGB_MULT)
                out.blit(ch, (dx, 0), special_flags=pygame.BLEND_RGB_ADD)
            f = out
        if config.SHAKE and self.zoom > 0.01:                # zoom punch around the centre
            k = 1 + 0.07 * self.zoom ** 2
            w, h = int(config.SCREEN_W * k) // 2 * 2, int(config.SCREEN_H * k) // 2 * 2
            f = pygame.transform.scale(f, (w, h)).subsurface(((w - config.SCREEN_W) // 2, (h - config.SCREEN_H) // 2,
                                                              config.SCREEN_W, config.SCREEN_H))
        ox, oy = self.shake.offset()
        self.screen.fill((0, 0, 0))
        self.screen.blit(f, (ox, oy))
