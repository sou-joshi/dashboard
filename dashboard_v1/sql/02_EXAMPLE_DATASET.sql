-- Optional: paste this into AI/BI Dashboards > Data > Add dataset
-- Use when debugging a manual dataset; not required to import the ready-made dashboard.
-- 30-day Genie billing-by-user, based on validated IFBI schema.
SELECT
    LOWER(COALESCE(identity_metadata.run_as,'UNATTRIBUTED')) AS user_identity,
    CAST(workspace_id AS STRING) AS workspace_id,
    COALESCE(usage_metadata.genie.surface,'UNKNOWN') AS genie_product,
    ROUND(SUM(usage_quantity),2) AS total_dbus,
    ROUND(SUM(CASE WHEN sku_name='GENIE_FREE_USAGE' THEN usage_quantity ELSE 0 END),2) AS free_dbus,
    ROUND(SUM(CASE WHEN sku_name<>'GENIE_FREE_USAGE' THEN usage_quantity ELSE 0 END),2) AS billed_dbus,
    COUNT(DISTINCT usage_date) AS active_billing_days
FROM system.billing.usage
WHERE billing_origin_product='GENIE'
  AND usage_unit='DBU'
  AND usage_date >= DATE_SUB(CURRENT_DATE(),29)
GROUP BY identity_metadata.run_as, workspace_id, usage_metadata.genie.surface
ORDER BY billed_dbus DESC, total_dbus DESC;
