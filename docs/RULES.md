# POKE'R — Rules

All numbers below are the defaults in `config.py`. Where a rule says "configurable", the constant name is given.

## 1. Goal

Clear all **50 rounds**, in order. They are grouped in **10 acts of 5 rounds** (Trial, Skirmish, Challenge, Elite and the act's
Guardian): Meadowlands, Riverlands, Stormpeak, Sunken Ruins, Ashen Wastes, Frozen Crown, Starfall, Shadowrealm,
Celestial Spire, Void Throne. **Every 2nd act ends with a boss** instead of a Guardian (section 8). In every round you must reach that round's **target score** before you run out of
hands. Reaching the target ends the round immediately (after the scoring animation); running out of hands below the
target ends the run. Beating round 50 — Aeon, the Void Emperor — is a **victory**. It is meant to be almost impossible.

## 2. The dice

* The **deck** has **24 dice**: **four of each value 1–6**. Dice only show their pips: there are no symbols.
* Your **Hand** starts at **5 dice** (`HAND_SIZE`); each **Hand +1** voucher adds one die *and* one Element slot (up to 7).
  You can **play (and discard) as many dice as your Hand holds**.
* **Special dice** (section 6) are the **Elements** you own. They take up hand slots; the rest of the
  hand is normal dice drawn from the deck.

### Drawing ("smart draw")

New normal dice are not purely random. The game rolls `6` candidate draws (`SMART_DRAW_CANDIDATES`), rates each by the best
poker combo your hand would then contain, and picks one at random with weight `1 + rank × 0.6`
(`SMART_DRAW_BIAS`). So you see pairs and straights more often than pure chance, but it is still random.

When the draw pile is too small, the discard pile is shuffled back in. Special dice never enter the piles: they are
created fresh (new random value) every time the hand is refilled.

## 3. A round

| Resource | Default | Notes |
|----------|---------|-------|
| Plays | **3** | +1 per **Extra Play** voucher level (max +3) |
| Discards | **3** | +1 per **Extra Discard** voucher level (max +3) |
| Hand (dice in hand, and Element slots) | **5** | +1 per **Hand +1** voucher level (max +2) |

* **PLAY** — select **1 to Hand-size** dice and play them. Costs 1 hand. The dice are scored (section 4), thrown away, and the
  hand is refilled to your hand size.
* **DISCARD** — select **1 to Hand-size** dice and throw them away for new ones. Costs 1 discard. No score.
  Discarding a special die **re-rolls** it (new value).
* **SORT** — free, orders your hand by value (Elements last).
* The round ends **right after a hand is scored** when either:
  * round score ≥ target → **round cleared**, or
  * hands = 0 → if the score is below the target the **run is over**.
* If the last hand both uses your last hand and reaches the target, the round is **cleared**.
* There is no cash-out and no bonus play after reaching the target.

## 4. Poker combos

The best matching combo is used (first row that matches wins). You may play fewer than 5 dice, but a few combos
need 5. If you play **more than 5** (a bigger Hand), the best 5 of them form the combo and the rest are kickers
(handy for Thorn, Storm and for playing many Elements at once).

| Rank | Combo | Needs | Bonus |
|------|-------|-------|-------|
| 8 | **Five of a Kind** | 5 dice with the same value — only possible with Elements (the deck holds four of each) | +500 |
| 7 | **Four of a Kind** | 4 dice with the same value | +300 |
| 6 | **Full House** | 3 of one value + 2 of another | +200 |
| 5 | **Straight** | 5 in a row (1-5 or 2-6) | +150 |
| 4 | **Three of a Kind** | 3 dice with the same value | +120 |
| 3 | **Two Pair** | two different pairs | +80 |
| 2 | **Pair** | 2 dice with the same value | +40 |
| 1 | **High Card** | anything else | +10 |

### Only the combo dice score

The dice **value** that counts is the sum of **only the dice that form the combo**:

| Combo | Dice that count |
|-------|-----------------|
| High Card | the single highest die |
| Pair | the two paired dice |
| Two Pair | the four dice in the two pairs |
| Three / Four of a Kind | the matching dice |
| Straight, Full House, Five of a Kind | all five dice |

Dice you played that are **not** in the combo (the "kickers") score nothing and are shown dimmed during scoring.
They are still spent, so play only what you need. Special dice still trigger their effect even when they are not part of
the combo.

## 5. The scoring pipeline (exact order)

Every hand goes through these steps, in this order. The on-screen breakdown shows each step as a chip.

| Step | What happens |
|------|--------------|
| **A. Face changes** | **Grass**, **Jester**, **Star**, **Gaia**, **Mirror** and **Sulfur** rewrite the other played dice — **Element dice too** (they keep their Element and still act; only the value changes). This happens first, so the combo is read *after* the changes. |
| **B. Dice value** | Sum of the dice that form the combo (every played die with **Storm**; each counts as 6 with **Metal**; with **Ice** any below 4 counts as 4). Then every Element you played acts on this number, **left to right in hand order**: Lightning ×(2 + 1 per other Element die played), Ice ×2, Storm ×2, Glass ×4, Wizard ×3 (else ×1.5), Tsunami × scoring dice, Cutlass ×2, Prism (odd scoring dice ×3), Hawk (top scoring die ×5), Fire +20, Water +6 per scoring die. Order matters. Then the **Tide** faction ×3 / ×6. |
| **C. Combo bonus and flat bonuses** | `+` the combo's bonus (**Crystal** adds it again, **Terra** ×2 / ×4). Then the flat Elements (Stone, Wind, Thorn, Quake, Moon, Ghost, Gear, Wolf, Doubloon, Comet, Aurora, Mercury, Piston, Devil) and the flat factions (**Terra**, **Tempest**, **Night**, **Grove**, **Spirit**, **Harmony**, **Clockwork**, **Plunder**, **Wild**, **Alchemy**, **Cosmos**). Then the hand multipliers in hand order (Void, Sun, Eclipse, Chrono, Kraken, Taiji, Dragon, Galaxy, Phoenix, Piston on the last play), then **Inferno** ×1.5 / ×3, **Chaos** ×1.5 / ×2.5. |
| **D. Penalties, then combo level** | Midas ×0.85, Hourglass ×0.7, Glass shatter (20 %) → 0 (in hand order, rounded down). Then the **combo level**: ×(1 + 0.2 per level above 1) (section 7). |

The result is rounded down and added to the round score. The live preview under your hand shows the same pipeline with
average luck (Wizard/Glass don't trigger their bad outcome, Jester rolls a 3).

### Worked examples

Hand: 6★ 6● 5◆ 4▲ 1★ (all normal dice), play all five.

* Pair of 6s. Combo dice = 6+6 = **12**. Score = 12 + 40 = **52**. The 5, 4 and 1 add nothing.
* With **Pair Power ×2** (+200): 52 + 200 = **252**.

Same pair, but one of the played dice is a **Lightning die** (a third die, value irrelevant):

* Combo dice 12 → Lightning ×2 (no other Element die) = 24 → + Pair 40 = **64**.
* Add an **Ice die**: Lightning now chains 1 more Element: 12 → ×3 → ×2 = 72 → +40 = **112**.
* Add a **Fire die** *after* Lightning (Lightning ×3): 12×3 = 36 → +20 = 56 → +40 = **96**.
  Fire *before* Lightning: (12+20)×3 = 96 → +40 = **136**.

Full House 3-3-3-5-5: all five dice count = 19, + Full House 200 = **219**.

A **Midas** die on the 52-point pair: int(52 × 0.85) = **44** and +$10. Midas together with **Hourglass** (Fortune faction): no penalties, **52**, +$25 and +1 play.

## 6. Elements (special dice)

Elements are bought in the shop (**no gacha**). Each Element you own becomes **one special die in your hand every
round**. You have **one Element slot per die in your Hand** (5 at the start, up to 7 with Hand +1 vouchers);
duplicates are allowed. A special die is a normal die too: it has a value (1–6) and takes part in combos.
It is only *active* if you **play** it. Playing or discarding it throws it away, and a fresh one with a new value
appears in your next hand.

### Tiers

| Tier | Price | Chance per shop offer | Feel |
|------|------:|----------------------:|------|
| **Common** | $10 | 60 % | small, steady boosts, some with a cost |
| **Rare** | $15 | 30 % | strong effects and rule-changers |
| **Super** | $25 | 10 % | the big multipliers |

Each shop offer rolls its tier first (`ELEMENT_TIER_WEIGHTS`), then an Element of that tier (no repeats in one shop).
There are **16 Elements in every tier**.

### Element levels

Buying an Element you **already own** does not take a new slot: it **levels it up**. Every level makes all of its
numbers **10 % bigger than the level before** (`ELEMENT_LEVEL_STEP`, compounding): Lv2 ×1.1, Lv3 ×1.21, Lv4 ×1.33,
Lv5 ×1.46 … (Fire +20 → +22 → +24 …, Lightning ×2 → ×2.2 → ×2.42 …). Elements without a number of their own (Grass,
Jester, Star, Gaia, Hourglass, Mirror, Sulfur) give **×1.1 hand score per level** instead. An **Echo** copies at its own level. The
level is shown on the card (L2, L3 …) and above the die ("FIRE LV3"). Chances (Glass shatter, Wizard 50 %) never change.

### Factions

The 48 Elements form **16 factions**, each with **one Common, one Rare and one Super**; the faction name is printed on
every Element card. On their own, Elements are modest and roughly worth their price. The **faction bonuses are where the
big scores come from**: play **2 different members of a faction in the same hand** for its bonus, **all 3** for the full
bonus. Owning them is not enough: they must be played together. All numbers are in `config.py` (`EL`, `FACTION_NUM`).

| Faction | Common | Rare | Super | 2 played | All 3 played |
|---------|--------|------|-------|----------|--------------|
| **Inferno** | Fire: dice +20 | Devil: +80, costs 1 discard | Sun: hand ×1.5 | hand ×1.5 | hand ×3 |
| **Tide** | Water: +6 dice value per scoring die | Ice: scoring dice below 4 count as 4, then dice ×2 | Tsunami: dice × number of scoring dice | dice value ×3 | dice value ×6 |
| **Tempest** | Wind: +20 and +1 discard | Glass: dice ×4, 20 % the hand scores 0 | Lightning: dice ×(2 + 1 per other Element die played) | +150, Glass never breaks | +500, Glass never breaks |
| **Terra** | Stone: +20, +8 per pip below 6 on the scoring dice | Metal: scoring dice count as 6 | Quake: +50 per scoring die | combo bonus ×2 | combo bonus ×4 |
| **Grove** | Grass: copies its value onto the lowest other die | Thorn: +35 per kicker | Gaia: every die becomes the highest value | +100, +$10 | +300, +$25 |
| **Fortune** | Midas: +$10, hand ×0.85 | Hourglass: +1 play (once a round), hand ×0.7 | Crystal: combo bonus counts twice | no penalties, +$15 | no penalties, +$30 |
| **Chaos** | Jester: re-rolls the other dice | Wizard: 50 % dice ×3, else ×1.5 | Storm: every played die scores, then dice ×2 | Wizard always hits, hand ×1.5 | Wizard always hits, hand ×2.5 |
| **Night** | Star: other dice +1 (max 6) | Moon: +20 per owned Element | Eclipse: hand ×(1 + 0.15 per owned Element) | +30 per owned Element | +80 per owned Element |
| **Spirit** | Ghost: +15 per die kept in your hand | Echo: copies the Element just to its left | Void: hand ×(1 + 0.3 per discard left) | +1 discard, +150 | +2 discards, +400, hand ×1.5 |
| **Clockwork** | Gear: +25 per play already used this round | Piston: hand ×2.5 on the last play, else +40 | Chrono: hand ×(1 + 0.5 per play left) | +120, +1 play (once a round) | +400, +1 play, hand ×1.5 |
| **Plunder** | Doubloon: +2 per $1 held (max +120) | Cutlass: dice ×2, +$1 per scoring die | Kraken: pays $5 for hand ×3 (else ×1.3) | +150, +$8 | +300, +$20, hand ×1.5 |
| **Harmony** | Mirror: flips the other dice (1↔6, 2↔5, 3↔4) | Prism: odd scoring dice ×3 | Taiji: hand ×(1 + 0.4 per extra different value) | combo bonus of the next rank up | bonus 2 ranks up, hand ×1.5 |
| **Wild** | Wolf: +20 per Element die played | Hawk: the top scoring die ×5 | Dragon: hand ×1.2 per scoring die | +60 per Element die played | +150 per Element die, hand ×1.5 |
| **Cosmos** | Comet: +15 per round cleared this run | Aurora: +15 % of the round score so far (min +60), added after every multiplier | Galaxy: hand ×(1.2 + 0.05 per skill bought, max ×3) | every combo +1 level | every combo +3 levels, hand ×1.5 |
| **Alchemy** | Sulfur: every played 1 becomes a 6 | Mercury: + raw dice points × combo rank | Phoenix: hand ×(1.5 + 0.4 per discard used this round) | +100, +$1 per scoring die | +300, +$3 per scoring die, hand ×2 |
| **Royal** | Knight: +30 per scoring normal die | Queen: the Element to her right triggers twice | King: hand ×1.5, every other Element played +2 levels | every Element played +1 level | every Element played +3 levels, hand ×1.5 |

**Echo** acts as the Element to its left (an Echo after an Echo copies the same thing), but it still counts as an
Echo for its own faction. Grass, Jester, Star and Gaia change **Element dice as well as normal dice** (never themselves). A changed Element die
keeps working: e.g. Gaia turning an Ice die into a 6 makes it count in the Five of a Kind *and* still doubles.

Hover a special die in your hand (or an Element in the shop) to read its full text and its faction. The **Collection**
screen (title menu) shows every faction as a row.

## 7. Money and the shop

### Money (round payout)

After each cleared round you receive:

* **Round reward** — **$15** (`ROUND_REWARD`).
* **Unused plays** — **$3 for every play you did not need** (`HAND_LEFTOVER_PAY`).
* **Interest** — on the coins you **hold** when the round is cleared: **+$3 for every $10**, counted up to $40
  ($10 → +3, $20 → +6, $30 → +9, $40 or more → **+12**, the maximum). Saving pays; spending everything earns nothing.

Example: you clear a round with 1 play left while holding $33 → 15 + 3 + 9 = **$27**.
Midas gives +$10 immediately when played. Selling an Element refunds **50 %** of its price (`SELL_REFUND`).

### The shop (after every cleared round except the last)

There is no gacha and no reroll. Every visit shows a **fresh random selection**; you pick and buy directly, and each
offer can be bought **once** (it then shows SOLD).

**Elements** — **3 random Elements** (`ELEMENT_OFFERS`): $10 common, $15 rare, $25 super (`ELEMENT_TIER_PRICE`). With all slots full, sell one
first or buy a Hand +1 voucher.

**Refresh** — re-rolls the Element and skill offers (not the voucher): **$10**, **+$2** for every further refresh in
the same shop ($10, $12, $14 …); the price resets in the next shop.

**Skills** — **5 random skills** (`SKILL_OFFERS`), every one **$16** (`SKILL_PRICE`), however many you already own.

Every skill **levels up one combo** for the rest of the run. A combo starts at **level 1**; each level above 1 adds
**+20 %** to the hand score of that combo (`COMBO_LEVEL_STEP`): level 2 ×1.2, level 3 ×1.4, level 6 ×2.0 … It is applied
after the penalties. Buying the same skill again raises the level again.

| Skill | Levels up |
|-------|-----------|
| Lone Star | High Card |
| Pair Power | Pair |
| Twin Force | Two Pair |
| Triple Threat | Three of a Kind |
| Straight Rush | Straight |
| Full House | Full House |
| Quad Force | Four of a Kind |
| Penta Power | Five of a Kind |

There is no DOUBLE mechanic any more; Eclipse is a hand multiplier that grows with the Elements you own.

**INFO** — the INFO button (or `I`) in a round and in the shop opens a book with your **combo levels** (bonus, level,
multiplier, which skill raises it) plus your hand, slots, plays, discards and interest, and every **Element by faction**.

**Vouchers** — permanent upgrades. The shop holds **one random voucher**, on sale **from the first shop**, for **$40**
(`VOUCHER_PRICE`). It can be bought once; every **3 rounds** the stock is refilled with a new random voucher (in the
shops after rounds 1, 4, 7, 10 …). A voucher already at its max level is never offered.

| Voucher | Effect | Max level |
|---------|--------|----------:|
| Hand +1 | +1 die in your Hand **and** +1 Element slot | 2 |
| Extra Play | +1 play every round | 3 |
| Extra Discard | +1 discard every round | 3 |
| Bank Vault | interest counts $20 more coins (max interest +6 per level) | 2 |
| Coupon | skills cost $3 less | 2 |
| Lucky Charm | Rare and Super Elements show up more often | 2 |

## 8. Targets and bosses

The ladder is exponential **and its growth grows**: each act multiplies the previous act's targets by its own factor
(`TARGET_GROWTH`), gentle at first and steep in the second half; every act asks at least double the previous one, act 10 nearly four times act 9. Inside an act the
Skirmish asks ×1.15, Challenge ×1.3, Elite ×1.45 and the Guardian ×1.6 of the Trial; a **boss** round asks ×1.85 (`BOSS_MULT`).

| Act | Name | Growth | Trial | Skirmish | Challenge | Elite | Guardian / Boss |
|----:|------|-------:|------:|------:|------:|------:|------:|
| 1 | Meadowlands | ×1 | 170 | 200 | 220 | 250 | 270 |
| 2 | Riverlands | ×2.2 | 370 | 430 | 490 | 540 | **690** (boss) |
| 3 | Stormpeak | ×2.3 | 860 | 990 | 1120 | 1250 | 1380 |
| 4 | Sunken Ruins | ×2.6 | 2240 | 2570 | 2910 | 3240 | **4140** (boss) |
| 5 | Ashen Wastes | ×2.8 | 6260 | 7200 | 8140 | 9080 | 10020 |
| 6 | Frozen Crown | ×3 | 18790 | 21600 | 24420 | 27240 | **34760** (boss) |
| 7 | Starfall | ×3.1 | 58240 | 66970 | 75710 | 84450 | 93180 |
| 8 | Shadowrealm | ×3.3 | 192190 | 221020 | 249850 | 278670 | **355550** (boss) |
| 9 | Celestial Spire | ×3.4 | 653440 | 751460 | 849470 | 947490 | 1045510 |
| 10 | Void Throne | ×3.8 | 2483080 | 2855540 | 3228000 | 3600460 | **4593690** (boss) |

### Bosses

The last round of acts 2, 4, 6, 8 and 10 is a **boss**. Each boss bends one rule of the dice for that round; the rule
is shown on the round intro and under the top bar.

| Act | Boss | Rule |
|----:|------|------|
| 2 | **Morgra, the Stone Gaze** | Every 1 and 2 is petrified: they score nothing. |
| 4 | **Thalassor, the Drowned King** | The tide took your discards: you start with 0. |
| 6 | **Kryovex, Warden of the Frozen Crown** | Every 6 is frozen: it scores as a 1. |
| 8 | **Nyxara, the Starless Queen** | Your normal dice lie face-down until you play them. |
| 10 | **Aeon, the Void Emperor** | Each combo scores only once this round: repeats score 0. |

## 9. Game flow

```
Title ─► Round select ─► Round intro ─► Play ─┬─► Round cleared ─► Shop ─► Round intro (next round)
  │                                            │        └─ (round 50) ─► Victory
  ├─► Collection                               └─► Game over ─► Play again / Main menu
  └─► Settings
```

* **Game over** shows the round reached, how far you were from the target, your total score and best hand.
  *Play again* starts a fresh run at round 1 (skills, Elements, vouchers and money are reset).
* There is no save file: closing the game ends the run.

## 10. Quick FAQ

* **Do dice I don't use in the combo count?** No. Only the combo dice add value (section 4).
* **Can a special die be in the combo?** Yes, it is a normal die for combos. Its face value counts if it is a combo die.
* **Why did my skill bonus not get doubled?** By design: skill bonuses are added flat after penalties.
* **Can I get more than 5 special dice?** Yes, with Hand +1 vouchers: one Element slot per die in your Hand (max 7).
* **What if I own 5 special dice?** With a 5-dice Hand it is all special dice. A **Hand +1** voucher adds a die, but also a slot.
* **Does the order of my hand matter?** Yes for step B/D: special dice act left to right in the order they are played
  (their hand order). Sorting changes the order.

## Saving, records and options

* **Saving** — the run is saved at the start of every round (`savegame.json`). **CONTINUE** on the title screen puts
  you back at the start of that round. NEW RUN over a saved run asks for a second click. Game over / victory clears it.
* **Records** — best round, best hand, runs and wins are kept in `records.json` and shown on the title screen.
* **How to Play** — a 4-page tutorial, shown before your very first run and from the title menu.
* **Shop** — each Element offer has a 35 % chance (`FACTION_BIAS`) to be a missing member of a faction you already
  own; such offers are labelled with the faction count they would reach (e.g. "ROYAL 2/3").
* **Settings** — game speed (1x / 1.5x / 2x / 3x scoring animations), screen shake & zoom, flashing effects
  (off = soft flashes, no colour split, for photosensitive players), scan lines, volumes, board colour.
* **Developer tools** (demo mode F9, cash F10, endgame skip F11) only work when started with `python main.py --dev`.
