import hashlib
import json

PLAYER_DATA_FILE = "character/player_data.json"

ALL_CLASSES = [
    "Warrior", "Mage", "Healer", "Rogue", "Paladin", "Battlemage", "Hunter", "Bard",
    "Necromancer", "Druid", "Monk", "Priest", "Shaman", "Sorcerer", "Assassin",
    "Knight", "Ranger", "Alchemist", "Enchanter", "Berserker"
]


def load_player_data():
    try:
        with open(PLAYER_DATA_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_player_data(data):
    with open(PLAYER_DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def hash_password(password):
    if password is None:
        password = ""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_player_password(player_id, password):
    data = load_player_data()
    player = data.get(player_id)
    if player is None:
        return False
    stored_password = player.get("password")
    if stored_password is None:
        return password in (None, "")
    return stored_password == hash_password(password)


def create_player(player_id, first_class, password=None):
    if first_class not in ALL_CLASSES:
        print(f"Invalid class: {first_class}")
        return False
    data = load_player_data()
    if player_id in data:
        return False  # Player already exists
    data[player_id] = {
        "first_class": {"name": first_class, "level": 1, "skills": []},
        "second_class": None,
        "hybrid_class": None,
        "professions": [],
        "gold": 100,
        "password": hash_password(password) if password is not None else None
    }
    save_player_data(data)

    # Create empty inventory for the player
    try:
        with open("character/player_inventories.json", "r") as f:
            inventories = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        inventories = {}
    if player_id not in inventories:
        inventories[player_id] = []
        with open("character/player_inventories.json", "w") as f:
            json.dump(inventories, f, indent=2)
    

    return True

def get_player_profile(player_id):
    data = load_player_data()
    player = data.get(player_id)
    if player is None:
        return None
    return {
        key: value
        for key, value in player.items()
        if key != "password"
    }


def level_up_first_class(player_id):
    data = load_player_data()
    if player_id in data and data[player_id]["first_class"]:
        data[player_id]["first_class"]["level"] += 1
        save_player_data(data)
        return True
    return False

if __name__ == "__main__":
    print("Available classes:")
    print(", ".join(ALL_CLASSES))
    print("1. Create player")
    print("2. Level up first class")
    choice = input("Choose an option: ")
    if choice == "1":
        player_id = input("Enter player ID: ")
        first_class = input("Enter first class: ")
        if create_player(player_id, first_class):
            print(f"Player {player_id} created as {first_class}!")
        else:
            print(f"Player {player_id} already exists or invalid class.")
    elif choice == "2":
        player_id = input("Enter player ID: ")
        if level_up_first_class(player_id):
            print(f"Player {player_id}'s first class leveled up!")
        else:
            print(f"Player {player_id} not found or no first class.")