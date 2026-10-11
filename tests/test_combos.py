from core.combos import detect_combo
from core.dice import Die


def D(v):
    return Die(v)


def mk(vals):
    return [Die(v) for v in vals]


def test_five_kind():
    r = detect_combo(mk([3, 3, 3, 3, 3]))
    assert r.name == "Five of a Kind" and len(r.combo_dice) == 5 and r.bonus == 500


def test_four_kind():
    r = detect_combo(mk([4, 4, 4, 4, 1]))
    assert r.name == "Four of a Kind" and [d.value for d in r.combo_dice] == [4] * 4
    assert detect_combo(mk([6, 6, 6, 6])).name == "Four of a Kind"


def test_full_house():
    r = detect_combo(mk([3, 3, 3, 5, 5]))
    assert r.name == "Full House" and len(r.combo_dice) == 5


def test_no_flush_any_more():
    assert detect_combo(mk([1, 2, 4, 5, 6])).name == "High Card"


def test_straight():
    assert detect_combo(mk([1, 2, 3, 4, 5])).name == "Straight"
    assert detect_combo(mk([6, 5, 4, 3, 2])).name == "Straight"


def test_three_kind():
    r = detect_combo(mk([2, 2, 2, 4, 6]))
    assert r.name == "Three of a Kind" and [d.value for d in r.combo_dice] == [2, 2, 2]
    assert detect_combo(mk([2, 2, 2])).name == "Three of a Kind"


def test_two_pair():
    r = detect_combo(mk([2, 2, 5, 5]))
    assert r.name == "Two Pair" and sorted(d.value for d in r.combo_dice) == [2, 2, 5, 5]
    assert detect_combo(mk([2, 2, 5, 5, 6])).name == "Two Pair"


def test_pair():
    r = detect_combo(mk([6, 6]))
    assert r.name == "Pair" and len(r.combo_dice) == 2
    assert detect_combo(mk([1, 3, 3, 5, 6])).name == "Pair"


def test_high_card_and_small_hands():
    r = detect_combo(mk([4, 5, 6]))
    assert r.name == "High Card" and [d.value for d in r.combo_dice] == [6]
    assert detect_combo(mk([3])).name == "High Card"


def test_fewer_than_five_never_straight():
    assert detect_combo([D(1), D(2), D(3), D(4)]).name == "High Card"
