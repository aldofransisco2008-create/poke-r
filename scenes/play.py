import math
import random
from functools import partial

import pygame

import config
from core.cards import CARD_COLOR, CARD_TIER, FACTION_COLOR, FACTIONS, CardType
from core.scoring import PRE_KINDS, after_hand_in, apply_side, preview_score, score_hand
from effects import glow
from effects.element_fx import ElementFX, Firework, Slam, hype_word
from effects.tween import Sequence, approach, in_out, lerp, out_back, out_cubic
from scenes.base import Scene
from ui import layout as L
from ui.card_view import draw_tooltip
from ui.tier_fx import TierShow
from ui.water_bar import WaterBar
from ui.dice_view import DieSprite, draw_kind_icon
from ui.info_overlay import InfoOverlay
from ui.layout import DIE_SIZE
from ui.widgets import GlowButton, draw_dots, draw_money_pill, draw_panel, draw_pill

CARD_KINDS = tuple(t.name.lower() for t in CardType)
KIND_TIER = {t.name.lower(): CARD_TIER[t] for t in CardType}
STEP_GAP = {1: 0.72, 2: 1.0, 3: 1.7}          # Rare and Super Elements get room for their show
KIND_COLOR = {"dice": config.CREAM, "combo": config.NEON_CYAN, "skill": config.NEON_LIME,
              "final": config.NEON_PINK, "faction": config.NEON_GOLD,
              "boss": config.RED}
KIND_COLOR.update({t.name.lower(): c for t, c in CARD_COLOR.items()})
WATER_RECT = pygame.Rect(24, 80, 1232, 72)
TOTAL_POS = (1010, 330)


class PlayScene(Scene):
    music = "game"
    def enter(self):
        g = self.g
        run = g.run
        self.t = 0.0
        self.sprites, self.fx, self.played = [], [], []
        self.floats, self.chips = [], []
        self.banner = None
        self.ffx = None                      # the faction-combo show (dict) while it plays
        self.tshows = []                     # Rare / Super Element shows
        self.efx = []                        # every Element's own trigger burst (flames, bolts, shards ...)
        self.fireworks, self.slams = [], []
        self.hype = None                     # GREAT! / MEGA! / INSANE!! / GODLIKE!!! for big hands
        self.state = "idle"
        self.seq = None
        self.speed = 1.0
        self.paused = False
        self.total_shown = self.total_target = 0.0
        self.pop = 0.0
        self.show_total = False
        self.disp_score = float(run.round_score)
        self.wb = WaterBar()
        self.wb.level = min(1.0, self.disp_score / run.target)
        self.final_done = False
        self.fill = None
        self.reached = False
        self.sparkle_t = 0.0
        self.bd = None
        self.tray = L.tray_rect(run.hand_size)
        bw = (self.tray.w - 20) // 2
        self.btn_play = GlowButton((self.tray.x, 650, bw, 48), "PLAY", None, 24, style="primary")
        self.btn_disc = GlowButton((self.tray.right - bw, 650, bw, 48), "DISCARD", None, 22)
        self.btn_info = GlowButton((1010, 14, 112, 42), "INFO", None, 18, style="gold")
        self.skip_dot = pygame.Rect(0, 0, 0, 0)   # tiny dot after the round name: jump to the endgame (placed in draw_top)
        self.info = InfoOverlay()
        self.buttons = [self.btn_play, self.btn_disc, self.btn_info]
        self.pause_btns = {
            "resume": GlowButton((490, 250, 300, 50), "RESUME", None, 22, style="primary"),
            "vol-": GlowButton((490, 314, 145, 46), "VOL -", None, 20),
            "vol+": GlowButton((645, 314, 145, 46), "VOL +", None, 20),
            "mute": GlowButton((490, 374, 145, 46), "MUTE", None, 20),
            "shake": GlowButton((645, 374, 145, 46), "SHAKE", None, 20),
            "title": GlowButton((490, 434, 300, 50), "QUIT TO TITLE", None, 22),
        }
        self.deal(g.deck.refill())
        g.sfx.play("deal")

    # ------------------------------------------------------------ hand helpers
    def deal(self, dice, delay0=0.0):
        for i, d in enumerate(dice):
            self.sprites.append(DieSprite(d, L.DECK_POS, delay0 + i * 0.07))
        self.layout()

    def layout(self):
        for i, s in enumerate(self.sprites):
            s.tx = L.hand_x(i, self.g.run.hand_size)
            s.ty = L.HAND_CY - (28 if s.selected else 0)

    def selected(self):
        return [i for i, s in enumerate(self.sprites) if s.selected]

    def clear_board(self):
        """Remove last hand's breakdown so it never overlaps the hand."""
        self.chips, self.show_total, self.banner = [], False, None

    def toggle(self, i):
        if self.state != "idle" or not (0 <= i < len(self.sprites)):
            return
        s = self.sprites[i]
        if s.selected:
            s.selected = False
            self.g.sfx.play("click")
        elif len(self.selected()) < self.g.run.hand_size:
            self.clear_board()
            s.selected = True
            self.g.sfx.play(f"select{len(self.selected()) - 1}")
            self.g.particles.burst(s.x, s.y - 40, 6, [s.color, (255, 255, 255)], 140, life=(0.3, 0.6), grav=200)
        else:
            s.shake = 1.0
            self.g.sfx.play("error")
        self.layout()

    def can_play(self):
        n = len(self.selected())
        return self.state == "idle" and 1 <= n <= self.g.run.hand_size and self.g.run.hand_ins > 0

    def can_discard(self):
        n = len(self.selected())
        return self.state == "idle" and 1 <= n <= self.g.run.hand_size and self.g.run.discards > 0

    # ------------------------------------------------------------ events
    def handle_event(self, e):
        g = self.g
        if self.info.open:
            self.info.handle_event(e, g.sfx)
            return
        if self.paused:
            self._pause_event(e)
            return
        if self.btn_info.handle_event(e, g.sfx) or (e.type == pygame.KEYDOWN and e.key == pygame.K_i):
            self.info.toggle()
            return
        if config.DEV_MODE and e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.skip_dot.collidepoint(e.pos):
            g.skip_to_endgame()
            return
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.paused = True
            return
        if self.state == "scoring":
            if e.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                self.speed = max(4.0, self.g.game_speed * 2)
            return
        if self.state != "idle":
            return
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i in range(len(self.sprites) - 1, -1, -1):
                if self.sprites[i].delay <= 0 and self.sprites[i].hit_rect().collidepoint(e.pos):
                    self.toggle(i)
                    break
        if self.btn_play.handle_event(e, g.sfx) and self.can_play():
            self.do_play()
        if self.btn_disc.handle_event(e, g.sfx) and self.can_discard():
            self.do_discard()
        if e.type == pygame.KEYDOWN:
            keys = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7]
            if e.key in keys:
                self.toggle(keys.index(e.key))

            elif e.key in (pygame.K_SPACE, pygame.K_RETURN):
                self.do_play() if self.can_play() else g.sfx.play("error")
            elif e.key == pygame.K_d:
                self.do_discard() if self.can_discard() else g.sfx.play("error")

    def _pause_event(self, e):
        g = self.g
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.paused = False
            return
        for k, b in self.pause_btns.items():
            if b.handle_event(e, g.sfx):
                if k == "resume":
                    self.paused = False
                elif k == "vol-":
                    g.sfx.change_volume(-0.1)
                elif k == "vol+":
                    g.sfx.change_volume(0.1)
                elif k == "mute":
                    g.sfx.toggle_mute()
                elif k == "shake":
                    config.SHAKE = not config.SHAKE
                elif k == "title":
                    g.scenes.goto("title")

    # ------------------------------------------------------------ actions
    def do_discard(self):
        g = self.g
        self.clear_board()
        idxs = self.selected()
        for i in idxs:
            s = self.sprites[i]
            s.mode, s.selected = "out", False
            s.tx, s.ty = L.DISCARD_POS
            s.spin = random.choice([-1, 1]) * random.uniform(500, 900)
            self.fx.append(s)
            g.particles.burst(s.x, s.y, 8, [s.color], 200, life=(0.3, 0.6))
        self.sprites = [s for s in self.sprites if s.mode == "hand"]
        g.deck.remove(idxs)
        g.run.discards -= 1
        g.run.discards_used += 1
        g.sfx.play("whoosh")
        self.deal(g.deck.refill(), 0.12)

    def do_play(self):
        g, run = self.g, self.g.run
        idxs = self.selected()
        dice = [self.sprites[i].die for i in idxs]
        bd = self.bd = score_hand(dice, run, held=len(self.sprites) - len(idxs))
        run.hand_ins -= 1
        run.round_combos.add(bd.combo.name)                 # Aeon: a combo scores only once per round
        self.played = [self.sprites[i] for i in idxs]
        self.sprites = [s for s in self.sprites if not s.selected]
        g.deck.remove(idxs)
        n = len(self.played)
        start = L.PLAY_X - (n * (DIE_SIZE + L.PLAY_GAP) - L.PLAY_GAP) / 2 + DIE_SIZE / 2
        for k, s in enumerate(self.played):
            s.selected, s.mode = False, "played"
            s.tx, s.ty = start + k * (DIE_SIZE + L.PLAY_GAP), L.PLAY_CY
            s.scale = 1.22                                   # a soft pop as it glides out of the hand
            g.particles.burst(s.x, s.y, 5, [s.color, (255, 255, 255)], 120, life=(0.25, 0.5), size=(2, 4), grav=0)
        self.layout()
        self.chips, self.floats, self.banner = [], [], None
        self.total_shown = self.total_target = 0.0
        self.show_total = True
        self.state, self.speed = "scoring", self.g.game_speed
        self.final_done = False
        g.sfx.play("whoosh")

        seq = self.seq = Sequence()
        t = 0.35
        for i, step in enumerate(bd.steps):
            if step.kind in PRE_KINDS:                       # face changes happen before the combo is read
                seq.at(t, partial(self.on_step, i, step))
                t += 0.8
        seq.at(t, partial(self.on_combo, bd))
        t += 0.6
        for i, step in enumerate(bd.steps):
            if step.kind not in PRE_KINDS:
                seq.at(t, partial(self.on_step, i, step))
                if step.kind == "faction":
                    t += 2.6 if step.roll == 3 else 1.9                 # leave room for the faction show
                else:
                    t += STEP_GAP[KIND_TIER[step.kind]] if step.kind in CARD_KINDS else 0.4
        fill_dur = min(2.6, 0.9 + 0.2 * len(str(bd.final)))
        seq.at(t + 0.15, partial(self.on_final, fill_dur))
        seq.at(t + 0.15 + fill_dur + 0.9, self.on_finish)

    # ------------------------------------------------------------ scoring animation callbacks
    def on_combo(self, bd):
        g, c = self.g, bd.combo
        self.banner = dict(text=c.name.upper(), rank=c.rank, t=0.0, life=1.9 + (0.4 if c.rank >= 8 else 0))
        g.sfx.play(f"combo{c.rank}")
        g.shake.add(L.COMBO_SHAKE[c.rank])
        for i, s in enumerate(self.played):
            s.dim = i not in bd.used and not s.die.kind      # dice outside the combo do not score
            if s.dim:
                continue
            s.flash = 1.0
            g.particles.burst(s.x, s.y, 6 + c.rank * 2, [s.color, (255, 255, 255)], 160 + c.rank * 30, life=(0.3, 0.8))
        tiers = [CARD_TIER[s.die.kind] for i, s in enumerate(self.played) if s.die.kind and i in bd.used]
        top = max(tiers, default=1)
        if top >= 2:                                         # a Rare / Super Element is part of the combo
            self.banner["sub"] = "SUPER COMBO!" if top == 3 else "RARE COMBO!"
            self.banner["subcol"] = config.NEON_GOLD if top == 3 else (110, 180, 255)
            for s in self.played:
                if s.die.kind and CARD_TIER[s.die.kind] >= 2:
                    g.particles.burst(s.x, s.y, 40 + 30 * top, [s.color, (255, 255, 255), config.NEON_GOLD], 460, life=(0.5, 1.2),
                                      size=(3, 7), grav=100)
            g.flash = max(g.flash, 0.35 * (top - 1))
            g.shake.add(0.35 * top)
        ccol = L.combo_color(c.rank, self.t)
        g.particles.emit(L.PLAY_X, L.PLAY_CY, 0, 0, 0.6, ccol, 10 + 3 * c.rank, "ring")        # shock ring
        if c.rank >= 4:                                      # Three of a Kind and up: the screen kicks
            g.punch(0.25 + 0.08 * c.rank, ccol, 0.4 + 0.08 * c.rank, 0.15 * (c.rank - 3))
            g.particles.burst(640, 240, 20 * c.rank, [ccol, (255, 255, 255), config.NEON_GOLD], 300 + 60 * c.rank, "star",
                              (0.5, 1.2), (3, 7), 120)
        if c.rank >= 6:                                      # Full House and up
            g.hitstop = max(g.hitstop, 0.04 + 0.02 * (c.rank - 6))
            g.particles.confetti([config.NEON_GOLD, config.NEON_PINK, config.NEON_CYAN, ccol], 40 + c.rank * 10)
        if c.rank >= 7:                                      # Four / Five of a Kind: fireworks
            for k in range(2 * (c.rank - 6)):
                self.fireworks.append(Firework(random.uniform(160, 1120), random.uniform(90, 260),
                                               [ccol, config.NEON_GOLD, config.NEON_PINK, config.NEON_CYAN],
                                               g.particles, k * 0.12, c.rank == 8))

    def on_step(self, i, step):
        g = self.g
        self.chips.append(dict(label=step.label, color=KIND_COLOR[step.kind], t=0.0))
        if step.kind not in PRE_KINDS:
            self.total_target = float(step.value) if step.value < 10 ** 300 else 1e300
        self.pop = 1.0
        self.wb.nudge(0.22)
        g.sfx.play(f"tick{min(i, 11)}")
        if step.kind in CARD_KINDS:
            s = self.played[step.die_index]
            col = s.color
            tier = KIND_TIER[step.kind]
            s.scale = 1.35 if tier == 1 else 1.6
            s.flash = 0.7 if tier == 1 else 1.0
            bad = step.mult_text == "SHATTER" or step.mult_text.startswith("-")
            kind = CardType[step.kind.upper()]
            if tier >= 2 and not bad:
                self.tshows.append(TierShow(kind, tier, (s.x, s.y), g.particles))
                g.hitstop = max(g.hitstop, 0.05 if tier == 2 else 0.14)
                g.sfx.play("reveal" if tier == 2 else "win")
            if not bad and step.mult_text not in ("...", "ECHO"):
                fx = ElementFX(kind, tier, (s.x, s.y), g.particles)
                self.efx.append(fx)
                g.sfx.play(fx.sound)
                g.punch((0.15, 0.4, 0.85)[tier - 1], glow.mix(col, (255, 255, 255), .4), (0.3, 0.6, 1.0)[tier - 1],
                        (0.0, 0.3, 0.8)[tier - 1])
            else:
                g.sfx.play("error" if bad else "double")
            if bad:
                g.punch(0.6, (255, 60, 70), 0.5, 0.6)
            if step.mult_text.startswith("x") and not bad:
                self.slam(step.mult_text, col)
            self.floats.append(L.FloatText(s.x, s.y - 80, step.mult_text, (255, 70, 90) if bad else col, 44, 1.4, 50))
            g.particles.burst(s.x, s.y, 16 + 22 * tier, [col, (255, 255, 255)] if not bad else [col, (255, 70, 90)], 300, life=(0.3, 0.9))
            g.shake.add(0.5 if step.mult_text == "SHATTER" else (0.15, 0.4, 0.95)[tier - 1])
            for j, new in step.changes:                    # Grass / Jester rewrite other dice faces
                t = self.played[j]
                t.die, t.flash, t.scale = new, 1.0, 1.4
                g.particles.burst(t.x, t.y, 22, [col, (255, 255, 255)], 260, life=(0.3, 0.8))
        elif step.kind == "faction":                       # 2 or 3 Elements of one faction played together
            self.start_faction_fx(step)
        else:
            for s in self.played:
                s.flash = max(s.flash, 0.5)
            if step.kind == "skill":                       # the combo level multiplier slams in too
                self.slam(step.label.split()[-1], config.NEON_LIME)

    def slam(self, text, col):
        """A giant multiplier crashing onto the hand score."""
        g = self.g
        self.slams.append(Slam(text, col, TOTAL_POS))
        g.sfx.play("slam")
        g.punch(0.2, col, 0.7, 0.2, 0.35)
        g.particles.burst(TOTAL_POS[0] + 150, TOTAL_POS[1] - 34, 26, [col, (255, 255, 255), config.NEON_GOLD], 520, "shard",
                          (0.3, 0.7), (3, 7), 900)

    def start_faction_fx(self, step):
        """The big show when a faction triggers: tinted screen, spinning rays, shock rings, lightning beams between
        the member dice, a huge title and the faction's three emblems."""
        g = self.g
        f = next(x for x in FACTIONS if x.key == step.tag)
        full = step.roll == 3
        col = FACTION_COLOR[f.key]
        members = [s for s in self.played if s.die.kind in f.members]
        self.ffx = dict(t=0.0, life=2.4 if full else 1.75, faction=f, full=full, col=col, members=members,
                        desc=step.label.split("! ", 1)[-1], spark=0.0)
        self.banner = None
        g.hitstop = 0.16 if full else 0.1
        g.punch(1.0 if full else 0.7, glow.mix(col, (255, 255, 255), .45), 1.0, 1.0 if full else 0.6, 1.3 if full else 0.8)
        g.sfx.play("boom")
        for k in range(6 if full else 2):                    # a salvo of fireworks in the faction's colours
            self.fireworks.append(Firework(random.uniform(120, 1160), random.uniform(70, 240),
                                           [col, glow.mix(col, (255, 255, 255), .5), config.NEON_GOLD], g.particles,
                                           0.25 + k * 0.18, full))
        g.sfx.play("reveal")
        g.sfx.play("win" if full else "double")
        colors = [col, glow.mix(col, (255, 255, 255), .5), (255, 255, 255)]
        for s in members:
            s.flash, s.scale = 1.0, 1.6
            g.particles.burst(s.x, s.y, 70 if full else 45, colors, 520, life=(0.5, 1.3), size=(3, 8))
        g.particles.burst(640, 250, 140 if full else 80, colors, 700, life=(0.6, 1.5), size=(3, 9), grav=120)
        g.particles.confetti(colors + [config.NEON_GOLD], 160 if full else 80)

    def update_faction_fx(self, dt):
        fx, g = self.ffx, self.g
        fx["t"] += dt
        t = fx["t"]
        for k, s in enumerate(fx["members"]):                 # member dice bob and glow
            s.scale = 1.25 + 0.12 * math.sin(t * 14 + k)
            if math.sin(t * 12 + k * 2) > 0.7:
                s.flash = max(s.flash, 0.5)
        fx["spark"] += dt
        while fx["spark"] > 0.03:
            fx["spark"] -= 0.03
            a = random.uniform(0, math.tau)
            r = 120 + t * 500
            g.particles.emit(640 + math.cos(a) * r, 250 + math.sin(a) * r * .6, math.cos(a) * 200, math.sin(a) * 120,
                             0.6, random.choice([fx["col"], (255, 255, 255)]), 4)
            if fx["members"]:
                s = random.choice(fx["members"])
                g.particles.emit(s.x + random.uniform(-40, 40), s.y + random.uniform(-40, 40), random.uniform(-60, 60),
                                 random.uniform(-220, -80), 0.7, fx["col"], 5)
        if t >= fx["life"]:
            for s in fx["members"]:
                s.scale = 1.0
            self.ffx = None

    def draw_faction_fx(self, surf):
        fx = self.ffx
        t, life, col, full = fx["t"], fx["life"], fx["col"], fx["full"]
        fade = min(1.0, t / 0.12, (life - t) / 0.35)
        C = (640, 250)
        ov = pygame.Surface((1280, 720), pygame.SRCALPHA)
        ov.fill((*glow.scale(col, .25), int((150 if full else 110) * fade)))
        for i in range(18 if full else 12):                  # spinning rays
            a = t * (1.6 if full else 1.0) + i * math.tau / (18 if full else 12)
            w = 0.07
            pts = [C, (C[0] + math.cos(a - w) * 1100, C[1] + math.sin(a - w) * 1100),
                   (C[0] + math.cos(a + w) * 1100, C[1] + math.sin(a + w) * 1100)]
            pygame.draw.polygon(ov, (*col, int(60 * fade)), pts)
        for k in range(4 if full else 3):                    # shock rings
            rr = (t - k * 0.18) * 1100
            if 10 < rr < 1300:
                pygame.draw.circle(ov, (*glow.mix(col, (255, 255, 255), .4), int(200 * fade * max(0.0, 1 - rr / 1300))),
                                   C, int(rr), 10 if full else 6)
        surf.blit(ov, (0, 0))
        m = fx["members"]                                    # crackling beams between the member dice
        pairs = [(m[i], m[(i + 1) % len(m)]) for i in range(len(m) if len(m) > 2 else 1)] if len(m) > 1 else []
        for a, b in pairs:
            pts = [(a.x, a.y)]
            for k in range(1, 8):
                f = k / 8
                pts.append((a.x + (b.x - a.x) * f + random.uniform(-14, 14), a.y + (b.y - a.y) * f + random.uniform(-14, 14)))
            pts.append((b.x, b.y))
            pygame.draw.lines(surf, col, False, pts, 9 if full else 6)
            pygame.draw.lines(surf, (255, 255, 255), False, pts, 3)
        for s in m:
            s.draw(surf, self.t)
        k = out_back(min(1.0, t / 0.35))                       # title
        size = int((128 if full else 100) * max(0.1, k)) // 2 * 2
        tcol = glow.rainbow(self.t * 3) if full else glow.mix(col, (255, 255, 255), .35 + .3 * math.sin(t * 18))
        glow.draw_glow_text(surf, fx["faction"].name.upper() + "!", size, tcol, (640, 128), "center", fade)
        sub = "FULL FACTION  3/3" if full else "FACTION  2/3"
        glow.draw_glow_text(surf, sub, 26, glow.mix(col, (255, 255, 255), .6), (640, 192), "center", fade, kind="ui")
        glow.draw_glow_text(surf, fx["desc"].upper(), 30, (255, 255, 255), (640, 226), "center", fade, kind="ui")
        played = {s.die.kind for s in m}
        for i, kind in enumerate(fx["faction"].members):     # the three emblems, lit if played
            x, y = 640 + (i - 1) * 110, 430
            on = kind in played
            pop = out_back(min(1.0, max(0.0, (t - 0.15 - i * 0.12) / 0.3)))
            r = int(36 * pop) + (4 if on and full else 0)
            if r <= 2:
                continue
            ccol = CARD_COLOR[kind] if on else (70, 74, 90)
            pygame.draw.circle(surf, (20, 14, 30), (x, y), r + 5)
            pygame.draw.circle(surf, ccol, (x, y), r)
            if on:
                pygame.draw.circle(surf, (255, 255, 255), (x, y), r + 5, 3)
            draw_kind_icon(surf, kind, (x, y), int(r * .6), (255, 248, 230) if on else (120, 124, 140))
            glow.draw_text(surf, kind.value.upper(), 15, ccol if on else (140, 144, 160), (x, y + r + 18), kind="ui")

    def on_final(self, dur):
        g, run, bd = self.g, self.g.run, self.bd
        self.chips.append(dict(label=f"FINAL {L.fmt_num(bd.final)}", color=KIND_COLOR["final"], t=0.0))
        self.total_target = float(bd.final) if bd.final < 10 ** 300 else 1e300
        self.pop = 1.0
        self.final_done = True
        run.round_score += bd.final
        run.record_hand(bd.combo.name, bd.final)
        hi = run.hand_ins
        apply_side(run, bd)
        for txt, col, on in ((f"+${bd.side['money']}", config.NEON_GOLD, bd.side["money"] > 0),
                             ("+1 PLAY", config.NEON_LIME, run.hand_ins > hi),
                             ("-1 DISCARD", (255, 70, 90), bd.side["discards"] < 0),
                             (f"+{bd.side['discards']} DISCARD", config.NEON_LIME, bd.side["discards"] > 0)):
            if on:
                self.floats.append(L.FloatText(640, 470 - 34 * len(self.floats), txt, col, 34, 1.8, 30))
        end = float(run.round_score) if run.round_score < 10 ** 300 else 1e300
        self.fill = dict(t=0.0, dur=dur, start=self.disp_score, end=end, tick=0.0, stream=0.0)
        g.sfx.play("coin")
        g.shake.add(0.45)
        self.wb.surge(1.0 if bd.final >= run.target * 0.25 else 0.7)
        self.splash_bar(60)
        for _ in range(3):
            g.particles.burst(TOTAL_POS[0], TOTAL_POS[1], 14, [config.NEON_GOLD], 320, "coin", (0.6, 1.2), (5, 8), 500)
        self.floats.append(L.FloatText(TOTAL_POS[0], TOTAL_POS[1] - 90, f"+{L.fmt_num(bd.final)}", config.NEON_GOLD, 48, 1.4, 40))
        word, k = hype_word(bd.final, run.target)
        if word:                                           # a big hand: shout it, and light up the sky
            self.hype = dict(word=word, k=k, t=0.0, life=1.8)
            cols = [config.NEON_GOLD, config.NEON_PINK, config.NEON_CYAN, config.NEON_LIME]
            n = {0.25: 2, 0.5: 4, 1.0: 7, 3.0: 12}[k]
            for j in range(n):
                self.fireworks.append(Firework(random.uniform(100, 1180), random.uniform(60, 280), cols, g.particles,
                                               j * 0.11, k >= 1.0))
            g.punch(0.5 + 0.2 * min(k, 2), config.NEON_GOLD, 1.0, 0.4 + 0.3 * min(k, 2), 0.5 + 0.3 * min(k, 2))
            g.sfx.play("win" if k >= 1.0 else "reveal")
            if k >= 1.0:
                g.particles.confetti(cols, int(120 * min(k, 3)))

    def splash_bar(self, n):
        """Water leaping out of the score bar at the wavefront."""
        g = self.g
        tx, ty = self.wb.tip(WATER_RECT)
        cols = [(112, 214, 255), (255, 255, 255), (60, 150, 240), config.NEON_GOLD]
        g.particles.burst(tx, ty, n, cols, 520, life=(0.4, 1.1), size=(2, 6), grav=900, spread=math.radians(150), angle=-math.pi / 2)

    def update_fill(self, dt):
        """Score-bar count-up: eased, with rising ticks, a spark stream from the hand score and sparks at the bar tip."""
        f, g, run = self.fill, self.g, self.g.run
        f["t"] += dt
        x = min(1.0, f["t"] / f["dur"])
        self.disp_score = lerp(f["start"], f["end"], in_out(x) ** 0.85)
        tip = self.wb.tip(WATER_RECT)
        f["tick"] += dt
        if f["tick"] > 0.06 and x < 1:
            f["tick"] = 0.0
            g.sfx.play(f"tick{min(11, int(x * 12))}")
        f["stream"] += dt
        while f["stream"] > 0.02 and x < 1:
            f["stream"] -= 0.02
            life = 0.5
            g.particles.emit(TOTAL_POS[0] + random.uniform(-60, 60), TOTAL_POS[1] + random.uniform(-20, 20),
                             (tip[0] - TOTAL_POS[0]) / life, (tip[1] - TOTAL_POS[1]) / life, life,
                             random.choice([config.NEON_GOLD, config.NEON_PINK, config.NEON_CYAN]), 4)
        if x < 1:
            self.wb.kick = max(self.wb.kick, 0.9)
            for _ in range(2):
                g.particles.emit(tip[0], tip[1] + random.uniform(-20, 20), random.uniform(-140, 140), random.uniform(-380, -120),
                                 0.6, random.choice([(112, 214, 255), (255, 255, 255), config.NEON_GOLD]), 4, "spark", 900)
        else:
            self.disp_score = f["end"]
            self.fill = None
            g.sfx.play("coin")
            self.splash_bar(40)

    def on_finish(self):
        g, run = self.g, self.g.run
        for s in self.played:
            s.mode, s.tx, s.ty = "out", L.DISCARD_POS[0], L.DISCARD_POS[1]
            s.spin = random.choice([-1, 1]) * 500
            self.fx.append(s)
        self.played = []
        outcome = after_hand_in(run)
        if outcome == "CLEARED":
            self.state = "ending"
            g.scenes.goto("round_result")
        elif outcome == "GAME_OVER":
            self.state = "ending"
            g.scenes.goto("game_over")
        else:
            self.state = "idle"
            self.seq = None
            self.clear_board()
            self.deal(g.deck.refill(), 0.1)
            g.sfx.play("deal")

    # ------------------------------------------------------------ update
    def update(self, dt):
        if self.info.open:                         # the game waits while the INFO book is open
            self.info.update(dt)
            return
        if self.paused:
            for b in self.pause_btns.values():
                b.update(dt)
            return
        g, run = self.g, self.g.run
        self.t += dt
        if self.seq:
            self.seq.update(dt * self.speed)
        if self.ffx:
            self.update_faction_fx(dt * min(self.speed, 3.0))
        for ts in self.tshows:
            ts.update(dt * min(self.speed, 3.0))
        self.tshows = [ts for ts in self.tshows if not ts.dead()]
        for fx in self.efx:
            fx.update(dt * min(self.speed, 3.0))
        self.efx = [fx for fx in self.efx if not fx.dead()]
        for fw in self.fireworks:
            fw.update(dt, g.sfx)
        self.fireworks = [fw for fw in self.fireworks if not fw.done]
        self.slams = [sl for sl in self.slams if sl.update(dt)]
        if self.hype:
            self.hype["t"] += dt
            if self.hype["t"] > self.hype["life"]:
                self.hype = None
        idle = self.state == "idle"
        mp = pygame.mouse.get_pos()
        top = None
        if idle:
            for s in reversed(self.sprites):
                if s.delay <= 0 and s.hit_rect().collidepoint(mp):
                    top = s
                    break
        self.hover_sprite = top
        self.sparkle_t += dt
        emit = self.sparkle_t > 0.07
        if emit:
            self.sparkle_t = 0
        hide = run.boss_is("nyxara")
        for s in self.sprites:
            s.hidden = hide and not s.die.kind and s.mode == "hand"
            s.level = run.element_level(s.die.kind) if s.die.kind else 1
        for s in self.played:
            s.hidden = False
        for s in self.sprites + self.played + self.fx:
            s.update(dt)
            s.hover = approach(s.hover, 1.0 if s is top else 0.0, 16, dt)
            if emit and s.selected:
                g.particles.emit(s.x + random.uniform(-40, 40), s.y - 50, random.uniform(-20, 20), -50,
                                 0.6, random.choice([s.color, (255, 255, 255)]), 3)
        self.fx = [s for s in self.fx if not s.dead()]
        for b in self.buttons:
            b.update(dt)
        self.wb.update(dt, self.disp_score / run.target, self.state == "scoring", self.reached)
        self.btn_play.enabled = self.can_play()
        self.btn_disc.enabled = self.can_discard()
        self.floats = [f for f in self.floats if f.update(dt)]
        for c in self.chips:
            c["t"] += dt
        if self.banner:
            self.banner["t"] += dt
            if self.banner["t"] > self.banner["life"]:
                self.banner = None
        self.pop = max(0.0, self.pop - dt * 4)
        self.total_shown = approach(self.total_shown, self.total_target, 10, dt)
        if abs(self.total_shown - self.total_target) < 1:
            self.total_shown = self.total_target
        if self.fill:
            self.update_fill(dt * min(self.speed, 3.0))
        if not self.reached and run.round_score >= run.target and self.disp_score >= run.target - 1:
            self.reached = True
            g.sfx.play("reveal")
            g.particles.burst(640, 46, 60, [config.NEON_GOLD, (255, 255, 255), config.NEON_PINK], 420, life=(0.6, 1.4))
            self.floats.append(L.FloatText(640, 100, "TARGET REACHED!", config.NEON_GOLD, 40, 1.6, 20))

    # ------------------------------------------------------------ drawing
    def draw_top(self, surf):
        run, t = self.g.run, self.t
        n = len(config.ROUND_NAMES)
        draw_pill(surf, (24, 16, 200, 40), f"ROUND {run.round_idx + 1} / {n}", 19)
        # target panel: emblem + round name + progress bar (like the reference "boss" bar)
        panel = pygame.Rect(280, 8, 720, 62)
        draw_panel(surf, panel, config.NAVY_LINE, 235, radius=12)
        em = pygame.Rect(panel.x + 8, panel.y + 8, 46, 46)
        pygame.draw.rect(surf, (60, 34, 30), em, border_radius=8)
        pygame.draw.rect(surf, config.BRONZE, em, 2, border_radius=8)
        pygame.draw.polygon(surf, (196, 84, 52), [(em.x + 6, em.bottom - 8), (em.centerx, em.y + 8), (em.right - 6, em.bottom - 8)])
        pygame.draw.polygon(surf, (250, 200, 90), [(em.centerx - 6, em.y + 15), (em.centerx, em.y + 8), (em.centerx + 6, em.y + 15)])
        size = 32                                             # long boss names shrink to fit the panel
        while size > 16 and glow.render_text(run.round_name, size, config.CREAM).get_width() > panel.w - 110:
            size -= 2
        name = glow.draw_glow_text(surf, run.round_name.upper(), size, config.GOLD if self.reached else config.CREAM,
                                   (panel.x + 66 + (panel.w - 66) // 2, panel.centery), "center")
        if config.DEV_MODE:                                   # dev: a tiny dot after the name skips to the endgame
            dot = (min(name.right + 14, panel.right - 12), panel.centery)
            self.skip_dot = pygame.Rect(0, 0, 18, 18)
            self.skip_dot.center = dot
            hover = self.skip_dot.collidepoint(pygame.mouse.get_pos())
            pygame.draw.circle(surf, config.GOLD if hover else config.MUTED, dot, 4)
        draw_money_pill(surf, 1256, 34, L.fmt_num(run.money), t)

    def draw_banner(self, surf):
        b = self.banner
        if not b:
            return
        k = b["t"]
        sc = lerp(2.0, 1.0, out_cubic(k / 0.22))
        fade = min(1.0, (b["life"] - k) / 0.4)
        col = b.get("color") or L.combo_color(b["rank"], self.t)
        size = int((64 if b["rank"] < 7 else 78) * sc) // 2 * 2
        if b["rank"] < 5:
            glow.draw_glow_text(surf, b["text"], size, col, (640, 240), "center", fade)
        else:                                               # big combos: letters ride a wave
            widths = [glow.render_text(ch, size, col).get_width() for ch in b["text"]]
            x = 640 - sum(widths) / 2
            for i, ch in enumerate(b["text"]):
                y = 240 + math.sin(k * 10 - i * 0.6) * (4 + 2 * (b["rank"] - 4))
                c = glow.rainbow(self.t * 3 + i * .1) if b["rank"] >= 7 else col
                glow.draw_glow_text(surf, ch, size, c, (x + widths[i] / 2, y), "center", fade)
                x += widths[i]
        if b.get("sub"):
            k2 = out_cubic(min(1.0, k / 0.3))
            glow.draw_glow_text(surf, b["sub"], int(34 * (0.6 + 0.4 * k2)) // 2 * 2, glow.mix(b["subcol"], (255, 255, 255), .5 * (0.5 + 0.5 * math.sin(k * 14))),
                                (640, 296 + 10 * (1 - k2)), "center", fade, kind="ui")

    def draw_hype(self, surf):
        """GREAT! / MEGA! / INSANE!! / GODLIKE!!! - wobbling, rainbow for the biggest."""
        h = self.hype
        k = h["t"]
        sc = lerp(2.6, 1.0, out_back(min(1.0, k / 0.3)))
        fade = min(1.0, (h["life"] - k) / 0.4)
        size = int((70 if h["k"] < 1 else 96) * sc) // 2 * 2
        col = glow.rainbow(self.t * 5) if h["k"] >= 1 else config.NEON_GOLD
        word = h["word"]
        widths = [glow.render_text(ch, size, col).get_width() for ch in word]
        x = 640 - sum(widths) / 2
        for i, ch in enumerate(word):                       # every letter bounces on its own
            y = 200 + math.sin(k * 12 + i * 0.8) * 10 * min(2.0, h["k"] + 0.5)
            glow.draw_glow_text(surf, ch, size, col if h["k"] >= 1 else glow.mix(col, (255, 255, 255), .3 * math.sin(k * 20 + i)),
                                (x + widths[i] / 2, y), "center", fade)
            x += widths[i]

    def draw_chips(self, surf):
        x, y, maxx = 150, 392, 1130
        for c in self.chips:
            tw = glow.render_text(c["label"], 15, c["color"]).get_width() + 22
            if x + tw > maxx:
                x, y = 150, y + 28
            pop = min(1.0, c["t"] / 0.15)
            r = pygame.Rect(0, 0, tw, 24 * (0.6 + 0.4 * pop))
            r.topleft = (x, y)
            col = c["color"]
            glow.draw_shadow(surf, r, 12, (0, 3), 90)
            pygame.draw.rect(surf, config.PARCH_TOP, r, border_radius=12)
            pygame.draw.rect(surf, glow.scale(col, .75), r, 2, border_radius=12)
            pygame.draw.circle(surf, col, (r.x + 11, r.centery), 4)
            glow.draw_text(surf, c["label"], 15, config.INK, (r.x + 20, r.centery), "midleft", kind="ui")
            x += tw + 8

    def draw(self, surf):
        run, t = self.g.run, self.t
        self.draw_top(surf)
        pending = None
        if self.state == "scoring" and not self.final_done and self.show_total:
            pending = (run.round_score + self.total_shown) / run.target
        self.wb.draw(surf, WATER_RECT, t, pending, self.reached, f"{L.fmt_num(self.disp_score)} / {L.fmt_num(run.target)}",
                     f"{min(999, int(self.disp_score * 100 / run.target))}%")
        if run.boss:                                       # the boss rule, always in sight
            glow.draw_glow_text(surf, f"BOSS  {run.boss['name'].upper()}:  {run.boss['desc']}", 15, config.RED,
                                (640, 166), "center", kind="ui")
        if self.show_total:
            glow.draw_text(surf, "HAND SCORE", 14, config.MUTED, (TOTAL_POS[0], TOTAL_POS[1] - 52), kind="ui")
            heat = min(1.0, self.total_shown / max(1, run.target))     # the number trembles and burns as it grows
            size = (56 + int(20 * self.pop) + int(16 * heat)) // 2 * 2
            jx = random.uniform(-1, 1) * 6 * heat * (self.state == "scoring")
            jy = random.uniform(-1, 1) * 4 * heat * (self.state == "scoring")
            col = glow.mix(config.GOLD, glow.rainbow(t * 3), heat) if heat > 0.5 else config.GOLD
            glow.draw_glow_text(surf, L.fmt_num(self.total_shown), size, col, (TOTAL_POS[0] + jx, TOTAL_POS[1] + jy), "center", 1.0)
        for sl in self.slams:
            sl.draw(surf)
        for s in self.played:
            s.draw(surf, t)
        for fx in self.efx:
            fx.draw(surf)
        self.draw_chips(surf)
        glow.draw_text(surf, "HIGHEST SCORE PLAY", 13, config.MUTED, (24, 184), "midleft", kind="ui")
        glow.draw_text(surf, L.fmt_num(self.g.run.best_hand[1]), 26, config.GOLD, (24, 208), "midleft")
        if self.g.run.best_hand[1]:
            glow.draw_text(surf, self.g.run.best_hand[0], 13, config.CREAM, (24, 232), "midleft", kind="ui")
        draw_panel(surf, self.tray, config.NAVY_LINE, 200, radius=16)          # the tray the hand rests on
        for s in sorted(self.sprites, key=lambda s: s.hover):
            s.draw(surf, t)
        for s in self.fx:
            s.draw(surf, t)
        hs = getattr(self, "hover_sprite", None)
        if hs and hs.die.kind and hs.roll <= 0 and self.state == "idle":
            draw_tooltip(surf, (hs.x, hs.y - DIE_SIZE / 2 - 34), hs.die.kind, level=self.g.run.element_level(hs.die.kind))
        for ts in self.tshows:
            ts.draw(surf)
        self.draw_banner(surf)
        if self.ffx:
            self.draw_faction_fx(surf)
        self.draw_info(surf)
        self.btn_play.draw(surf, t, "PLAY")
        self.btn_disc.draw(surf, t, "DISCARD")
        base = run.max_hand_ins
        px = self.tray.right + 18
        room = config.SCREEN_W - 16 - px                       # a 7-dice tray leaves little space on the right
        glow.draw_text(surf, "Plays", 15, config.MUTED, (px, 480), "midleft", kind="ui")
        draw_dots(surf, px, 506, run.hand_ins, max(base, run.hand_ins), config.CREAM, max_w=room)
        dbase = run.max_discards
        glow.draw_text(surf, "Discards", 15, config.MUTED, (px, 546), "midleft", kind="ui")
        draw_dots(surf, px, 572, run.discards, max(dbase, run.discards), config.CREAM, max_w=room)
        if self.hype:
            self.draw_hype(surf)
        for f in self.floats:
            f.draw(surf)
        self.btn_info.draw(surf, t)
        if self.paused:
            self.draw_pause(surf)
        if self.info.open:
            self.info.draw(surf, run)

    def draw_info(self, surf):
        g, run = self.g, self.g.run
        bar = pygame.Rect(self.tray.x, 612, self.tray.w, 32)
        draw_panel(surf, bar, config.NAVY_LINE, 225, radius=10)
        idxs = self.selected()
        if self.state == "idle" and idxs:
            if run.boss_is("nyxara") and any(not self.sprites[i].die.kind for i in idxs):
                glow.draw_text(surf, "Nyxara hides your dice - the score is a mystery", 16, config.RED, bar.center, kind="ui")
                return
            combo, pts = preview_score([self.sprites[i].die for i in idxs], run, len(self.sprites) - len(idxs))
            col = L.combo_color(combo.rank, self.t)
            glow.draw_text(surf, combo.name, 20, glow.mix(col, config.CREAM, .3), (bar.x + 16, bar.centery), "midleft")
            need = max(1, run.target - run.round_score)          # the estimate, and how much of the rest it covers
            share = pts / need
            ecol = config.GREEN if share >= 1 else config.GOLD if share >= 1 / max(1, run.hand_ins) else config.CREAM
            glow.draw_text(surf, f"est. {L.fmt_num(pts)}  ({min(999, int(share * 100))}% of what's left)", 16, ecol,
                           (bar.right - 16, bar.centery), "midright", kind="ui")
            if run.discards == 0 and any(self.sprites[i].die.kind is CardType.DEVIL for i in idxs):
                glow.draw_text(surf, "no discards: Devil gives nothing", 13, (240, 110, 96), (bar.centerx - 40, bar.centery), kind="ui")
        elif self.state == "idle":
            glow.draw_text(surf, f"select 1-{run.hand_size} dice   (keys 1-7)      Space = play      D = discard (re-rolls special dice)", 14,
                           config.MUTED, bar.center, kind="ui")
        else:
            glow.draw_text(surf, "scoring...  (click to speed up)", 14, config.MUTED, bar.center, kind="ui")

    def draw_pause(self, surf):
        ov = pygame.Surface((1280, 720), pygame.SRCALPHA)
        ov.fill((6, 14, 28, 200))
        surf.blit(ov, (0, 0))
        draw_panel(surf, (450, 170, 380, 340), config.NAVY_LINE, 245, corners=True)
        glow.draw_glow_text(surf, "PAUSED", 48, config.CREAM, (640, 216))
        for b in self.pause_btns.values():
            b.draw(surf, self.t)
        glow.draw_text(surf, f"sound {int(self.g.sfx.volume * 100)}%  {'(muted)' if self.g.sfx.muted else ''}", 14,
                       config.MUTED, (640, 497), kind="ui")
