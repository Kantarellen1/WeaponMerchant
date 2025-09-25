from branch_guild_data import branch_guild_modifiers
from town_guild_data import town_guild_modifiers
from main_guild_data import main_guild_prices

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

def build_prompt(merchant_id, history):
    merchant_id = merchant_id.lower()
    print(f"DEBUG: merchant_id = {merchant_id}")
    merchants = {
        "gerik": {
            "name": "Gerik",
            "location": "Edvin",
            "description": (
                "You are Gerik, the cheerful and knowledgeable weapon and armorsmith of the small town of Edvin. "
                "You've been the town's go-to craftsman for decades and know everyone and everything that happens here. "
                "You're always in a good mood, love chatting with adventurers, and are eager to make deals. "
                "You encourage customers to try on armor and test the balance of weapons (but no damaging them!)."
            ),
            "traits": [
                "Always cheerful and welcoming",
                "Loves to share town gossip and stories", 
                "Eager to negotiate and make deals",
                "Proud of your craftsmanship",
                "Knows every resident of Edvin"
            ],
            "inventory": [
                {"name": "Longsword", "type": "Weapon"},
                {"name": "Shortsword", "type": "Weapon"},
                {"name": "Battle Axe", "type": "Weapon"},
                {"name": "Dagger", "type": "Weapon"},
                {"name": "Wooden Shield", "type": "Shield"},
                {"name": "Iron Shield", "type": "Shield"},
                {"name": "Leather Armor", "type": "Armor"},
                {"name": "Chainmail", "type": "Armor"},
                {"name": "Plate Armor", "type": "Armor"}
            ]
        },
        "elara": {
            "name": "Elara",
            "location": "Buglia",
            "description": (
                "You are Elara, the wise potion master of Buglia. Your shop smells of herbs and bubbling cauldrons. "
                "You've been brewing healing potions and magical elixirs for 40 years. You speak softly but with "
                "great knowledge, and always warn customers about proper potion usage."
            ),
            "traits": [
                "Wise and speaks softly",
                "Passionate about alchemy and herbs",
                "Always gives safety warnings",
                "Knows healing properties of everything", 
                "Slightly mysterious but caring"
            ],
            "inventory": [
                {"name": "Healing potion", "type": "Potion"},
                {"name": "Mana potion", "type": "Potion"},
                {"name": "Stamina elixir", "type": "Potion"}
            ]
        },
        "finn": {
            "name": "Finn",
            "description": (
                "You are Finn, the practical general goods trader in Edvin's marketplace. Your stall is crammed "
                "with everything - rope, rations, tools, lanterns. You're a shrewd but fair businessman who "
                "loves to gossip about trade routes and other merchants."
            ),
            "traits": [
                "Sharp businessman but fair",
                "Knows prices and trade routes",
                "Loves merchant gossip", 
                "Practical and no-nonsense",
                "Always claims to have 'just what you need'"
            ]
        }
    }
    
    merchant = merchants.get(merchant_id)
    location = merchant.get("location", "Edvin")  # Default to Edvin if no location specified
    
    base = (
        f"{merchant['description']}\n\n"
        f"PERSONALITY TRAITS:\n"
    )
    
    for trait in merchant['traits']:
        base += f"- {trait}\n"

    # Add inventory with dynamic prices for Gerik
    if "inventory" in merchant:
        base += "\nCURRENT INVENTORY (prices set by the town's guild):\n"
        for item in merchant["inventory"]:
            price = get_guild_price(item["name"], location)
            base += f"- {item['name']} ({item['type']}): {price} gold\n"
    
    base += (
        "\nRESPONSE RULES:\n"
        "- Keep responses 1-2 sentences maximum\n"
        "- Stay in character\n"
        "- Be helpful and try to make sales\n\n"
        "Here's your conversation history with this adventurer:\n\n"
    )

    convo = ""
    for entry in history[-6:]:
        if entry["role"] == "player":
            convo += f"Adventurer: {entry['message']}\n"
        else:
            convo += f"{merchant['name']}: {entry['message']}\n"

    return base + convo + f"\n{merchant['name']}:"
