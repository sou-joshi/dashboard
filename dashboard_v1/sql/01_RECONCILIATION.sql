-- IFBI Genie dashboard reconciliation checks (read-only)
-- Before publishing, compare totals with Dashboard page 01 using the same time interval.

-- 30-day control totals
SELECT
  ROUND(SUM(usage_quantity),2) AS total_metered_dbus,
  ROUND(SUM(CASE WHEN sku_name='GENIE_FREE_USAGE' THEN usage_quantity ELSE 0 END),2) AS free_dbus,
  ROUND(SUM(CASE WHEN sku_name<>'GENIE_FREE_USAGE' THEN usage_quantity ELSE 0 END),2) AS billed_dbus,
  COUNT(DISTINCT identity_metadata.run_as) AS distinct_non_null_identities,
  COUNT(*) AS billing_records
FROM system.billing.usage
WHERE billing_origin_product='GENIE' AND usage_unit='DBU'
  AND usage_date >= DATE_SUB(CURRENT_DATE(),29);

-- Month-to-date billed Genie DBUs. Useful to compare with page 03.
SELECT usage_metadata.genie.surface AS genie_product,
       ROUND(SUM(CASE WHEN sku_name<>'GENIE_FREE_USAGE' THEN usage_quantity ELSE 0 END),2) AS billed_dbus,
       ROUND(SUM(CASE WHEN sku_name='GENIE_FREE_USAGE' THEN usage_quantity ELSE 0 END),2) AS free_dbus
FROM system.billing.usage
WHERE billing_origin_product='GENIE' AND usage_unit='DBU'
  AND usage_date >= DATE_TRUNC('MONTH',CURRENT_DATE())
GROUP BY usage_metadata.genie.surface ORDER BY billed_dbus DESC;
