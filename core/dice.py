from dataclasses import dataclass


@dataclass(frozen=True)
class Die:
    value: int            # 1..6 - dice only show their pips
    kind: object = None   # None = normal die, else a CardType (an Element's special die)


def build_deck():
    """24 dice: four of every value 1-6."""
    return [Die(v) for _ in range(4) for v in range(1, 7)]
