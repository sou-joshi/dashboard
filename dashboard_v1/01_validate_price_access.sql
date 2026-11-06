
-- Check that Genie billing records exist
SELECT
  usage_date,
  usage_metadata.genie.surface AS genie_product,
  sku_name,
  ROUND(SUM(usage_quantity), 2) AS total_dbus
FROM system.billing.usage
WHERE billing_origin_product = 'GENIE'
  AND usage_unit = 'DBU'
  AND usage_date >= DATE_SUB(CURRENT_DATE(), 30)
GROUP BY usage_date, usage_metadata.genie.surface, sku_name
ORDER BY usage_date DESC, total_dbus DESC;

-- Check that list price rows are available for the paid Genie SKUs
SELECT
  lp.sku_name,
  lp.cloud,
  lp.usage_unit,
  lp.price_start_time,
  lp.price_end_time,
  lp.pricing.effective_list.default AS effective_list_price
FROM system.billing.list_prices lp
WHERE lp.sku_name IN (
  SELECT DISTINCT sku_name
  FROM system.billing.usage
  WHERE billing_origin_product = 'GENIE'
    AND sku_name <> 'GENIE_FREE_USAGE'
)
ORDER BY lp.sku_name, lp.price_start_time DESC;
