"""Balance simulation: a decent (not perfect) bot plays many runs; prints how far it gets.

usage: python tools/simulate.py [runs] [nobuy]
Bot: plays the best-scoring subset of the hand (special dice included); if that will not reach the pace
needed it first discards the dice outside that subset. After each round it shops from the random offers (see
go_shopping). It never uses the active skills (+1 / -1 / reroll), so real players should do a little better.
usage: python tools/simulate.py [runs] [nobuy] [reserve=N]
"""
import os
import random
import sys
from itertools import combinations

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from core.numfmt import fmt_num
from core import shop
from core.cards import CARD_TIER, CardType, element_price
from core.deck import DeckManager
from core.run_state import RunState
from core.scoring import apply_side, preview_score, score_hand


RISKY = {CardType.GLASS, CardType.MIDAS, CardType.HOURGLASS, CardType.JESTER, CardType.MIRROR}   # the bot never buys these
RESERVE = 0          # coins the bot keeps for interest (reserve=N on the command line)


def go_shopping(run):
    """One shop visit: the bot sees 3 random Elements and 5 random skills, like a player. Each offer can be bought once.
    Priority: the voucher on sale, then Elements (highest tier first, never the risky ones), then passive skills, never dipping below
    RESERVE coins so that it keeps earning interest."""
    elements, skills = shop.element_offers(run=run), shop.skill_offers()
    spend = lambda price: run.money - price >= RESERVE
    key = run.voucher_offer()
    if key and spend(run.voucher_price(key)):
        shop.buy_voucher(run, key)
    for ctype in sorted((c for c in elements if c not in RISKY), key=lambda c: -CARD_TIER[c]):     # best tier first
        if spend(element_price(ctype)) and (run.element_card(ctype) or not run.slots_full()):
            shop.buy_element(run, ctype)
    for key in skills:
        if spend(run.skill_price()):
            shop.buy_skill(run, key)


def best_subset(hand, run):
    best, best_s = None, -1
    for n in range(1, len(hand) + 1):
        for c in combinations(range(len(hand)), n):
            s = preview_score([hand[i] for i in c], run, len(hand) - n)[1]
            if s > best_s:
                best, best_s = list(c), s
    return best, best_s


def play_round(run, deck):
    run.start_round()
    deck.new_round([c.type for c in run.slots], run.hand_size)
    deck.refill()
    while True:
        idx, s = best_subset(deck.hand, run)
        need = (run.target - run.round_score) / run.hand_ins
        if run.discards > 0 and s < need and len(idx) < len(deck.hand):
            drop = [i for i in range(len(deck.hand)) if i not in idx]
            deck.remove(drop)
            run.discards -= 1
            run.discards_used += 1
            deck.refill()
            continue
        bd = score_hand([deck.hand[i] for i in idx], run, held=len(deck.hand) - len(idx))
        run.hand_ins -= 1
        run.round_combos.add(bd.combo.name)
        apply_side(run, bd)
        run.round_score += bd.final
        run.record_hand(bd.combo.name, bd.final)
        deck.remove(idx)
        deck.refill()
        if run.round_score >= run.target:
            return True
        if run.hand_ins == 0:
            return False


def main(n=300, buy=True):
    reached = [0] * (len(config.TARGETS) + 1)
    for _ in range(n):
        run, deck = RunState(), DeckManager()
        while True:
            reached[run.round_idx] += 1
            if not play_round(run, deck):
                break
            run.money += run.payout()
            if run.is_last_round:
                reached[-1] += 1
                break
            if buy:
                go_shopping(run)
            run.round_idx += 1
    print(f"{n} runs, buy-bot={buy}")
    for i, name in enumerate(config.ROUND_NAMES):
        print(f"{i + 1:2d} {name:26s} target {fmt_num(config.TARGETS[i]):>9s}  reached {reached[i] / n:6.1%}")
    print(f"VICTORY {reached[-1] / n:.1%}")


if __name__ == "__main__":
    for a in sys.argv[1:]:
        if a.startswith("reserve="):
            RESERVE = int(a.split("=")[1])
    main(int(sys.argv[1]) if sys.argv[1:] and sys.argv[1].isdigit() else 300, "nobuy" not in sys.argv)
