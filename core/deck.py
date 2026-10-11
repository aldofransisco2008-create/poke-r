import random
from collections import Counter

import config
from core.combos import best_combo_rank
from core.dice import Die, build_deck


class DeckManager:
    """draw_pile / hand / discard_pile with 'smart draw' (biased toward combos).

    Multiplier cards live in the hand as *special dice*: every hand always contains one special die per
    owned card (Lightning / Ice / Fire) and the remaining slots are normal dice from the 24-dice deck.
    A special die that is played or discarded is re-rolled (new face) when the hand is refilled.
    """

    def __init__(self, rng=None):
        self.rng = rng or random
        self.draw_pile, self.hand, self.discard_pile, self.specials = [], [], [], []
        self.hand_size = config.HAND_SIZE
        self.cheat = False              # developer demo mode: strongly favour high combos

    def new_round(self, specials=(), hand_size=config.HAND_SIZE):
        self.hand_size = hand_size
        self.specials = list(specials)[:hand_size]
        self.draw_pile = build_deck()
        self.rng.shuffle(self.draw_pile)
        self.hand, self.discard_pile = [], []

    def _ensure(self, n):
        if len(self.draw_pile) < n:
            self.draw_pile += self.discard_pile
            self.discard_pile = []
            self.rng.shuffle(self.draw_pile)

    def draw(self, n):
        """Smart draw n normal dice into the hand; returns the new dice."""
        self._ensure(n)
        n = min(n, len(self.draw_pile))
        if n <= 0:
            return []
        k = config.DEMO_CANDIDATES if self.cheat else config.SMART_DRAW_CANDIDATES
        cands = [self.rng.sample(self.draw_pile, n) for _ in range(k)]
        if self.cheat:
            weights = [1 + best_combo_rank(self.hand + c) ** config.DEMO_RANK_POWER for c in cands]
        else:
            weights = [1 + best_combo_rank(self.hand + c) * config.SMART_DRAW_BIAS for c in cands]
        pick = self.rng.choices(cands, weights)[0]
        for d in pick:
            self.draw_pile.remove(d)
        self.hand += pick
        return pick

    def missing_specials(self):
        have = Counter(d.kind for d in self.hand if d.kind)
        out = []
        for k in self.specials:
            if have[k] > 0:
                have[k] -= 1
            else:
                out.append(k)
        return out

    def refill(self):
        """Top the hand back up to hand_size: missing special dice first, then smart-drawn normals."""
        new = [Die(self.rng.randint(1, 6), k) for k in self.missing_specials()]
        self.hand += new
        return new + self.draw(self.hand_size - len(self.hand))

    def remove(self, indices):
        """Take hand dice out (played or discarded). Normal dice go to the discard pile; special dice vanish
        (they are re-rolled into the hand by refill)."""
        idx = set(indices)
        out = [self.hand[i] for i in sorted(idx)]
        self.hand = [d for i, d in enumerate(self.hand) if i not in idx]
        self.discard_pile += [d for d in out if not d.kind]
        return out
