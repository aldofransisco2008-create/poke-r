import random

import config
from core.cards import CARD_TIER, FACTION_OF, CardType, MultiplierCard, SKILL_DEFS, VOUCHER_DEFS, element_price

ELEMENT_TYPES = list(CardType)
VOUCHER_KEYS = list(VOUCHER_DEFS)


def tier_weights(run=None):
    """Tier odds per offer: common 60%, rare 30%, super 10% - the Lucky Charm voucher moves weight to rare/super."""
    w = dict(config.ELEMENT_TIER_WEIGHTS)
    lucky = run.level("lucky") if run else 0
    w[1] -= config.LUCKY_SHIFT * lucky
    w[2] += config.LUCKY_SHIFT * lucky // 2
    w[3] += config.LUCKY_SHIFT * lucky // 2
    return w


def faction_wants(run):
    """Elements that would grow a faction you already own (members you don't have yet)."""
    if not run:
        return []
    owned = {c.type for c in run.slots}
    return [m for f in {FACTION_OF[c] for c in owned} for m in f.members if m not in owned]


def element_offers(rng=random, n=config.ELEMENT_OFFERS, run=None):
    """A fresh random selection of Elements for one shop visit (no repeats). Each offer has a FACTION_BIAS chance to be a
    missing member of a faction you own (so factions can actually be built); otherwise it rolls a tier with
    tier_weights() and then an Element of that tier."""
    w = tier_weights(run)
    tiers = list(w)
    weights = [w[t] for t in tiers]
    wants = faction_wants(run)
    out = []
    while len(out) < n:
        pool = [c for c in wants if c not in out]
        if pool and rng.random() < config.FACTION_BIAS:
            out.append(rng.choice(pool))
            continue
        tier = rng.choices(tiers, weights)[0]
        pool = [c for c in ELEMENT_TYPES if CARD_TIER[c] == tier and c not in out]
        if pool:
            out.append(rng.choice(pool))
    return out


def skill_offers(rng=random, n=config.SKILL_OFFERS):
    """A fresh random selection of skills for one shop visit (no repeats)."""
    return rng.sample(list(SKILL_DEFS), n)


def buy_element(run, ctype):
    """Buy an Element (special die). If you already own it, it levels up instead of taking a slot.
    Returns the card, or a reason string: 'money' | 'full'."""
    price = element_price(ctype)
    owned = run.element_card(ctype)
    if owned is None and run.slots_full():
        return "full"
    if run.money < price:
        return "money"
    run.money -= price
    if owned is not None:
        owned.level += 1
        owned.price += price
        return owned
    card = MultiplierCard(ctype, price)
    run.add_card(card)
    return card


def refresh_price(refreshes):
    """Re-rolling the Element and skill offers: $10, +$2 for every refresh already made in this shop visit."""
    return config.REFRESH_PRICE + config.REFRESH_STEP * refreshes


def refresh(run, refreshes, rng=random):
    """Pay for a refresh and return new (element offers, skill offers), or None if it cannot be afforded."""
    price = refresh_price(refreshes)
    if run.money < price:
        return None
    run.money -= price
    return element_offers(rng, run=run), skill_offers(rng)


def buy_skill(run, key):
    price = run.skill_price()
    if run.money < price or run.skill_full(key):
        return False
    run.money -= price
    run.add_skill(key)
    return True


def buy_voucher(run, key=None):
    """Buy the voucher of the current stock (one random voucher, refilled every VOUCHER_RESTOCK rounds)."""
    key = key or run.voucher_offer()
    if key is None or key != run.voucher_offer() or run.voucher_sold(key) or run.voucher_maxed(key):
        return False
    price = run.voucher_price(key)
    if run.money < price:
        return False
    run.money -= price
    run.vouchers[key] = run.level(key) + 1
    run.voucher_bought[key] = run.voucher_stock()
    return True
