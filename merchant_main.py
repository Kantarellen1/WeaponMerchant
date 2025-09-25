from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from merchant_data import get_merchant_response
from auction_data import load_auction_listings, save_auction_listings
from datetime import datetime, timedelta, timezone

app = FastAPI()

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
    return FileResponse("town_square.html")

@app.get("/smithy")
async def gerik_smithy():
    return FileResponse("gerik_smithy.html")

@app.get("/apothecary") 
async def elara_apothecary():
    return FileResponse("elara_apothecary.html")

@app.get("/general-store")
async def finn_store():
    return FileResponse("finn_general_store.html")

@app.get("/auction-house")
async def auction_house():
    return FileResponse("auction_house.html")

# Testing purposes
@app.post("/talk_to_merchant")
async def talk_to_merchant(request: Request):
    data = await request.json()
    player_id = data.get("player_id")
    message = data.get("message")
    player_location = data.get("player_location", "Edvin")  # Default to Edvin
    shop_type = data.get("shop_type", "market")             # Default to market

    response = get_merchant_response(player_id, player_location, shop_type, message)
    print(f"merchant: {response}")
    return {"response": response}


# Correct code
# @app.post("/talk_to_merchant")
#async def talk_to_merchant(request: Request):
#    data = await request.json()
#    player_id = data.get("player_id")
#    message = data.get("message")
#    merchant_id = data.get("merchant_id")  # Expect merchant_id from frontend

#    response = get_merchant_response(merchant_id, player_id, message)
#    print(f"merchant: {response}")
#    return {"response": response}

@app.post("/auction/list")
async def list_item(request: Request):
    data = await request.json()
    now = datetime.now(timezone.utc)
    duration_hours = int(data.get("duration", 1))
    data["time_listed"] = now.isoformat()
    data["expires_at"] = (now + timedelta(hours=duration_hours)).isoformat()
    listings = load_auction_listings()
    listings.append(data)
    save_auction_listings(listings)
    return {"message": "Item listed!"}

@app.get("/auction/browse")
async def browse_auction():
    listings = load_auction_listings()
    now = datetime.now(timezone.utc)
    valid_listings = [
        item for item in listings
        if "expires_at" not in item or parse_iso_datetime(item["expires_at"]) > now
    ]
    return {"auction_listings": valid_listings}

@app.post("/auction/buy")
async def buy_item(request: Request):
    data = await request.json()
    item_id = data.get("item_id")
    # Handle purchase logic
    return {"message": "Item purchased", "item_id": item_id}

@app.post("/auction/cancel")
async def cancel_listing(request: Request):
    data = await request.json()
    item_id = data.get("item_id")
    return {"message": "Listing canceled", "item_id": item_id}
    # Remove a listing from the auction house
