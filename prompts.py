def build_prompt(history):
    base = (
        "You are Gerik, a friendly but sarcastic weapon merchant in a medieval fantasy world. "
        "You sell swords, armor, and gossip. Speak naturally. Here's your past with this player:\n\n"
    )

    convo = ""
    for entry in history[-6:]:  # Only include the last few exchanges
        if entry["role"] == "player":
            convo += f"Player: {entry['message']}\n"
        else:
            convo += f"Merchant: {entry['message']}\n"

    return base + convo + "\nMerchant:"
