import json
import math
import random
import time
from pathlib import Path
from typing import Optional

from auction_house.auction_data import (
    get_market_price,
    get_market_snapshot,
    get_player_gold,
    change_player_gold,
    load_player_inventories,
    save_player_inventories,
    add_item_to_inventory,
    remove_item_from_inventory,
)
from guilds.main_guild_data import get_baseline_price

INVENTORY_FILE = Path(__file__).resolve().parent / "inventories.json"


class MerchantInventory:
    """Simple per-merchant inventory manager with pricing tied to auction market data.

    Each merchant entry in `inventories.json` should look like:
    {
      "name": "Finn General Store",
      "bias": -0.02,   # merchant-specific price bias (negative => slightly cheaper)
      "competitiveness": 0.6, # 0..1, larger => more aggressive undercutting
      "inventory": [ {"item_id":"potion_small","name":"Small Potion","base_price":10,"quantity":20,"demand":5,"supply":20} ]
    }
    """

    def __init__(self, merchant_id: str):
        self.merchant_id = merchant_id
        self._load_all()
        self.data = self._all.get(merchant_id, {"name": merchant_id, "inventory": [], "bias": 0.0, "competitiveness": 0.5})

    def _load_all(self):
        try:
            with open(INVENTORY_FILE, "r", encoding="utf-8") as f:
                self._all = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._all = {}

    def save(self):
        self._all[self.merchant_id] = self.data
        INVENTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(INVENTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self._all, f, indent=2, ensure_ascii=False)

    def get_item(self, item_key: str):
        for it in self.data.get("inventory", []):
            if it.get("item_id") == item_key or it.get("name", "").lower() == item_key.lower():
                return it
        return None

    def change_quantity(self, item_key: str, delta: int) -> bool:
        it = self.get_item(item_key)
        if not it:
            return False
        # If merchant has unlimited stock, don't reduce stored quantity on purchases,
        # but still track demand for pricing.
        if self.data.get("unlimited") and int(delta) < 0:
            # only update demand counter
            it["last_modified"] = int(time.time())
            it["demand"] = int(it.get("demand", 0)) + abs(int(delta))
            self.save()
            return True

        it["quantity"] = max(0, int(it.get("quantity", 0)) + int(delta))
        it["last_modified"] = int(time.time())
        # update simple supply/demand counters
        if delta < 0:
            it["demand"] = int(it.get("demand", 0)) + abs(int(delta))
        else:
            it["supply"] = int(it.get("supply", 0)) + int(delta)
        self.save()
        return True

    def compute_price(self, item_key: str, fallback_base: Optional[float] = None) -> float:
        """Compute a merchant's price for an item by combining market price and local factors."""
        item = self.get_item(item_key)
        if item is None:
            base_price = fallback_base or 1.0
            item_name = item_key
            demand = 0
            supply = 0
        else:
            base_price = float(item.get("base_price", fallback_base or 1.0))
            item_name = item.get("name", item.get("item_id", item_key))
            demand = float(item.get("demand", 0))
            supply = float(item.get("supply", 0))

        # market-derived price (may be None)
        market_price = get_market_price(item_name)
        if market_price is None:
            market_price = base_price

        # derive market snapshot data to correlate demand with auction house
        try:
            snapshot = get_market_snapshot(item_name)
            market_total_qty = float(snapshot.get("total_quantity", 0))
        except Exception:
            market_total_qty = 0.0

        # If this merchant is unlimited, treat its local supply as very large
        if self.data.get("unlimited"):
            local_supply = 1e6
        else:
            local_supply = float(item.get("quantity", 0))

        # Compute supply-driven multiplier: more items on market -> lower price.
        # Use log scaling to avoid extreme swings. gamma controls sensitivity.
        gamma = 0.12
        supply_factor = math.log1p(market_total_qty)  # increases with market quantity
        price = market_price * math.exp(-gamma * supply_factor)

        # apply merchant bias and competitiveness (undercut or markup)
        bias = float(self.data.get("bias", 0.0))
        competitiveness = float(self.data.get("competitiveness", 0.5))
        # competitiveness -> merchant will undercut market up to ~5% * competitiveness
        undercut = 1.0 - (0.05 * competitiveness)
        price *= (1.0 + bias) * undercut

        # Clamp extreme swings to avoid market-manipulation exploits. Merchant
        # price won't go below `min_mult * market_price` or above `max_mult * market_price`.
        min_mult = 0.6
        max_mult = 2.0
        price = max(min_mult * market_price, min(price, max_mult * market_price))

        # small volatility to avoid identical pricing every call
        volatility = 0.02
        price *= 1.0 + random.uniform(-volatility, volatility)

        # floor, round
        price = max(0.01, round(price, 2))

        # enforce guild baseline price when available so regulated items
        # cannot be sold below the guild's minimum.
        try:
            baseline = get_baseline_price(item_name)
            if baseline is not None:
                price = max(price, float(baseline))
        except Exception:
            pass

        return price


if __name__ == "__main__":
    # quick demo
    m = MerchantInventory("finn")
    print("Inventory for finn:", m.data)
    print("Price for Small Potion:", m.compute_price("potion_small", fallback_base=10))


def purchase_from_merchant(player_id: str, merchant_id: str, item_key: str, quantity: int = 1):
    """Handle a player buying `quantity` of `item_key` from `merchant_id`.

    Returns (True, details) on success or (False, error_message) on failure.
    This will deduct player gold, add the item to the player's inventory,
    and decrease the merchant's stock. Basic rollback attempts are made
    if a step fails after gold deduction.
    """
    if quantity <= 0:
        return False, "Quantity must be positive"

    inv = MerchantInventory(merchant_id)
    item = inv.get_item(item_key)
    if not item:
        return False, "Item not found"

    # Allow unlimited merchants to sell arbitrary amounts; otherwise enforce stock
    if not inv.data.get("unlimited") and int(item.get("quantity", 0)) < int(quantity):
        return False, "Merchant does not have enough stock"

    unit_price = inv.compute_price(item_key, fallback_base=item.get("base_price"))
    total_price = round(unit_price * int(quantity), 2)

    player_gold = get_player_gold(player_id)
    if player_gold is None:
        return False, "Player not found"
    if player_gold < total_price:
        return False, "Insufficient gold"

    # Deduct gold first
    ok = change_player_gold(player_id, -total_price)
    if not ok:
        return False, "Failed to deduct gold"

    # Add item to player's inventories
    inventories = load_player_inventories()
    try:
        added = add_item_to_inventory(inventories, player_id, item.get("name", item.get("item_id")), int(quantity))
        if not added:
            # rollback gold
            change_player_gold(player_id, total_price)
            return False, "Failed to add item to player inventory"
        save_player_inventories(inventories)
    except Exception as e:
        change_player_gold(player_id, total_price)
        return False, f"Error updating player inventory: {e}"

    # Decrease merchant stock
    try:
        inv.change_quantity(item_key, -int(quantity))
    except Exception as e:
        # attempt rollback: remove from player and refund
        inv.change_quantity(item_key, int(quantity))
        inventories = load_player_inventories()
        # remove simple: try to remove quantity we added
        removed = False
        try:
            removed = remove_item_from_inventory(inventories, player_id, item.get("name", item.get("item_id")), int(quantity))
            save_player_inventories(inventories)
        except Exception:
            pass
        change_player_gold(player_id, total_price)
        return False, f"Failed to update merchant stock: {e}"

    return True, {"item": item.get("name", item.get("item_id")), "quantity": int(quantity), "unit_price": unit_price, "total": total_price}


def quote_purchase(player_id: str, merchant_id: str, item_key: str, quantity: int = 1):
    """Return a quote for buying `quantity` of `item_key` from `merchant_id`.

    Returns a dict: {unit_price, total_price, affordable, player_gold, available_quantity}
    `available_quantity` is None for unlimited merchants.
    """
    if quantity <= 0:
        return {"error": "Quantity must be positive"}

    inv = MerchantInventory(merchant_id)
    item = inv.get_item(item_key)
    if not item:
        return {"error": "Item not found"}

    unit_price = inv.compute_price(item_key, fallback_base=item.get("base_price"))
    total_price = round(unit_price * int(quantity), 2)

    player_gold = get_player_gold(player_id)
    affordable = (player_gold is not None and player_gold >= total_price)

    if inv.data.get("unlimited"):
        available = None
    else:
        available = int(item.get("quantity", 0))

    return {
        "unit_price": unit_price,
        "total_price": total_price,
        "affordable": affordable,
        "player_gold": player_gold,
        "available_quantity": available,
    }
