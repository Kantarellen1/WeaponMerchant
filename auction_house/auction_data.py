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
