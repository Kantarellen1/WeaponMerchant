import json
from prompts import build_prompt
import subprocess

# Simple JSON memory (can be upgraded to a DB later)
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

def run_ollama(prompt):
    result = subprocess.run(
        ["ollama", "run", "mistral", prompt],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()

def get_merchant_response(player_id, message):
    memory = load_memory()
    history = memory.get(player_id, [])

    # Add new message to history
    history.append({"role": "player", "message": message})

    prompt = build_prompt(history)
    response = run_ollama(prompt)

    history.append({"role": "merchant", "message": response})
    memory[player_id] = history
    save_memory(memory)

    return response 
