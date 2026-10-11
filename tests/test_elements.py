"""The 48 Elements: 16 per tier, every Element's own effect, and the 16 three-member factions."""
from core.cards import CARD_TIER, FACTION_OF, FACTIONS, CardType as C, MultiplierCard
from core.dice import Die
from core.run_state import RunState
from core.scoring import active_factions, score_hand
import config


class Rng:
    def __init__(self, r=0.999, ints=(3,)):
        self.r, self.ints, self.i = r, list(ints), 0

    def random(self):
        return self.r

    def randint(self, a, b):
        v = self.ints[self.i % len(self.ints)]
        self.i += 1
        return v


def pair66(*kinds):
    """A 6-6 pair (dice value 12, Pair bonus 40 -> 52) plus one Element die per kind (values 2, 3, 4: never in the pair)."""
    return [Die(6), Die(6)] + [Die(2 + n, k) for n, k in enumerate(kinds)]


def final(dice, run=None, rng=None):
    return score_hand(dice, run or RunState(), rng or Rng()).final


def test_48_elements_16_per_tier():
    tiers = [CARD_TIER[c] for c in C]
    assert len(tiers) == 48 and tiers.count(1) == tiers.count(2) == tiers.count(3) == 16


def test_each_faction_is_one_common_one_rare_one_super():
    assert len(FACTIONS) == 16
    for f in FACTIONS:
        assert [CARD_TIER[m] for m in f.members] == [1, 2, 3]
    assert all(c in FACTION_OF for c in C)


def test_common_effects():
    assert final(pair66(C.FIRE)) == 12 + 20 + 40
    assert final(pair66(C.WATER)) == 12 + 6 * 2 + 40                     # +6 per scoring die
    assert final(pair66(C.STONE)) == 52 + 20                             # 6s are not heavy: base only
    assert final([Die(2), Die(2), Die(3, C.STONE)]) == 4 + 40 + 20 + 8 * 8  # +8 per pip below 6
    bd = score_hand(pair66(C.WIND), RunState(), Rng())
    assert bd.final == 52 + 20 and bd.side["discards"] == 1
    star = score_hand([Die(5), Die(6), Die(4, C.STAR)], RunState(), Rng())
    assert star.combo.name == "Pair" and star.dice_points == 12          # the 5 becomes a 6
    assert final(pair66(C.MIDAS)) == int(52 * 0.85)


def test_rare_effects():
    assert final(pair66(C.ICE)) == 24 + 40
    assert final([Die(1), Die(1), Die(5, C.ICE)]) == 8 * 2 + 40           # frozen 1s count as 4s
    run = RunState()
    run.slots = [MultiplierCard(C.MOON), MultiplierCard(C.FIRE), MultiplierCard(C.ICE)]
    assert final(pair66(C.MOON), run) == 52 + 60                          # +20 per owned Element
    assert final([Die(2), Die(2), Die(3, C.METAL)]) == 12 + 40           # scoring dice count as 6s
    assert final([Die(6), Die(6), Die(1), Die(2), Die(3, C.THORN)]) == 52 + 35 * 3   # +35 per kicker
    assert final(pair66(C.WIZARD), rng=Rng(r=0.4)) == 36 + 40              # 50%: x3
    assert final(pair66(C.WIZARD), rng=Rng(r=0.6)) == 18 + 40              # else x1.5
    assert final(pair66(C.GLASS), rng=Rng(r=0.1)) == 0                     # 20% shatter


def test_super_effects():
    assert final(pair66(C.LIGHTNING)) == 24 + 40                          # alone: x2
    assert final(pair66(C.LIGHTNING, C.FIRE, C.STONE)) == 12 * 4 + 20 + 40 + 20     # 3 Elements: x4, then Fire, Stone
    assert final(pair66(C.SUN)) == int(52 * 1.5)
    assert final(pair66(C.CRYSTAL)) == 12 + 40 + 40
    assert final(pair66(C.TSUNAMI)) == 12 * 2 + 40
    assert final(pair66(C.QUAKE)) == 52 + 50 * 2
    storm = score_hand([Die(6), Die(6), Die(4), Die(1, C.STORM)], RunState(), Rng())
    assert storm.dice_points == 17 and storm.final == 17 * 2 + 40
    run = RunState()
    run.slots = [MultiplierCard(C.ECLIPSE), MultiplierCard(C.FIRE)]
    assert final(pair66(C.ECLIPSE), run) == int(52 * 1.3)                # x(1 + 0.15 per owned Element)


def test_face_changers_also_change_element_dice():
    # Grass (5) copies onto the lowest other die - here an Ice die showing 1: it becomes a 5 and still doubles
    bd = score_hand([Die(5, C.GRASS), Die(1, C.ICE), Die(3)], RunState(), Rng())
    assert bd.combo.name == "Pair" and bd.dice_points == 10 and bd.final == 10 * 2 + 40
    # Gaia turns every die, Elements included, into the highest value: Five of a Kind
    gaia = score_hand([Die(6), Die(2), Die(3, C.FIRE), Die(4, C.ICE), Die(1, C.GAIA)], RunState(), Rng())
    assert gaia.combo.name == "Five of a Kind" and gaia.dice_points == 30
    # Star raises the Element dice too
    star = score_hand([Die(5, C.FIRE), Die(6), Die(2, C.STAR)], RunState(), Rng())
    assert star.combo.name == "Pair" and star.dice_points == 12
    # Jester re-rolls Element dice too (all other dice become 4 here)
    jest = score_hand([Die(1, C.STONE), Die(2), Die(3, C.JESTER)], RunState(), Rng(ints=(4,)))
    assert jest.combo.name == "Pair" and jest.dice_points == 8


def test_faction_needs_two_different_members():
    assert active_factions(pair66(C.FIRE)) == {}
    assert active_factions(pair66(C.FIRE, C.SUN)) == {"inferno": 2}
    assert active_factions(pair66(C.FIRE, C.DEVIL, C.SUN)) == {"inferno": 3}


def test_two_and_three_member_bonuses_are_big():
    assert final(pair66(C.FIRE, C.SUN)) == int(int((32 + 40) * 1.5) * 1.5)          # Inferno 2: x1.5
    run = RunState()
    run.start_round()
    assert final(pair66(C.FIRE, C.DEVIL, C.SUN), run) == int((32 + 40 + 80) * 1.5) * 3   # Inferno 3: x3
    assert final(pair66(C.WATER, C.ICE)) == ((12 + 12) * 2) * 3 + 40           # Tide 2: dice x3
    assert final(pair66(C.STONE, C.METAL)) == 12 + 40 + 20 + 40                # Terra 2: combo bonus counts twice
    assert final(pair66(C.WIND, C.GLASS), rng=Rng(r=0.0)) > 0                  # Tempest: Glass never shatters
    grove = score_hand(pair66(C.GRASS, C.THORN), RunState(), Rng())
    assert grove.side["money"] == 10 and grove.final >= 100
    fortune = score_hand(pair66(C.MIDAS, C.HOURGLASS), RunState(), Rng())
    assert fortune.final == 52 and fortune.side["money"] == 10 + 15            # no penalties, +$15
    full = score_hand(pair66(C.MIDAS, C.HOURGLASS, C.CRYSTAL), RunState(), Rng())
    assert full.side["money"]== 10 + 30                                   # Fortune 3: +$30
    chaos = score_hand(pair66(C.JESTER, C.WIZARD), RunState(), Rng(r=0.9, ints=(1,)))
    assert any(s.kind == "wizard" and s.mult_text == "x3" for s in chaos.steps)
    run = RunState()
    run.slots = [MultiplierCard(C.STAR), MultiplierCard(C.MOON), MultiplierCard(C.ECLIPSE)]
    night = score_hand(pair66(C.STAR, C.MOON, C.ECLIPSE), run, Rng())
    assert any(s.kind == "faction" and s.roll == 3 and s.mult_text == "+240" for s in night.steps)


def test_spirit_elements():
    held = score_hand(pair66(C.GHOST), RunState(), Rng(), held=3)
    assert held.final == 52 + 15 * 3                                    # Ghost: +15 per die kept in hand
    assert final([Die(6), Die(6), Die(2, C.FIRE), Die(3, C.ECHO)]) == 12 + 20 + 20 + 40   # Echo copies Fire
    assert final([Die(6), Die(6), Die(2, C.ICE), Die(3, C.ECHO)]) == 12 * 2 * 2 + 40     # Echo copies Ice
    assert final([Die(6, C.ECHO), Die(6)]) == 52                          # nothing to its left: no effect
    run = RunState()
    run.discards = 3
    assert final(pair66(C.VOID), run) == int(52 * 1.9)                  # x(1 + 0.3 per discard left)
    run.discards = 0
    assert final(pair66(C.VOID), run) == 52


def test_spirit_faction():
    run = RunState()
    run.discards = 0
    two = score_hand(pair66(C.GHOST, C.VOID), run, Rng(), held=0)
    assert two.final == 52 + 150 and two.side["discards"] == 1
    three = score_hand(pair66(C.GHOST, C.ECHO, C.VOID), run, Rng(), held=0)
    assert three.final == int((52 + 400) * 1.5) and three.side["discards"] == 2


def test_element_levels_grow_ten_percent_compounding():
    from core.cards import level_scale
    assert [round(level_scale(n), 3) for n in (1, 2, 3, 4)] == [1.0, 1.1, 1.21, 1.331]
    run = RunState()
    run.slots = [MultiplierCard(C.FIRE, level=3), MultiplierCard(C.LIGHTNING, level=2), MultiplierCard(C.GRASS, level=2)]
    assert final(pair66(C.FIRE), run) == 12 + round(20 * 1.21) + 40       # +24
    assert final(pair66(C.LIGHTNING), run) == int(12 * 2.2) + 40          # x2.2
    grass = score_hand([Die(6, C.GRASS), Die(1), Die(6)], run, Rng())
    assert grass.final == int((18 + 120) * 1.1)                           # no number: hand x1.1 per level (Three of a Kind)


def test_play_more_than_five_dice():
    from core.combos import detect_combo
    r = detect_combo([Die(v) for v in (6, 6, 6, 2, 2, 1, 3)])
    assert r.name == "Full House" and sorted(d.value for d in r.combo_dice) == [2, 2, 6, 6, 6]
    bd = score_hand([Die(6), Die(6), Die(1), Die(2), Die(3), Die(4, C.THORN)], RunState(), Rng())
    assert bd.combo.name == "Pair" and bd.final == 52 + 35 * 4            # 4 kickers for Thorn


def test_bosses():
    from core.combos import detect_combo
    run = RunState()
    run.round_idx = 9                                                     # act 2 Guardian -> Morgra
    assert run.boss["key"] == "morgra" and run.stage_name == "Boss"
    assert final([Die(2), Die(2)], run) == 0 + 40                         # petrified 2s score nothing
    run.round_idx = 19                                                    # act 4 -> Thalassor
    run.start_round()
    assert run.discards == 0
    run.round_idx = 29                                                    # act 6 -> Kryovex
    assert final([Die(6), Die(6)], run) == 2 + 40                         # frozen 6s count as 1
    run.round_idx = 49                                                    # act 10 -> Aeon
    run.round_combos = {"Pair"}
    assert final([Die(6), Die(6)], run) == 0 and final([Die(6), Die(6), Die(6)], run) > 0
    run.round_idx = 4                                                     # act 1 Guardian: no boss
    assert run.boss is None and run.stage_name == "Guardian"
    assert [a for a in range(10) if RunState().__class__ and (a * 5 + 4) // 5 in config.BOSSES] == [1, 3, 5, 7, 9]
