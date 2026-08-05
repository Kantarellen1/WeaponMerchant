from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from merchants.merchant_data import (
    get_merchant_response,
    get_merchant_response_by_id,
    save_memory,
    load_memory,
    get_memory_key,
    build_prompt,
    run_ollama,
    get_fallback_response,
)
from auction_house.auction_data import (
    create_listing,
    cleanup_expired_auctions,
    cancel_auction_listing,
    load_auction_listings,
    save_auction_listings,
    load_player_inventories,
    save_player_inventories,
)
from datetime import datetime, timedelta, timezone
import json
from character.main_class_data import create_player
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

MINIMUM_PRICES = {
    "Longsword": 40,
    "Shortsword": 25,
    "Battle Axe": 45,
    "Dagger": 10,
    "Wooden Shield": 15,
    "Iron Shield": 30,
    "Leather Armor": 20,
    "Chainmail": 60,
    "Plate Armor": 120,
    "Healing potion": 20,
    "Mana potion": 20,
    "Stamina elixir": 15
}

def get_merchant_buy_price(item_name):
    min_price = MINIMUM_PRICES.get(item_name)
    if min_price is not None:
        return round(min_price * 0.95, 2)  # 5% under minimum price, rounded to 2 decimals
    return None

def parse_iso_datetime(dt_str):
    # Remove duplicate timezone info if present
    if "+00:00+00:00" in dt_str:
        dt_str = dt_str.replace("+00:00+00:00", "+00:00")
    if dt_str.endswith("Z"):
        dt_str = dt_str[:-1] + "+00:00"
    dt = datetime.fromisoformat(dt_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt

def get_merchant_response_by_id(player_id, merchant_id, message):
    memory = load_memory()
    memory_key = get_memory_key(player_id, merchant_id)
    history = memory.get(memory_key, [])

    history.append({"role": "player", "message": message})

    prompt = build_prompt(merchant_id, history)
    response = run_ollama(prompt)

    if not response:
        response = get_fallback_response(merchant_id, message)

    history.append({"role": "merchant", "message": response})
    memory[memory_key] = history
    save_memory(memory)

    return response

@app.get("/merchant/last_message")
async def merchant_last_message(player_id: str, merchant_id: str):
    memory = load_memory()
    key = get_memory_key(player_id, merchant_id)
    convo = memory.get(key, [])
    if not convo:
        return {"message": "No conversation found."}
    return {"last": convo[-1], "full_length": len(convo)}

@app.get("/")
async def read_root():
    return {
        "message": "Welcome to Edvin's Merchant District!",
        "endpoints": {
            "/town": "Visit the town square",
            "/smithy": "Visit Gerik's Smithy", 
            "/apothecary": "Visit Elara's Apothecary",
            "/general-store": "Visit Finn's General Store"
        }
    }

@app.get("/town")
async def town_square():
    return FileResponse("static/town_square.html")

@app.get("/smithy")
async def gerik_smithy():
    return FileResponse("static/gerik_smithy.html")

@app.get("/apothecary") 
async def elara_apothecary():
    return FileResponse("static/elara_apothecary.html")

@app.get("/general-store")
async def finn_store():
    return FileResponse("static/finn_general_store.html")

@app.get("/auction-house")
async def auction_house():
    return FileResponse("static/auction_house.html")

@app.get("/create_character")
async def create_character():
    return FileResponse("static/create_character.html")

@app.post("/talk_to_merchant")
async def talk_to_merchant(request: Request):
    data = await request.json()
    player_id = data.get("player_id")
    message = data.get("message")
    merchant_id = data.get("merchant_id")        # optional: allow direct merchant lookup
    player_location = data.get("player_location")  # optional
    shop_type = data.get("shop_type")              # optional

    if not player_id or not message:
        return {"error": "Missing player_id or message."}

    if merchant_id:
        # If merchant_id provided, use the ID-based flow (no town/shop required)
        response = get_merchant_response_by_id(player_id, merchant_id, message)
    else:
        # Fallback to location+shop_type flow (both required if merchant_id not given)
        if not player_location or not shop_type:
            return {"error": "Missing merchant_id or player_location+shop_type."}
        response = get_merchant_response(player_id, player_location, shop_type, message)

    logger.info(f"merchant (resolved): {response}")
    return {"response": response}

@app.post("/talk_to_merchant/{merchant_id}")
async def talk_to_merchant_by_id(merchant_id: str, request: Request):
    data = await request.json()
    player_id = data.get("player_id")
    message = data.get("message")
    player_location = data.get("player_location")   # optional
    shop_type = data.get("shop_type")               # optional

    if not player_id or not message:
        return {"error": "Missing player_id or message."}

    if player_location and shop_type:
        response = get_merchant_response(player_id, player_location, shop_type, message)
    else:
        response = get_merchant_response_by_id(player_id, merchant_id, message)

    logger.info(f"merchant ({merchant_id}): {response}")  # <-- log the response
    return {"response": response}

@app.post("/merchant/sell")
async def merchant_buy(request: Request):
    data = await request.json()
    item_name = data.get("item_name")
    quantity = int(data.get("quantity", 1))
    buy_price = get_merchant_buy_price(item_name)
    if buy_price is None:
        return {"message": f"{item_name} cannot be sold to merchants."}
    total = buy_price * quantity
    return {
        "message": f"The merchant offers {buy_price} gold per {item_name} (total: {total} gold) for your {quantity} item(s)."
    }

@app.post("/create_player")
async def create_player_endpoint(request: Request):
    data = await request.json()
    player_id = data.get("player_id")
    first_class = data.get("first_class")
    if not player_id or not first_class:
        return {"message": "Missing player_id or first_class."}
    if create_player(player_id, first_class):
        return {"message": f"Player {player_id} created as {first_class}!"}
    else:
        return {"message": f"Player {player_id} already exists or invalid class."}
    

@app.post("/auction/list")
async def list_item(request: Request):
    data = await request.json()
    item_name = data.get("item_name")
    seller_id = data.get("seller_id")
    price = data.get("price")
    quantity = data.get("quantity", 1)
    duration_hours = data.get("duration", 1)

    if not item_name or not seller_id or price is None:
        return {"message": "Missing item_name, seller_id, or price."}

    try:
        price = float(price)
        quantity = int(quantity)
        duration_hours = int(duration_hours)
    except (TypeError, ValueError):
        return {"message": "Price, quantity, and duration must be numbers."}

    min_price = MINIMUM_PRICES.get(item_name)
    if min_price is not None and price < min_price:
        return {"message": f"Minimum price for {item_name} is {min_price}."}

    listing = create_listing(item_name, seller_id, price, quantity, duration_hours)
    return {"message": "Item listed!", "listing": listing}

@app.get("/auction/browse")
async def browse_auction():
    active_listings = cleanup_expired_auctions()
    now = datetime.now(timezone.utc)
    valid_listings = [
        item for item in active_listings
        if "expires_at" not in item or parse_iso_datetime(item["expires_at"]) > now
    ]
    return {"auction_listings": valid_listings}

@app.post("/auction/buy")
async def buy_item(request: Request):
    data = await request.json()
    item_id = data.get("item_id")
    quantity = int(data.get("quantity", 1))
    buyer_id = data.get("buyer_id")

    if not item_id or not buyer_id:
        return {"message": "Missing item_id or buyer_id."}

    listings = load_auction_listings()
    now = datetime.now(timezone.utc)
    for i, item in enumerate(listings):
        if item.get("item_id") != item_id:
            continue

        if "expires_at" in item and parse_iso_datetime(item["expires_at"]) <= now:
            return {"message": "This listing has expired."}

        if item["quantity"] < quantity:
            return {"message": "Insufficient quantity available."}

        total_price = item["price"] * quantity
        tax = round(total_price * 0.05, 2)
        payout = round(total_price - tax, 2)

        if item["quantity"] == quantity:
            listings.pop(i)
        else:
            item["quantity"] -= quantity

        save_auction_listings(listings)

        inventories = load_player_inventories()
        buyer_items = inventories.setdefault(buyer_id, [])
        for inv_item in buyer_items:
            if inv_item["item_name"] == item["item_name"]:
                inv_item["quantity"] += quantity
                break
        else:
            buyer_items.append({"item_name": item["item_name"], "quantity": quantity})
        save_player_inventories(inventories)

        return {
            "message": (
                f"Purchase successful! {item['seller_id']} receives {payout} gold after 5% tax ({tax} gold taken)."
            ),
            "tax": tax,
            "seller_payout": payout,
            "item": item,
            "quantity_bought": quantity
        }

    return {"message": "Listing not found."}

@app.post("/auction/cancel")
async def cancel_listing(request: Request):
    data = await request.json()
    item_id = data.get("item_id")
    if not item_id:
        return {"message": "Missing item_id."}

    canceled = cancel_auction_listing(item_id)
    if canceled:
        return {"message": "Listing canceled.", "listing": canceled}
    return {"message": "Listing not found."}
