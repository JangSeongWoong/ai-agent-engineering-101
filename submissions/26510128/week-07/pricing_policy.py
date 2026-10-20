"""Week 07 price adaptation from own observed deals and real review feedback.

Source data:
- .market/seller-sales.jsonl: receipts signed by *this* seller (A2A trades).
- .market/seller-reviews.json: reviews transcribed/exported from own market page.
The price policy does not claim a review exists until it is supplied. Neither
a test-run deal nor a simulated review is counted as a market dashboard metric.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent
SALES = ROOT / ".market" / "seller-sales.jsonl"
REVIEWS = ROOT / ".market" / "seller-reviews.json"


def record_sale(item: str, price: int, reserve: int, task: str) -> None:
    SALES.parent.mkdir(exist_ok=True, parents=True)
    entry = {"at": datetime.now(timezone.utc).isoformat(), "item": item,
             "price": int(price), "reserve": int(reserve), "task": str(task)}
    with SALES.open("a", encoding="utf-8") as out:
        out.write(json.dumps(entry, ensure_ascii=False) + "\n")


def market_reviews(shop: str) -> list[dict]:
    try:
        blob = json.loads(REVIEWS.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    if isinstance(blob, dict) and blob.get("shop") == shop:
        return [r for r in blob.get("reviews", []) if isinstance(r, dict)
                and isinstance(r.get("stars"), int) and 1 <= r["stars"] <= 5]
    return []


def local_sales(item: str) -> list[dict]:
    if not SALES.exists():
        return []
    result = []
    for line in SALES.read_text(encoding="utf-8").splitlines():
        try:
            sale = json.loads(line)
            if sale.get("item") == item and isinstance(sale.get("price"), int):
                result.append(sale)
        except json.JSONDecodeError:
            pass
    return result


def quote_adjustment(shop: str, item: str) -> tuple[int, dict]:
    """Small, auditable adjustment. The hard reserve is enforced by caller."""
    sales = local_sales(item)
    reviews = market_reviews(shop)
    info = {
        "observed_deals": len(sales),
        "recent_avg_deal": round(mean(x["price"] for x in sales[-10:]), 2) if sales else None,
        "review_count": len(reviews),
        "review_mean": round(mean(x["stars"] for x in reviews[-10:]), 2) if reviews else None,
        "review_source": str(REVIEWS) if reviews else "no market feedback loaded",
    }
    delta = 0
    # Do not call a source "market data" merely because the local test
    # generated trades: reviews must actually be present.
    if len(reviews) >= 2 and len(sales) >= 2:
        score = mean(x["stars"] for x in reviews[-10:])
        if score < 3.0:
            delta = -5
        elif score >= 4.3:
            delta = 3
        # Avoid increasing price if the customer has complained of overcharging.
        if any("overcharg" in str(r.get("review", "")).lower()
               for r in reviews[-10:]):
            delta = min(delta, -5)
    info["price_adjustment"] = delta
    return delta, info
