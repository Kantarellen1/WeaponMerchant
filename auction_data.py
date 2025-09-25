import json

AUCTION_FILE = "auction_house.json"

def load_auction_listings():
    try:
        with open(AUCTION_FILE, "r") as f:
            data = json.load(f)
            return data.get("auction_listings", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_auction_listings(listings):
    with open(AUCTION_FILE, "w") as f:
        json.dump({"auction_listings": listings}, f, indent=2)

def return_expired_auctions():
    from auction_data import load_auction_listings, save_auction_listings
    import json
    from datetime import datetime

    # Load current auctions and inventories
    listings = load_auction_listings()
    try:
        with open("player_inventories.json", "r") as f:
            inventories = json.load(f)
    except FileNotFoundError:
        inventories = {}

    now = datetime.utcnow()
    active_listings = []
    for item in listings:
        expires_at = item.get("expires_at")
        if expires_at and datetime.fromisoformat(expires_at) < now:
            # Auction expired, return to seller
            seller = item["seller_id"]
            item_name = item["item_name"]
            quantity = item["quantity"]
            player_items = inventories.setdefault(seller, [])
            for inv_item in player_items:
                if inv_item["item_name"] == item_name:
                    inv_item["quantity"] += quantity
                    break
            else:
                player_items.append({"item_name": item_name, "quantity": quantity})

    # Save updated auctions and inventories
    save_auction_listings(active_listings)
    with open("player_inventories.json", "w") as f:
        json.dump(inventories, f, indent=2)