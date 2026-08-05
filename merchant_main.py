from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
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
    load_player_data,
    change_player_gold,
    get_player_gold,
    player_exists,
    remove_item_from_inventory,
    add_item_to_inventory,
)
from datetime import datetime, timedelta, timezone
from pathlib import Path
import secrets
import json
from character.main_class_data import (
    create_player,
    verify_player_password,
    get_player_profile,
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

SESSION_FILE = Path(__file__).resolve().parent.parent / "character" / "player_sessions.json"

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

def load_player_sessions():
    try:
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_player_sessions(sessions):
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, indent=2)


def create_session(player_id):
    sessions = load_player_sessions()
    token = secrets.token_hex(24)
    sessions[token] = {
        "player_id": player_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    save_player_sessions(sessions)
    return token


def validate_session(session_token):
    if not session_token:
        return None
    sessions = load_player_sessions()
    session = sessions.get(session_token)
    if not session:
        return None
    return session.get("player_id")


def delete_session(session_token):
    sessions = load_player_sessions()
    if session_token in sessions:
        sessions.pop(session_token)
        save_player_sessions(sessions)
        return True
    return False


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
    return RedirectResponse(url="/login")

@app.get("/login")
async def login_page():
    login_path = STATIC_DIR / "login.html"
    if not login_path.exists():
        logger.error(f"Login file not found at {login_path}")
        return {"message": "Login page not found on server."}
    return FileResponse(login_path)

@app.get("/town")
async def town_square():
    return FileResponse(STATIC_DIR / "town_square.html")

@app.get("/smithy")
async def gerik_smithy():
    return FileResponse(STATIC_DIR / "gerik_smithy.html")

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
    password = data.get("password")
    if not player_id or not first_class:
        return {"message": "Missing player_id or first_class."}
    if create_player(player_id, first_class, password):
        return {"message": f"Player {player_id} created as {first_class}!"}
    else:
        return {"message": f"Player {player_id} already exists or invalid class."}


@app.post("/auth/register")
async def register_player(request: Request):
    data = await request.json()
    player_id = data.get("player_id")
    first_class = data.get("first_class")
    password = data.get("password")
    if not player_id or not first_class or not password:
        return {"message": "Missing player_id, first_class, or password."}
    if create_player(player_id, first_class, password):
        return {"message": f"Registered player {player_id}. You can now log in."}
    return {"message": "Player already exists or invalid class."}


@app.post("/auth/login")
async def login_player(request: Request):
    data = await request.json()
    player_id = data.get("player_id")
    password = data.get("password")
    if not player_id or password is None:
        return {"message": "Missing player_id or password."}
    if not verify_player_password(player_id, password):
        return {"message": "Invalid login credentials."}

    session_token = create_session(player_id)
    profile = get_player_profile(player_id)
    inventory = load_player_inventories().get(player_id, [])
    gold = get_player_gold(player_id)
    return {
        "message": "Login successful.",
        "session_token": session_token,
        "player_id": player_id,
        "profile": profile,
        "inventory": inventory,
        "gold": gold,
    }


@app.post("/auth/logout")
async def logout_player(request: Request):
    data = await request.json()
    session_token = data.get("session_token")
    if not session_token:
        return {"message": "Missing session_token."}
    if delete_session(session_token):
        return {"message": "Logout successful."}
    return {"message": "Invalid session_token."}


@app.get("/player/profile")
async def player_profile(player_id: str = None, session_token: str = None):
    if session_token:
        player_id = validate_session(session_token)
    if not player_id:
        return {"message": "Missing or invalid player_id/session_token."}
    if not player_exists(player_id):
        return {"message": "Player not found."}

    profile = get_player_profile(player_id)
    inventory = load_player_inventories().get(player_id, [])
    gold = get_player_gold(player_id)
    return {
        "player_id": player_id,
        "profile": profile,
        "inventory": inventory,
        "gold": gold,
    }


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

    inventories = load_player_inventories()
    if not remove_item_from_inventory(inventories, seller_id, item_name, quantity):
        return {"message": "Seller does not have enough of this item to list."}
    save_player_inventories(inventories)

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

        if not player_exists(buyer_id):
            return {"message": "Buyer does not exist."}

        buyer_gold = get_player_gold(buyer_id)
        if buyer_gold is None:
            return {"message": "Buyer does not exist."}
        if buyer_gold < total_price:
            return {"message": "Buyer does not have enough gold."}

        seller_id = item["seller_id"]
        if not player_exists(seller_id):
            return {"message": "Seller does not exist."}

        if item["quantity"] == quantity:
            listings.pop(i)
        else:
            item["quantity"] -= quantity

        change_player_gold(buyer_id, -total_price)
        change_player_gold(seller_id, payout)

        save_auction_listings(listings)

        inventories = load_player_inventories()
        add_item_to_inventory(inventories, buyer_id, item["item_name"], quantity)
        save_player_inventories(inventories)

        return {
            "message": (
                f"Purchase successful! {seller_id} receives {payout} gold after 5% tax ({tax} gold taken)."
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
