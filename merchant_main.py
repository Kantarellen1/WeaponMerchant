from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from merchant_data import get_merchant_response

app = FastAPI()

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

@app.post("/talk_to_merchant")
async def talk_to_merchant(request: Request):
    data = await request.json()
    player_id = data.get("player_id")
    message = data.get("message")

    response = get_merchant_response(player_id, message)
    return {"response": response}
