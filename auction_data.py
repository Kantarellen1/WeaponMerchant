import json

AUCTION_FILE = "auction_house.json"

def load_auction_listings():
    try:
        with open(AUCTION_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_auction_listings(listings):
    with open(AUCTION_FILE, "w") as f:
        json.dump(listings, f, indent=2)