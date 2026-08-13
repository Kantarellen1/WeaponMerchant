import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

AUCTION_FILE = Path(__file__).resolve().parent / "auction_house.json"
PLAYER_INVENTORIES_FILE = Path(__file__).resolve().parent.parent / "character" / "player_inventories.json"
PLAYER_DATA_FILE = Path(__file__).resolve().parent.parent / "character" / "player_data.json"


def load_player_data():
    try:
        with open(PLAYER_DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

    migrated = False
    for player_id, player in data.items():
        if not isinstance(player, dict):
            continue
        if "gold" not in player:
            player["gold"] = 0
            migrated = True
    if migrated:
        save_player_data(data)
    return data


def save_player_data(data):
    PLAYER_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PLAYER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_player_gold(player_id):
    data = load_player_data()
    player = data.get(player_id)
    if player is None:
        return None
    return player.get("gold", 0)


def player_exists(player_id):
    data = load_player_data()
    return player_id in data


def remove_item_from_inventory(inventories, player_id, item_name, quantity):
    if quantity <= 0:
        return False
    player_items = inventories.get(player_id, [])
    for inv_item in player_items:
        if inv_item["item_name"] == item_name:
            if inv_item["quantity"] < quantity:
                return False
            inv_item["quantity"] -= quantity
            if inv_item["quantity"] == 0:
                player_items.remove(inv_item)
            inventories[player_id] = player_items
            return True
    return False


def add_item_to_inventory(inventories, player_id, item_name, quantity):
    if quantity <= 0:
        return False
    player_items = inventories.setdefault(player_id, [])
    for inv_item in player_items:
        if inv_item["item_name"] == item_name:
            inv_item["quantity"] += quantity
            return True
    player_items.append({"item_name": item_name, "quantity": quantity})
    return True


def change_player_gold(player_id, amount):
    data = load_player_data()
    player = data.get(player_id)
    if player is None:
        return False
    player["gold"] = player.get("gold", 0) + amount
    save_player_data(data)
    return True


def load_auction_listings():
    try:
        with open(AUCTION_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("auction_listings", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_auction_listings(listings):
    with open(AUCTION_FILE, "w", encoding="utf-8") as f:
        json.dump({"auction_listings": listings}, f, indent=2)


def load_player_inventories():
    try:
        with open(PLAYER_INVENTORIES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_player_inventories(inventories):
    PLAYER_INVENTORIES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PLAYER_INVENTORIES_FILE, "w", encoding="utf-8") as f:
        json.dump(inventories, f, indent=2)


def parse_iso_datetime(dt_str):
    if dt_str.endswith("Z"):
        dt_str = dt_str[:-1] + "+00:00"
    dt = datetime.fromisoformat(dt_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _return_item_to_inventory(inventories, seller_id, item_name, quantity):
    player_items = inventories.setdefault(seller_id, [])
    for inv_item in player_items:
        if inv_item["item_name"] == item_name:
            inv_item["quantity"] += quantity
            break
    else:
        player_items.append({"item_name": item_name, "quantity": quantity})


def create_listing(item_name, seller_id, price, quantity, duration_hours=1):
    now = datetime.now(timezone.utc)
    listing = {
        "item_id": uuid.uuid4().hex,
        "item_name": item_name,
        "seller_id": seller_id,
        "price": round(float(price), 2),
        "quantity": int(quantity),
        "time_listed": now.isoformat(),
        "expires_at": (now + timedelta(hours=int(duration_hours))).isoformat(),
    }
    listings = load_auction_listings()
    listings.append(listing)
    save_auction_listings(listings)
    return listing


def cleanup_expired_auctions():
    listings = load_auction_listings()
    inventories = load_player_inventories()
    now = datetime.now(timezone.utc)
    active_listings = []

    for item in listings:
        expires_at = item.get("expires_at")
        if expires_at and parse_iso_datetime(expires_at) <= now:
            _return_item_to_inventory(
                inventories,
                item["seller_id"],
                item["item_name"],
                item["quantity"],
            )
            continue
        active_listings.append(item)

    save_auction_listings(active_listings)
    save_player_inventories(inventories)
    return active_listings


def cancel_auction_listing(item_id):
    listings = load_auction_listings()
    inventories = load_player_inventories()
    for index, item in enumerate(listings):
        if item.get("item_id") == item_id:
            _return_item_to_inventory(
                inventories,
                item["seller_id"],
                item["item_name"],
                item["quantity"],
            )
            listings.pop(index)
            save_auction_listings(listings)
            save_player_inventories(inventories)
            return item
    return None


def get_market_price(item_name, lookback_hours=24, method="median"):
    """Return a market price for item_name based on current auction listings.
    Uses active listings as a simple market snapshot. Returns None if no data.
    """
    listings = load_auction_listings()
    prices = [float(l.get("price", 0)) for l in listings if l.get("item_name", "").lower() == item_name.lower()]
    if not prices:
        return None
    if method == "median":
        try:
            import statistics

            return round(statistics.median(prices), 2)
        except Exception:
            return round(sum(prices) / len(prices), 2)
    # fallback to average
    return round(sum(prices) / len(prices), 2)


def get_market_snapshot(item_name):
    """Return a small snapshot (count, avg, median) for diagnostics or decisions."""
    listings = load_auction_listings()
    prices = []
    total_quantity = 0
    for l in listings:
        if l.get("item_name", "").lower() == item_name.lower():
            try:
                prices.append(float(l.get("price", 0)))
            except Exception:
                continue
            try:
                total_quantity += int(l.get("quantity", 1))
            except Exception:
                total_quantity += 1

    if not prices:
        return {"count": 0, "avg": None, "median": None, "total_quantity": 0}
    import statistics

    return {
        "count": len(prices),
        "avg": round(sum(prices) / len(prices), 2),
        "median": round(statistics.median(prices), 2),
        "total_quantity": int(total_quantity),
    }


def buy_auction_listing(listing_id: str, buyer_id: str, quantity: int = 1):
    """Attempt to buy `quantity` units from an auction listing.

    Transfers gold from buyer to seller, moves items into buyer inventory,
    and updates/removes the listing. Returns (True, details) or (False, error).
    """
    if quantity <= 0:
        return False, "Quantity must be positive"

    listings = load_auction_listings()
    for idx, listing in enumerate(listings):
        if listing.get("item_id") == listing_id:
            avail = int(listing.get("quantity", 1))
            if quantity > avail:
                return False, "Not enough quantity in listing"

            unit_price = float(listing.get("price", 0))
            total_price = round(unit_price * int(quantity), 2)

            buyer_gold = get_player_gold(buyer_id)
            if buyer_gold is None:
                return False, "Buyer not found"
            if buyer_gold < total_price:
                return False, "Insufficient gold"

            # Deduct buyer gold
            if not change_player_gold(buyer_id, -total_price):
                return False, "Failed to deduct buyer gold"

            # Credit seller (if seller exists in player data)
            seller_id = listing.get("seller_id")
            try:
                change_player_gold(seller_id, total_price)
            except Exception:
                # best effort; if seller not a player this may fail silently
                pass

            # Add item to buyer inventory
            inventories = load_player_inventories()
            item_name = listing.get("item_name")
            added = add_item_to_inventory(inventories, buyer_id, item_name, int(quantity))
            if not added:
                # rollback buyer gold and seller credit
                change_player_gold(buyer_id, total_price)
                change_player_gold(seller_id, -total_price)
                return False, "Failed to add item to buyer inventory"
            save_player_inventories(inventories)

            # Update or remove listing
            if quantity == avail:
                listings.pop(idx)
            else:
                listing["quantity"] = avail - int(quantity)
            save_auction_listings(listings)

            return True, {"item": item_name, "quantity": int(quantity), "unit_price": unit_price, "total": total_price}

    return False, "Listing not found"
