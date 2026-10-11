"""All tunable constants for Neon Dice. Logic and rendering both read from here."""


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# ---------------------------------------------------------------- display
SCREEN_W, SCREEN_H = 1280, 720
FPS = 60
SHAKE = True
FLASHES = True             # screen flashes and colour split; off = soft flashes only (photosensitivity)
GAME_SPEEDS = (1.0, 1.5, 2.0, 3.0)   # scoring animation speed (Settings)
CRT = True                 # faint scan-lines over the picture
SOUND = True
MASTER_VOLUME = 0.7
MUSIC = True

# ---------------------------------------------------------------- palette (storybook / painted look)
BACKGROUND_TOP = hex_rgb("#1d2b53")
BACKGROUND_BOTTOM = hex_rgb("#12183a")
# Selectable colours for the in-game backdrop (Settings): (name, top, bottom)
BOARD_COLORS = [
    ("Navy", BACKGROUND_TOP, BACKGROUND_BOTTOM),
    ("Violet", hex_rgb("#3a2466"), hex_rgb("#1d1240")),
    ("Forest", hex_rgb("#1f4a3a"), hex_rgb("#0f2a22")),
    ("Crimson", hex_rgb("#5a1f2f"), hex_rgb("#2e0f1a")),
    ("Teal", hex_rgb("#16505c"), hex_rgb("#0b2a33")),
    ("Brown", hex_rgb("#58381f"), hex_rgb("#2c1b0e")),
    ("Slate", hex_rgb("#3a3d4a"), hex_rgb("#1b1c24")),
    ("Midnight", hex_rgb("#0c0f1f"), hex_rgb("#05060f")),
]
CREAM = hex_rgb("#fff1e8")
PARCH_TOP = hex_rgb("#ffe9bd")
PARCH_BOTTOM = hex_rgb("#f0c890")
INK = hex_rgb("#2a1830")              # dark text on parchment
NAVY_LINE = hex_rgb("#6f7fc0")
MUTED = hex_rgb("#a4b4e8")            # secondary text on navy
BRONZE = hex_rgb("#e0a040")
RED = hex_rgb("#ff4d5e")
TEAL = hex_rgb("#4cc4ff")
GOLD = hex_rgb("#ffd84a")
GREEN = hex_rgb("#4cdc6a")
VIOLET = hex_rgb("#b48cff")
EMBER = hex_rgb("#ff9a2e")
# legacy names used across the code base, now mapped to the muted palette
NEON_CYAN, NEON_PINK, NEON_GOLD, NEON_LIME, NEON_PURPLE, NEON_ORANGE = TEAL, RED, GOLD, GREEN, VIOLET, EMBER

# ---------------------------------------------------------------- rounds
# 10 acts of 5 rounds each (50 rounds): Trial, Skirmish, Challenge, Elite and the act's Guardian.
# Every 2nd act ends with a BOSS instead of a Guardian.
ACTS = ["Meadowlands", "Riverlands", "Stormpeak", "Sunken Ruins", "Ashen Wastes", "Frozen Crown", "Starfall",
        "Shadowrealm", "Celestial Spire", "Void Throne"]
STAGES = ["Trial", "Skirmish", "Challenge", "Elite", "Guardian"]
ROUNDS_PER_ACT = len(STAGES)
# Bosses: the last round of acts 2, 4, 6, 8 and 10 (act index -> boss). Each one bends the rules of the dice.
BOSSES = {
    1: dict(key="morgra", name="Morgra, the Stone Gaze", desc="Every 1 and 2 is petrified: they score nothing."),
    3: dict(key="thalassor", name="Thalassor, the Drowned King", desc="The tide took your discards: you start with 0."),
    5: dict(key="kryovex", name="Kryovex, Warden of the Frozen Crown", desc="Every 6 is frozen: it scores as a 1."),
    7: dict(key="nyxara", name="Nyxara, the Starless Queen", desc="Your normal dice lie face-down until you play them."),
    9: dict(key="aeon", name="Aeon, the Void Emperor", desc="Each combo scores only once this round: repeats score 0."),
}
LAST_STAGE = ROUNDS_PER_ACT - 1
ROUND_NAMES = [(BOSSES[a]["name"] if st == LAST_STAGE and a in BOSSES else f"{ACTS[a]} - {STAGES[st]}")
               for a in range(len(ACTS)) for st in range(ROUNDS_PER_ACT)]           # 50 rounds
# Exponential ladder whose growth itself grows: act a asks TARGET_GROWTH[a] x the previous act. Early acts are gentle,
# the middle steepens and the last act is close to impossible. Inside an act: Trial x1, Skirmish x1.15, Challenge x1.3,
# Elite x1.45, Guardian x1.6, Boss x1.85. Fitted with tools/simulate.py: the first act is a gentle start, every act
# after it grows steeply.
TARGET_BASE = 170
TARGET_GROWTH = [1.0, 2.2, 2.3, 2.6, 2.8, 3.0, 3.1, 3.3, 3.4, 3.8]
STAGE_MULT = (1.0, 1.15, 1.3, 1.45, 1.6)
BOSS_MULT = 1.85


def _targets():
    out, level = [], TARGET_BASE
    for a in range(len(ACTS)):
        level *= TARGET_GROWTH[a]
        for st in range(ROUNDS_PER_ACT):
            m = BOSS_MULT if (st == LAST_STAGE and a in BOSSES) else STAGE_MULT[st]
            out.append(int(round(level * m, -1)))
    return out


TARGETS = _targets()
assert len(TARGETS) == len(ROUND_NAMES) == len(TARGET_GROWTH) * ROUNDS_PER_ACT

# ---------------------------------------------------------------- resources
HAND_SIZE = 5                 # "Hand": dice held at the start of a run, and also the number of Element slots
BASE_HANDINS = 3              # plays per round
BASE_DISCARDS = 3
MAX_SKILL_STACK = 99
ELEMENT_LEVEL_STEP = 1.10       # buying an Element you own levels it up: its numbers x1.1 per level (compounding)
MAX_REFUNDS_PER_ROUND = 1        # Hourglass play refunds allowed per round (stops infinite plays)

# ---------------------------------------------------------------- income (round payout)
# payout = ROUND_REWARD + HAND_LEFTOVER_PAY per unused play + interest on the coins you hold when the round is cleared:
# +3 for every 10 coins, counted up to 40 coins (10 -> +3, 20 -> +6, 30 -> +9, 40 or more -> +12).
ROUND_REWARD = 15
HAND_LEFTOVER_PAY = 3            # for every play you did not need
INTEREST_EVERY = 10              # coins per interest step
INTEREST_STEP = 3                # interest per step
INTEREST_MAX_COINS = 40          # coins above this earn nothing more (max interest = 12)

# ---------------------------------------------------------------- smart draw
SMART_DRAW_CANDIDATES = 6
SMART_DRAW_BIAS = 0.6

# ---------------------------------------------------------------- developer tools
# Off in a release build: the demo mode (F9), cash key (F10), endgame skip (F11) and the skip dot in the round bar are
# only reachable with DEV_MODE on (or by starting the game with  --dev).
DEV_MODE = False

# ---------------------------------------------------------------- developer demo mode (hidden, F9)
DEMO_CANDIDATES = 400            # candidate draws per refill: with this many, strong hands nearly always show up
DEMO_RANK_POWER = 6              # weight = 1 + rank ** power  (full house / straight beat pairs by a mile)
DEMO_PAYOUT_MULT = 10            # round payout multiplier in demo mode
DEMO_PAYOUT_MIN = 100            # ...and never less than this
DEMO_CASH_KEY = 100              # dollars added by F10 in demo mode

# ---------------------------------------------------------------- endgame skip (hidden, F11)
# F11 starts a fresh run on the 2nd-to-last round with an overpowered build (CardType names: config cannot import cards).
SKIP_ROUNDS_LEFT = 2             # jump to the last this-many rounds
SKIP_ELEMENTS = ("GAIA", "STORM", "SUN", "FIRE", "ICE", "TSUNAMI", "LIGHTNING")   # 7 = 5 + both Hand vouchers
SKIP_ELEMENT_LEVEL = 5
SKIP_SKILL_LEVEL = 10            # every combo at this level
SKIP_MONEY = 200

# ---------------------------------------------------------------- scoring
COMBO_BONUS = {
    "High Card": 10,
    "Pair": 40,
    "Two Pair": 80,
    "Three of a Kind": 120,
    "Straight": 150,
    "Full House": 200,
    "Four of a Kind": 300,
    "Five of a Kind": 500,         # needs Elements: the deck holds only four of each value
}
COMBO_LEVEL_STEP = 0.20          # every combo level above 1 adds +20% to the hand score of that combo

# ---------------------------------------------------------------- shop
# No gacha: every shop visit shows a fresh random selection; you pick and buy directly. Each offer can be bought once.
# Elements come in 3 tiers. Each shop offer rolls a tier first (rarer tiers are less likely), then an Element of it.
ELEMENT_TIER_PRICE = {1: 10, 2: 15, 3: 25}          # common, rare, super
ELEMENT_TIER_WEIGHTS = {1: 60, 2: 30, 3: 10}        # % chance per offer
ELEMENT_OFFERS = 3               # Elements on sale per shop visit
FACTION_BIAS = 0.35              # chance per offer to show a missing member of a faction you already own
SKILL_PRICE = 16                 # every skill costs the same, every time
SKILL_OFFERS = 5                 # skills on sale per shop visit
SELL_REFUND = 0.5                # selling an Element returns half its price

# Skills level up a combo for the whole run: each level adds +20% (COMBO_LEVEL_STEP) to that combo's hand score.
SKILLS = (
    dict(key="high_card", name="Lone Star", desc="High Card level +1", combo="High Card"),
    dict(key="pair", name="Pair Power", desc="Pair level +1", combo="Pair"),
    dict(key="two_pair", name="Twin Force", desc="Two Pair level +1", combo="Two Pair"),
    dict(key="three_kind", name="Triple Threat", desc="Three of a Kind level +1", combo="Three of a Kind"),
    dict(key="straight", name="Straight Rush", desc="Straight level +1", combo="Straight"),
    dict(key="full_house", name="Full House", desc="Full House level +1", combo="Full House"),
    dict(key="four_kind", name="Quad Force", desc="Four of a Kind level +1", combo="Four of a Kind"),
    dict(key="five_kind", name="Penta Power", desc="Five of a Kind level +1", combo="Five of a Kind"),
)
# ---------------------------------------------------------------- Element and faction numbers
# Every Element's own effect is modest and roughly worth its tier price; the faction bonuses (2 or 3 members played in
# the same hand) are where the big scores come from.
EL = dict(
    fire=20,            # + dice value
    water=6,            # + dice value per scoring die
    wind_score=20,      # + score (and +1 discard)
    stone=20, stone_pip=8,  # + score, + per pip below 6 on the scoring dice
    midas_money=10, midas_mult=0.85,
    star=1,             # + value to every other die
    devil=80,           # + score, costs 1 discard
    ice=2,              # x dice value
    glass=4, glass_break=0.20,
    thorn=35,           # + score per kicker
    hourglass_mult=0.7,
    wizard_hit=3, wizard_miss=1.5, wizard_chance=0.5,
    moon=20,            # + score per owned Element
    sun=1.5,            # x hand
    lightning=2,        # x dice value, +1 per other Element die played
    quake=50,           # + score per scoring die
    storm=2,            # x dice value (and every die scores)
    eclipse=0.15,       # x hand: 1 + this per owned Element
    ice_floor=4,        # Ice: scoring dice below this count as this
    ghost=15,           # + score per die held in hand (not played)
    void=0.3,           # x hand: 1 + this per discard left
    gear=25,            # + score per play used this round
    piston_mult=2.5, piston_flat=40,
    chrono=0.5,         # x hand: 1 + this per play left
    doubloon=2, doubloon_max=120,
    cutlass=2,          # x dice value (and +$1 per scoring die)
    kraken_cost=5, kraken_hit=3.0, kraken_miss=1.3,
    prism=3,            # odd scoring dice x this
    taiji=0.4,          # x hand: 1 + this per extra distinct value
    wolf=20,            # + score per Element die played
    hawk=5,             # highest scoring die x this
    dragon=1.2,         # x hand per scoring die
    comet=15,           # + score per round already cleared this run
    aurora=0.15, aurora_min=60,
    galaxy_base=1.2, galaxy=0.05, galaxy_max=3.0,
    phoenix_base=1.5, phoenix=0.4,
    knight=30,          # + score per scoring normal die
    king=1.5, king_levels=2,
)
FACTION_NUM = dict(
    inferno=(1.5, 3),           # x hand
    tide=(3, 6),                # x dice value
    tempest=(150, 500),         # + score (and Glass never breaks)
    terra=(1, 3),               # + combo bonus x this (so the bonus counts 2x / 4x)
    grove=((10, 100), (25, 300)),  # (+ money, + score)
    fortune=(15, 30),           # + money; 2 and 3 members: no penalties
    chaos=(1.5, 2.5),           # x hand (and Wizard always hits)
    night=(30, 80),             # + score per owned Element
    spirit=((1, 150, 1.0), (2, 400, 1.5)),   # (+ discards, + score, x hand)
    clockwork=((120, 1.0), (400, 1.5)),      # (+ score, x hand), both +1 play (once a round)
    plunder=((8, 150, 1.0), (20, 300, 1.5)),  # (+ money, + score, x hand)
    harmony=((1, 1.0), (2, 1.5)),            # (combo bonus ranks up, x hand)
    wild=((60, 1.0), (150, 1.5)),            # (+ score per Element die played, x hand)
    cosmos=((1, 1.0), (3, 1.5)),             # (+ combo levels, x hand)
    alchemy=((1, 100, 1.0), (3, 300, 2.0)),  # (+ money per scoring die, + score, x hand)
    royal=((1, 1.0), (3, 1.5)),              # (+ levels for every Element die played, x hand)
)
REFRESH_PRICE = 10               # re-roll the Element and skill offers; each further refresh in the same shop +2
REFRESH_STEP = 2

# Vouchers are permanent upgrades. The shop holds ONE random voucher per stock, on sale from the first shop; it can be
# bought once, and the stock is refilled with a new random voucher every VOUCHER_RESTOCK rounds (shops after rounds
# 1, 4, 7 ...). A voucher already at its max level is never offered.
VOUCHER_RESTOCK = 3
VOUCHER_PRICE = 40
VOUCHERS = (
    dict(key="hand_size", name="Hand +1", desc="+1 die in hand, +1 Element slot", max_level=2),
    dict(key="plays", name="Extra Play", desc="+1 play every round", max_level=3),
    dict(key="discards", name="Extra Discard", desc="+1 discard every round", max_level=3),
    dict(key="bank", name="Bank Vault", desc="Interest counts $20 more coins (max interest +6)", max_level=2),
    dict(key="coupon", name="Coupon", desc="Skills cost $3 less", max_level=2),
    dict(key="lucky", name="Lucky Charm", desc="Rare and Super Elements show up more often", max_level=2),
)
BANK_COINS = 20                  # Bank Vault: interest counts this many more coins per level
COUPON_OFF = 3                   # Coupon: skills cost this much less per level
LUCKY_SHIFT = 12                 # Lucky Charm: tier weight moved from common to rare/super per level
