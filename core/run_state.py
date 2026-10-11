import random

import config
from core.cards import SKILL_DEFS, VOUCHER_DEFS


class RunState:
    def __init__(self):
        self.round_idx = 0
        self.money = 0
        self.slots = []                 # Elements (special dice), list[MultiplierCard], left -> right
        self.skills = {}                # skill key -> stacks
        self.vouchers = {}              # voucher key -> level
        self.voucher_bought = {}        # voucher key -> stock number it was last bought from
        self._offer = (None, None)      # (stock number, voucher key on sale in that stock)
        self.round_score = 0
        self.hand_ins = config.BASE_HANDINS
        self.discards = config.BASE_DISCARDS
        self.best_hand = ("-", 0)
        self.total_score = 0
        self.demo = False               # developer demo mode (bigger payouts)
        self.refunds_used = 0
        self.discards_used = 0          # discards spent this round (Phoenix)
        self.round_combos = set()

    # ----------------------------------------------------------- round info
    @property
    def target(self):
        return config.TARGETS[self.round_idx]

    @property
    def round_name(self):
        return config.ROUND_NAMES[self.round_idx]

    @property
    def act_idx(self):
        return self.round_idx // config.ROUNDS_PER_ACT

    @property
    def act_name(self):
        return config.ACTS[self.act_idx]

    @property
    def stage_name(self):
        return "Boss" if self.boss else config.STAGES[self.round_idx % config.ROUNDS_PER_ACT]

    @property
    def is_last_round(self):
        return self.round_idx >= len(config.ROUND_NAMES) - 1

    def stacks(self, key):
        return self.skills.get(key, 0)

    def level(self, key):
        return self.vouchers.get(key, 0)

    # ----------------------------------------------------------- resources (base + vouchers)
    @property
    def hand_size(self):
        return config.HAND_SIZE + self.level("hand_size")

    @property
    def max_hand_ins(self):
        return config.BASE_HANDINS + self.level("plays")

    @property
    def max_discards(self):
        return config.BASE_DISCARDS + self.level("discards")

    def start_round(self):
        self.round_score = 0
        self.refunds_used = 0
        self.discards_used = 0          # discards spent this round (Phoenix)
        self.round_combos = set()           # combos already scored this round (Aeon)
        self.hand_ins = self.max_hand_ins
        self.discards = 0 if self.boss_is("thalassor") else self.max_discards

    # ----------------------------------------------------------- skills
    def combo_level(self, combo_name):
        """Level 1 + one per skill bought for that combo."""
        return 1 + sum(n for k, n in self.skills.items() if SKILL_DEFS[k].combo == combo_name)

    def combo_mult(self, combo_name):
        """Hand-score multiplier of a combo: +20% per level above 1."""
        return 1 + config.COMBO_LEVEL_STEP * (self.combo_level(combo_name) - 1)

    def skill_full(self, key):
        return self.stacks(key) >= config.MAX_SKILL_STACK

    def add_skill(self, key):
        self.skills[key] = min(config.MAX_SKILL_STACK, self.stacks(key) + 1)

    # ----------------------------------------------------------- vouchers
    def voucher_stock(self):
        """Which voucher stock is on sale. Inside the shop round_idx is still the cleared round, so rounds 1-3 share
        stock 0, rounds 4-6 stock 1 ... : the stock is refilled in the shops after rounds 1, 4, 7 ..."""
        return self.round_idx // config.VOUCHER_RESTOCK

    def voucher_offer(self, rng=random):
        """The one voucher of the current stock (picked at random the first time a stock is looked at, then kept).
        None when every voucher is already at its max level."""
        stock = self.voucher_stock()
        if self._offer[0] != stock:
            keys = [k for k in VOUCHER_DEFS if not self.voucher_maxed(k)]
            self._offer = (stock, rng.choice(keys) if keys else None)
        return self._offer[1]

    def voucher_sold(self, key=None):
        """The current stock's voucher was bought already (a new one comes at the next restock)."""
        key = key or self.voucher_offer()
        return self.voucher_bought.get(key) == self.voucher_stock()

    def rounds_to_restock(self):
        return config.VOUCHER_RESTOCK - self.round_idx % config.VOUCHER_RESTOCK

    def voucher_price(self, key):
        return VOUCHER_DEFS[key].price

    def voucher_maxed(self, key):
        return self.level(key) >= VOUCHER_DEFS[key].max_level

    # ----------------------------------------------------------- money
    def interest(self, coins=None):
        """+2 for every 10 coins held, counted up to 40 coins (max +8)."""
        coins = self.money if coins is None else coins
        return min(max(0, coins), self.interest_cap) // config.INTEREST_EVERY * config.INTEREST_STEP

    @property
    def interest_cap(self):
        """Coins that still earn interest (raised by the Bank Vault voucher)."""
        return config.INTEREST_MAX_COINS + config.BANK_COINS * self.level("bank")

    def skill_price(self):
        """Every skill costs the same (lowered by the Coupon voucher)."""
        return max(1, config.SKILL_PRICE - config.COUPON_OFF * self.level("coupon"))

    def leftover_pay(self):
        """Money for every play still unused when the round was cleared."""
        return config.HAND_LEFTOVER_PAY * max(0, self.hand_ins)

    def payout(self):
        """Paid when a round is cleared: reward + unused plays + interest on the coins held right now."""
        total = config.ROUND_REWARD + self.leftover_pay() + self.interest()
        if self.demo:
            return max(total * config.DEMO_PAYOUT_MULT, config.DEMO_PAYOUT_MIN)
        return total

    # ----------------------------------------------------------- elements (special dice)
    @property
    def element_slots(self):
        """One Element slot per die in the hand."""
        return self.hand_size

    def element_card(self, ctype):
        return next((c for c in self.slots if c.type is ctype), None)

    def element_level(self, ctype):
        card = self.element_card(ctype)
        return card.level if card else 1

    # ----------------------------------------------------------- boss
    @property
    def boss(self):
        """The boss of this round (dict from config.BOSSES), or None."""
        if self.round_idx % config.ROUNDS_PER_ACT == config.ROUNDS_PER_ACT - 1:
            return config.BOSSES.get(self.act_idx)
        return None

    def boss_is(self, key):
        return bool(self.boss) and self.boss["key"] == key

    def slots_full(self):
        return len(self.slots) >= self.element_slots

    def add_card(self, card):
        if self.slots_full():
            return False
        self.slots.append(card)
        return True

    def sell_value(self, card):
        return int(card.price * config.SELL_REFUND)

    def sell(self, index):
        card = self.slots.pop(index)
        self.money += self.sell_value(card)
        return card

    def record_hand(self, name, score):
        self.total_score += score
        if score >= self.best_hand[1]:
            self.best_hand = (name, score)
