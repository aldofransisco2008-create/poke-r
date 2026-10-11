import random
from dataclasses import dataclass, field

import config
from core.cards import FACTIONS, CardType as C, level_scale
from core.combos import RANKS, detect_combo
from core.dice import Die

PRE_KINDS = ("grass", "jester", "star", "gaia", "mirror", "sulfur")
RANK_NAME = {v: k for k, v in RANKS.items()}        # steps that change dice faces before the combo is read


@dataclass
class Step:
    kind: str               # dice | combo | skill | faction | <special die kind, lowercase>
    label: str
    value: int              # running score AFTER this step
    roll: int = 0
    mult_text: str = ""
    die_index: int = -1     # index of the special die inside the played dice
    changes: list = field(default_factory=list)   # [(index, new Die)] for the face-changing Elements
    tag: str = ""           # faction key for a faction step


@dataclass
class ScoreBreakdown:
    combo: object
    dice_points: int
    steps: list = field(default_factory=list)
    final: int = 0
    side: dict = field(default_factory=lambda: dict(money=0, discards=0, hand_ins=0))
    used: list = field(default_factory=list)      # indices of the played dice that form the combo (only these score)


class _NoLuck:
    """Deterministic 'average' rolls for the live preview."""
    @staticmethod
    def random():
        return 0.999

    @staticmethod
    def randint(a, b):
        return (a + b) // 2


def preview_score(dice, run, held=0):
    bd = score_hand(dice, run, _NoLuck, held)
    return bd.combo, bd.final


def apply_side(run, bd):
    """Costs and rewards of special dice that touch the run (money, discards, hand-ins)."""
    run.money += bd.side["money"]
    run.discards = max(0, run.discards + bd.side["discards"])
    gain = min(bd.side["hand_ins"], config.MAX_REFUNDS_PER_ROUND - run.refunds_used)
    if gain > 0:
        run.hand_ins += gain
        run.refunds_used += gain


def active_factions(dice):
    """{faction key: members played (2 or 3)} for every faction with at least 2 different members in these dice."""
    kinds = {d.kind for d in dice if d.kind}
    out = {}
    for f in FACTIONS:
        n = sum(1 for m in f.members if m in kinds)
        if n >= 2:
            out[f.key] = n
    return out


def effective_kinds(dice):
    """The Element each played die acts as: an Echo acts as the Element just to its left (an Echo after an Echo
    copies what that one copied); anything else acts as itself."""
    eff = []
    for i, d in enumerate(dice):
        eff.append(eff[i - 1] if d.kind is C.ECHO and i > 0 else (None if d.kind is C.ECHO else d.kind))
    return eff


def _x(m):
    """Multiplier text: x3, x3.3, x1.65."""
    return f"x{m:.2f}".rstrip("0").rstrip(".")


def score_hand(dice, run, rng=random, held=0):
    """Pipeline for ONE play.

    A. face changes (Grass, Jester, Star, Gaia)
    B. dice points (only the combo dice - every played die with Storm; Metal makes them 6s; bosses may petrify or
       freeze dice), then the Elements in hand order act on the dice value; Tide faction
    C. + combo bonus (Crystal, Terra add more), + flat Elements and factions, then the hand multipliers
    D. penalties (Midas, Hourglass, Glass shatter = 0), then the combo level (+20% per level)
    Every Element's numbers grow x1.1 per level (`level_scale`); Elements without a number (Grass, Jester, Star, Gaia,
    Hourglass) give x1.1 hand score per level instead. `held` is how many dice stay in the hand (Ghost).
    """
    dice = list(dice)
    work = list(dice)
    fac = active_factions(dice)
    lvl = lambda key: fac.get(key, 0)
    steps, side, penalties = [], dict(money=0, discards=0, hand_ins=0), []
    owned = len(run.slots)
    eff = effective_kinds(dice)
    levels = [run.element_level(d.kind) if d.kind else 1 for d in dice]   # an Echo copies at its own level
    kings = [i for i, k in enumerate(eff) if k is C.KING]
    royal = config.FACTION_NUM["royal"][fac["royal"] - 2][0] if "royal" in fac else 0
    for j, d in enumerate(dice):                          # King (and the Royal faction) raise the other Elements
        if d.kind:
            levels[j] += config.EL["king_levels"] * sum(1 for i in kings if i != j) + royal
    order = []                                            # Queen: the Element to her right triggers twice
    for i, d in enumerate(dice):
        order.append(i)
        if i > 0 and eff[i - 1] is C.QUEEN and eff[i]:
            order.append(i)
    sc = [level_scale(n) for n in levels]
    tag = lambda i, name: f"{name} Lv{levels[i]}" if levels[i] > 1 else name
    boost = []                                            # (index, x) for the level of number-less Elements
    for i, d in enumerate(dice):
        if d.kind is C.ECHO:
            steps.append(Step("echo", f"Echo copies {eff[i].value}" if eff[i] else "Echo: nothing to copy", 0, 0,
                              "ECHO", i))
        if eff[i] is C.QUEEN:
            nxt = eff[i + 1] if i + 1 < len(dice) else None
            steps.append(Step("queen", f"Queen crowns {nxt.value}: it triggers twice" if nxt else "Queen: no Element to crown",
                              0, 0, "CROWN" if nxt else "...", i))

    def faction(key, value, txt):
        f = next(x for x in FACTIONS if x.key == key)
        n = fac[key]
        steps.append(Step("faction", f"{f.name} {n}/3! {f.three if n == 3 else f.two}", value, n, txt, tag=key))

    for i, d in enumerate(dice):                                            # A
        d = Die(d.value, eff[i])
        others = [j for j in range(len(work)) if j != i]      # Element dice can be changed too (they keep their kind)
        me = work[i].value                                    # this die may itself have been changed already
        ch = []
        if d.kind is C.GRASS and others:
            j = min(others, key=lambda j: (work[j].value, j))
            if work[j].value != me:
                ch = [(j, Die(me, work[j].kind))]
            label = f"Grass: die {j + 1} becomes a {me}"
        elif d.kind is C.JESTER:
            ch = [(j, Die(rng.randint(1, 6), work[j].kind)) for j in others]
            label = "Jester: dice re-rolled"
        elif d.kind is C.STAR:
            ch = [(j, Die(work[j].value + 1, work[j].kind)) for j in others if work[j].value < 6]
            label = "Star: other dice +1"
        elif d.kind is C.GAIA and others:
            top = max(x.value for x in work)
            ch = [(j, Die(top, work[j].kind)) for j in range(len(work)) if work[j].value != top]
            label = f"Gaia: every die becomes a {top}"
        elif d.kind is C.MIRROR:
            ch = [(j, Die(7 - work[j].value, work[j].kind)) for j in others]
            label = "Mirror: dice flipped upside down"
        elif d.kind is C.SULFUR:
            ch = [(j, Die(6, work[j].kind)) for j in range(len(work)) if work[j].value == 1]
            label = "Sulfur: every 1 turns into a 6"
        else:
            continue
        if levels[i] > 1:
            boost.append((i, sc[i]))
        if not ch:
            steps.append(Step(d.kind.name.lower(), f"{d.kind.value}: nothing to change", 0, 0, "...", i))
            continue
        for j, new in ch:
            work[j] = new
        steps.append(Step(d.kind.name.lower(), label, 0, 0, d.kind.name if d.kind is not C.STAR else "+1", i, ch))

    combo = detect_combo(work)
    kinds = eff
    storm = C.STORM in kinds
    used = list(range(len(work))) if storm else [i for i, x in enumerate(work) if any(x is c for c in combo.combo_dice)]
    n_used = len(used)
    faces = [work[i].value for i in used]
    if C.METAL in kinds:
        m = max(sc[i] for i, k in enumerate(kinds) if k is C.METAL)
        faces = [6 * m] * n_used
    if C.ICE in kinds:                                    # frozen: low dice count as 4s
        faces = [max(v, config.EL["ice_floor"]) for v in faces]
    if run.boss_is("morgra"):
        faces = [0 if v <= 2 else v for v in faces]
    if run.boss_is("kryovex"):
        faces = [1 if v >= 6 else v for v in faces]
    pts = int(sum(faces))                                 # dice outside the combo do not score (unless Storm)
    label = f"{'All dice' if storm else 'Combo dice'}{' as 6s' if C.METAL in kinds else ''} {pts}"
    val = pts
    steps.append(Step("dice", label, pts))

    E, F = config.EL, config.FACTION_NUM
    pick = lambda key: F[key][lvl(key) - 2]                # the faction's number for 2 or 3 members played
    n_el = sum(1 for d in dice if d.kind)                  # Element dice played
    odd = [f for f, i in zip(faces, used) if work[i].value % 2]
    plays_used = max(0, run.max_hand_ins - run.hand_ins)
    cash = run.money                                       # Kraken pays from this
    for i in order:                                                         # B
        d = dice[i]
        k, x = eff[i], sc[i]
        if k in (C.LIGHTNING, C.ICE, C.STORM, C.TSUNAMI):
            base = {C.LIGHTNING: E["lightning"] + n_el - 1, C.ICE: E["ice"], C.STORM: E["storm"],
                    C.TSUNAMI: max(1, n_used)}[k]
            m = base * x
            val = int(val * m)
            name = {C.STORM: "Storm: every die scores,", C.TSUNAMI: "Tsunami dice", C.ICE: "Ice: frozen dice",
                    C.LIGHTNING: f"Lightning chains {n_el - 1} Elements:"}.get(k, f"{k.value} dice")
            steps.append(Step(k.name.lower(), f"{tag(i, name)} {_x(m)}", val, base, _x(m), i))
        elif k is C.FIRE:
            n = round(E["fire"] * x)
            val += n
            steps.append(Step("fire", f"{tag(i, 'Fire dice')} +{n}", val, n, f"+{n}", i))
        elif k is C.WATER:
            n = round(E["water"] * x * n_used)
            val += n
            steps.append(Step("water", f"{tag(i, 'Water')} +{n} ({n_used} dice)", val, n, f"+{n}", i))
        elif k is C.CUTLASS:
            m = E["cutlass"] * x
            val = int(val * m)
            side["money"] += n_used
            steps.append(Step("cutlass", f"{tag(i, 'Cutlass')} dice {_x(m)}, +${n_used}", val, 2, _x(m), i))
        elif k is C.PRISM:
            m = E["prism"] * x
            n = int(sum(odd) * (m - 1))
            val += n
            steps.append(Step("prism", f"{tag(i, 'Prism')}: {len(odd)} odd dice {_x(m)} (+{n})", val, n, f"+{n}", i))
        elif k is C.HAWK:
            m = E["hawk"] * x
            top = max(faces, default=0)
            n = int(top * (m - 1))
            val += n
            steps.append(Step("hawk", f"{tag(i, 'Hawk')}: top die {_x(m)} (+{n})", val, n, f"+{n}", i))
        elif k is C.WIND:
            side["discards"] += 1
            steps.append(Step("wind", "Wind: +1 discard", val, 0, "+DSC", i))
        elif k is C.GLASS:
            m = E["glass"] * x
            val = int(val * m)
            steps.append(Step("glass", f"{tag(i, 'Glass dice')} {_x(m)}", val, 4, _x(m), i))
            if not lvl("tempest") and rng.random() < E["glass_break"]:
                penalties.append((i, "glass", "Glass SHATTERED! hand = 0", 0.0, "SHATTER"))
        elif k is C.WIZARD:
            if lvl("chaos") or rng.random() < E["wizard_chance"]:
                m = E["wizard_hit"] * x
                steps_label = f"{tag(i, 'Wizard')}: dice {_x(m)}!"
            else:
                m = E["wizard_miss"] * x
                steps_label = f"{tag(i, 'Wizard')}: dice {_x(m)}"
            val = int(val * m)
            steps.append(Step("wizard", steps_label, val, 3, _x(m), i))
        elif k is C.MIDAS:
            money = round(E["midas_money"] * x)
            side["money"] += money
            if lvl("fortune"):
                steps.append(Step("midas", f"{tag(i, 'Midas')}: +${money}", val, 0, f"${money}", i))
            else:
                cut = round((1 - E["midas_mult"]) * 100)
                penalties.append((i, "midas", f"Midas: score -{cut}%  (+${money})", E["midas_mult"], f"-{cut}%"))
        elif k is C.HOURGLASS:
            side["hand_ins"] += 1
            if levels[i] > 1:
                boost.append((i, x))
            if lvl("fortune"):
                steps.append(Step("hourglass", "Hourglass: +1 play (once a round)", val, 0, "+PLAY", i))
            else:
                cut = round((1 - E["hourglass_mult"]) * 100)
                penalties.append((i, "hourglass", f"Hourglass: score -{cut}%  (+1 play, once a round)", E["hourglass_mult"], f"-{cut}%"))
    if lvl("tide"):
        val *= pick("tide")
        faction("tide", val, f"x{pick('tide')}")

    score = val + combo.bonus                                               # C
    steps.append(Step("combo", f"+{combo.name} {combo.bonus}", score))
    left = run.discards                                   # each Devil bonus is paid for with one discard
    low = sum(6 - work[i].value for i in used)            # Stone: pips below 6 on the scoring dice
    pawns = sum(1 for i in used if not dice[i].kind)      # Knight: scoring normal dice
    flat = {C.STONE: ("stone", "Stone", E["stone"] + E["stone_pip"] * low, 1),
            C.WIND: ("wind", "Wind", E["wind_score"], 1),
            C.THORN: ("thorn", "Thorn", E["thorn"], len(dice) - n_used), C.QUAKE: ("quake", "Quake", E["quake"], n_used),
            C.MOON: ("moon", "Moon", E["moon"], owned), C.GHOST: ("ghost", "Ghost", E["ghost"], held),
            C.GEAR: ("gear", "Gear", E["gear"], plays_used), C.WOLF: ("wolf", "Wolf pack", E["wolf"], n_el),
            C.DOUBLOON: ("doubloon", "Doubloon", min(E["doubloon_max"], E["doubloon"] * max(0, run.money)), 1),
            C.COMET: ("comet", "Comet", E["comet"], run.round_idx),
            C.MERCURY: ("mercury", f"Mercury {pts}x{combo.rank}", pts * combo.rank, 1),
            C.KNIGHT: ("knight", "Knight", E["knight"], pawns)}
    last = run.hand_ins <= 1                              # Piston: the last play of the round
    if not last:
        flat[C.PISTON] = ("piston", "Piston", E["piston_flat"], 1)
    for i in order:
        k, x = eff[i], sc[i]
        if k is C.CRYSTAL:
            n = round(combo.bonus * x)
            score += n
            steps.append(Step("crystal", f"{tag(i, 'Crystal')}: +{combo.name} {n} again", score, 2, f"+{n}", i))
        elif k in flat:
            key, name, per, count = flat[k]
            n = round(per * x) * count
            score += n
            more = f" ({count})" if k in (C.THORN, C.QUAKE, C.MOON, C.GHOST, C.GEAR, C.WOLF, C.COMET, C.KNIGHT) else ""
            steps.append(Step(key, f"{tag(i, name)} +{n}{more}", score, per, f"+{n}", i))
        elif k is C.DEVIL:
            n = round(E["devil"] * x)
            if left > 0:
                left -= 1
                score += n
                side["discards"] -= 1
                steps.append(Step("devil", f"{tag(i, 'Devil')} +{n}  (-1 discard)", score, n, f"+{n}", i))
            else:
                steps.append(Step("devil", "Devil: no discards left, no bonus", score, 0, "+0", i))
    if lvl("terra"):
        score += combo.bonus * pick("terra")
        faction("terra", score, f"BONUS x{pick('terra') + 1}")
    if lvl("tempest"):
        score += pick("tempest")
        faction("tempest", score, f"+{pick('tempest')}")
    if lvl("night"):
        score += pick("night") * owned
        faction("night", score, f"+{pick('night') * owned}")
    if lvl("grove"):
        money, gain = pick("grove")
        score += gain
        side["money"] += money
        faction("grove", score, f"+{gain} +${money}")
    if lvl("spirit"):
        disc, gain, mult = pick("spirit")
        side["discards"] += disc
        score = int((score + gain) * mult)
        faction("spirit", score, f"+{gain}")
    if lvl("harmony"):
        up, mult = pick("harmony")
        better = config.COMBO_BONUS[RANK_NAME[min(max(RANKS.values()), combo.rank + up)]]
        score = int((score + better - combo.bonus) * mult)
        faction("harmony", score, f"BONUS {better}")
    if lvl("clockwork"):
        gain, mult = pick("clockwork")
        side["hand_ins"] += 1
        score = int((score + gain) * mult)
        faction("clockwork", score, f"+{gain} +PLAY")
    if lvl("plunder"):
        money, gain, mult = pick("plunder")
        side["money"] += money
        score = int((score + gain) * mult)
        faction("plunder", score, f"+{gain} +${money}")
    if lvl("wild"):
        per, mult = pick("wild")
        score = int((score + per * n_el) * mult)
        faction("wild", score, f"+{per * n_el}")
    if lvl("alchemy"):
        per, gain, mult = pick("alchemy")
        side["money"] += per * n_used
        score = int((score + gain) * mult)
        faction("alchemy", score, f"+{gain} +${per * n_used}")
    if lvl("royal"):
        score = int(score * pick("royal")[1])
        faction("royal", score, f"LV +{pick('royal')[0]}")
    if lvl("cosmos"):
        score = int(score * pick("cosmos")[1])
        faction("cosmos", score, f"LV +{pick('cosmos')[0]}")
    for i in order:
        if eff[i] is C.VOID:
            m = (1 + E["void"] * run.discards) * sc[i]
            score = int(score * m)
            steps.append(Step("void", f"{tag(i, 'Void')} {_x(m)} ({run.discards} discards left)", score, 0, _x(m), i))
        elif eff[i] is C.SUN:
            m = E["sun"] * sc[i]
            score = int(score * m)
            steps.append(Step("sun", f"{tag(i, 'Sun')}: hand {_x(m)}", score, 0, _x(m), i))
        elif eff[i] in HAND_MULTS:
            k = eff[i]
            if k is C.KRAKEN:
                paid = cash >= E["kraken_cost"]
                if paid:
                    cash -= E["kraken_cost"]
                    side["money"] -= E["kraken_cost"]
                base, why = (E["kraken_hit"], f"pays ${E['kraken_cost']}") if paid else (E["kraken_miss"], "no $")
            elif k is C.PISTON:
                if not last:
                    continue
                base, why = E["piston_mult"], "last play"
            else:
                base, why = hand_mult(k, run, E, work, n_used, owned)
            m = base * sc[i]
            score = int(score * m)
            steps.append(Step(k.name.lower(), f"{tag(i, k.value)}: hand {_x(m)} ({why})", score, 0, _x(m), i))
    for i, m in boost:                                    # levelled Elements without a number of their own
        score = int(score * m)
        steps.append(Step(eff[i].name.lower(), f"{tag(i, eff[i].value)}: hand {_x(m)}", score, 0, _x(m), i))
    if lvl("inferno"):
        score = int(score * pick("inferno"))
        faction("inferno", score, f"x{pick('inferno')}")
    if lvl("chaos"):
        score = int(score * pick("chaos"))
        faction("chaos", score, f"x{pick('chaos')}")
    if lvl("fortune"):
        side["money"] += pick("fortune")
        faction("fortune", score, f"+${pick('fortune')}")

    for i, kind, label, f, txt in penalties:                                # D
        score = int(score * f)
        steps.append(Step(kind, label, score, 0, txt, i))
    lv = run.combo_level(combo.name) + (pick("cosmos")[0] if lvl("cosmos") else 0)
    if lv > 1:
        cm = 1 + config.COMBO_LEVEL_STEP * (lv - 1)
        score = int(score * cm)
        steps.append(Step("skill", f"{combo.name} Lv{lv}  x{cm:.1f}", score))

    for i in order:                                       # Aurora comes last: no multiplier may grow it
        if eff[i] is C.AURORA:
            n = round(max(E["aurora_min"], run.round_score * E["aurora"]) * sc[i])
            score += n
            steps.append(Step("aurora", f"{tag(i, 'Aurora')} +{n} (after multipliers)", score, n, f"+{n}", i))

    if run.boss_is("aeon") and combo.name in run.round_combos:             # boss: every combo scores once per round
        score = 0
        steps.append(Step("boss", f"AEON devours the repeated {combo.name}: 0", score, 0, "0"))
    return ScoreBreakdown(combo, pts, steps, int(score), side, used)


HAND_MULTS = (C.ECLIPSE, C.CHRONO, C.KRAKEN, C.TAIJI, C.DRAGON, C.GALAXY, C.PHOENIX, C.PISTON, C.KING)


def hand_mult(k, run, E, work, n_used, owned):
    """(base multiplier, short reason) of the hand-multiplier Elements whose size depends on the situation."""
    if k is C.ECLIPSE:
        return 1 + E["eclipse"] * owned, f"{owned} owned"
    if k is C.CHRONO:
        n = max(1, run.hand_ins)
        return 1 + E["chrono"] * n, f"{n} plays left"
    if k is C.TAIJI:
        n = len({d.value for d in work})
        return 1 + E["taiji"] * (n - 1), f"{n} different"
    if k is C.DRAGON:
        return E["dragon"] ** n_used, f"{n_used} roars"
    if k is C.KING:
        return E["king"], f"others +{E['king_levels']} levels"
    if k is C.GALAXY:
        n = sum(run.skills.values())
        return min(E["galaxy_max"], E["galaxy_base"] + E["galaxy"] * n), f"{n} skills"
    n = run.discards_used                                     # Phoenix
    return E["phoenix_base"] + E["phoenix"] * n, f"{n} discards used"


def after_hand_in(run):
    if run.round_score >= run.target:
        return "CLEARED"
    if run.hand_ins == 0:
        return "GAME_OVER"
    return "CONTINUE"
