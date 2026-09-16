"""Average USDC borrowing per chain: the denominator of expected credit loss.

Inputs (both fetched and saved by fetch_denominator_wip.py):
  data/raw/morpho_api_usdc_markets_daily_borrow_20260916.json   daily borrowing
  data/raw/morpho_api_usdc_markets_listed_20260916.json         listed flag

Exclusion rule: drop a market if it is not listed AND its borrowing ever
exceeds $1bn. Those are frozen markets where unpaid debt keeps accruing
interest at the maximum rate, so the balance does not reflect real lending.
Both conditions are needed: peak alone would also drop Base's largest healthy
market, cbBTC/USDC, which peaks around $1.4bn.

Targets: Ethereum $695.7M, Base $721.3M (before the exclusion: Ethereum
about $1,418M).
"""
import datetime as dt
import json

import pandas as pd

BORROW = "data/raw/morpho_api_usdc_markets_daily_borrow_20260916.json"
LISTED = "data/raw/morpho_api_usdc_markets_listed_20260916.json"
DAYS = pd.date_range("2024-04-24", "2026-09-11").date       # 871 days
CHAINS = {1: "Ethereum", 8453: "Base"}


def make_series(points):
    """API points -> Series indexed by date, in USDC (raw units have 6 dp).

    Some days come back as null; drop them here and let the caller's
    reindex fill those dates with zero.
    """
    s = pd.Series({dt.datetime.utcfromtimestamp(p["x"]).date(): p["y"] / 1e6
                   for p in points if p["y"] is not None})
    return s.sort_index()


markets = json.load(open(BORROW))
listed_map = {m["marketId"]: m["listed"] for m in json.load(open(LISTED))}

total = {1: 0, 8453: 0}          # after the exclusion
gross = {1: 0, 8453: 0}          # before it, for comparison
dropped = []

for m in markets:
    # markets start on different dates, so align them all to the same index
    # and treat a missing day as zero borrowing
    s = make_series(m["points"]).reindex(DAYS).fillna(0)
    gross[m["chain"]] = gross[m["chain"]] + s

    if not listed_map[m["marketId"]] and s.max() > 1e9:
        sym = (m["collateral"] or {}).get("symbol")
        dropped.append((CHAINS[m["chain"]], sym, s.max()))
        continue

    total[m["chain"]] = total[m["chain"]] + s

print(f"{len(markets)} markets, {len(dropped)} excluded:")
for chain, sym, peak in dropped:
    print(f"  {chain} {sym}/USDC  peak ${peak/1e9:.2f}B")

print()
for cid, name in CHAINS.items():
    print(f"{name}: average borrowing ${total[cid].mean()/1e6:,.1f}M"
          f"   (before exclusion ${gross[cid].mean()/1e6:,.1f}M)")
