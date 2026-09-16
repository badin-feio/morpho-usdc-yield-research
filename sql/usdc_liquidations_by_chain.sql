-- Liquidations in Morpho's USDC markets, by chain.
-- Supplies every numerator for EL = liquidation intensity
--   x P(bad debt | liquidation) x LGD.
--
-- Self-check (run of 2026-09-14):
--   ethereum  n 2,235   repaid $227,867,665  bad $1,184,227
--             numbers 206   repaid_baddebt $2,967
--   base      n 24,809  repaid $485,270,661  bad $111,885
--             numbers 405   repaid_baddebt $487,588
-- The query has no end date, so later runs return slightly larger counts.
WITH blue_market AS (
    SELECT
        id,
        from_hex(json_value(marketParams, 'lax $.loanToken'))       AS loan_token,
        from_hex(json_value(marketParams, 'lax $.collateralToken')) AS collateral_token,
        from_hex(json_value(marketParams, 'lax $.oracle'))          AS oracle_address,
        from_hex(json_value(marketParams, 'lax $.irm'))             AS irm_address,
        CAST(json_value(marketParams, 'lax $.lltv') AS double) / pow(10, 18) AS lltv,
        chain AS blockchain
    FROM morpho_blue_multichain.morphoblue_evt_createmarket
)                                   -- no comma after the last CTE

SELECT
    li.chain,
    COUNT(*)                                                                   AS n,                   -- all liquidations
    SUM(li.repaidAssets / 1e6)                                                 AS repaid_assets_usd,   -- repaid debt (USDC has 6 decimals, ~$1)
    SUM(li.badDebtAssets / 1e6)                                                AS bad_debt_usd,        -- bad debt (only arises in failed liquidations)
    SUM(CASE WHEN li.badDebtShares > 0 THEN 1 ELSE 0 END)                      AS numbers,             -- liquidations that left bad debt
    SUM(CASE WHEN li.badDebtShares > 0 THEN li.repaidAssets / 1e6 ELSE 0 END)  AS repaid_baddebt_usd   -- repaid debt within those liquidations
FROM morpho_blue_multichain.morphoblue_evt_liquidate li
JOIN blue_market bl
    ON li.id = bl.id
   AND li.chain = bl.blockchain     -- match the chain too: the same market id can exist on both
WHERE li.chain IN ('ethereum', 'base')
  AND bl.loan_token IN (
        0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48,   -- Ethereum USDC (varbinary literal, no quotes)
        0x833589fcd6edb6e08f4c7c32d4f71b54bda02913    -- Base USDC
      )
GROUP BY li.chain
