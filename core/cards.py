import itertools
from dataclasses import dataclass, field
from enum import Enum

import config


class CardType(Enum):
    # common
    FIRE = "Fire"
    WATER = "Water"
    WIND = "Wind"
    STONE = "Stone"
    GRASS = "Grass"
    MIDAS = "Midas"
    JESTER = "Jester"
    STAR = "Star"
    GHOST = "Ghost"
    GEAR = "Gear"
    DOUBLOON = "Doubloon"
    MIRROR = "Mirror"
    WOLF = "Wolf"
    COMET = "Comet"
    SULFUR = "Sulfur"
    KNIGHT = "Knight"
    # rare
    DEVIL = "Devil"
    ICE = "Ice"
    GLASS = "Glass"
    METAL = "Metal"
    THORN = "Thorn"
    HOURGLASS = "Hourglass"
    WIZARD = "Wizard"
    MOON = "Moon"
    ECHO = "Echo"
    PISTON = "Piston"
    CUTLASS = "Cutlass"
    PRISM = "Prism"
    HAWK = "Hawk"
    AURORA = "Aurora"
    MERCURY = "Mercury"
    QUEEN = "Queen"
    # super
    SUN = "Sun"
    TSUNAMI = "Tsunami"
    LIGHTNING = "Lightning"
    QUAKE = "Quake"
    GAIA = "Gaia"
    CRYSTAL = "Crystal"
    STORM = "Storm"
    ECLIPSE = "Eclipse"
    VOID = "Void"
    CHRONO = "Chrono"
    KRAKEN = "Kraken"
    TAIJI = "Taiji"
    DRAGON = "Dragon"
    GALAXY = "Galaxy"
    PHOENIX = "Phoenix"
    KING = "King"


C = CardType
COMMON, RARE, SUPER = 1, 2, 3
TIER_NAME = {COMMON: "Common", RARE: "Rare", SUPER: "Super"}
TIER_COLOR = {COMMON: (150, 140, 120), RARE: (70, 140, 230), SUPER: (240, 180, 40)}


@dataclass(frozen=True)
class Faction:
    """Three Elements, one of each tier. Playing 2 of them in the same hand triggers the faction bonus,
    all 3 the full (much stronger) bonus."""
    key: str
    name: str
    members: tuple          # (common, rare, super)
    two: str                # bonus with 2 members played
    three: str              # bonus with all 3 played


FACTIONS = (
    Faction("inferno", "Inferno", (C.FIRE, C.DEVIL, C.SUN), "hand score x1.5", "hand score x3"),
    Faction("tide", "Tide", (C.WATER, C.ICE, C.TSUNAMI), "dice value x3", "dice value x6"),
    Faction("tempest", "Tempest", (C.WIND, C.GLASS, C.LIGHTNING), "+150, Glass never breaks", "+500, Glass never breaks"),
    Faction("terra", "Terra", (C.STONE, C.METAL, C.QUAKE), "combo bonus x2", "combo bonus x4"),
    Faction("grove", "Grove", (C.GRASS, C.THORN, C.GAIA), "+100 score, +$10", "+300 score, +$25"),
    Faction("fortune", "Fortune", (C.MIDAS, C.HOURGLASS, C.CRYSTAL), "no penalties, +$15",
            "no penalties, +$30"),
    Faction("chaos", "Chaos", (C.JESTER, C.WIZARD, C.STORM), "Wizard always hits, hand x1.5",
            "Wizard always hits, hand x2.5"),
    Faction("night", "Night", (C.STAR, C.MOON, C.ECLIPSE), "+30 per Element owned", "+80 per Element owned"),
    Faction("spirit", "Spirit", (C.GHOST, C.ECHO, C.VOID), "+1 discard, +150", "+2 discards, +400, hand x1.5"),
    Faction("clockwork", "Clockwork", (C.GEAR, C.PISTON, C.CHRONO), "+120, +1 play (once a round)",
            "+400, +1 play, hand x1.5"),
    Faction("plunder", "Plunder", (C.DOUBLOON, C.CUTLASS, C.KRAKEN), "+150, +$8", "+300, +$20, hand x1.5"),
    Faction("harmony", "Harmony", (C.MIRROR, C.PRISM, C.TAIJI), "combo bonus 1 rank higher",
            "combo bonus 2 ranks higher, hand x1.5"),
    Faction("wild", "Wild", (C.WOLF, C.HAWK, C.DRAGON), "+60 per Element die played",
            "+150 per Element die played, hand x1.5"),
    Faction("cosmos", "Cosmos", (C.COMET, C.AURORA, C.GALAXY), "every combo +1 level", "every combo +3 levels, hand x1.5"),
    Faction("alchemy", "Alchemy", (C.SULFUR, C.MERCURY, C.PHOENIX), "+100, +$1 per scoring die",
            "+300, +$3 per scoring die, hand x2"),
    Faction("royal", "Royal", (C.KNIGHT, C.QUEEN, C.KING), "every Element played +1 level",
            "every Element played +3 levels, hand x1.5"),
)
FACTION_OF = {m: f for f in FACTIONS for m in f.members}
FACTION_COLOR = {
    "inferno": (255, 110, 40), "tide": (60, 150, 255), "tempest": (190, 140, 255), "terra": (210, 150, 90),
    "grove": (90, 220, 110), "fortune": (255, 215, 70), "chaos": (240, 90, 170), "night": (150, 120, 255),
    "spirit": (140, 240, 220), "clockwork": (214, 168, 84), "plunder": (40, 190, 170), "harmony": (236, 236, 250),
    "wild": (200, 120, 60), "cosmos": (110, 170, 255), "alchemy": (255, 120, 60), "royal": (230, 70, 120),
}
CARD_TIER = {m: tier for f in FACTIONS for tier, m in enumerate(f.members, 1)}
assert set(FACTION_OF) == set(CardType) and len(FACTION_OF) == 3 * len(FACTIONS), "each Element in exactly one faction"

CARD_COLOR = {
    C.FIRE: config.NEON_ORANGE, C.WATER: (52, 112, 200), C.WIND: (150, 200, 190), C.STONE: (140, 126, 110),
    C.GRASS: config.NEON_LIME, C.MIDAS: config.NEON_GOLD, C.JESTER: (208, 82, 140), C.STAR: (236, 210, 110),
    C.DEVIL: (196, 54, 66), C.ICE: config.NEON_CYAN, C.GLASS: (150, 186, 214), C.METAL: (128, 140, 160),
    C.THORN: (60, 130, 70), C.HOURGLASS: (48, 158, 130), C.WIZARD: (72, 122, 222), C.MOON: (150, 140, 210),
    C.SUN: (255, 150, 40), C.TSUNAMI: (30, 80, 170), C.LIGHTNING: config.NEON_PURPLE, C.QUAKE: (150, 96, 60),
    C.GAIA: (40, 170, 110), C.CRYSTAL: (230, 110, 210), C.STORM: (90, 100, 150), C.ECLIPSE: (70, 50, 110),
    C.GHOST: (190, 210, 220), C.ECHO: (90, 190, 180), C.VOID: (110, 80, 170),
    C.GEAR: (176, 140, 80), C.PISTON: (150, 156, 170), C.CHRONO: (226, 186, 70),
    C.DOUBLOON: (232, 196, 60), C.CUTLASS: (120, 180, 200), C.KRAKEN: (40, 150, 140),
    C.MIRROR: (200, 214, 236), C.PRISM: (170, 230, 255), C.TAIJI: (60, 60, 76),
    C.WOLF: (130, 130, 150), C.HAWK: (176, 110, 60), C.DRAGON: (220, 50, 40),
    C.COMET: (110, 200, 255), C.AURORA: (90, 230, 170), C.GALAXY: (90, 70, 200),
    C.SULFUR: (226, 220, 70), C.MERCURY: (180, 186, 200), C.PHOENIX: (255, 110, 30),
    C.KNIGHT: (150, 160, 190), C.QUEEN: (210, 80, 150), C.KING: (240, 190, 50),
}
# short text printed at the bottom of a card
CARD_DESC = {
    C.FIRE: "dice +20", C.WATER: "+6/die", C.WIND: "+20 +DSC", C.STONE: "heavy low", C.GRASS: "copy die",
    C.MIDAS: "+$10 -15%", C.JESTER: "chaos", C.STAR: "others +1",
    C.DEVIL: "+80 -1 DSC", C.ICE: "frost x2", C.GLASS: "x4 / break", C.METAL: "all 6s", C.THORN: "+35/kicker",
    C.HOURGLASS: "+PLAY -30%", C.WIZARD: "x3 or x1.5", C.MOON: "+20 each",
    C.SUN: "hand x1.5", C.TSUNAMI: "x per die", C.LIGHTNING: "chain x", C.QUAKE: "+50/die", C.GAIA: "all match",
    C.CRYSTAL: "bonus x2", C.STORM: "all x2", C.ECLIPSE: "x owned",
    C.GHOST: "+15/held", C.ECHO: "copy left", C.VOID: "x per DSC",
    C.GEAR: "+25/play", C.PISTON: "last x2.5", C.CHRONO: "x plays",
    C.DOUBLOON: "+2 per $", C.CUTLASS: "x2 +$", C.KRAKEN: "$5: x3",
    C.MIRROR: "flip dice", C.PRISM: "odd x3", C.TAIJI: "x variety",
    C.WOLF: "+20/pack", C.HAWK: "top x5", C.DRAGON: "x1.2/die",
    C.COMET: "+15/round", C.AURORA: "+15% rnd", C.GALAXY: "x skills",
    C.SULFUR: "1s -> 6s", C.MERCURY: "x rank", C.PHOENIX: "x ashes",
    C.KNIGHT: "+30/pawn", C.QUEEN: "right x2", C.KING: "others +2LV",
}
CARD_LONG = {
    C.FIRE: "Adds +20 to the dice value.",
    C.WATER: "Adds +6 to the dice value for every die that scores.",
    C.WIND: "+20 score and +1 discard this round.",
    C.STONE: "+20 score, +8 more for every pip below 6 on the scoring dice (low dice are heavy).",
    C.GRASS: "Copies its value onto the lowest other die played (Elements too).",
    C.MIDAS: "Earn $10, but the hand score is -15%.",
    C.JESTER: "Re-rolls every other die you play (Elements too) - great or awful.",
    C.STAR: "Every other die played gets +1, up to 6 (Elements too).",
    C.DEVIL: "+80 score, costs 1 discard (no bonus at 0 discards).",
    C.ICE: "Freezes the scoring dice: any below 4 counts as a 4, then dice value x2.",
    C.GLASS: "Dice value x4, but 20% chance it SHATTERS: hand scores 0.",
    C.METAL: "Every scoring die counts as a 6.",
    C.THORN: "+35 score for every played die that does NOT score.",
    C.HOURGLASS: "Refunds 1 play (once per round), but the hand score is -30%.",
    C.WIZARD: "A gamble with no downside: 50% dice value x3, else x1.5.",
    C.MOON: "+20 score for every Element you own.",
    C.SUN: "Hand score x1.5 (after the combo bonus).",
    C.TSUNAMI: "Dice value x the number of scoring dice (Pair x2, Full House x5).",
    C.LIGHTNING: "Chain lightning: dice value x(2 + 1 for every other Element die played).",
    C.QUAKE: "+50 score for every scoring die.",
    C.GAIA: "Every die played becomes the highest value played (Elements too).",
    C.CRYSTAL: "The combo bonus counts twice.",
    C.STORM: "Every played die scores (kickers too), then dice value x2.",
    C.ECLIPSE: "Hand score x(1 + 0.15 for every Element you own).",
    C.GHOST: "+15 score for every die you keep in your hand (not played).",
    C.ECHO: "Copies the effect of the Element just to its left in the played dice.",
    C.VOID: "Hand score x(1 + 0.3 per discard you have left).",
    C.GEAR: "+25 score for every play you already used this round.",
    C.PISTON: "Hand score x2.5 on your LAST play of the round, otherwise +40.",
    C.CHRONO: "Hand score x(1 + 0.5 per play you have left, this one included): strongest early.",
    C.DOUBLOON: "+2 score for every $1 you hold (up to +120).",
    C.CUTLASS: "Dice value x2, and +$1 for every scoring die.",
    C.KRAKEN: "Pays $5 to strike: hand score x3. Can't pay: only x1.3.",
    C.MIRROR: "Flips every other played die upside down (1<>6, 2<>5, 3<>4), Elements too.",
    C.PRISM: "Every scoring die showing an odd value counts x3.",
    C.TAIJI: "Hand score x(1 + 0.4 for every different value among the played dice beyond the first).",
    C.WOLF: "Pack hunter: +20 score for every Element die played (itself too).",
    C.HAWK: "Dives on the highest scoring die: it counts x5.",
    C.DRAGON: "Roars once per scoring die: hand score x1.2 for each.",
    C.COMET: "+15 score for every round you already cleared this run.",
    C.AURORA: "+15% of your round score so far (at least +60), added after every multiplier.",
    C.GALAXY: "Hand score x(1.2 + 0.05 for every skill you bought), up to x3.",
    C.SULFUR: "Transmutes: every played die showing a 1 becomes a 6 (Elements too).",
    C.MERCURY: "+ the raw dice points x the combo rank (Pair 2 ... Five of a Kind 8).",
    C.PHOENIX: "Rises from the ashes: hand score x(1.5 + 0.4 per discard already used this round).",
    C.KNIGHT: "Leads the pawns: +30 score for every normal (non-Element) die that scores.",
    C.QUEEN: "Crowns the Element just to her right: it triggers TWICE (its costs too).",
    C.KING: "Hand score x1.5, and every other Element played acts 2 levels higher.",
}


def level_scale(level):
    """How much bigger an Element's numbers are at this level: x1.1 per level above 1, compounding."""
    return config.ELEMENT_LEVEL_STEP ** (level - 1)


def element_price(ctype):
    return config.ELEMENT_TIER_PRICE[CARD_TIER[ctype]]


_uid = itertools.count(1)


@dataclass
class MultiplierCard:
    type: CardType
    price: int = 0                      # what was paid in total (selling refunds half); 0 = the tier price
    uid: int = field(default_factory=lambda: next(_uid))
    level: int = 1                      # buying the same Element again levels it up (numbers x1.1 per level)

    def __post_init__(self):
        self.price = self.price or element_price(self.type)

    @property
    def tier(self):
        return CARD_TIER[self.type]


@dataclass(frozen=True)
class SkillDef:
    key: str
    name: str
    desc: str
    combo: str          # the combo this skill levels up
    kind: str = "level"
    price: int = config.SKILL_PRICE


@dataclass(frozen=True)
class VoucherDef:
    key: str
    name: str
    desc: str
    max_level: int
    price: int = config.VOUCHER_PRICE


SKILL_DEFS = {s["key"]: SkillDef(**s) for s in config.SKILLS}
VOUCHER_DEFS = {v["key"]: VoucherDef(**v) for v in config.VOUCHERS}
