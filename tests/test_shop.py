import random

import config
from core import shop
from core.cards import CardType, SKILL_DEFS, VOUCHER_DEFS
from core.deck import DeckManager
from core.run_state import RunState


# ---------------------------------------------------------------- what is on sale
def test_each_shop_offers_3_random_elements_and_5_random_skills():
    rng = random.Random(1)
    seen_e, seen_s = set(), set()
    for _ in range(30):
        e, s = shop.element_offers(rng), shop.skill_offers(rng)
        assert len(e) == 3 == len(set(e)) and len(s) == 5 == len(set(s))
        seen_e.update(e)
        seen_s.update(s)
    assert seen_s == set(SKILL_DEFS)


def test_element_offers_favour_common_tiers():
    from core.cards import CARD_TIER
    rng = random.Random(7)
    counts = {1: 0, 2: 0, 3: 0}
    for _ in range(2000):
        for c in shop.element_offers(rng):
            counts[CARD_TIER[c]] += 1
    assert counts[1] > counts[2] > counts[3] > 0
    assert 0.05 < counts[3] / sum(counts.values()) < 0.16                # super is rare (~10% of rolls)


# ---------------------------------------------------------------- elements (special dice)
def test_element_price_depends_on_its_tier():
    run = RunState()
    run.money = 100
    for ctype, price in ((CardType.FIRE, 10), (CardType.ICE, 15), (CardType.LIGHTNING, 25)):
        before = run.money
        card = shop.buy_element(run, ctype)
        assert card.price == price and run.money == before - price


def test_element_slots_follow_the_hand_size():
    run = RunState()
    run.money = 9
    assert shop.buy_element(run, CardType.FIRE) == "money" and not run.slots
    run.money = 10 ** 4
    for c in (CardType.FIRE, CardType.WATER, CardType.WIND, CardType.STONE, CardType.GRASS):
        shop.buy_element(run, c)
    assert len(run.slots) == 5 and shop.buy_element(run, CardType.STAR) == "full"
    run.vouchers["hand_size"] = 1                                     # Hand +1 -> a 6th slot
    assert run.element_slots == 6 and shop.buy_element(run, CardType.STAR) != "full"


def test_buying_an_owned_element_levels_it_up():
    run = RunState()
    run.money = 100
    shop.buy_element(run, CardType.FIRE)
    card = shop.buy_element(run, CardType.FIRE)
    assert len(run.slots) == 1 and card.level == 2 and run.money == 80 and card.price == 20
    for c in (CardType.WATER, CardType.WIND, CardType.STONE, CardType.GRASS):
        run.slots.append(type(card)(c))
    run.money = 100
    assert shop.buy_element(run, CardType.FIRE).level == 3              # slots full, but a level-up needs no slot


def test_selling_an_element_refunds_half():
    run = RunState()
    run.money = 25
    shop.buy_element(run, CardType.SUN)
    run.sell(0)
    assert run.money == 12 and not run.slots


# ---------------------------------------------------------------- skills
def test_every_skill_levels_a_combo_and_costs_16():
    from core.combos import RANKS
    assert sorted(d.combo for d in SKILL_DEFS.values()) == sorted(RANKS)      # one skill per combo
    assert all(d.price == 16 for d in SKILL_DEFS.values())


def test_refresh_costs_10_then_2_more_each_time():
    assert [shop.refresh_price(n) for n in range(4)] == [10, 12, 14, 16]
    run = RunState()
    run.money = 30
    e, s = shop.refresh(run, 0, random.Random(1))
    assert run.money == 20 and len(e) == 3 and len(s) == 5
    assert shop.refresh(run, 1) and run.money == 8
    assert shop.refresh(run, 2) is None and run.money == 8          # $14 not affordable


# ---------------------------------------------------------------- vouchers
def test_prices():
    assert config.ELEMENT_TIER_PRICE == {1: 10, 2: 15, 3: 25}
    assert (config.SKILL_PRICE, config.VOUCHER_PRICE) == (16, 40)


def test_one_random_voucher_on_sale_from_the_first_shop():
    run = RunState()
    run.money = 500                                   # round_idx 0: the shop after round 1
    key = run.voucher_offer(random.Random(3))
    assert key in VOUCHER_DEFS and run.voucher_offer() == key        # stays the same within a stock
    other = next(k for k in VOUCHER_DEFS if k != key)
    assert not shop.buy_voucher(run, other)                          # only the offered one is for sale
    assert shop.buy_voucher(run) and run.level(key) == 1 and run.money == 500 - 40
    assert run.voucher_sold() and not shop.buy_voucher(run)          # sold out until the restock


def test_one_voucher_per_3_rounds():
    run = RunState()
    run.money = 10 ** 4
    bought = []
    for cleared in range(1, 24):                      # shops after rounds 1 .. 23
        run.round_idx = cleared - 1                   # inside the shop round_idx is still the cleared round
        if shop.buy_voucher(run):
            bought.append(cleared)
    assert bought == [1, 4, 7, 10, 13, 16, 19, 22]            # one voucher per act
    assert sum(run.vouchers.values()) == 8 and all(not (v > VOUCHER_DEFS[k].max_level) for k, v in run.vouchers.items())


def test_maxed_vouchers_are_never_offered():
    run = RunState()
    run.vouchers = {k: v.max_level for k, v in VOUCHER_DEFS.items() if k != "discards"}
    assert run.voucher_offer() == "discards"
    run.vouchers["discards"] = 3
    run.round_idx = 3                                 # next stock
    assert run.voucher_offer() is None and not shop.buy_voucher(run)


def test_rounds_to_restock():
    run = RunState()
    assert [run.rounds_to_restock() for run.round_idx in range(6)] == [3, 2, 1, 3, 2, 1]


def test_hand_voucher_deals_more_dice():
    run = RunState()
    run.vouchers["hand_size"] = 1
    dm = DeckManager(random.Random(5))
    dm.new_round([CardType.FIRE], run.hand_size)
    dm.refill()
    assert len(dm.hand) == 6 and sum(1 for d in dm.hand if d.kind) == 1
    dm.remove(range(6))
    dm.refill()
    assert len(dm.hand) == 6


def test_hand_layout_fits_the_tray():
    from ui import layout as L
    for n in (5, 6, 7):
        xs = [L.hand_x(i, n) for i in range(n)]
        assert xs == sorted(xs) and abs((xs[0] + xs[-1]) / 2 - 640) < 1
        assert xs[-1] + L.DIE_SIZE / 2 - (xs[0] - L.DIE_SIZE / 2) <= L.tray_rect(n).w - 2 * L.TRAY_PAD + 1
