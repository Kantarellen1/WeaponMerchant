from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from merchant_data import get_merchant_response

app = FastAPI()

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
    item = data.get("item")
    price = data.get("price")
    # Add item to auction house
    return {"message": "Item listed for auction", "item": item, "price": price}

@app.get("/auction/browse")
async def browse_auction():
    # Return all current listings
    return {"listings": []}

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
