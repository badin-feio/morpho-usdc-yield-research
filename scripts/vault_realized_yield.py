"""Realised net yield for USDC vault depositors, by chain, against the bill.

Data: data/raw/morpho_api_usdc_vaults_daily_shareprice_tvl.json.gz
      (Morpho API historicalState: daily share price and size per vault)
      data/raw/fred_DGS3MO.csv (three-month Treasury yield)

Each vault's daily return comes from its share price, vaults are weighted by
their size on the previous day, and the daily averages are compounded and
annualised. This is a time-weighted return: what a dollar left in the vaults
throughout would have earned. It includes interest, curator fees and
recognised bad debt, and excludes reward tokens.
"""
import gzip
import json
import datetime as dt

import numpy as np
import pandas as pd

VAULTS = "data/raw/morpho_api_usdc_vaults_daily_shareprice_tvl.json.gz"
RF = "data/raw/fred_DGS3MO.csv"
DAYS = pd.date_range("2024-04-23", "2026-09-11").date      # day 0 only seeds the first return
MIN_TVL = 1e6                                              # skip a vault-day below $1M
# vaults whose share price is impossible (a constant +2.2% a day, or +194%
# in a year): drop the whole vault, never single days by size of move, or a
# real loss such as Gauntlet USDC Core's -29.5% would be dropped too
BOGUS = {"Adpend USDC", "1337 USDC", "Duplicated Key", "ABRC", "Clearstar Yield USDC", "Everstone"}
CHAINS = {1: "Ethereum", 8453: "Base"}


def daily(points):
    return pd.Series({dt.datetime.utcfromtimestamp(p["x"]).date(): p["y"]
                      for p in (points or []) if p["y"] is not None}).sort_index().reindex(DAYS)


vaults = json.load(gzip.open(VAULTS))
rows = []
for v in vaults:
    sp, tvl = daily(v["hist"].get("sp")), daily(v["hist"].get("tvl"))
    rows.append(pd.DataFrame(dict(date=DAYS, r=(sp / sp.shift(1) - 1).values, w=tvl.shift(1).values,
                                  chain=v["chain"], type=v["type"], name=v["name"],
                                  addr=v["address"].lower())))
df = pd.concat(rows)
df = df[df.date > DAYS[0]].dropna(subset=["r", "w"])
df = df[(df.w >= MIN_TVL) & ~df.name.isin(BOGUS)]

rf = pd.read_csv(RF, parse_dates=["observation_date"])
rf = pd.to_numeric(rf.DGS3MO, errors="coerce").set_axis(rf.observation_date.dt.date).reindex(DAYS).ffill() / 100


def annualize(r):
    return (1 + r).prod() ** (365.25 / len(r)) - 1


for cid, name in CHAINS.items():
    s = df[df.chain == cid]
    idx = s.groupby("date").apply(lambda x: np.average(x.r, weights=x.w))
    idx = idx.reindex([d for d in DAYS if d >= idx.index.min()]).fillna(0)
    n_vaults = s.groupby("type").addr.nunique().to_dict()   # distinct contracts
    net, rfm = annualize(idx), rf.loc[idx.index].mean()
    print(f"{name}: {idx.index.min()} → {idx.index.max()}  vaults used {n_vaults}  avg TVL ${s.groupby('date').w.sum().mean()/1e9:.2f}B")
    print(f"  realized net {net:.2%}   Rf {rfm:.2%}   excess {(net - rfm) * 1e4:+.0f} bps")
    for y in (2024, 2025, 2026):
        sub = idx[[d.year == y for d in idx.index]]
        print(f"  {y}: realized {annualize(sub):.2%}  Rf {rf.loc[sub.index].mean():.2%}  "
              f"excess {(annualize(sub) - rf.loc[sub.index].mean()) * 1e4:+.0f} bps  "
              f"avg TVL ${s[s.date.isin(sub.index)].groupby('date').w.sum().mean()/1e9:.2f}B")
    big_losses = s[s.r < -0.01].sort_values("date")
    for r in big_losses.itertuples():
        print(f"  loss day {r.date}  {r.name}  {r.r:.1%}  (TVL ${r.w/1e6:.1f}M)")
