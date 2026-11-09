"""Round 3 market decision policy: deterministic money and inventory guardrails.

Only observed .market files supplied by market_kit v4 are used. Financial
rules are code-enforced; LLM decisions may only influence bounded choices.
This module never calls the market or invents transaction outcomes.
"""
from __future__ import annotations

import json
import math
import os
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
MARKET = Path(os.environ.get("MARKET_DIR", ROOT / ".market"))
MIN_CASH = 1_300_000
RESTOCK_BUDGET_FRACTION = 0.12
MAX_STOCK_UNITS = 18
MAX_PER_SKU = 3
FOOD_MAX_HOURS_STORED = 40
SAFE_MARGIN = 0.16
KNOWN_KINDS_FOOD = {"food", "foods", "식품"}


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return default


def inventory() -> dict[str, Any]:
    return load_json(MARKET / "inventory.json", {})


def catalog() -> dict[str, dict[str, Any]]:
    data = load_json(MARKET / "catalog.json", {})
    if isinstance(data, list):
        return {str(x["sku"]): x for x in data if isinstance(x, dict) and x.get("sku")}
    if isinstance(data, dict):
        return {str(k): v for k, v in data.items() if isinstance(v, dict)}
    return {}


def money(value: Any, default: int = 0) -> int:
    try:
        n = float(value)
        return int(n) if math.isfinite(n) and n >= 0 else default
    except (TypeError, ValueError, OverflowError):
        return default


def age_hours(unit: dict[str, Any], now: float | None = None) -> float:
    ts = unit.get("expires_at")
    if not ts:
        return float("inf")
    return (float(ts) - (time.time() if now is None else now)) / 3600


def food_like(unit: dict[str, Any], product: dict[str, Any] | None = None) -> bool:
    product = product or {}
    return str(unit.get("kind") or product.get("kind") or "").lower() in KNOWN_KINDS_FOOD or bool(unit.get("expires_at"))


def reserve_for_unit(unit: dict[str, Any], product: dict[str, Any] | None = None,
                     now: float | None = None) -> int:
    """Guard against below-cost sales, storage and warranty risk.

    We charge only a small extra cushion on food nearing expiry, which is
    never allowed to become a fabricated grade or warranty claim.
    """
    product = product or {}
    cost = money(unit.get("cost"), 0)
    list_price = money(unit.get("list_price") or product.get("list_price"), cost)
    storage = max(0, int(cost * .01 / 24 * min(24, max(0, (time.time() if now is None else now) - float(unit.get("supplied_at") or time.time())) / 3600)))
    risk = .02 if food_like(unit, product) else .05
    floor = math.ceil((cost + storage) * (1 + risk))
    return max(cost, min(max(list_price, cost), floor)) if list_price >= cost else cost


def suggested_ask(unit: dict[str, Any], product: dict[str, Any] | None = None,
                  demand_score: float = 0) -> int:
    product = product or {}
    cost = money(unit.get("cost"), 1)
    list_price = money(unit.get("list_price") or product.get("list_price"), cost)
    floor = reserve_for_unit(unit, product)
    premium = max(.06, min(.22, SAFE_MARGIN + .015 * max(0, min(demand_score, 4))))
    ask = max(floor, int(round(max(list_price, floor) * (1 - .09) + cost * premium)))
    if food_like(unit, product):
        hours = age_hours(unit)
        if hours < 12:
            ask = max(floor, int(list_price * .78))
        elif hours < 30:
            ask = max(floor, int(list_price * .86))
    return max(floor, min(max(list_price, floor), ask))


def find_unit(query: str, taken: set[str] | None = None) -> dict[str, Any] | None:
    """Pick a listed in-stock SKU (or category) without inventing inventory."""
    taken = taken or set()
    inv = inventory()
    products = catalog()
    text = query.casefold()
    units = [u for u in inv.get("units", []) if isinstance(u, dict)
             and u.get("unit") not in taken and u.get("grade") != "expired"
             and (not u.get("expires_at") or age_hours(u) > .5)]
    def matches(u: dict[str, Any]) -> bool:
        sku = str(u.get("sku", "")).casefold()
        name = str(u.get("name", "")).casefold()
        cat = str(u.get("category", "")).casefold()
        last = cat.split(">")[-1].strip()
        return bool((sku and re.search(r"(?<![a-z0-9])"+re.escape(sku)+r"(?![a-z0-9])", text))
                    or (name and name in text) or (last and last in text))
    fits = [u for u in units if matches(u)]
    if not fits:
        return None
    # Prefer exactly named SKU, then oldest sellable stock.
    return min(fits, key=lambda u: (0 if re.search(r"(?<![a-z0-9])"+re.escape(str(u.get("sku","")).casefold())+r"(?![a-z0-9])",text) else 1,
                                     float(u.get("expires_at") or float("inf")),
                                     float(u.get("supplied_at") or 0)))


def buyer_target(list_price: int, budget: int, past_failures: int = 0) -> int:
    """Aim for real savings and never exceed either the actual mandate cap or list."""
    if not isinstance(budget, int) or budget <= 0:
        return 0
    lp = max(1, money(list_price, budget))
    target = math.floor(lp * min(.84, .70 + .035 * max(0, min(past_failures, 4))))
    return min(budget, max(1, target))


def reputation_risk(shop: dict[str, Any], memory: dict[str, Any]) -> float:
    history = memory.get(shop.get("name", ""), {})
    if history.get("injection_attempts", 0):
        return float("inf")
    reviews = shop.get("reviews", []) or []
    good = sum(1 for x in reviews[:20] if int(x.get("stars", 3)) >= 4)
    bad = sum(1 for x in reviews[:20] if int(x.get("stars", 3)) <= 2)
    failures = int(history.get("failures", 0))
    settled = int(history.get("settled", 0))
    return 2.5*bad-0.9*good+4*failures-2*min(settled, 8)


def safe_accept_policy(order: dict[str, Any]) -> dict[str, Any]:
    """Kit v4 validates certificate, shelf life, grade and warranty at checkout."""
    policy: dict[str, Any] = {"cert": True, "grades": ["A", "B"]}
    if str(order.get("kind", "")).lower() == "food":
        needed = float(order.get("use_within_hours") or 0)
        policy["min_hours_left"] = max(2, needed)
    else:
        # 6-hour minimum mitigates a fraction of unknown breakage risk.
        policy["warranty_hours"] = 6
    return policy


def demand_weights(demand: Any) -> dict[str, float]:
    if isinstance(demand, dict):
        demand = demand.get("categories", demand.get("demand", []))
    if not isinstance(demand, list):
        return {}
    result: dict[str, float] = {}
    for x in demand:
        if not isinstance(x, dict) or not x.get("category"):
            continue
        category = str(x["category"])
        v = next((x[k] for k in ("count", "orders", "weight", "demand", "score") if k in x), 1)
        try:
            result[category] = max(.1, min(float(v), 10000))
        except (ValueError, TypeError):
            result[category] = 1.0
    return result


def plan_restock(inv: dict[str, Any], products: dict[str, dict[str, Any]],
                 demand: Any, now: float | None = None) -> list[dict[str, Any]]:
    """Restrained, diversified inventory orders using only public demand.

    Supply unit cost is random and SKU-dependent. Spend at most a fraction
    of free cash, reserve an emergency buffer, avoid bulk food stock.
    """
    if int(inv.get("round", 0)) < 3:
        return []
    balance = money(inv.get("balance"), 0)
    funds = max(0, min(int(balance * RESTOCK_BUDGET_FRACTION), balance - MIN_CASH))
    units = [u for u in inv.get("units", []) if isinstance(u, dict) and u.get("grade") != "expired"]
    if funds <= 0 or len(units) >= MAX_STOCK_UNITS:
        return []
    weights = demand_weights(demand)
    if not weights:
        return []
    by_sku = Counter(str(u.get("sku", "")) for u in units)
    now_ts = time.time() if now is None else now
    # Stable ordering for reproducibility; avoid supply-crowding penalties
    # by restocking only 1-2 units of a SKU at a time.
    picks = []
    for sku, product in products.items():
        category = str(product.get("category", ""))
        demand_strength = weights.get(category, 0)
        if not demand_strength or by_sku[sku] >= MAX_PER_SKU:
            continue
        lp = money(product.get("list_price"))
        if lp <= 0 or lp > funds / 0.9:
            continue
        is_food = str(product.get("kind", "")).lower() in KNOWN_KINDS_FOOD
        if is_food and by_sku[sku] >= 1:
            continue
        if is_food and money(product.get("shelf_hours"), 999) < FOOD_MAX_HOURS_STORED:
            continue
        # Conservative 90% of retail as a pre-purchase upper budget estimate.
        estimate = int(math.ceil(lp * .90))
        if estimate > funds:
            continue
        # Rank using relative demand * margin capacity, not pure unit count.
        edge = max(1, lp - estimate) / max(1, estimate)
        score = math.log1p(demand_strength) * edge / (1 + by_sku[sku])
        if not is_food:
            score *= 1.1
        picks.append((score, sku, estimate))
    picks.sort(key=lambda x: (-x[0], x[1]))
    result = []
    for _, sku, expense in picks:
        if len(result) >= 6 or len(units) + len(result) >= MAX_STOCK_UNITS:
            break
        if expense > funds:
            continue
        result.append({"sku": sku, "qty": 1})
        funds -= expense
    return result
