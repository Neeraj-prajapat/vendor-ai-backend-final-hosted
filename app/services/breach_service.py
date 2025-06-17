# app/services/breach_service.py

import requests
from datetime import datetime
from sqlalchemy.orm import Session
from ..crud import upsert_breach

HIBP_URL = "https://haveibeenpwned.com/api/v3/breaches"
HEADERS = {"user-agent": "VendorRiskApp/1.0"}

def fetch_all_hibp_breaches(db: Session) -> int:
    resp = requests.get(HIBP_URL, headers=HEADERS)
    resp.raise_for_status()
    breaches_data = resp.json()

    count = 0
    for b in breaches_data:
        breach_date = (
            datetime.strptime(b["BreachDate"], "%Y-%m-%d").date()
            if b.get("BreachDate")
            else None
        )
        added_date = (
            datetime.strptime(b["AddedDate"][:10], "%Y-%m-%d").date()
            if b.get("AddedDate")
            else None
        )
        data = {
            "name": b.get("Name", ""),
            "title": b.get("Title", "") or b.get("Name", ""),
            "domain": b.get("Domain", ""),
            "breach_date": breach_date,
            "added_date": added_date,
            "pwn_count": b.get("PwnCount", 0),
            "description": b.get("Description", ""),
            "data_classes": ";".join(b.get("DataClasses", [])),
            "is_verified": b.get("IsVerified", False),
            "is_fabricated": b.get("IsFabricated", False),
            "is_sensitive": b.get("IsSensitive", False),
            "is_retired": b.get("IsRetired", False),
            "is_spam_list": b.get("IsSpamList", False),
        }
        upsert_breach(db, data)
        count += 1
    return count
