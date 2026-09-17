# What DeFi rates should be, measured on Morpho

Code and queries behind the note
[*What DeFi Rates Should Be, Measured on Morpho*](what-defi-rates-should-be-measured-on-morpho.pdf). The note takes Tom Dunleavy's bond-math
decomposition of a DeFi lending yield and measures the credit-loss term
on-chain instead of assuming it, for USDC lending on Morpho on Ethereum
and Base, April 2024 to September 2026.

## What it finds

| | Ethereum | Base |
|---|---:|---:|
| Credit loss, per year | 7.1 bps | 0.7 bps |
| Operational loss (Morpho's own record to the sector average) | 2–62 bps | 2–62 bps |
| Realized vault yield | 5.96% | 4.19% |
| Buffer left for tail risk, full period | +145 bps | −18 bps |
| Buffer in 2026 | −42 bps | +7 bps |

Expected credit loss is decomposed as

```
EL = liquidation intensity × P(bad debt | liquidation) × LGD
```

Almost all of the credit loss on each chain comes from a single event: the
Resolv exploit of March 2026 on Ethereum, and an oracle manipulation of an
Aerodrome cUSDO/USDC LP token in May 2025 on Base. The largest markets,
cbBTC/USDC on both chains, recorded less than one cent of bad debt.

## Reproducing the numbers

Everything is measured in dollars rather than in number of events, and all
data come from Morpho itself.

**1. Liquidations and bad debt (the numerator).** Run either query on Dune:

- `sql/usdc_liquidations_by_chain.sql` — whole period
- `sql/usdc_liquidations_by_chain_year.sql` — by year

Both filter to markets whose loan asset is USDC by contract address, since
several tokens on-chain also call themselves USDC. Export the result as CSV.
Published version: <https://dune.com/queries/8715535/>

**2. Borrowing (the denominator).**

```
python scripts/fetch_usdc_markets.py   # ~3,900 markets, daily borrowing, ~15 min
python scripts/denominator.py          # average borrowing per chain
```

`scripts/fetch_usdc_markets.py` pages through Morpho's GraphQL API for every market
whose loan asset is USDC, then pulls each market's daily `borrowAssets`
series. `scripts/denominator.py` aligns the series to a common date index, drops two
frozen markets whose recorded borrowing is unpaid interest compounding at the
maximum rate, and reports the average.

**3. What depositors actually earned.**

```
python scripts/vault_realized_yield.py
```

Reads daily share prices and sizes for every USDC vault, computes each
vault's daily return, weights vaults by their size on the previous day,
compounds and annualizes. The result is net of curator fees and of bad debt
the vaults have recognized, and excludes reward tokens.

**4. Figures.**

```
python scripts/make_figures.py
```

## Data

Raw pulls are not committed; the scripts fetch them. The risk-free rate is
the three-month Treasury yield (FRED series `DGS3MO`), saved as
`data/raw/fred_DGS3MO.csv`.

## Caveats

- Morpho records bad debt only when a position is liquidated. A market whose
  collateral has collapsed can sit at 100% utilization with the loss
  unrecorded, so the credit loss here is a lower bound.
- Two events per chain are far too few to estimate a tail distribution, and
  no attempt is made to.
- The vault samples differ in risk profile between the chains, so part of the
  gap between them reflects vault mix rather than the chain itself.

## Requirements

Python 3.9+, with `pandas`, `requests` and `matplotlib`.

Run the scripts from the repository root, so that the relative paths to
`data/` and `figures/` resolve.
