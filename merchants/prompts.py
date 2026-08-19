from guilds.branch_guild_data import branch_guild_modifiers
from guilds.town_guild_data import town_guild_modifiers
from guilds.main_guild_data import main_guild_prices
import json
import os

def load_merchant_json(town, merchant_file):
    lore_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "lore"))
    country_root = os.path.join(lore_root, "country_lore")

    # Search country_lore/<Country>/town_lore/<Town>/<merchant_file>
    if os.path.isdir(country_root):
        for country in os.listdir(country_root):
            path = os.path.join(country_root, country, "town_lore", town, merchant_file)
            print(f"DEBUG: checking merchant path: {path}")
            if os.path.isfile(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception as e:
                    print(f"DEBUG: failed loading merchant json {path}: {e}")
                    return None

    # Legacy fallback: lore/town_lore/<town>/<merchant_file>
    legacy = os.path.join(lore_root, "town_lore", town, merchant_file)
    print(f"DEBUG: checking legacy merchant path: {legacy}")
    if os.path.isfile(legacy):
        try:
            with open(legacy, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"DEBUG: failed loading legacy merchant json {legacy}: {e}")
            return None

    return None

def find_merchant_in_lore(merchant_id):
    """
    Search all merchant JSONs under lore for a merchant with name matching merchant_id (case-insensitive).
    Returns merchant dict or None.
    """
    lore_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "lore"))
    country_root = os.path.join(lore_root, "country_lore")

    # search country_lore layout
    if os.path.isdir(country_root):
        for country in os.listdir(country_root):
            town_base = os.path.join(country_root, country, "town_lore")
            if not os.path.isdir(town_base):
                continue
            for town in os.listdir(town_base):
                town_folder = os.path.join(town_base, town)
                if not os.path.isdir(town_folder):
                    continue
                for fname in os.listdir(town_folder):
                    if not fname.lower().endswith(".json"):
                        continue
                    path = os.path.join(town_folder, fname)
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        name = (data.get("name") or "").lower()
                        if name == merchant_id.lower():
                            print(f"DEBUG: found merchant {merchant_id} in {path}")
                            return data
                    except Exception:
                        continue

    # legacy town_lore layout
    legacy_base = os.path.join(lore_root, "town_lore")
    if os.path.isdir(legacy_base):
        for town in os.listdir(legacy_base):
            town_folder = os.path.join(legacy_base, town)
            if not os.path.isdir(town_folder):
                continue
            for fname in os.listdir(town_folder):
                if not fname.lower().endswith(".json"):
                    continue
                path = os.path.join(town_folder, fname)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    name = (data.get("name") or "").lower()
                    if name == merchant_id.lower():
                        print(f"DEBUG: found merchant {merchant_id} in legacy {path}")
                        return data
                except Exception:
                    continue

    return None

def load_town_lore(town):
    lore_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "lore"))
    country_root = os.path.join(lore_root, "country_lore")

    # Search country_lore/<Country>/town_lore/<Town>/<Town>.json
    if os.path.isdir(country_root):
        for country in os.listdir(country_root):
            path = os.path.join(country_root, country, "town_lore", town, f"{town}.json")
            if os.path.isfile(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    return {}

    # Legacy fallback: lore/town_lore/<town>/<town>.json
    legacy = os.path.join(lore_root, "town_lore", town, f"{town}.json")
    if os.path.isfile(legacy):
        try:
            with open(legacy, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    return {}

def get_guild_price(item_name, location):
    # Determine if location is a branch or town
    if location in branch_guild_modifiers:
        modifier = branch_guild_modifiers[location]
    else:
        modifier = town_guild_modifiers.get(location, 1.0)
    base_price = main_guild_prices.get(item_name, 0)
    return int(base_price * modifier)

def get_sell_price(item_name, town):
    # Merchants buy at 20% below the guild price
    return int(get_guild_price(item_name, town) * 0.8)

def build_prompt(merchant_id, history, town=None, merchant_file=None):
    merchant_id = merchant_id.lower()
    print(f"DEBUG: merchant_id = {merchant_id}")

    lore_snippet = ""
    # (initial town-lore section remains but will be re-run if merchant provides location)
    if town:
        town_lore = load_town_lore(town)
        if town_lore:
            if town_lore.get("current_events"):
                lore_snippet += "Current Events in town:\n"
                for event in town_lore["current_events"]:
                    lore_snippet += f"- {event}\n"
            if town_lore.get("rumors"):
                lore_snippet += "Rumors:\n"
                for rumor in town_lore["rumors"]:
                    lore_snippet += f"- {rumor}\n"
            if town_lore.get("notable_figures"):
                lore_snippet += "Notable Figures:\n"
                for fig in town_lore["notable_figures"]:
                    lore_snippet += f"- {fig['name']} ({fig['role']}): {fig['description']}\n"

    merchant = None

    # Try to load from JSON if town and merchant_file are provided
    if town and merchant_file:
        merchant = load_merchant_json(town, merchant_file)

    # If not found, try to find the merchant anywhere in lore by name
    if merchant is None:
        merchant = find_merchant_in_lore(merchant_id)

    # If merchant found but no town was passed, populate town from merchant and include its lore
    if merchant and not town:
        inferred_town = merchant.get("location")
        if inferred_town:
            town = inferred_town
            # load town lore and append to lore_snippet (same logic as above)
            town_lore = load_town_lore(town)
            if town_lore:
                if town_lore.get("current_events"):
                    lore_snippet += "Current Events in town:\n"
                    for event in town_lore["current_events"]:
                        lore_snippet += f"- {event}\n"
                if town_lore.get("rumors"):
                    lore_snippet += "Rumors:\n"
                    for rumor in town_lore["rumors"]:
                        lore_snippet += f"- {rumor}\n"
                if town_lore.get("notable_figures"):
                    lore_snippet += "Notable Figures:\n"
                    for fig in town_lore["notable_figures"]:
                        lore_snippet += f"- {fig['name']} ({fig['role']}): {fig['description']}\n"

    # Defensive handling: if still not found, return an explicit short prompt
    if merchant is None:
        return (
            f"You are acting as the merchant '{merchant_id}', but the merchant's data file is missing.\n"
            "Respond in-character in 1-2 brief sentences apologizing that you cannot be found or that your stall is closed,\n"
            "offer a suggestion (visit the town square or another merchant), and keep the tone helpful and polite.\n"
            "Do not attempt to access inventory or town-specific details.\n\n"
            f"Adventurer: {history[-1]['message'] if history else ''}\n"
            f"{merchant_id.title()}:"
        )

    location = merchant.get("location", town if town else "Edvin")

    base = (
        f"{merchant.get('description','')}\n\n"
        f"{lore_snippet}\n"
        f"PERSONALITY TRAITS:\n"
    )
    for trait in merchant.get('traits', []):
        base += f"- {trait}\n"

    # Add inventory with dynamic prices
    if "inventory" in merchant and merchant["inventory"]:
        base += "\nCURRENT INVENTORY (prices set by the town's guild):\n"
        for item in merchant["inventory"]:
            name = item.get("name", "unknown")
            itype = item.get("type", "item")
            price = get_guild_price(name, location)
            base += f"- {name} ({itype}): {price} gold\n"

    base += (
        "\nRESPONSE RULES:\n"
        "- Keep responses 1-2 sentences maximum\n"
        "- Stay in character\n"
        "- Be helpful and try to make sales\n\n"
        "- 'Iron Sword' is a player synonym for the listed Longsword; always call the item 'Longsword' in your replies.\n"
        "- Do not explain or mention the Iron Sword synonym unless the player specifically asks about the name.\n"
        "- Never substitute Battle Axe or any other inventory item for the Longsword.\n"
        "- Mention only items shown in CURRENT INVENTORY.\n"
        "- Write each word once; do not repeat words or phrases.\n\n"
        "Here's your conversation history with this adventurer:\n\n"
    )

    convo = ""
    for entry in history[-6:]:
        if entry["role"] == "player":
            player_display = entry.get("player_name") or "Adventurer"
            convo += f"{player_display}: {entry['message']}\n"
        else:
            convo += f"{merchant.get('name', merchant_id.title())}: {entry['message']}\n"

    return base + convo + f"\n{merchant.get('name', merchant_id.title())}:"

