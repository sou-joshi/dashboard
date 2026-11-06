-- OPTIONAL. Validate price table permission and rate windows before attempting to publish USD metrics.
-- Databricks list-price USD estimates are NOT actual IFBI invoice costs.
-- Safe LEFT JOIN: free usage remains visible; missing prices are not silently zeroed.
WITH priced AS (
 SELECT u.account_id,u.workspace_id,u.record_id,u.usage_date,
        LOWER(COALESCE(u.identity_metadata.run_as,'UNATTRIBUTED')) AS user_identity,
        COALESCE(u.usage_metadata.genie.surface,'UNKNOWN') AS genie_product,
        u.sku_name,u.usage_quantity,
        CASE WHEN u.sku_name='GENIE_FREE_USAGE' THEN 0D
             WHEN lp.pricing.effective_list.default IS NULL THEN NULL
             ELSE CAST(u.usage_quantity AS DOUBLE)*CAST(lp.pricing.effective_list.default AS DOUBLE)
        END AS list_cost_usd,
        CASE WHEN u.sku_name<>'GENIE_FREE_USAGE' AND lp.sku_name IS NULL THEN 1 ELSE 0 END AS missing_price,
        ROW_NUMBER() OVER (
           PARTITION BY u.account_id,u.record_id ORDER BY lp.price_start_time DESC NULLS LAST
        ) AS rn
 FROM system.billing.usage u
 LEFT JOIN system.billing.list_prices lp
   ON u.sku_name=lp.sku_name
  AND u.cloud=lp.cloud AND u.usage_unit=lp.usage_unit
  AND u.usage_end_time >= lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
 WHERE u.billing_origin_product='GENIE' AND u.usage_unit='DBU'
   AND u.usage_date >= DATE_SUB(CURRENT_DATE(),29)
)
SELECT user_identity,genie_product,
       ROUND(SUM(CASE WHEN sku_name<>'GENIE_FREE_USAGE' THEN usage_quantity ELSE 0 END),2) AS billed_dbus,
       SUM(missing_price) AS paid_records_without_list_price,
       CASE WHEN SUM(missing_price)>0 THEN NULL
            ELSE ROUND(SUM(list_cost_usd),2) END AS estimated_list_usd
FROM priced WHERE rn=1
GROUP BY user_identity,genie_product
ORDER BY billed_dbus DESC;
