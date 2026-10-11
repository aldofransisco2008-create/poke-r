"""The 18 Elements of the six newer factions: Clockwork, Plunder, Harmony, Wild, Cosmos, Alchemy."""
from core.cards import CardType as C, MultiplierCard
from core.dice import Die
from core.run_state import RunState
from core.scoring import active_factions, score_hand


class Rng:
    def random(self):
        return 0.999

    def randint(self, a, b):
        return 3


def pair66(*kinds):
    """A 6-6 pair (dice value 12, Pair bonus 40 -> 52) plus one Element die per kind (values 2, 3, 4)."""
    return [Die(6), Die(6)] + [Die(2 + n, k) for n, k in enumerate(kinds)]


def fresh():
    run = RunState()
    run.start_round()
    return run


def bd(dice, run=None, held=0):
    return score_hand(dice, run or fresh(), Rng(), held)


def test_clockwork():
    run = fresh()
    run.hand_ins = 1                                                     # 2 of 3 plays used, this is the last
    assert bd(pair66(C.GEAR), run).final == 52 + 25 * 2
    assert bd(pair66(C.PISTON), run).final == int(52 * 2.5)             # last play: x2.5
    assert bd(pair66(C.PISTON)).final == 52 + 40                        # otherwise +40
    assert bd(pair66(C.CHRONO)).final == int(52 * 2.5)                  # 3 plays left: x(1 + 0.5 * 3)
    two = bd(pair66(C.GEAR, C.CHRONO))
    assert two.side["hand_ins"] == 1 and any(s.kind == "faction" for s in two.steps)


def test_plunder():
    run = fresh()
    run.money = 30
    assert bd(pair66(C.DOUBLOON), run).final == 52 + 60                  # +2 per $1 held
    run.money = 500
    assert bd(pair66(C.DOUBLOON), run).final == 52 + 120                 # capped
    cut = bd(pair66(C.CUTLASS))
    assert cut.final == 24 + 40 and cut.side["money"] == 2              # x2 dice, +$1 per scoring die
    run.money = 5
    kr = bd(pair66(C.KRAKEN), run)
    assert kr.final == 52 * 3 and kr.side["money"] == -5                # pays $5 for x3
    run.money = 4
    assert bd(pair66(C.KRAKEN), run).final == int(52 * 1.3)             # can't pay


def test_harmony():
    mir = bd([Die(1), Die(1), Die(5, C.MIRROR)])                        # 1s flip to 6s
    assert mir.combo.name == "Pair" and mir.dice_points == 12
    assert bd([Die(3), Die(3), Die(2, C.PRISM)]).final == 18 + 40       # odd scoring dice x3
    assert bd([Die(6), Die(6), Die(1), Die(2, C.TAIJI)]).final == int(52 * 1.8)   # 3 different values
    two = bd([Die(6), Die(6), Die(1, C.PRISM), Die(2, C.TAIJI)])
    assert any(s.kind == "faction" and s.mult_text == "BONUS 80" for s in two.steps)     # Pair pays like Two Pair


def test_wild():
    assert bd(pair66(C.WOLF, C.FIRE)).final == 12 + 20 + 40 + 20 * 2    # +20 per Element die played
    assert bd([Die(6), Die(6), Die(2, C.HAWK)]).final == 12 + 24 + 40   # top die x5
    assert bd(pair66(C.DRAGON)).final == int(52 * 1.2 ** 2)             # x1.2 per scoring die
    assert active_factions(pair66(C.WOLF, C.HAWK, C.DRAGON)) == {"wild": 3}


def test_cosmos():
    run = fresh()
    run.round_idx = 4
    assert bd(pair66(C.COMET), run).final == 52 + 15 * 4                # +15 per round cleared
    run.round_score = 1000
    assert bd(pair66(C.AURORA), run).final == 52 + 150                  # 15% of the round score
    assert bd(pair66(C.AURORA)).final == 52 + 60                        # at least +60
    run.skills = {"pair": 3}
    gal = bd(pair66(C.GALAXY), run)
    assert any(s.kind == "galaxy" and s.mult_text == "x1.35" for s in gal.steps)
    lv = bd(pair66(C.COMET, C.GALAXY), run)                             # Cosmos 2: every combo +1 level
    assert any(s.kind == "skill" and "Lv5" in s.label for s in lv.steps)


def test_alchemy():
    sul = bd([Die(1), Die(6), Die(1, C.SULFUR)])                        # all three 1s become 6s
    assert sul.combo.name == "Three of a Kind" and sul.dice_points == 18
    assert bd(pair66(C.MERCURY)).final == 52 + 12 * 2                    # raw dice points x combo rank
    run = fresh()
    run.discards_used = 2
    assert bd(pair66(C.PHOENIX), run).final == int(52 * 2.3)            # x(1.5 + 0.4 per discard used)
    full = bd(pair66(C.SULFUR, C.MERCURY, C.PHOENIX))
    assert full.side["money"] == 3 * 2                                  # +$3 per scoring die


def test_lightning_chains_and_eclipse_counts_owned():
    assert bd(pair66(C.LIGHTNING, C.WOLF)).steps[1].mult_text == "x3"   # 1 other Element die
    run = fresh()
    run.slots = [MultiplierCard(k) for k in (C.ECLIPSE, C.FIRE, C.ICE, C.SUN)]
    assert bd(pair66(C.ECLIPSE), run).final == int(52 * 1.6)


def test_royal():
    assert bd([Die(6), Die(6), Die(1), Die(2, C.KNIGHT)]).final == 52 + 30 * 2        # 2 scoring normal dice
    two = bd([Die(6), Die(6), Die(2, C.QUEEN), Die(3, C.FIRE)])                     # Fire triggers twice
    assert two.final == 12 + 40 + 40 and sum(s.kind == "fire" for s in two.steps) == 2
    king = bd(pair66(C.FIRE, C.KING))                                                # Fire acts 2 levels higher
    assert any(s.kind == "fire" and s.mult_text == f"+{round(20 * 1.21)}" for s in king.steps)
    assert any(s.kind == "king" and s.mult_text == "x1.5" for s in king.steps)
    assert active_factions(pair66(C.KNIGHT, C.QUEEN, C.KING)) == {"royal": 3}
