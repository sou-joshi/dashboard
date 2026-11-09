-- Query 1: The definitive Genie usage breakdown. Does NOT require pricing access.
SELECT
    COALESCE(usage_metadata.genie.surface, 'UNKNOWN') AS genie_product,
    COUNT(DISTINCT identity_metadata.run_as) AS active_identities,
    ROUND(SUM(usage_quantity), 2) AS total_dbus,
    ROUND(SUM(CASE WHEN sku_name = 'GENIE_FREE_USAGE' THEN usage_quantity ELSE 0 END), 2) AS free_dbus,
    ROUND(SUM(CASE WHEN sku_name <> 'GENIE_FREE_USAGE' THEN usage_quantity ELSE 0 END), 2) AS billed_dbus
FROM system.billing.usage
WHERE billing_origin_product = 'GENIE'
  AND usage_date >= DATE_SUB(CURRENT_DATE(), 29)
GROUP BY COALESCE(usage_metadata.genie.surface, 'UNKNOWN')
ORDER BY total_dbus DESC;

-- Query 2: Paid Genie SKU prices. Verify price matches before relying on USD.
SELECT
    u.sku_name,
    u.usage_unit,
    ROUND(SUM(u.usage_quantity), 2) AS billed_dbus,
    COUNT(*) AS paid_billing_rows,
    SUM(CASE WHEN lp.pricing.effective_list.default IS NULL THEN 1 ELSE 0 END) AS unpriced_rows,
    ROUND(SUM(CASE WHEN lp.pricing.effective_list.default IS NULL THEN NULL
                   ELSE u.usage_quantity * lp.pricing.effective_list.default END), 2) AS estimated_list_usd
FROM system.billing.usage u
LEFT JOIN system.billing.list_prices lp
    ON u.sku_name = lp.sku_name
   AND u.cloud = lp.cloud
   AND u.usage_unit = lp.usage_unit
   AND u.usage_end_time >= lp.price_start_time
   AND (lp.price_end_time IS NULL OR u.usage_end_time < lp.price_end_time)
WHERE u.billing_origin_product = 'GENIE'
  AND u.sku_name <> 'GENIE_FREE_USAGE'
  AND u.usage_date >= DATE_SUB(CURRENT_DATE(), 29)
GROUP BY u.sku_name, u.usage_unit
ORDER BY billed_dbus DESC;



-- Query for service principles

SELECT
    identity_metadata.run_as AS run_as_identity,
    usage_metadata.genie.surface AS genie_product,
    sku_name,

    COUNT(*) AS billing_records,

    ROUND(SUM(usage_quantity), 2) AS total_dbus,

    ROUND(SUM(
        CASE
            WHEN sku_name <> 'GENIE_FREE_USAGE'
            THEN usage_quantity
            ELSE 0
        END
    ), 2) AS billed_dbus

FROM system.billing.usage

WHERE billing_origin_product = 'GENIE'
  AND usage_unit = 'DBU'
  AND usage_date >= DATE_TRUNC('MONTH', CURRENT_DATE())

GROUP BY
    identity_metadata.run_as,
    usage_metadata.genie.surface,
    sku_name

ORDER BY billed_dbus DESC, total_dbus DESC;



SELECT
    identity_metadata.run_as AS run_as_identity,
    usage_metadata.genie.surface AS genie_product,
    usage_metadata.genie.channel AS access_channel,
    sku_name,

    COUNT(*) AS billing_records,
    ROUND(SUM(usage_quantity), 2) AS total_dbus

FROM system.billing.usage
WHERE billing_origin_product = 'GENIE'
  AND usage_unit = 'DBU'
  AND usage_date >= DATE_SUB(CURRENT_DATE(), 89)

GROUP BY
    identity_metadata.run_as,
    usage_metadata.genie.surface,
    usage_metadata.genie.channel,
    sku_name

ORDER BY
    genie_product,
    total_dbus DESC;


