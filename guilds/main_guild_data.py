main_guild_prices = {
    "Longsword": 50,
    "Shortsword": 35,
    "Battle Axe": 60,
    "Dagger": 15,
    "Wooden Shield": 20,
    "Iron Shield": 40,
    "Leather Armor": 25,
    "Chainmail": 75,
    "Plate Armor": 150,
    "Healing potion": 30,
    "Mana potion": 25,
    "Stamina elixir": 20
}


def get_baseline_price(item_name):
    """Return the guild baseline price for an item, or None if unknown.

    Performs a case-insensitive exact match against known names in
    `main_guild_prices`.
    """
    if not item_name:
        return None
    key = item_name.strip().lower()
    for k, v in main_guild_prices.items():
        if k.lower() == key:
            try:
                return float(v)
            except Exception:
                return None
    return None
