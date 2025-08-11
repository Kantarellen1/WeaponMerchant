from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from merchant_data import get_merchant_response

app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Welcome to Gerik's Weapon Shop!", "endpoints": {"/talk_to_merchant": "POST to chat with the merchant", "/chat": "GET to open chat interface"}}

@app.get("/chat")
async def get_chat_interface():
    return FileResponse("merchant.html")

@app.get("/talk_to_merchant")
async def talk_to_merchant_info():
    return {
        "message": "This endpoint requires POST method",
        "usage": "POST /talk_to_merchant with JSON body: {\"player_id\": \"your_id\", \"message\": \"your_message\"}"
    }

@app.post("/talk_to_merchant")
async def talk_to_merchant(request: Request):
    data = await request.json()
    player_id = data.get("player_id")
    message = data.get("message")

    response = get_merchant_response(player_id, message)
    return {"response": response}
