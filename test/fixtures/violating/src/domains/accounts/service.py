from domains.billing.service import total_invoiced  # forbidden: accounts -> billing

def account_summary(user_id: str) -> dict:
    return {"id": user_id, "invoiced": total_invoiced(user_id)}
