#!/usr/bin/env python3
"""Fetch global FX rates + Iranian free-market rial prices into data/rates.json.

Global (per 1 USD): fawazahmed0 currency-api (jsDelivr / Cloudflare mirror), fallback open.er-api.com.
Iran free market (rial per unit): tgju.org public ajax feed.
Never wipes good data: if a source fails, the previous values are kept.
"""
from __future__ import annotations
import json, re, sys, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "rates.json"
UA = {"User-Agent": "Mozilla/5.0 (NABZ Tools rates bot; +https://nabzkhabarofficial.github.io/nabz-tools/)"}
GLOBAL_SOURCES = [
    "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.min.json",
    "https://latest.currency-api.pages.dev/v1/currencies/usd.min.json",
]
ER_API = "https://open.er-api.com/v6/latest/USD"
TGJU = "https://call1.tgju.org/ajax.json"
CRYPTO = ["btc", "eth", "usdt", "usdc", "bnb", "sol", "xrp", "ton", "trx", "doge", "ada", "ltc", "dot", "avax", "shib"]
METALS = ["xau", "xag", "xpt", "xpd"]
GOLD_KEYS = {"sekee": ["sekee"], "sekeb": ["sekeb"], "nim": ["nim", "retail_nim"], "rob": ["rob", "retail_rob"],
             "gerami": ["gerami", "retail_gerami"], "geram18": ["geram18", "tgju_gold_irg18"], "mesghal": ["mesghal"]}
MAJORS = ["eur", "gbp", "aed", "try", "cad", "aud", "chf", "cny", "sar", "qar", "omr", "kwd", "sgd", "sek", "nok", "nzd", "myr"]
# currencies that are obsolete/duplicate in the feed
DROP = {"ats", "bef", "dem", "esp", "fim", "frf", "grd", "iep", "itl", "luf", "nlg", "pte", "cyp", "eek", "lvl", "ltl",
        "mtl", "sit", "skk", "val", "trl", "rol", "mgf", "mzm", "sdd", "srg", "tmm", "veb", "vef", "zwd", "byr", "ghc",
        "azm", "mro", "std", "xbt", "zmk", "sll", "hrk", "spl", "cuc", "mxv", "tvd"}


def get_json(url: str, timeout: int = 25):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def num(v) -> float | None:
    try:
        x = float(re.sub(r"[^\d.]", "", str(v)))
        return x if x > 0 else None
    except ValueError:
        return None


def fetch_global() -> tuple[dict, str, str] | None:
    for url in GLOBAL_SOURCES:
        try:
            d = get_json(url)
            raw = d.get("usd") or {}
            fiat = {k: float(v) for k, v in raw.items() if re.fullmatch(r"[a-z]{3}", k) and k not in DROP and isinstance(v, (int, float)) and v > 0}
            extra = {k: float(raw[k]) for k in CRYPTO + METALS if isinstance(raw.get(k), (int, float)) and raw[k] > 0}
            fiat.update(extra)
            if len(fiat) > 100 and "eur" in fiat:
                fiat["usd"] = 1.0
                return fiat, str(d.get("date", "")), "currency-api"
        except Exception as e:  # noqa: BLE001
            print("global source failed", url, e, file=sys.stderr)
    try:
        d = get_json(ER_API)
        if d.get("result") == "success":
            rates = {k.lower(): float(v) for k, v in d["rates"].items() if v}
            return rates, d.get("time_last_update_utc", ""), "exchangerate-api"
    except Exception as e:  # noqa: BLE001
        print("er-api failed", e, file=sys.stderr)
    return None


def fetch_market(global_rates: dict) -> tuple[dict, dict, str] | None:
    try:
        d = get_json(TGJU)
    except Exception as e:  # noqa: BLE001
        print("tgju failed", e, file=sys.stderr)
        return None
    cur = d.get("current") or {}
    market, newest = {}, ""
    usd = cur.get("price_dollar_rl") or {}
    usd_p = num(usd.get("p"))
    newest = usd.get("ts", "")
    if not usd_p:
        # derive the free-market dollar from major currencies' rial prices x global cross rates (median)
        est = []
        for c in MAJORS:
            item = cur.get(f"price_{c}") or {}
            p, g = num(item.get("p")), global_rates.get(c)
            if p and g:
                est.append(p * g)
                newest = max(newest, item.get("ts", ""))
        if len(est) < 3:
            print("tgju: no usable dollar price", file=sys.stderr)
            return None
        est.sort()
        usd_p = round(est[len(est) // 2], -2)
    market["usd"] = usd_p
    for key, item in cur.items():
        m = re.fullmatch(r"price_([a-z]{3})", key)
        if not m or not isinstance(item, dict):
            continue
        code, p = m.group(1), num(item.get("p"))
        if not p or code in DROP:
            continue
        # sanity check: must be within 35% of the USD-cross value, otherwise the feed entry is stale/odd
        g = global_rates.get(code)
        if g:
            implied = usd_p / g
            if not (0.65 * implied <= p <= 1.35 * implied):
                continue
        market[code] = p
    gold = {}
    for out_key, keys in GOLD_KEYS.items():
        for key in keys:
            p = num((cur.get(key) or {}).get("p"))
            if p:
                gold[out_key] = p
                break
    return market, gold, newest


def main() -> int:
    old = {}
    if OUT.exists():
        try:
            old = json.loads(OUT.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            old = {}
    data = dict(old)
    data.pop("seed", None)
    g = fetch_global()
    if g:
        data["usd"], data["global_date"], data["global_source"] = g
    if not data.get("usd"):
        print("no global rates at all", file=sys.stderr)
        return 1
    m = fetch_market(data["usd"])
    if m:
        data["market"], data["gold"], data["market_ts"] = m
        data["market_source"] = "tgju.org"
    data["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True), encoding="utf-8")
    print(f"rates: {len(data['usd'])} global, {len(data.get('market', {}))} market, usd_irr_market={data.get('market', {}).get('usd')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
