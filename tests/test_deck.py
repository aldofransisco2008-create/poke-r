import random

import config
from core.cards import CardType
from core.deck import DeckManager
from core.dice import build_deck


def test_deck_is_four_of_each_value():
    from collections import Counter
    d = build_deck()
    assert len(d) == 24 and Counter(x.value for x in d) == {v: 4 for v in range(1, 7)}


def test_hand_is_five():
    assert config.HAND_SIZE == 5


def test_deal_and_refill_conserve_dice():
    dm = DeckManager(random.Random(1))
    dm.new_round()
    dm.refill()
    assert len(dm.hand) == 5 and len(dm.draw_pile) == 19
    dm.remove([0, 1, 2])
    assert len(dm.hand) == 2 and len(dm.discard_pile) == 3
    dm.refill()
    assert len(dm.hand) == 5
    assert len(dm.hand) + len(dm.draw_pile) + len(dm.discard_pile) == 24


def test_reshuffle_when_pile_empty():
    dm = DeckManager(random.Random(2))
    dm.new_round()
    dm.refill()
    for _ in range(40):
        dm.remove(range(5))
        dm.refill()
        assert len(dm.hand) == 5
        assert len(dm.hand) + len(dm.draw_pile) + len(dm.discard_pile) == 24


def test_special_dice_live_in_hand():
    dm = DeckManager(random.Random(3))
    dm.new_round([CardType.LIGHTNING, CardType.ICE])
    dm.refill()
    kinds = sorted(d.kind.name for d in dm.hand if d.kind)
    assert kinds == ["ICE", "LIGHTNING"] and sum(1 for d in dm.hand if not d.kind) == 3
    # playing everything re-rolls the specials back into the next hand; they never enter the discard pile
    dm.remove(range(5))
    assert all(not d.kind for d in dm.discard_pile) and len(dm.discard_pile) == 3
    dm.refill()
    assert sorted(d.kind.name for d in dm.hand if d.kind) == ["ICE", "LIGHTNING"]
    assert all(1 <= d.value <= 6 for d in dm.hand)


def test_demo_mode_strongly_favours_strong_combos():
    from core.combos import detect_combo

    def strong_share(cheat, n=200):
        rng, hits = random.Random(7), 0
        for _ in range(n):
            dm = DeckManager(rng)
            dm.cheat = cheat
            dm.new_round()
            dm.refill()
            hits += detect_combo(dm.hand).rank >= 5          # straight or better
        return hits / n

    assert strong_share(True) > 0.75                      # no flushes any more: fewer strong combos exist
    assert strong_share(False) < 0.35
