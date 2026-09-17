"""Fetch daily borrowing for every Morpho market whose loan asset is USDC.

Two stages:
  1. list the markets (paged through the `markets` query)
  2. pull each market's daily borrowAssets series (`marketById`)

Output: data/raw/morpho_api_usdc_markets_daily_borrow_<date>.json
Use borrowAssets (token units, 6 decimals) rather than borrowAssetsUsd: the
API's USD figures are wrong for a few frozen markets.
"""
import datetime as dt
import json
import time

import requests

URL = "https://api.morpho.org/graphql"
USDC_ETH = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
USDC_BASE = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
OUT_FILE = "data/raw/morpho_api_usdc_markets_daily_borrow_20260916.json"

# ---------- 1. sample window ----------
t0 = int(dt.datetime(2024, 4, 24, tzinfo=dt.timezone.utc).timestamp())
t1 = int(dt.datetime(2026, 9, 11, tzinfo=dt.timezone.utc).timestamp())

# ---------- 2. market list, one page at a time ----------
MARKET_TPL = """
{
  markets(first: 500, skip: SKIP,
          where: {chainId_in: [1, 8453],
                  loanAssetAddress_in: ["ADDR_ETH", "ADDR_BASE"]}) {
    items { marketId chain { id } collateralAsset { symbol } }
    pageInfo { countTotal }
  }
}
"""

all_items = []
skip = 0
while True:
    query = (MARKET_TPL.replace("SKIP", str(skip))
                       .replace("ADDR_ETH", USDC_ETH)
                       .replace("ADDR_BASE", USDC_BASE))
    d = requests.post(URL, json={"query": query}).json()["data"]["markets"]
    all_items.extend(d["items"])
    skip += 500
    if skip >= d["pageInfo"]["countTotal"]:
        break

print("markets:", len(all_items))

# ---------- 3. one market's daily borrowing ----------
HIST_TPL = """
{
  marketById(marketId: "MARKET_ID", chainId: CHAIN_ID) {
    historicalState {
      borrowAssets(options: {startTimestamp: T0, endTimestamp: T1,
                             interval: DAY}) { x y }
    }
  }
}
"""

# the window never changes inside the loop, so fill it in once
HIST_TPL = HIST_TPL.replace("T0", str(t0)).replace("T1", str(t1))


def fetch_points(market_id, chain_id):
    """Daily borrowing for one market; None if the request keeps failing."""
    query = (HIST_TPL.replace("MARKET_ID", market_id)
                     .replace("CHAIN_ID", str(chain_id)))
    for attempt in range(3):                      # two retries, backing off
        try:
            r = requests.post(URL, json={"query": query}, timeout=30).json()
            return r["data"]["marketById"]["historicalState"]["borrowAssets"]
        except Exception:
            time.sleep(2 * (attempt + 1))
    return None


# ---------- 4. every market ----------
out, failed = [], []
for i, m in enumerate(all_items):
    pts = fetch_points(m["marketId"], m["chain"]["id"])
    if pts is None:
        failed.append(m["marketId"])
        continue
    out.append({"marketId": m["marketId"],
                "chain": m["chain"]["id"],
                "collateral": m["collateralAsset"],
                "points": pts})
    if i % 200 == 0:
        print(f"  {i}/{len(all_items)} ok {len(out)} failed {len(failed)}", flush=True)

print("ok:", len(out), "failed:", len(failed))
json.dump(out, open(OUT_FILE, "w"))
print("saved:", OUT_FILE)
