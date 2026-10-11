# POKE'R — Design notes

Why the game is the way it is, how it changed, how it was balanced, and what it does not do (yet).

## 1. Design pillars

1. **Poker feel with dice.** Pairs, straights, flushes and full houses — but with only five dice in hand, every choice
   (what to keep, what to throw, when to gamble) matters.
2. **Risk and reward, not just "bigger numbers".** Special dice are deliberately double-edged: Glass can wipe a hand,
   Wizard can curse you, Midas and Hourglass trade score for money and tempo, Devil trades a discard for points.
3. **Satisfying numbers.** Scoring is a sequence you can read step by step, with a count-up bar, rising sounds and
   particles, so a good hand feels good.
4. **Everything in code.** No asset files: painting, dice, cards, sounds and music are all generated, which keeps the game
   tiny and lets every value be tuned from `config.py`.

## 2. How the game evolved

The project started from a written spec (a neon-styled game called *Neon Dice*). It was then reshaped by feedback. In order:

| Step | Change | Reason |
|------|--------|--------|
| 1 | Built the spec: 10-dice hand, 23 rounds, target = 400 × round, money = 20 % of score, three passive multiplier cards in 8 slots (Lightning ×2ⁿ, Ice +P×score, Fire ×2v). | The original design. |
| 2 | Reported "too easy" | Multipliers stacked into millions, so a linear target ladder was trivial (a card-buying bot won 100 % of runs). |
| 3 | **Hand size 10 → 5.** Skills moved to a list at the top of the screen; multiplier cards became **special dice that live in the hand** and only act when played. | More tension per decision; cards become tangible objects. |
| 4 | Targets rebuilt from simulation; prices escalate; payout capped. | Keep the economy from snowballing. |
| 5 | Effects rescaled to act on the **dice value** (Lightning ×3, Ice ×2, Fire +10). | Tame the explosive growth. |
| 6 | **Seven new special dice** (Grass, Wizard, Glass, Devil, Midas, Hourglass, Jester). | More interesting choices with real costs. |
| 7 | Skill bonus added **flat at the end**. | Penalties should not erase or double your skills' investment. |
| 8 | Devil: +50, costs a discard, playable with 0 discards (no bonus). | Devil first could not be played at 0 discards; now it is a soft cost instead of a lock. |
| 9 | Money = **5 %** of the round score, no cap. | Slower, tighter economy. *(Replaced in step 14.)* |
| 10 | **Only combo dice score.** Kickers add nothing (and are dimmed). | Rewards precise play; pairs are no longer the same as "dump five dice". |
| 11 | Score-bar count-up animation. | Satisfying feedback. |
| 12 | **Re-skin**: neon → storybook painting (navy panels, parchment cards, ivory dice), title renamed *Elements*, new Collection and Settings screens. | Requested visual direction (reference image). |
| 14 | **Economy and shop rework**: fixed round income ($10, +$2 per round, max $40) plus $3 per unused hand; no gacha; Jokers ($40) and skills ($20) are bought directly; active skills (Pip +1 / Pip -1 / Reroll Face); a voucher shop every 3 rounds (hand size, hands, discards). Targets re-fitted. | Requested: a predictable interest-style income, choosing what to buy instead of gambling, and permanent upgrades. |
| 15 | **Shop rework 2**: Jokers renamed **Elements**; income = $10 + $3 per unused play + interest (+$2 per $10 held, max +$8); 3 random Elements and 5 random skills per shop, each bought once; vouchers on sale from the first shop, restocked every 3 rounds; **Hand** = dice in hand = Element slots (Hand +1 voucher), the old hand-in voucher renamed Extra Play. Targets re-fitted. | Requested: interest on savings, curated random shop offers, one Hand stat. |
| 16 | Prices: Element **$20**, skill **$40**, voucher **$40** (flat); only **one random voucher** per 3 rounds. Targets re-fitted (170 → 2700). | Requested. Cheap Elements make the dice multipliers the early engine, so targets had to grow much faster. |
| 17 | **Element tiers and synergies**: 18 Elements (8 new: Wind, Water, Stone, Metal, Moon, Storm, Sun, Crystal) in three tiers (Common $15 / Rare $20 / Super $30, offered 60 / 30 / 10 %); Wizard, Glass, Devil and Hourglass reworked to fit their tier; every Element has one partner and the pair triggers a synergy when played together. Targets re-fitted (170 → 1770). | Requested: more variety, rarity, and combos between Elements. |
| 18 | **No symbols, factions, refresh**: dice only show pips (Flush, Straight Flush, Royal Flush removed; Five of a Kind added, only reachable with Elements); 24 Elements in 8 factions of Common + Rare + Super (2 played = bonus, 3 = full bonus) replace the pairs; skills $30, all passive (Pip ±1 / Reroll Face removed); shop REFRESH $10 +$2 per repeat, reset each round. Targets re-fitted (170 → 1700). | Requested. |
| 19 | **Rebalance**: Element numbers moved to `config.EL` and evened out (weak commons buffed, harsh penalties softened); faction bonuses made much stronger (`config.FACTION_NUM`, e.g. Inferno ×3, Tide ×6, Terra ×4 bonus); Grass / Jester / Star / Gaia also change Element dice; the faction name is printed on every card. Targets re-fitted (170 → 4000). | Requested: balanced Elements, overpowered combos. The steeper target curve makes factions the way to win the late game. |
| 20 | **Acts, levels, Spirit**: 24 rounds in 8 named acts of 3 (Trial / Challenge / Guardian) with an exponential target ladder (×1.6 per act); income $15 + $3 per $10 held (max +$12); skills ($20) now level combos (+20 % hand score per level); new Spirit faction (Ghost, Echo, Void); in-game INFO book. | Requested. The exponential ladder keeps the opening relaxed and makes levels and factions decisive late. |
| 21 | **10 acts, bosses, Element levels, bigger plays**: 30 rounds; per-act growth rising from ×1.4 to ×2.6; 5 bosses (Morgra, Thalassor, Kryovex, Nyxara, Aeon) with dice-bending rules on the last round of every 2nd act; buying an owned Element levels it up (×1.1 compounding); you may play as many dice as your Hand holds. | Requested: much harder late game, an almost impossible act 10, more depth per Element. |
| 13 | **Retro pixel-art pass**: bitmap fonts, notched pixel panels and buttons, pixel-art dice, cards and backdrops, optional scan-lines. | Requested "more retro vibes and pixelated". |

Differences from the original spec that remain, in one place:

* Hand of 5 (not 10). Five special-die slots (not 8). Multiplier cards are dice, not passive triggers.
* Lightning / Ice / Fire formulas are different (section 3 of RULES.md).
* Targets: 170 → 48 680 over 30 rounds; the per-act growth itself rises (×1.4 … ×2.6).
* Money: $10 per round + $3 per unused play + interest on savings (max +$8). Fixed prices: Element $15 / $20 / $30 by tier, skill $30, voucher $40, refresh $10 (+$2).
* No *practice mode* from the optional part of the spec.

## 3. Balance

### 3.1 What made it hard to balance

* Special dice multiply the *dice value*, but the flat combo bonuses (up to +600) and skill bonuses (+100 per stack) are
  added *after* the multipliers. So multipliers matter early and less later; skill stacks and better combos drive the late game.
* Only combo dice count, so a Pair is worth ~50–70 points however many dice you play, and a Full House ~200+.
* Money is tiny (about $13–21 per round), so the shop is a series of hard choices. Interest rewards holding $40 (+$8 a round); a cheap common Element competes with it, a Super one ($30) is a real decision.
* Unused plays pay $3 each: finishing early is richer, but a play you keep is also your safety net.
* The shop only shows 3 Elements and 5 skills, so you build around what is offered instead of always buying the best item.

### 3.2 Method

`tools/simulate.py` runs a bot through many runs. The targets were fitted so that a *decent but imperfect* bot
reaches deep rounds only occasionally. The bot always plays its best-scoring subset and discards intelligently, but it
buys skills at random and never plans around special dice, so a human should beat it.

Results of the current settings (500 runs; share of runs that *reached* each round):

| Round | Reached | Round | Reached |
|------:|--------:|------:|--------:|
| 3 | 99 % | 18 (boss) | 42 % |
| 6 (boss) | 99 % | 21 | 18 % |
| 9 | 98 % | 24 (boss) | 11 % |
| 12 (boss) | 94 % | 27 | 6 % |
| 15 | 67 % | 30 (boss) | 2 % |

Victory: **0.7 %** of 1000 bot runs. Acts 1-4 teach the game, acts 5-8 are the real fight, acts 9-10 are a wall that
needs levelled Elements, full factions and high combo levels.

The bot shops from the random offers (the voucher, then Elements by highest tier, never Glass / Midas / Hourglass /
Jester; then skills). It never refreshes, never aims for factions, so players should do better.

**About 10 % of bot runs win the game.** The early rounds are forgiving, the curve bends down around rounds 6–9 (when the
targets outgrow what you can score without stacked skills), and then flattens because surviving players have snowballed.

### 3.3 Tuning knobs (in order of impact)

1. `TARGET_BASE`, `TARGET_GROWTH` (one factor per act), `STAGE_MULT`, `BOSS_MULT` — shape the whole curve.
2. `EL` and `FACTION_NUM` (every Element and faction number), then `ROUND_REWARD`, `HAND_LEFTOVER_PAY`, `INTEREST_*`, `ELEMENT_TIER_PRICE`, `SKILL_PRICE` and the voucher prices — how fast you can build.
3. `COMBO_BONUS` — how valuable each combo is.
4. `VOUCHERS` (max levels and prices) — how far the resources can grow.
5. Special-die numbers in `core/scoring.py`.

After any change run `python tools/simulate.py 500` and check the curve.

## 4. Strategy guide

* **Play only what scores.** Kickers add nothing and are wasted dice. A Pair needs two dice; playing two keeps three in
  hand for next time.
* **Use discards for the dice you don't need**, not the ones that already form a combo. Discarding a special die re-rolls it
  (a Lightning die showing a 1 is a great candidate — but its value only counts if it is in the combo).
* **Special dice are best when they are in the combo**, because then their own face value is multiplied too.
* **Order matters.** Fire before Lightning: (v + 10) × 3. Lightning before Fire: v × 3 + 10. Sort the hand to control it.
* **Grass** is a combo engine: pair it with a high die and it clones onto your worst die for a guaranteed pair (and a flush
  if the symbols match).
* **Gamble at the right time.** Glass and Wizard are best when you are far behind a target and safe plays will not get you
  there; avoid them on the final hand unless you must.
* **Hourglass** is a tempo tool, not a score tool: use it on a hand that would score little anyway, to get an extra hand.
* **Devil** is worth it when you have discards to spare (skills that add discards make it stronger).
* **Skills:** stack the skill that matches the combo you actually make. Flat +100 per stack is the largest late-game lever, and
  it is added after penalties, so it is always safe.
* **Money:** an early Second Chance (+1 hand) or Discard Token is worth more than a marginal special die.

## 5. Visual design

The look is **retro pixel art on a 2 px grid** (a 640x360 picture magnified x2), with a PICO-8-like palette: deep navy tables,
peach parchment, a red main action and blue secondary actions. Text uses an upper-case bitmap font; panels and buttons have
stepped corners, chunky borders and bevels; dice and cards are drawn as low-resolution sprites; the menu backdrop is a dithered
sunset landscape. Elements (fire, water, grass, earth) still give the special dice their colours and icons.

Animation is used for feedback, not decoration and it moves in pixel steps: drifting pixel clouds, birds and petals on menus,
marching highlights on the progress bar, rotating rays behind card medallions, flickering flames on the game-over screen,
a blinking ring on special dice, a stop-motion tumble when a special die appears, and faint CRT scan-lines (toggle in Settings).

Accessibility notes: suits are distinguished by **shape and colour** together; effects are readable from text (tags above
special dice, tooltips, the collection); screen shake and scan-lines can be turned off in Settings; all audio can be muted.

## 6. Known limits and ideas

* **No save file** and no meta-progression: a run lives in memory only.
* **No practice mode** (replaying a round) — it was optional in the original spec.
* `effects/glow.py` and the folder name `neon_dice` are historical names from the neon version; nothing glows any more.
* Drag-reordering owned cards in the shop only changes the *initial* order of special dice in a new hand. Playing order is
  the hand order, which you control with the sort buttons.
* The bot in `tools/simulate.py` does not model special-die strategy, so it underestimates skilled human play.
* Fullscreen uses pygame's toggle and depends on the OS/driver.
* Ideas: more special dice, a boss modifier per tenth round, a persistent collection that unlocks dice, a daily seed,
  a save/resume file, controller support.

## 7. Credits and technical notes

* Written entirely in Python with pygame; no external assets or libraries besides pygame (and pytest for tests).
* All visuals are drawn procedurally; all audio is synthesized procedurally.
* Balance tooling and the smoke tests were used throughout development.
