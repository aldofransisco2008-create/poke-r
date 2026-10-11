from collections import Counter
from dataclasses import dataclass
from itertools import combinations

from config import COMBO_BONUS

FIVE_KIND, FOUR_KIND, FULL_HOUSE, STRAIGHT = "Five of a Kind", "Four of a Kind", "Full House", "Straight"
THREE_KIND, TWO_PAIR, PAIR, HIGH_CARD = "Three of a Kind", "Two Pair", "Pair", "High Card"

RANKS = {
    HIGH_CARD: 1, PAIR: 2, TWO_PAIR: 3, THREE_KIND: 4, STRAIGHT: 5, FULL_HOUSE: 6, FOUR_KIND: 7, FIVE_KIND: 8,
}


COMBO_TEXT = {
    "High Card": "nothing else - only the highest die scores",
    "Pair": "2 dice of the same value",
    "Two Pair": "two different pairs",
    "Three of a Kind": "3 dice of the same value",
    "Straight": "5 in a row (1-5 or 2-6)",
    "Full House": "3 of one value + 2 of another",
    "Four of a Kind": "4 dice of the same value",
    "Five of a Kind": "5 of the same value",
}


@dataclass(frozen=True)
class ComboResult:
    name: str
    rank: int
    bonus: int
    combo_dice: tuple


def _res(name, combo_dice):
    return ComboResult(name, RANKS[name], COMBO_BONUS[name], tuple(combo_dice))


def detect_combo(dice):
    """Best combo of the dice actually played. With more than 5 dice (a bigger Hand) the best 5 of them form the combo
    (highest rank, then the most pips) and the rest are kickers."""
    dice = list(dice)
    if not dice:
        raise ValueError("no dice")
    if len(dice) > 5:
        return max((_detect5(c) for c in combinations(dice, 5)),
                   key=lambda r: (r.rank, sum(d.value for d in r.combo_dice)))
    return _detect5(dice)


def _detect5(dice):
    """Best combo of 1-5 dice. First match wins."""
    dice = list(dice)
    vals = sorted(d.value for d in dice)
    counts = Counter(vals)
    freq = sorted(counts.values(), reverse=True)
    five = len(dice) == 5
    straight = five and vals in ([1, 2, 3, 4, 5], [2, 3, 4, 5, 6])

    def of(pred):
        return [d for d in dice if pred(counts[d.value])]

    if freq[0] == 5:                                   # only with Elements: the deck holds four of each value
        return _res(FIVE_KIND, dice)
    if freq[0] == 4:
        return _res(FOUR_KIND, of(lambda c: c == 4))
    if freq[:2] == [3, 2]:
        return _res(FULL_HOUSE, dice)
    if straight:
        return _res(STRAIGHT, dice)
    if freq[0] == 3:
        return _res(THREE_KIND, of(lambda c: c == 3))
    if freq[:2] == [2, 2]:
        return _res(TWO_PAIR, of(lambda c: c == 2))
    if freq[0] == 2:
        return _res(PAIR, of(lambda c: c == 2))
    return _res(HIGH_CARD, [max(dice, key=lambda d: d.value)])


def best_combo_rank(dice):
    """Highest rank obtainable from any <=5 subset (adding dice never lowers rank)."""
    dice = list(dice)
    if not dice:
        return 0
    if len(dice) <= 5:
        return detect_combo(dice).rank
    return max(detect_combo(c).rank for c in combinations(dice, 5))
