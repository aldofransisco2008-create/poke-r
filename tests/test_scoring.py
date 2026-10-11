import config
from core.cards import CardType as C
from core.dice import Die
from core.run_state import RunState
from core.scoring import after_hand_in, apply_side, preview_score, score_hand


class Rng:
    """random() returns `r`, randint() cycles through `ints`."""

    def __init__(self, r=0.999, ints=(3,)):
        self.r, self.ints, self.i = r, list(ints), 0

    def random(self):
        return self.r

    def randint(self, a, b):
        v = self.ints[self.i % len(self.ints)]
        self.i += 1
        return v


def pair66():
    return [Die(6), Die(6)]


def test_plain_pair():
    assert score_hand(pair66(), RunState(), Rng()).final == 12 + 40


def test_combo_level_adds_20_percent_per_level():
    run = RunState()
    assert run.combo_level("Pair") == 1 and run.combo_mult("Pair") == 1.0
    run.skills["pair"] = 3                                             # level 4 -> x1.6
    assert run.combo_level("Pair") == 4 and abs(run.combo_mult("Pair") - 1.6) < 1e-9
    assert score_hand(pair66(), run, Rng()).final == int(52 * 1.6)
    assert run.combo_level("Two Pair") == 1                            # other combos are not affected


def test_lightning_ice_fire_act_on_dice_value():
    # Pair of 6,6 -> dice value 12 (the 3 is not in the combo) -> lightning x4 (chains 2 more Elements) = 48 -> ice x2 = 96 -> fire +20 = 116, + Pair 40
    dice = [Die(6, C.LIGHTNING), Die(6, C.ICE), Die(3, C.FIRE)]
    bd = score_hand(dice, RunState(), Rng())
    assert bd.combo.name == "Pair" and bd.final == 116 + 40


def test_order_matters_for_fire():
    fire_first = [Die(3, C.FIRE), Die(3, C.LIGHTNING)]     # (6+20)*3
    fire_last = [Die(3, C.LIGHTNING), Die(3, C.FIRE)]      # 6*3+20
    a = score_hand(fire_first, RunState(), Rng()).final
    b = score_hand(fire_last, RunState(), Rng()).final
    assert a == (6 + 20) * 3 + 40 and b == 6 * 3 + 20 + 40


def test_unplayed_special_does_nothing():
    assert score_hand(pair66(), RunState(), Rng()).final == 52


def test_grass_copies_its_value_onto_lowest_normal_die():
    dice = [Die(5, C.GRASS), Die(2), Die(4)]
    bd = score_hand(dice, RunState(), Rng())
    (idx, new), = bd.steps[0].changes
    assert idx == 1 and new == Die(5)
    assert bd.combo.name == "Pair" and bd.dice_points == 5 + 5 and bd.used == [0, 1]


def test_grass_makes_bigger_multiples():
    dice = [Die(3, C.GRASS), Die(1), Die(3), Die(3), Die(5)]
    assert score_hand(dice, RunState(), Rng()).combo.name == "Four of a Kind"   # the 1 becomes a 3


def test_wizard_x3_or_x1_5():
    dice = [Die(6, C.WIZARD), Die(6)]
    assert score_hand(dice, RunState(), Rng(r=0.4)).final == 12 * 3 + 40          # 50%: dice x3
    assert score_hand(dice, RunState(), Rng(r=0.6)).final == 18 + 40              # else x1.5, no curse


def test_glass_x4_or_shatter():
    dice = [Die(6, C.GLASS), Die(6)]
    assert score_hand(dice, RunState(), Rng(r=0.9)).final == 12 * 4 + 40
    assert score_hand(dice, RunState(), Rng(r=0.1)).final == 0                    # 20% shatter


def test_devil_flat_and_costs_a_discard():
    run = RunState()
    run.start_round()
    dice = [Die(6, C.DEVIL), Die(6)]
    bd = score_hand(dice, run, Rng())
    assert bd.final == 52 + 80
    apply_side(run, bd)
    assert run.discards == config.BASE_DISCARDS - 1


def test_midas_and_hourglass_trade_score_for_rewards():
    run = RunState()
    run.start_round()
    bd = score_hand([Die(6, C.MIDAS), Die(6)], run, Rng())
    assert bd.final == int(52 * 0.85)
    apply_side(run, bd)
    assert run.money == 10
    bd = score_hand([Die(6, C.HOURGLASS), Die(6)], run, Rng())
    assert bd.final == int(52 * 0.7)
    hi = run.hand_ins
    apply_side(run, bd)
    assert run.hand_ins == hi + 1


def test_jester_rerolls_other_normal_dice():
    dice = [Die(1, C.JESTER), Die(2), Die(3)]
    bd = score_hand(dice, RunState(), Rng(ints=(6,)))
    assert [x.value for _, x in bd.steps[0].changes] == [6, 6] and bd.combo.name == "Pair"


def test_preview_is_deterministic():
    dice = [Die(4, C.WIZARD), Die(4, C.JESTER), Die(2)]
    assert preview_score(dice, RunState())[1] == preview_score(dice, RunState())[1]


def test_interest_is_three_per_ten_coins_held_up_to_forty():
    run = RunState()
    assert [run.interest(c) for c in (0, 9, 10, 19, 20, 30, 40, 55, 1000)] == [0, 0, 3, 3, 6, 9, 12, 12, 12]


def test_payout_is_reward_plus_unused_plays_plus_interest():
    run = RunState()
    run.start_round()
    run.hand_ins, run.money = 0, 0                      # cleared on the last play, no savings
    assert run.payout() == config.ROUND_REWARD == 15
    run.hand_ins = 2
    assert run.payout() == 15 + 2 * config.HAND_LEFTOVER_PAY
    run.money = 25                                      # interest on the coins held: 25 -> +6
    assert run.payout() == 15 + 6 + 6
    run.round_idx, run.round_score = 20, 10 ** 6        # neither the round nor the score matter
    assert run.payout() == 15 + 6 + 6


def test_devil_without_discards_can_be_played_but_gives_no_bonus():
    run = RunState()
    run.start_round()
    devil = [Die(6, C.DEVIL), Die(6)]
    run.discards = 0
    bd = score_hand(devil, run, Rng())
    assert bd.final == 52 and bd.side["discards"] == 0            # playable, no +80, no cost
    apply_side(run, bd)
    assert run.discards == 0
    run.discards = 1
    two = [Die(6, C.DEVIL), Die(6, C.DEVIL)]
    assert score_hand(two, run, Rng()).final == 52 + 80           # only one discard to pay: one bonus


def test_round_end():
    run = RunState()
    run.round_score = run.target
    assert after_hand_in(run) == "CLEARED"
    run.round_score = run.target - 1
    assert after_hand_in(run) == "CONTINUE"
    run.hand_ins = 0
    assert after_hand_in(run) == "GAME_OVER"
    run.round_score = run.target
    assert after_hand_in(run) == "CLEARED"     # last hand-in reaching the target wins


def test_targets_10_acts_of_5_growing_faster_and_faster():
    t = config.TARGETS
    n = config.ROUNDS_PER_ACT
    assert len(t) == len(config.ROUND_NAMES) == 50 and len(config.ACTS) == 10 and n == 5
    trials = t[::n]
    ratios = [b / a for a, b in zip(trials, trials[1:])]
    assert all(r > 1 for r in ratios) and ratios[-1] > 2.4              # act 10 is a wall
    assert all(b >= a - 0.02 for a, b in zip(ratios, ratios[1:]))        # growth never slows down
    for a in range(10):                                                   # inside an act the stakes rise
        assert all(t[n * a + k] < t[n * a + k + 1] for k in range(n - 1))
    run = RunState()
    run.round_idx = 7
    assert (run.act_name, run.stage_name) == (config.ACTS[1], "Challenge")


def test_resources_with_vouchers():
    run = RunState()
    run.start_round()
    assert (run.hand_ins, run.discards, run.hand_size) == (3, 3, 5)
    run.vouchers.update(plays=2, discards=1, hand_size=1)
    run.start_round()
    assert (run.hand_ins, run.discards, run.hand_size) == (5, 4, 6)
    assert run.element_slots == 6                       # one Element slot per die in the hand


def test_every_skill_costs_the_same_however_often_you_buy_it():
    from core import shop
    run = RunState()
    run.money = 100
    for _ in range(3):
        assert shop.buy_skill(run, "pair")
    assert run.money == 100 - 3 * config.SKILL_PRICE == 52 and run.combo_level("Pair") == 4
    run.money = config.SKILL_PRICE - 1
    assert not shop.buy_skill(run, "two_pair")


def test_combo_level_applies_after_penalties_():
    run = RunState()
    run.skills["pair"] = 1                                             # level 2 -> x1.2
    midas = [Die(6, C.MIDAS), Die(6)]
    assert score_hand(midas, run, Rng()).final == int(int(52 * 0.85) * 1.2)
    assert score_hand(pair66(), run, Rng()).final == int(52 * 1.2)
    assert score_hand(pair66(), run, Rng()).steps[-1].kind == "skill"


def test_only_combo_dice_score():
    kick = [Die(6), Die(6), Die(5), Die(4), Die(1)]
    bd = score_hand(kick, RunState(), Rng())
    assert bd.combo.name == "Pair" and bd.dice_points == 12 and bd.used == [0, 1]
    assert bd.final == 12 + 40
    high = [Die(2), Die(5), Die(3)]
    bd = score_hand(high, RunState(), Rng())
    assert bd.combo.name == "High Card" and bd.dice_points == 5 and bd.final == 5 + 10
    straight = [Die(v) for v in (1, 2, 3, 4, 5)]
    assert score_hand(straight, RunState(), Rng()).dice_points == 15          # all five form the straight


def test_demo_payout_is_bigger_but_bounded():
    run = RunState()
    run.hand_ins = 0
    assert run.payout() == 15
    run.demo = True
    assert run.payout() == 150                                # 15 * 10
    run.money = 40                                            # (15 + 12) * 10
    assert run.payout() == 270
