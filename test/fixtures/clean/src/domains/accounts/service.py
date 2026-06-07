"""accounts public surface."""

def get_user(user_id: str) -> dict:
    return {"id": user_id}

def authenticate(token: str) -> bool:
    return bool(token)
