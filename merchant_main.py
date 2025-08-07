from fastapi import FastAPI, Request
from merchant_data import get_merchant_response

app = FastAPI()

@app.post("/talk_to_merchant")
async def talk_to_merchant(request: Request):
    data = await request.json()
    player_id = data.get("player_id")
    message = data.get("message")

    response = get_merchant_response(player_id, message)
    return {"response": response}
