-- Liquidations in Morpho's USDC markets, by chain and year.
-- Same as usdc_liquidations_by_chain.sql with DATE_TRUNC added.
--
-- Self-check (run of 2026-09-15), bad debt per chain-year:
--   ethereum  2024 $8.01   2025 $2,295.33   2026 $1,181,923.72
--   base      2024 $0      2025 $99,595.20  2026 $12,290.18
--   Years sum to the full period: ethereum $1,184,227 / base $111,885.
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
    DATE_TRUNC('year', li.evt_block_time)                                      AS year,
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
GROUP BY li.chain, DATE_TRUNC('year', li.evt_block_time)   -- GROUP BY cannot use the SELECT alias
ORDER BY li.chain, year                                   -- ORDER BY runs after SELECT, so the alias works
