# Poke'R

A roguelike arcade dice-poker game written in Python with pygame.

Roll dice, build poker combos and collect Elements, special dice with their own powers, to beat 50 increasingly hard rounds and the bosses that guard them.

Made by Aldo Fransisco for the Python Project course at Universitas Pelita Harapan. Designed, programmed and balanced on my own.

## How to play

Each round has a **target score**. You have a few **plays** and **discards** to reach it.

- Select dice from your hand, then **Play** them to score a poker combo, or **Discard** them to draw new ones.
- Combos range from High Card up to **Five of a Kind**, which is only possible with Elements, because the deck holds four of each value.
- Between rounds, spend your money in the **shop** on Elements, skills and vouchers.
- Play two Elements of the same faction in one hand for a faction bonus.
- Clear all **50 rounds across 10 acts** to win. Every second act ends with a boss that changes the rules. One freezes every 6, another takes away your discards.

The full rules are in [docs/RULES.md](docs/RULES.md).

## Features

- **48 Elements** (Fire, Ice, Lightning, Midas, Wizard, Glass and more), in common, rare and super tiers, grouped into factions
- **10 acts and 5 bosses** with their own rule-changing curses
- Step-by-step scoring animation, particles, screen shake and a custom effect for every Element
- Shop economy with escalating prices, skills that level up combos, and vouchers
- Save and continue, lifetime records, collection screen and an in-game rule book
- Visuals drawn entirely in code; sound effects and fallback music synthesized from waveforms

## Run it

Requires Python 3.10 or newer.

```bash
pip install -r requirements.txt
python main.py
```

## Music

My local build uses two background tracks I generated with mytunes.ai. Their terms allow personal, non-commercial use only, so the tracks are not included in this repository. Without them the game plays its own synthesized music loop, so it runs and sounds complete either way.

## Tests and balancing

```bash
pip install pytest
pytest
```

The tests check combo detection, scoring, the deck, the shop and the save system. `tools/simulate.py` plays thousands of automated runs; I used it to tune the round targets and the economy so the difficulty curve stays fair.

## Project structure

| Folder | Contents |
|---|---|
| `core/` | Game logic: dice, deck, combos, scoring, shop, run state, saving |
| `scenes/` | Screens: title, round select, play, shop, results, settings, how-to |
| `ui/` | Dice, cards, overlays and widgets |
| `effects/` | Backgrounds, particles, glow, screen shake, Element animations |
| `audio/` | Sound synthesis and music playback |
| `tests/` | Automated tests (pytest) |
| `tools/` | Balance simulator |
| `docs/` | Rules, design notes and program documentation |
| `config.py` | Every tunable number in one place |

About 7,800 lines of Python.

## Contact

Aldo Fransisco · aldofransisco2008@gmail.com
