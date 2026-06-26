import json
from character.main_class_data import ALL_CLASSES

PLAYER_DATA_FILE = "player_data.json"

def load_player_data():
    try:
        with open(PLAYER_DATA_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_player_data(data):
    with open(PLAYER_DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def set_second_class(player_id, second_class):
    data = load_player_data()
    if player_id in data:
        first_class = data[player_id]["first_class"]["name"]
        if second_class not in ALL_CLASSES:
            print(f"Invalid class: {second_class}")
            return False
        if second_class == first_class:
            print("Second class cannot be the same as the first class.")
            return False
        data[player_id]["second_class"] = {"name": second_class, "level": 1, "skills": []}
        save_player_data(data)
        return True
    return False

def level_up_second_class(player_id):
    data = load_player_data()
    if player_id in data and data[player_id]["second_class"]:
        data[player_id]["second_class"]["level"] += 1
        save_player_data(data)
        return True
    return False

def unlock_hybrid_class(player_id, hybrid_name):
    data = load_player_data()
    if player_id in data:
        data[player_id]["hybrid_class"] = hybrid_name
        save_player_data(data)
        return True
    return False

def add_profession(player_id, profession_name):
    data = load_player_data()
    if player_id in data:
        professions = data[player_id]["professions"]
        if len(professions) < 3 and all(p["name"] != profession_name for p in professions):
            professions.append({"name": profession_name, "level": 1})
            save_player_data(data)
            return True
    return False