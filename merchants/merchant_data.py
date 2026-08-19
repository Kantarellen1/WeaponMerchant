import json
import re
import os
import urllib.error
import urllib.request
from merchants.prompts import build_prompt
from merchants.inventory import MerchantInventory

ANSI_ESCAPE = re.compile(r"\x1B(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1B\\))")
ESCAPED_ANSI_ESCAPE = re.compile(r"\\x1[bB]\[[0-?]*[ -/]*[@-~]")
DUPLICATE_WORD = re.compile(r"\b([A-Za-z]+)([\s,.!?;:'-]+)\1\b", re.IGNORECASE)

# Ensure the memory file is always resolved relative to this module
MEMORY_FILE = os.path.join(os.path.dirname(__file__), "merchant_memory.json")

def load_memory():
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            memory = json.load(f)
        for history in memory.values():
            for entry in history:
                if "message" in entry:
                    entry["message"] = strip_ansi(entry["message"])
        return memory
    except FileNotFoundError:
        return {}
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        # tolerant fallback if file contains bad bytes
        try:
            with open(MEMORY_FILE, "rb") as f:
                raw = f.read()
            text = raw.decode("utf-8", errors="replace")
            return json.loads(text)
        except Exception:
            print(f"Warning: could not parse {MEMORY_FILE}: {e}")
            return {}


def save_memory(memory):
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memory, f, indent=2, ensure_ascii=False)
        print(f"Memory saved to {MEMORY_FILE}")
    except Exception as e:
        print(f"Error saving memory: {e}")


def get_memory_key(player_id, merchant_id):
    return f"{player_id}_{merchant_id}"


def get_current_merchant_id(player_location, shop_type=None):
    # Expand this mapping as you add merchants/locations
    if player_location and player_location.lower() == "edvin" and shop_type == "smithy":
        return "gerik"
    if player_location and player_location.lower() == "buglia" and shop_type == "apothecary":
        return "elara"
    if player_location and player_location.lower() == "edvin" and shop_type == "market":
        return "finn"
    return "gerik"  # default fallback


def get_merchant_file(shop_type):
    if shop_type:
        return f"{shop_type.lower()}.json"
    return None


def get_merchant_response(player_id, player_location, shop_type, message, player_name=None):
    merchant_id = get_current_merchant_id(player_location, shop_type)
    merchant_file = get_merchant_file(shop_type)
    town = player_location
    print(f"DEBUG: Using merchant_id={merchant_id}, merchant_file={merchant_file} for location={player_location}, shop_type={shop_type}")

    memory = load_memory()
    memory_key = get_memory_key(player_id, merchant_id)
    history = memory.get(memory_key, [])

    # Include player_name when available so prompts can use the adventurer's name
    entry = {"role": "player", "message": message}
    if player_name:
        entry["player_name"] = player_name
    history.append(entry)

    prompt = build_prompt(merchant_id, history, town=town, merchant_file=merchant_file)
    response = run_ollama(prompt)

    if not response:
        response = get_fallback_response(merchant_id, message)
    response = normalize_merchant_response(response, message)

    history.append({"role": "merchant", "message": response})
    memory[memory_key] = history
    save_memory(memory)
    print(f"Saved memory for {memory_key}: {history}")
    return response


def get_merchant_response_by_id(player_id, merchant_id, message, player_name=None):
    """
    Handle requests that specify merchant_id in the URL (no town/shop_type provided).
    """
    merchant_id = merchant_id.lower()
    memory = load_memory()
    memory_key = get_memory_key(player_id, merchant_id)
    history = memory.get(memory_key, [])

    entry = {"role": "player", "message": message}
    if player_name:
        entry["player_name"] = player_name
    history.append(entry)

    prompt = build_prompt(merchant_id, history)  # build_prompt will handle missing merchant file defensively
    response = run_ollama(prompt)

    if not response:
        response = get_fallback_response(merchant_id, message)
    response = normalize_merchant_response(response, message)

    history.append({"role": "merchant", "message": response})
    memory[memory_key] = history
    save_memory(memory)
    print(f"Saved memory for {memory_key}: {history}")
    return response


def get_fallback_response(merchant_id, message):
    message_lower = (message or "").lower()
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
            "supplies": "Rope, rations, torches — did I mention rope? You always need more rope.",
            "price": "Best prices in town, guaranteed! Well, maybe not guaranteed, but pretty good.",
            "default": "I bet I've got exactly what you're looking for somewhere in this mess!"
        }
    }
    merchant_responses = fallbacks.get(merchant_id, fallbacks["gerik"])
    if any(word in message_lower for word in ["hello", "hi", "greetings"]):
        return merchant_responses["greeting"]
    if any(word in message_lower for word in ["weapon", "sword", "blade"]):
        return merchant_responses.get("weapons", merchant_responses["default"])
    if any(word in message_lower for word in ["heal", "potion", "health"]):
        return merchant_responses.get("healing", merchant_responses["default"])
    if any(word in message_lower for word in ["price", "cost", "gold"]):
        return merchant_responses.get("price", merchant_responses["default"])
    return merchant_responses["default"]


def strip_ansi(text):
    """Remove terminal control sequences from CLI output so text remains readable."""
    if not text:
        return text
    text = ANSI_ESCAPE.sub("", text)
    text = ESCAPED_ANSI_ESCAPE.sub("", text)
    text = text.replace("\r", "")
    return DUPLICATE_WORD.sub(lambda match: match.group(1) + match.group(2), text).strip()


def normalize_merchant_response(response, player_message):
    response = strip_ansi(response)
    response = re.sub(r"\bIron Sword\b", "Longsword", response, flags=re.IGNORECASE)
    response = re.sub(
        r"\b(Longsword),?\s+also known as (?:the )?\1\b,?",
        r"\1",
        response,
        flags=re.IGNORECASE,
    )
    if "iron sword" in (player_message or "").lower():
        response = re.sub(r"\bBattle Axe\b", "Longsword", response, flags=re.IGNORECASE)
    return response


def run_ollama(prompt):
    """
    Generate a response through Ollama's JSON API instead of its interactive CLI.
    The CLI can emit cursor-edit sequences while rendering output in a terminal.
    """
    try:
        payload = json.dumps({
            "model": "mistral",
            "prompt": prompt,
            "stream": False,
        }).encode("utf-8")
        request = urllib.request.Request(
            "http://127.0.0.1:11434/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
        return normalize_merchant_response(result.get("response"), "")
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as e:
        print(f"Ollama error: {e}")
        return None


def get_merchant_price(merchant_id, item_key, fallback_base=None):
    """Return a merchant-specific price for an item, backed by market data when available."""
    try:
        inv = MerchantInventory(merchant_id)
        return inv.compute_price(item_key, fallback_base)
    except Exception as e:
        print(f"Error computing merchant price: {e}")
        # fallback simple behavior
        return fallback_base or 1.0

