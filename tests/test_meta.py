"""Vouchers added in the polish pass, the faction-aware shop, and the run save."""
import random

import config
from core import save, shop
from core.cards import FACTION_OF, CardType as C, MultiplierCard
from core.run_state import RunState


def test_bank_coupon_lucky_vouchers():
    run = RunState()
    run.money = 1000
    assert run.interest() == 12
    run.vouchers["bank"] = 2
    assert run.interest() == 3 * (40 + 40) // 10                       # counts 80 coins now: +24
    run.vouchers["coupon"] = 2
    before = run.money
    assert shop.buy_skill(run, "pair") and before - run.money == config.SKILL_PRICE - 6
    run.vouchers["lucky"] = 2
    w = shop.tier_weights(run)
    assert w[1] < 60 and w[2] > 30 and w[3] > 10 and sum(w.values()) == 100


def test_shop_favours_factions_you_own():
    run = RunState()
    run.slots = [MultiplierCard(C.KNIGHT)]
    rng = random.Random(4)
    hits = sum(c in (C.QUEEN, C.KING) for _ in range(400) for c in shop.element_offers(rng, run=run))
    assert hits / 1200 > 0.25                                            # ~1 in 3 offers instead of 2 in 48
    assert all(FACTION_OF[c] for c in shop.element_offers(rng))         # without a run: plain random


def test_save_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(save, "SAVE_PATH", str(tmp_path / "s.json"))
    monkeypatch.setattr(save, "RECORDS_PATH", str(tmp_path / "r.json"))
    run = RunState()
    run.round_idx, run.money = 12, 77
    run.skills, run.vouchers = {"pair": 3}, {"plays": 1}
    run.slots = [MultiplierCard(C.FIRE, level=3), MultiplierCard(C.KING)]
    run.best_hand = ("Full House", 999)
    save.save_run(run)
    back = save.load_run()
    assert (back.round_idx, back.money, back.skills, back.vouchers) == (12, 77, {"pair": 3}, {"plays": 1})
    assert [(c.type, c.level, c.price) for c in back.slots] == [(c.type, c.level, c.price) for c in run.slots]
    assert back.best_hand == ("Full House", 999) and back.max_hand_ins == config.BASE_HANDINS + 1
    save.delete_save()
    assert save.load_run() is None
    rec, new = save.record_run_end(run, won=False)
    assert rec["best_round"] == 12 and rec["runs"] == 1 and set(new) == {"round", "hand"}
    rec, new = save.record_run_end(run, won=False)
    assert rec["runs"] == 2 and new == []


def test_corrupt_save_is_ignored(tmp_path, monkeypatch):
    p = tmp_path / "s.json"
    p.write_text("{not json")
    monkeypatch.setattr(save, "SAVE_PATH", str(p))
    assert save.load_run() is None
