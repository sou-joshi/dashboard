-- IFBI Genie Dashboard • Read-only checks
-- Run each statement separately in Databricks SQL Editor using an APPROVED SQL warehouse.
-- No CREATE, GRANT or administrative privileges are required for the CORE dashboard.

-- 1. Genie usage is visible (should return daily records).
SELECT usage_date,
       usage_metadata.genie.surface AS genie_product,
       sku_name,
       ROUND(SUM(usage_quantity),2) AS dbus,
       COUNT(*) AS billing_rows
FROM system.billing.usage
WHERE billing_origin_product = 'GENIE'
  AND usage_date >= DATE_SUB(CURRENT_DATE(),29)
GROUP BY usage_date,usage_metadata.genie.surface,sku_name
ORDER BY usage_date DESC, dbus DESC;

-- 2. What workspaces and account(s) are covered?
SELECT account_id,CAST(workspace_id AS STRING) AS workspace_id,
       COUNT(DISTINCT identity_metadata.run_as) AS observed_identities,
       MIN(usage_date) AS earliest_usage_date,
       MAX(usage_date) AS most_recent_usage_date,
       ROUND(SUM(usage_quantity),2) AS dbus
FROM system.billing.usage
WHERE billing_origin_product = 'GENIE'
GROUP BY account_id,workspace_id ORDER BY dbus DESC;

-- 3. OPTIONAL: Can you query list prices? Only needed for the USD edition.
SELECT sku_name,cloud,usage_unit,price_start_time,price_end_time,
       pricing.effective_list.default AS unit_list_price
FROM system.billing.list_prices
WHERE sku_name <> 'GENIE_FREE_USAGE'
ORDER BY price_start_time DESC LIMIT 10;
