import random

import pygame

import config
from core import shop
from core.cards import (CARD_COLOR, CARD_DESC, CARD_LONG, CARD_TIER, FACTION_OF, TIER_COLOR, TIER_NAME, MultiplierCard, SKILL_DEFS,
                        VOUCHER_DEFS)
from effects import glow
from effects.tween import approach, out_cubic
from scenes.base import Scene
from ui import layout as L
from ui.card_view import (CARD_H, CARD_W, SKILL_COLOR, SlotBar, draw_element_offer, draw_skill_tile, draw_tooltip,
                          draw_voucher_tile, faction_lines, wrap_lines)
from ui.info_overlay import InfoOverlay
from ui.widgets import GlowButton, draw_money_pill, draw_panel

ELEMENT_RECTS = [pygame.Rect(55 + i * 135, 152, CARD_W, CARD_H) for i in range(config.ELEMENT_OFFERS)]
SKILL_RECTS = [pygame.Rect(486 + i * 150, 140, 144, 240) for i in range(config.SKILL_OFFERS)]
VOUCHER_RECT = pygame.Rect(880, 428, 356, 68)


class ShopScene(Scene):
    music = "game"
    """No gacha: each visit shows 3 random Elements and 5 random skills, plus one random voucher (restocked every 3 rounds).
    Everything is picked and bought directly; each offer can be bought once."""

    def enter(self):
        g = self.g
        run = g.run
        self.t = 0.0
        self.next_idx = run.round_idx + 1         # fixed here: act_next bumps round_idx while the shop still fades out
        payout = self.kw.get("payout", 0)
        self.disp_money = float(run.money)
        run.money += payout
        self.slotbar = SlotBar(run, 24, 548)
        self.elements = [MultiplierCard(c) for c in shop.element_offers(run=run)]
        self.skills = shop.skill_offers()
        self.sold_elements, self.sold_skills = set(), set()
        self.floats = []
        self.toast = ""
        self.toast_t = 0.0
        self.toast_col = config.GOLD
        self.pay_banner = payout
        self.banner_t = 0.0
        self.btn_next = GlowButton((1076, 545, 164, 60), "NEXT", None, 22, style="primary")
        self.btn_sell = GlowButton((900, 615, 340, 44), "", None, 20, style="gold")
        self.btn_refresh = GlowButton((900, 545, 166, 60), "", None, 17)
        self.refreshes = 0                    # refreshes in this shop visit: the price resets every round
        self.btn_info = GlowButton((1010, 26, 112, 40), "INFO", None, 18, style="gold")
        self.info = InfoOverlay()
        if payout:
            g.sfx.play("coin")
            for i in range(28):
                x, y, life = 640 + random.uniform(-60, 60), 300 + random.uniform(-40, 40), random.uniform(0.7, 1.1)
                g.particles.emit(x, y, (1200 - x) / life, (46 - y) / life, life, config.GOLD, 7, "coin")

    # ------------------------------------------------------------ helpers
    def say(self, text, color=config.GOLD):
        self.toast, self.toast_t, self.toast_col = text, 2.0, color

    def bought(self, rect, text, col):
        g = self.g
        g.sfx.play("coin")
        g.particles.burst(rect.centerx, rect.centery, 30, [col, (255, 255, 255)], 300, life=(0.4, 0.9))
        self.floats.append(L.FloatText(rect.centerx, rect.y + 16, text, col, 26, 1.4, 60))

    def refuse(self, text="Not enough money!"):
        self.g.sfx.play("error")
        self.say(text, config.RED)

    def synergy(self, ctype):
        """'ROYAL 2/3' when buying this Element grows a faction you own (None otherwise)."""
        run = self.g.run
        if run.element_card(ctype):
            return None
        f = FACTION_OF[ctype]
        have = sum(1 for m in f.members if run.element_card(m))
        return f"{f.name.upper()} {have + 1}/3" if have else None

    def act_next(self):
        if getattr(self, "leaving", False):          # a double click must not skip a round
            return
        self.leaving = True
        self.g.run.round_idx += 1
        self.g.scenes.goto("round_intro")

    def buy_element(self, i):
        if i in self.sold_elements:
            return
        ctype = self.elements[i].type
        res = shop.buy_element(self.g.run, ctype)
        if res == "full":
            self.refuse("Element slots full - sell one first (or buy Hand +1)")
        elif res == "money":
            self.refuse()
        else:
            self.sold_elements.add(i)
            if res.level > 1:
                self.bought(ELEMENT_RECTS[i], f"{ctype.value} Lv{res.level}!", CARD_COLOR[ctype])
                self.say(f"{ctype.value} levelled up to Lv{res.level}: numbers x{config.ELEMENT_LEVEL_STEP ** (res.level - 1):.2f}",
                         CARD_COLOR[ctype])
            else:
                self.bought(ELEMENT_RECTS[i], f"{ctype.value}!", CARD_COLOR[ctype])
                self.say(f"{ctype.value} Element added to slot {len(self.g.run.slots)}", CARD_COLOR[ctype])

    def buy_skill(self, i):
        if i in self.sold_skills:
            return
        key = self.skills[i]
        if shop.buy_skill(self.g.run, key):
            self.sold_skills.add(i)
            self.bought(SKILL_RECTS[i], f"{SKILL_DEFS[key].name} +1!", SKILL_COLOR[key])
        elif self.g.run.skill_full(key):
            self.refuse("Already at the maximum")
        else:
            self.refuse()

    def buy_voucher(self):
        run = self.g.run
        key = run.voucher_offer()
        if key is None or run.voucher_sold():
            return
        if shop.buy_voucher(run, key):
            self.bought(VOUCHER_RECT, f"{VOUCHER_DEFS[key].name}!", config.VIOLET)
        else:
            self.refuse()

    # ------------------------------------------------------------ events
    def handle_event(self, e):
        g, run = self.g, self.g.run
        if self.info.open:
            self.info.handle_event(e, g.sfx)
            return
        if self.btn_info.handle_event(e, g.sfx) or (e.type == pygame.KEYDOWN and e.key == pygame.K_i):
            self.info.toggle()
            return
        if self.slotbar.handle_event(e) in ("select", "reorder"):
            g.sfx.play("click")
        if self.btn_sell.handle_event(e, g.sfx) and self.slotbar.selected is not None:
            card = run.slots[self.slotbar.selected]
            gain = run.sell_value(card)
            run.sell(self.slotbar.selected)
            self.slotbar.selected = None
            self.say(f"Sold for ${gain}", config.EMBER)
            g.sfx.play("coin")
        if self.btn_next.handle_event(e, g.sfx):
            self.act_next()
        if self.btn_refresh.handle_event(e, g.sfx):
            new = shop.refresh(run, self.refreshes)
            if new is None:
                self.refuse()
            else:
                self.refreshes += 1
                self.elements = [MultiplierCard(c) for c in new[0]]
                self.skills = new[1]
                self.sold_elements, self.sold_skills = set(), set()
                g.sfx.play("deal")
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, r in enumerate(ELEMENT_RECTS):
                if r.collidepoint(e.pos):
                    self.buy_element(i)
            for i, r in enumerate(SKILL_RECTS):
                if r.collidepoint(e.pos):
                    self.buy_skill(i)
            if VOUCHER_RECT.collidepoint(e.pos):
                self.buy_voucher()
        if e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN:
            self.act_next()

    # ------------------------------------------------------------ update
    def update(self, dt):
        run = self.g.run
        self.t += dt
        self.banner_t += dt
        self.disp_money = approach(self.disp_money, run.money, 6, dt)
        if abs(self.disp_money - run.money) < 1:
            self.disp_money = float(run.money)
        self.slotbar.update(dt)
        self.toast_t = max(0.0, self.toast_t - dt)
        self.floats = [f for f in self.floats if f.update(dt)]
        self.btn_sell.visible = self.slotbar.selected is not None
        self.btn_refresh.enabled = run.money >= shop.refresh_price(self.refreshes)
        self.info.update(dt)
        for b in (self.btn_next, self.btn_sell, self.btn_refresh, self.btn_info):
            b.update(dt)

    # ------------------------------------------------------------ draw
    def draw(self, surf):
        run, t = self.g.run, self.t
        glow.draw_glow_text(surf, "SHOP", 64, config.CREAM, (36, 48), "midleft")
        pygame.draw.line(surf, config.BRONZE, (250, 48), (320, 48), 3)
        nxt = config.ROUND_NAMES[self.next_idx]
        glow.draw_text(surf, f"next: {nxt}  -  target {config.TARGETS[self.next_idx]}", 16,
                       config.MUTED, (342, 48), "midleft", kind="ui")
        draw_money_pill(surf, 1250, 46, L.fmt_num(self.disp_money), t)
        self.btn_info.draw(surf, t)
        glow.draw_text(surf, f"interest at next payout: +${run.interest()}   (+${config.INTEREST_STEP} per ${config.INTEREST_EVERY} held, max +${config.INTEREST_STEP * (run.interest_cap // config.INTEREST_EVERY)})", 13,
                       config.GOLD, (1250, 80), "midright", kind="ui")
        mp = pygame.mouse.get_pos()
        self.draw_elements(surf, mp)
        self.draw_skills(surf, mp)
        self.draw_vouchers(surf, mp)
        glow.draw_text(surf, "YOUR ELEMENTS", 16, config.GOLD, (26, 528), "midleft")
        glow.draw_text(surf, f"{len(run.slots)} / {run.element_slots} slots (= your hand size)  -  click one to sell it for half of what you paid", 13,
                       config.MUTED, (200, 529), "midleft", kind="ui")
        self.slotbar.draw(surf, t)
        self.btn_next.draw(surf, t)
        self.btn_refresh.draw(surf, t, f"REFRESH ${shop.refresh_price(self.refreshes)}")
        if self.btn_sell.visible and self.slotbar.selected is not None and self.slotbar.selected < len(run.slots):
            self.btn_sell.draw(surf, t, f"SELL  (+${run.sell_value(run.slots[self.slotbar.selected])})")
        if self.toast_t > 0:
            glow.draw_glow_text(surf, self.toast, 26, self.toast_col, (640, 706), "center", min(1.0, self.toast_t), kind="ui")
        if self.pay_banner and self.banner_t < 1.8:
            k = min(1.0, (1.8 - self.banner_t) / 0.5)
            glow.draw_glow_text(surf, f"PAYOUT  +{L.fmt_num(self.pay_banner)}", 60, config.GOLD,
                                (640, 300 - out_cubic(self.banner_t) * 30), "center", k)
        for f in self.floats:
            f.draw(surf)
        hi = self.slotbar.hover
        if hi is not None and hi < len(run.slots) and self.slotbar.dragging is None:
            draw_tooltip(surf, (self.slotbar.slot_rect(hi).centerx, self.slotbar.slot_rect(hi).y - 10), run.slots[hi].type,
                         level=run.slots[hi].level)
        if self.info.open:
            self.info.draw(surf, run)

    def draw_elements(self, surf, mp):
        run, t = self.g.run, self.t
        draw_panel(surf, (30, 96, 420, 412), config.NAVY_LINE, 235, corners=True)
        glow.draw_text(surf, "ELEMENTS", 20, config.GOLD, (54, 118), "midleft")
        free = run.element_slots - len(run.slots)
        glow.draw_text(surf, f"{free} of {run.element_slots} slots free" if free else "slots full - sell one first",
                       13, config.MUTED, (436, 119), "midright", kind="ui")
        shown = None
        for i, (r, card) in enumerate(zip(ELEMENT_RECTS, self.elements)):
            hov = r.collidepoint(mp) and i not in self.sold_elements
            mine = run.element_card(card.type)
            ok = (mine is not None or not run.slots_full()) and run.money >= card.price
            draw_element_offer(surf, r, card, t, 1.0 if hov else 0.0, ok, card.price, i in self.sold_elements,
                               mine.level if mine else 0, self.synergy(card.type))
            if hov:
                shown = card.type
        pygame.draw.line(surf, config.NAVY_LINE, (50, 358), (430, 358), 2)
        if shown is None:                                   # describe what is on sale; the hovered one in full
            glow.draw_text(surf, "buy an Element you own again to level it up (x1.1)", 13, config.MUTED,
                           (240, 376), kind="ui")
            for k, card in enumerate(self.elements):
                tier = CARD_TIER[card.type]
                glow.draw_text(surf, card.type.value.upper(), 16, CARD_COLOR[card.type], (54, 406 + k * 30), "midleft")
                glow.draw_text(surf, TIER_NAME[tier], 13, glow.mix(TIER_COLOR[tier], config.CREAM, .3), (180, 406 + k * 30),
                               "midleft", kind="ui")
                glow.draw_text(surf, CARD_DESC[card.type], 14, config.CREAM, (270, 406 + k * 30), "midleft", kind="ui")
        else:
            glow.draw_text(surf, shown.value.upper(), 18, CARD_COLOR[shown], (240, 378))
            lines = wrap_lines(CARD_LONG[shown], 15, 370)
            for k, ln in enumerate(lines):
                glow.draw_text(surf, ln, 15, config.CREAM, (240, 404 + k * 21), kind="ui")
            y = 412 + 21 * len(lines)
            for k, ln in enumerate(faction_lines(shown)):
                glow.draw_text(surf, ln, 13, config.GOLD if k == 0 else config.CREAM, (240, y + k * 18), kind="ui")

    def draw_skills(self, surf, mp):
        run = self.g.run
        draw_panel(surf, (470, 96, 780, 296), config.NAVY_LINE, 235, corners=True)
        glow.draw_text(surf, "SKILLS", 20, config.GOLD, (494, 118), "midleft")
        glow.draw_text(surf, f"${run.skill_price()} each  -  each one levels a combo up: +20% score  -  REFRESH re-rolls the offers",
                       13, config.MUTED, (1236, 119), "midright", kind="ui")
        for i, (r, key) in enumerate(zip(SKILL_RECTS, self.skills)):
            sd = SKILL_DEFS[key]
            hov = r.collidepoint(mp) and i not in self.sold_skills
            draw_skill_tile(surf, r, sd, run.combo_level(sd.combo), 1.0 if hov else 0.0, run.money >= run.skill_price(),
                            run.skill_full(key), i in self.sold_skills, run.skill_price())

    def draw_vouchers(self, surf, mp):
        run = self.g.run
        draw_panel(surf, (470, 404, 780, 104), config.NAVY_LINE, 235, corners=True)
        glow.draw_text(surf, "VOUCHER", 20, config.GOLD, (494, 420), "midleft")
        n = run.rounds_to_restock()
        glow.draw_text(surf, f"1 random permanent upgrade - new one in {n} round{'s' if n != 1 else ''}", 13, config.MUTED,
                       (494, 446), "midleft", kind="ui")
        owned = [f"{VOUCHER_DEFS[k].name} Lv{v}" for k, v in run.vouchers.items()]
        glow.draw_text(surf, "owned: " + (", ".join(owned) if owned else "none yet"), 13, config.MUTED, (494, 470),
                       "midleft", kind="ui")
        key = run.voucher_offer()
        if key is None:
            glow.draw_text(surf, "all vouchers maxed", 15, config.MUTED, VOUCHER_RECT.center, kind="ui")
            return
        sold = run.voucher_sold()
        draw_voucher_tile(surf, VOUCHER_RECT, VOUCHER_DEFS[key], run.level(key),
                          1.0 if VOUCHER_RECT.collidepoint(mp) and not sold else 0.0,
                          run.money >= run.voucher_price(key), run.voucher_price(key), run.voucher_maxed(key), sold)
