import json
from prompts import build_prompt
import subprocess

MEMORY_FILE = "merchant_memory.json"

def load_memory():
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

def get_memory_key(player_id, merchant_id):
    return f"{player_id}_{merchant_id}"

def get_current_merchant_id(player_location, shop_type=None):
    # You can expand this mapping as you add more merchants/locations
    if player_location.lower() == "edvin" and shop_type == "smithy":
        return "gerik"
    elif player_location.lower() == "buglia" and shop_type == "apothecary":
        return "elara"
    elif player_location.lower() == "edvin" and shop_type == "market":
        return "finn"
    # Add more logic as needed
    else:
        return "gerik"  # Default fallback

def get_merchant_response(player_id, player_location, shop_type, message):
    merchant_id = get_current_merchant_id(player_location, shop_type)
    print(f"DEBUG: Using merchant_id={merchant_id} for location={player_location}, shop_type={shop_type}")
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

def get_fallback_response(merchant_id, message):
    message_lower = message.lower()
    fallbacks = {
        "gerik": {
            "greeting": "Well hello there, adventurer! Welcome to my smithy. What can I forge for you today?",
            "weapons": "Ah, looking for a fine blade? I've got swords that'll serve you well - try the balance on this one!",
            "armor": "Smart thinking! Good armor saves lives. Here, feel the quality of this chainmail.",
            "price": "My prices are fair for the quality you get. Everything's negotiable for a fellow adventurer!",
            "default": "Hmm, let me think... have you seen my new sword designs? Finest work in Edvin!"
        },
        "elara": {
            "greeting": "Welcome, dear. My potions can heal what ails you... what do you seek?",
            "weapons": "Weapons? No, child. But I have potions that can sharpen your blade's bite.",
            "healing": "Ah yes, healing draughts are my specialty. This one will mend wounds quickly.",
            "price": "My prices reflect years of study and rare ingredients. Quality has its cost.",
            "default": "Perhaps a stamina elixir? Many adventurers find them... useful."
        },
        "finn": {
            "greeting": "Welcome to my stall! I've got everything an adventurer needs - and some things you didn't know you needed!",
            "weapons": "Basic weapons, sure! Nothing fancy like Gerik's, but they'll do the job.",
            "supplies": "Rope, rations, torches, rope - did I mention rope? You always need more rope.",
            "price": "Best prices in town, guaranteed! Well, maybe not guaranteed, but pretty good.",
            "default": "I bet I've got exactly what you're looking for somewhere in this mess!"
        }
    }
    merchant_responses = fallbacks.get(merchant_id, fallbacks["gerik"])
    if any(word in message_lower for word in ["hello", "hi", "greetings"]):
        return merchant_responses["greeting"]
    elif any(word in message_lower for word in ["weapon", "sword", "blade"]):
        return merchant_responses.get("weapons", merchant_responses["default"])
    elif any(word in message_lower for word in ["heal", "potion", "health"]):
        return merchant_responses.get("healing", merchant_responses["default"])
    elif any(word in message_lower for word in ["price", "cost", "gold"]):
        return merchant_responses.get("price", merchant_responses["default"])
    else:
        return merchant_responses["default"]

def run_ollama(prompt):
    try:
        result = subprocess.run(
            ["ollama", "run", "mistral", prompt],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        else:
            return None
    except Exception as e:
        print(f"Ollama error: {e}")
        return None