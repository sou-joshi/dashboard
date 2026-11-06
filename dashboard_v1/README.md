# IFBI Genie Usage & Governance — AI/BI Dashboard v1.0

**Importable Databricks AI/BI dashboard · GitHub-ready · Customer-approved SQL warehouse · No CREATE statements.**

This edition is built around **the Genie billing fields already verified in the IFBI DEV workspace**:
`system.billing.usage`, `billing_origin_product = 'GENIE'`,
`identity_metadata.run_as`, `usage_metadata.genie.surface`, `sku_name`,
`usage_quantity`, `workspace_id` and `usage_date`.

## Import now

1. Run `sql/00_VALIDATE_ACCESS.sql` in Databricks **SQL Editor** (one statement at a time).
2. Use an existing approved **Pro SQL warehouse**. No serverless requirement.
3. In **Dashboards → Import dashboard from file**, import
   `dashboard/IFBI_Genie_Usage_Core.lvdash.json`.
4. Configure the warehouse on the imported dashboard's Data page; refresh.
5. Validate `Executive Pulse` values against `sql/01_RECONCILIATION.sql`.
6. Publish only to authorized platform, finance, and governance viewers.

Full guide: [`docs/VDI_IMPORT_GUIDE.md`](docs/VDI_IMPORT_GUIDE.md).

## Main dashboard pages

| Page | What you can use it for |
|---|---|
| Executive Pulse | 30-day metered/free/billable DBUs, unique billing identities, daily trend, largest consumption |
| User Adoption | User/workspace monthly usage split, Code/One/Agents consumption, 90-day observed engagement |
| Free & Billed Usage | Billing SKU breakdown, month-end DBU run-rate, paid usage and recorded Code free allowance |
| Workspace & Product | Account/workspace usage visibility and product adoption |
| Governance Watchlist | 7-day usage rate versus prior 28 days, newly observed identities, paid-DBU concentration |
| Billing Quality & Coverage | Missing attribution, last metered date, SKU/account/workspace coverage |

## USD edition (optional)

After access to `system.billing.list_prices` is validated, import
`dashboard/IFBI_Genie_Usage_With_List_Price.lvdash.json`, which adds page 07:
**List-Price Estimates**. The SQL LEFT JOIN preserves free records and marks
unpriced billed records; any unknown priced row makes the applicable aggregate
cost `NULL` rather than pretending the charge is zero. These are **list-price
estimates**, not negotiated invoice charges. SQL warehouse DBUs/AWS spend
and Fivetran costs are excluded.

## Repository

```text
README.md
.gitignore
dashboard/
  IFBI_Genie_Usage_Core.lvdash.json
  IFBI_Genie_Usage_With_List_Price.lvdash.json
docs/
  VDI_IMPORT_GUIDE.md
sql/
  00_VALIDATE_ACCESS.sql
  01_RECONCILIATION.sql
  02_EXAMPLE_DATASET.sql
  03_OPTIONAL_PRICED_USAGE.sql
tools/
  build_dashboard.py
tests/
  test_dashboard.py
```

## Regeneration (optional, local computer)

```bash
python3 tools/build_dashboard.py
python3 -m unittest discover -s tests -v
```

Python only generates portable dashboard JSON and never accesses IFBI.
**Never commit tokens, credentials or employee data to GitHub.**

## Important interpretation rules

- `COUNT(*)` of billing rows is not a number of prompts or conversations.
- `identity_metadata.run_as` may represent an executing identity, not an actual end user, particularly for service principals. It is not a verified employee roster.
- The 150-DBU promotional allowance applies to eligible human users under applicable product terms. The dashboard reports **observed free DBUs**, not entitlement remaining. It cannot verify principal type.
- Forecasting is a simple calendar-day extrapolation, not an invoice forecast.
- 7-day usage-rate increases are **review signals**, never evidence of misconduct. New users or absence of a 28-day baseline are treated separately.
- System billing has latency and is scoped to a Databricks account; multiple workspaces within an account do not prove that other Databricks accounts are covered.
- For governance, no prompt text, raw insurance records or query results are extracted; people-level consumption must be access controlled.
- The dashboard has been **validated structurally and with local tests**, but not executed against the IFBI SQL warehouse. Some widget import format may change over time; use the UI error to tune the file if necessary.

Documentation:
- https://docs.databricks.com/aws/en/dashboards/automate/import-export
- https://docs.databricks.com/aws/en/genie/monitor-cost
- https://docs.databricks.com/aws/en/admin/system-tables/billing
- https://docs.databricks.com/aws/en/admin/system-tables/pricing
