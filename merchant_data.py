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

def get_fallback_response(message):
    """Fallback responses when Ollama isn't working"""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ["hello", "hi", "greetings"]):
        return "Well, well, another adventurer. What brings you to my humble shop? Looking for something sharp, or just here to waste my time?"
    
    elif any(word in message_lower for word in ["sword", "weapon", "blade"]):
        return "Ah, swords! I've got everything from rusty letter openers to blades that could cleave a dragon in two. Your coin purse feeling heavy today?"
    
    elif any(word in message_lower for word in ["armor", "shield", "protection"]):
        return "Armor, eh? Smart thinking. Nothing worse than a dead customer - terrible for repeat business. What's your budget, and more importantly, what's trying to kill you?"
    
    elif any(word in message_lower for word in ["price", "cost", "gold", "coin"]):
        return "*chuckles* Everything has a price, friend. Quality costs extra, but I suppose you could afford the rusty stuff if that's more your style."
    
    else:
        return "Hmm, interesting request. Let me think... *strokes beard* Have you considered that maybe what you really need is a good sword? Solves most problems, in my experience."

def get_merchant_response(player_id, message):
    memory = load_memory()
    history = memory.get(player_id, [])

    # Add new message to history
    history.append({"role": "player", "message": message})

    prompt = build_prompt(history)
    response = run_ollama(prompt)
    
    # If Ollama fails, use fallback
    if not response:
        response = get_fallback_response(message)

    history.append({"role": "merchant", "message": response})
    memory[player_id] = history
    save_memory(memory)

    return response
