"""Run save (continue a run after quitting) and lifetime records, both kept as small JSON files next to the game.

The run is saved at the start of every round, so CONTINUE puts you back at the start of the round you were on.
"""
import json
import os

from core.cards import CardType, MultiplierCard
from core.run_state import RunState

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVE_PATH = os.path.join(ROOT, "savegame.json")
RECORDS_PATH = os.path.join(ROOT, "records.json")
VERSION = 2

_RUN_FIELDS = ("round_idx", "money", "skills", "vouchers", "voucher_bought", "best_hand", "total_score")


def run_to_dict(run):
    d = {k: getattr(run, k) for k in _RUN_FIELDS}
    d["best_hand"] = list(run.best_hand)
    d["offer"] = list(run._offer)
    d["slots"] = [dict(type=c.type.name, level=c.level, price=c.price) for c in run.slots]
    d["version"] = VERSION
    return d


def run_from_dict(d):
    run = RunState()
    for k in _RUN_FIELDS:
        if k in d:
            setattr(run, k, d[k])
    run.best_hand = tuple(d.get("best_hand", run.best_hand))
    run._offer = tuple(d.get("offer", (None, None)))
    run.slots = [MultiplierCard(CardType[s["type"]], s["price"], level=s["level"]) for s in d.get("slots", [])]
    return run


def _write(path, data):
    try:
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f)
        os.replace(tmp, path)                       # never leave a half-written save behind
    except OSError:
        pass


def _read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def save_run(run):
    _write(SAVE_PATH, run_to_dict(run))


def load_run():
    """The saved run, or None when there is none (or it is unreadable / from an older version)."""
    d = _read(SAVE_PATH)
    if not d or d.get("version") != VERSION:
        return None
    try:
        return run_from_dict(d)
    except (KeyError, TypeError, ValueError):
        return None


def has_save():
    return load_run() is not None


def delete_save():
    try:
        os.remove(SAVE_PATH)
    except OSError:
        pass


def load_records():
    d = _read(RECORDS_PATH) or {}
    return dict(best_round=int(d.get("best_round", 0)), best_hand=int(d.get("best_hand", 0)),
                best_hand_name=str(d.get("best_hand_name", "-")), runs=int(d.get("runs", 0)), wins=int(d.get("wins", 0)),
                tutorial_done=bool(d.get("tutorial_done", False)))


def save_records(rec):
    _write(RECORDS_PATH, rec)


def record_run_end(run, won):
    """Fold a finished run into the lifetime records. Returns (records, list of what was beaten)."""
    rec = load_records()
    new = []
    reached = run.round_idx + (1 if won else 0)            # rounds cleared
    if reached > rec["best_round"]:
        rec["best_round"] = reached
        new.append("round")
    if run.best_hand[1] > rec["best_hand"]:
        rec["best_hand"], rec["best_hand_name"] = int(run.best_hand[1]), run.best_hand[0]
        new.append("hand")
    rec["runs"] += 1
    rec["wins"] += 1 if won else 0
    save_records(rec)
    return rec, new
