# POKE'R — How the program works

This document describes the code: how it is organised, how one frame and one hand-in flow through it, and how to
change or extend it. For the rules of the game see [RULES.md](RULES.md); for why things are the way they are see
[DESIGN.md](DESIGN.md).

## 1. Requirements and running

* Python 3.10+ and **pygame** (developed with `pygame-ce` 2.5 on Python 3.14). Nothing else at runtime.
* `python main.py` starts the game. `pytest` is only needed for the tests.
* No asset files exist. Pictures are drawn with `pygame.draw` and surface operations; sounds are synthesized with the
  `array` and `math` modules; text uses a bitmap font that is defined in code (see section 6), so no system font is needed.
* The window is created with `pygame.SCALED | pygame.RESIZABLE`, so the game always renders at a logical
  **1280×720** and pygame scales it to the window. Mouse positions are already in logical coordinates.

## 2. Architecture at a glance

```
              main.py  ──  pygame init, 60 FPS loop, scene registry
                 │
               game.py  ──  Game: shared context (screen, frame surface, run state, deck, sfx, background,
                 │          particles, shake, scene manager, hit-stop, flash)
                 │
   ┌─────────────┼───────────────────────────────┐
scenes/        ui/                             effects/ + audio/
one class per  widgets, dice & card art,       background, text/shape helpers,
screen         layout helpers                  particles, shake, tweens, synth
   │
   └── all game rules come from ──►  core/   (no pygame window needed, unit-tested)
                                      dice · combos · deck · scoring · cards · run_state · shop
```

**Golden rule: `core/` never imports pygame drawing or scenes.** It can be imported and tested in a plain Python
process (that is exactly what `tests/` and `tools/simulate.py` do). Scenes call into `core/`; `core/` knows nothing about
scenes.

## 3. Directory reference

### 3.1 `core/` — the rules

| File | Contents |
|------|----------|
| `dice.py` | frozen dataclass `Die(value, kind=None)` (`kind` is a `CardType` for special dice; dice have no symbols), `build_deck()` (24 dice, four of each value). |
| `combos.py` | `detect_combo(dice)` → `ComboResult(name, rank, bonus, combo_dice)`; `best_combo_rank(dice)` (best 5-subset, used by smart draw). `combo_dice` holds the *same objects* that were passed in, which scoring relies on (identity matching). |
| `deck.py` | `DeckManager`: `draw_pile`, `hand`, `discard_pile`, `specials`. `new_round(specials)`, `refill()` (special dice first, then smart-drawn normals), `draw(n)` (smart draw), `remove(indices)`. |
| `cards.py` | `CardType` enum (27 Elements), the 9 `FACTIONS` (which also define each Element's tier: `CARD_TIER`, `FACTION_OF`, `element_price`), colour/short-text/long-text tables (`CARD_COLOR`, `CARD_DESC`, `CARD_TAG`, `CARD_LONG`), `MultiplierCard`, `SkillDef`/`SKILL_DEFS`, `VoucherDef`/`VOUCHER_DEFS`. |
| `scoring.py` | `score_hand(dice, run, rng)` → `ScoreBreakdown`; `preview_score`; `apply_side`; `after_hand_in`. The whole pipeline lives here. |
| `run_state.py` | `RunState`: round index, money, owned cards (`slots`), skill stacks, hands/discards left, round score, best hand, prices, payout, skill calculations. |
| `shop.py` | `element_offers` (tier rolled by weight), `skill_offers` (the random picks of a shop visit), `refresh_price`, `refresh`, `buy_element`, `buy_skill`, `buy_voucher`. |

### 3.2 `scenes/` — the screens

`base.py` defines `Scene` (`enter`, `exit`, `handle_event`, `update(dt)`, `draw(surf)`; optional class attribute
`bg_mode = "scene" | "board"`) and `SceneManager` (fade-out → switch → fade-in via `goto(name, **kwargs)`; kwargs are
available to the new scene as `self.kw`).

| Scene | Screen |
|-------|--------|
| `title.py` | Title with painted landscape and menu (Play, Collection, Settings, Quit). |
| `collection.py` | Parchment reference book, tabs *Special dice / Skills / Combos*. |
| `settings.py` | Music and effects sliders, fullscreen, screen shake, mute. |
| `round_select.py` | The 23 rounds as a trail; starts the current round. |
| `round_intro.py` | Banner; **starts the round** (`run.start_round()` and `deck.new_round(...)`). |
| `play.py` | The gameplay screen (see section 5). |
| `round_result.py` | "Round cleared" summary with confetti; computes the payout. |
| `shop_scene.py` | 3 Element offers, 5 skill offers (each bought once), one random voucher (restocked every 3 rounds), owned Elements (sell). Applies the payout on entry. |
| `game_over.py`, `victory.py` | End screens. |

### 3.3 `ui/`

| File | Contents |
|------|----------|
| `layout.py` | Layout constants (`DIE_SIZE`, `hand_x(i)`, deck/discard positions), `fmt_num` (large-number formatting), combo colours and shake strengths, `FloatText`. |
| `widgets.py` | `draw_panel` (navy), `draw_parchment`, `GlowButton` (styles `primary` / `secondary` / `gold`), `draw_progress`, `draw_money_pill`, `draw_coin`, `draw_dots`, `Slider`, `Toggle`. |
| `dice_view.py` | Dice art (`die_art`, cached per die), kind icons (`draw_kind_icon`), and `DieSprite` (animated die: fly-in, bob, hover, selection ring, tumble, flash, dim). |
| `info_overlay.py` | `InfoOverlay`: the in-game INFO book (combo levels, run stats, Elements by faction), used by the play and shop scenes. |
| `card_view.py` | Parchment card art (`render_card`), `SlotBar` (owned cards: select / drag), skills strip, skill offer card, tooltip, `draw_dice_grid` (used by the collection and the shop guide). |

### 3.4 `effects/` and `audio/`

| File | Contents |
|------|----------|
| `retro.py` | The pixel toolkit: two bitmap fonts (5x7 and 3x5), `install()` (see section 6) and `upscale()`. |
| `glow.py` | Despite the name (kept for history) nothing glows: colour helpers, pixel-font text (`draw_text`), **outlined pixel text** (`draw_glow_text`), square dots, blocky shadows, highlight rings. |
| `background.py` | `Background`: two pixel-art backdrops on a 640x360 canvas magnified x2, *scene* (dithered sunset landscape) and *board* (dark diamond lattice). Static layers are cached; clouds, birds, petals, sparkles and motes move each frame. |
| `particles.py` | `ParticleSystem` (max 800): sparks, confetti, coins. |
| `shake.py` | Trauma-based screen shake. |
| `tween.py` | Easing functions, `approach` (frame-rate independent smoothing) and `Sequence` (a timeline of `(time, callback)` events). |
| `audio/synth.py` | `Sfx`: all sound effects and the music loop, generated at start-up. |

### 3.5 Other

* `config.py` — every tunable (section 8).
* `tools/simulate.py` — balance simulator (section 9).
* `tests/` — pytest suite (section 10).

## 4. The main loop

`main.py`:

```
clock.tick(60) → dt (clamped to 50 ms)
for event in pygame.event.get(): game.handle_event(event)
game.update(dt)
game.draw()
pygame.display.flip()
```

`Game.update`: applies **hit-stop** (dt becomes 0 for a moment on big combos), decays the flash and shake, updates the
background, particles and the current scene.

`Game.draw`: background (mode chosen by the scene's `bg_mode`) → scene → particles → cream flash overlay → scene-change
fade → blit to the screen with the shake offset. Everything is drawn onto an off-screen 1280×720 `frame` surface first.

Global keys handled by `Game`: `M` (mute), `F12` (fullscreen), `F11` (`skip_to_endgame`: last 2 rounds with an overpowered build, tuned by the `SKIP_*` constants in `config.py`). Everything else goes to the scene.

## 5. The play scene and one hand-in

`PlayScene` keeps a list of `DieSprite`s that mirrors `deck.hand` **in the same order** (sorting reorders both).
It has three states: `idle` (player input), `scoring` (a timeline is running) and `ending` (leaving for the result or
game-over screen).

```
player presses PLAY
 └─ do_play()
     ├─ bd = score_hand(dice, run)            # all rules; returns a ScoreBreakdown
     ├─ run.hand_ins -= 1; deck.remove(...)   # played dice leave the hand
     ├─ played sprites slide to the play area
     └─ a Sequence is built from bd.steps:
          Grass / Jester face changes  →  combo banner  →  every other step (chips, special die pop, floating text)
          →  on_final: round_score += bd.final, apply_side(run, bd), score bar count-up
          →  on_finish: after_hand_in(run) → next scene, or refill the hand and go back to idle
```

`ScoreBreakdown` is the contract between logic and animation:

* `steps` — ordered `Step(kind, label, value, roll, mult_text, die_index, changes)`. `value` is the running score after
  the step, `die_index` says which played die to animate, `changes` lists `(index, new Die)` for Grass/Jester.
* `combo`, `used` (indices of combo dice; the others are dimmed), `dice_points`, `final`.
* `side` — money / discards / hand-ins to apply (`apply_side` enforces the once-per-round Hourglass limit).

Because the animation is driven entirely by `steps`, adding a new special die needs no changes to the animation code
beyond a colour and a sound.

**Score count-up.** `on_final` starts a `fill` animation: the score bar eases from the old to the new value over
`0.9 + 0.2·digits` seconds (max 2.6 s) with rising tick sounds, a stream of sparks from the hand score to the tip of the
bar and a burst when it lands. Clicking or pressing a key sets `speed = 4` during scoring.

**Random numbers.** `score_hand(dice, run, rng)` takes an `rng` object with `random()` and `randint()`. The game passes
the `random` module; tests pass a fixed stub; the live preview passes an "average luck" stub (`_NoLuck`).

## 6. Rendering details (the pixel look)

The whole game sits on a **2 px grid**: think of a 640x360 picture magnified x2. Three things enforce that.

### 6.1 `effects/retro.py`

* **Bitmap fonts.** `_F5` (5x7 glyphs) and `_F3` (3x5 glyphs) are ASCII tables; text is upper-cased and each glyph pixel becomes
  a solid square. `font_spec(size)` maps the nominal size used throughout the code onto a font and an even scale:
  sizes up to 15 use the 3x5 font at x2, 16-27 the 5x7 font at x2, 28-47 at x4, 48-79 at x6, 80-109 at x8 and larger at x12.
  Rendered text is cached.
* **`install()`** (called once at the top of `main.py`) patches pygame so that existing drawing code becomes pixel art without edits:
  * `pygame.draw.rect(..., border_radius=r)` draws a **stepped, notched corner** instead of a round one (2, 4 or 6 px steps),
  * `pygame.transform.smoothscale` becomes nearest-neighbour,
  * `pygame.transform.rotozoom` becomes a nearest-neighbour scale followed by a hard `rotate`.
  Tests and tools that never draw do not need it.

### 6.2 Dice and cards

`die_art` and `render_card` draw on a **half-size canvas** (52x52 for a die, 50x70 for a card) with plain aliased shapes, then
magnify it x2 with nearest-neighbour: dark outline, flat body colour, light top/left edges, shaded bottom/right edges,
pixel pips and a kind icon for special dice. The card's name and blurb are drawn afterwards with the bitmap
font. `DieSprite` adds a blocky shadow, a square selection ring (gold), a hover ring and a blinking ring on special dice; hover
raises the die instead of scaling it, and spinning happens in 15-degree steps (stop-motion).

### 6.3 Panels, buttons and text

`ui/widgets.py` draws everything from flat colour **bands** (`_bands`) instead of smooth gradients: notched panels with a double
border and studded corners, cream parchment cards, and buttons with a bevel, a bottom slab that shrinks when pressed and a
1-pixel-offset text shadow. `draw_glow_text` draws bitmap text with a solid dark pixel outline (and a chunky drop shadow for
large sizes); `intensity < 1` fades it out.

### 6.4 Backgrounds

`Background` draws each backdrop on a 640x360 surface and magnifies it once. The scene uses dithered colour bands for the sky, pixel
mountains, a striped sea, pine trees and a sun; clouds, birds, petals and sea sparkles are redrawn each frame on the low-res
canvas, so they move in whole logical pixels. The board is a static navy field with a pixel diamond lattice and a darker border,
with slowly rising square motes.

### 6.5 CRT scan-lines

`Game` builds one translucent surface with a dark 2 px line every 4 px and blits it over the finished frame. The Settings screen
has a **Scan lines** toggle (`config.CRT`).

### 6.6 Performance notes

* Everything expensive is cached: dice art, card backgrounds, panel bands, text and glyphs, shadows.
* Headless measurements (dummy video driver) were about 3-8 ms per frame including a full scoring sequence.
* The particle system is capped at 800 particles; particles are square pixel dots, confetti quads and coins.

## 7. Audio

`audio/synth.py` builds every sound at start-up from generated waveforms (sine / square / triangle / saw, noise,
sweeps, simple envelopes) at 22 050 Hz mono 16-bit and wraps them in `pygame.mixer.Sound`. There are click/select/tick
tones whose pitch rises, a chord per combo rank, and sounds for lightning, ice, fire, coins, gacha reveal, win and
game over, plus an 8-bar looping arpeggio for music. `Sfx` exposes `play(name)`, `toggle_mute()`, `set_music_volume`,
`set_sfx_volume`. If no audio device is available the mixer error is caught and the game runs silently.

## 8. Configuration (`config.py`)

| Group | Constants |
|-------|-----------|
| Display / audio | `SCREEN_W/H`, `FPS`, `SHAKE`, `SOUND`, `MASTER_VOLUME`, `MUSIC` |
| Palette | `CREAM`, `INK`, `NAVY`, `RED`, `TEAL`, `GOLD`, `GREEN`, … (old `NEON_*` names are aliases for these) |
| Rounds | `ROUND_NAMES`, `TARGETS` |
| Resources | `HAND_SIZE`, `BASE_HANDINS`, `BASE_DISCARDS`, `MAX_PLAY_DICE`, `MAX_MULTIPLIER_SLOTS`, `MAX_SKILL_STACK`, `MAX_REFUNDS_PER_ROUND` |
| Money | `MONEY_RATE`, `GACHA_PRICE`, `GACHA_PRICE_STEP`, `SKILL_PRICE_STEP`, `REROLL_PRICE`, `SELL_REFUND`, `SKILL_OFFERS`, `GACHA_WEIGHTS` |
| Scoring | `COMBO_BONUS`, `SKILL_COMBO_BONUS` |
| Smart draw | `SMART_DRAW_CANDIDATES`, `SMART_DRAW_BIAS` |
| Skills | `SKILLS` (data table; `core/cards.py` turns it into `SKILL_DEFS`) |

A few numbers are still written inside `core/scoring.py` because they define what a specific die *is*: Lightning ×3, Ice ×2,
Fire +10, Glass ×4 and 30 % shatter, Wizard 30/40/30, Midas +$10 and ×0.8, Hourglass ×0.5, Devil +50 and Wizard ×0.7.
If you change one, also update its text in `core/cards.py` (`CARD_LONG`, `CARD_DESC`, `CARD_TAG`).

## 9. Balance simulator

```
python tools/simulate.py 300          # 300 runs; prints, per round, the share of runs that reached it
python tools/simulate.py 300 nobuy    # the bot never spends money
```

The bot plays the best-scoring subset of its hand (it evaluates every subset with `preview_score`); if that will
not reach the pace needed it first discards the dice outside that subset. In the shop it buys from the random offers: vouchers, then Elements by tier (never the risky ones) while a slot is free,
then passive skills. It is a *decent but not perfect* player, so its win rate is a lower bound for a human.
The `TARGETS` table was fitted with it (see DESIGN.md).

## 10. Tests

```
python -m pytest tests        # 38 tests
```

| File | Covers |
|------|--------|
| `test_combos.py` | all 10 combos, `combo_dice`, hands of 1–5 dice |
| `test_deck.py` | 24 unique dice, hand size, refill and reshuffle keep the dice conserved, special dice live in the hand and never enter the piles |
| `test_scoring.py` | the pipeline order, only-combo-dice scoring, each special die (fixed rolls), Devil with and without discards, Hourglass refund, reward, unused-play pay and interest, vouchers, fixed skill price, skills added flat after penalties, targets, round end rules |
| `test_elements.py` | the 27 Elements, 9 per tier, Spirit (Ghost / Echo / Void), every faction is Common + Rare + Super, each Element's effect, faction bonuses for 2 and 3 members |
| `test_shop.py` | random offers, Element slots = Hand, skill purchases ($30, all passive), refresh pricing, voucher purchases, one random voucher per 3 rounds, Hand +1 deals and layout |

A headless smoke run (SDL dummy drivers) that drives every screen — title, round, scoring, shop, collection,
settings, game over, victory — was used to check the UI without a display: set `SDL_VIDEODRIVER=dummy` and
`SDL_AUDIODRIVER=dummy`, create a `Game`, call `update`/`draw` in a loop and save `screen` with `pygame.image.save`.

## 11. Extending the game

### Add a special die

1. `core/cards.py`: add a `CardType` member and an entry in `CARD_COLOR`, `CARD_DESC`, `CARD_TAG`, `CARD_LONG`.
2. `config.py`: add the name to `GACHA_WEIGHTS`.
3. `core/scoring.py`: implement it in the right phase (A face change, B value effect, C flat bonus, D penalty) and append a
   `Step` whose `kind` is the lowercase enum name and whose `die_index` is the played die.
4. `ui/dice_view.py`: add its icon in `draw_kind_icon`.
5. `scenes/play.py`: nothing is required for a new die (colour comes from `CARD_COLOR`); add a sound mapping in
   `on_step` if you want a special one.
6. Add a test in `tests/test_scoring.py`.

### Add a skill

Append a dict to `SKILLS` in `config.py` (`kind` is one of `handin`, `discard`, `double`, `combo`). `combo` skills need a
`combo` name from `COMBO_BONUS`. Other kinds need a small hook in `RunState` (like `start_round` does for
Second Chance / Discard Token).

### Add a scene

Subclass `Scene`, register it in `build_registry()` in `main.py`, and go to it with `self.g.scenes.goto("name")`.
Set `bg_mode = "scene"` for the landscape backdrop.

### Re-tune the difficulty

Edit `TARGETS`, `MONEY_RATE`, the prices or `COMBO_BONUS` in `config.py`, then run `python tools/simulate.py 500` and look
at the reach-rate curve.

### Change the look

Colours are in `config.py` (a PICO-8 style palette); panels and buttons in `ui/widgets.py`; the bitmap fonts and pixel patches in
`effects/retro.py`; dice and cards in `ui/dice_view.py` and `ui/card_view.py`; backdrops in `effects/background.py`.
To get a smoother look back, remove the `retro.install()` line in `main.py` (the art then draws at its native resolution).

## 12. Developer demo mode (hidden)

For presentations there is a hidden cheat mode. It is **not shown anywhere in the UI** and not listed in the README or the
rules; there is no message or indicator when it is toggled.

| Key | Effect |
|-----|--------|
| `F9` | Toggle demo mode on/off (works on any screen, survives new runs and rounds) |
| `F10` | While demo mode is on: add `DEMO_CASH_KEY` ($100) to your money, with a coin sound |

While demo mode is on:

* **Strong hands.** `DeckManager.cheat` is set. Each refill looks at `DEMO_CANDIDATES` (400) candidate draws and picks
  one with weight `1 + rank ** DEMO_RANK_POWER` (rank 1-8, power 6), so Full House, Straight and Four of a Kind
  dominate. Measured: about 80 % of fresh hands are a Straight or better. Hands are still built from real
  random deals, just heavily filtered, so it does not look scripted. It applies to the first deal and every refill and
  discard.
* **Realistic money.** The round payout is multiplied by `DEMO_PAYOUT_MULT` (10) with a floor of `DEMO_PAYOUT_MIN` ($100),
  so the shop stays useful every round without being infinite. `F10` tops it up on demand.

All five numbers live in `config.py`. The implementation touches `game.py` (keys, toggle),
`core/deck.py` (`cheat`), `core/run_state.py` (`demo`, `payout`) and `scenes/round_intro.py` (re-applies the flag when a
round starts). Tests: `test_demo_mode_strongly_favours_strong_combos` and `test_demo_payout_is_bigger_but_bounded`.
Delete the `F9`/`F10` branches in `Game.handle_event` to remove the feature from a release build.
