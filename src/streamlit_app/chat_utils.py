def get_avatar(role: str) -> str | None:
    if role == "user":
        return "🧑‍🎓"
    elif role == "assistant":
        return "🤖"
    return None
