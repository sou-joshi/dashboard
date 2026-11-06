# IFBI Genie — VDI deployment guide

## Install the dashboard (no Python on VDI required)

1. In your local permitted GitHub workflow, commit this complete repository to an **approved private repository**. Do not commit employee data, access tokens, screenshots or query exports.
2. From the IFBI VDI, open your approved GitHub repository (or approved artifact transfer mechanism), and download `dashboard/IFBI_Genie_Usage_Core.lvdash.json`.
3. In Databricks, select **SQL Editor**, choose your existing approved **Pro SQL warehouse**, and run `sql/00_VALIDATE_ACCESS.sql` statements individually. You have already verified Genie billing access.
4. Open **Dashboards** from the Databricks left navigation. On the dashboards list, use **Import dashboard from file** and select `IFBI_Genie_Usage_Core.lvdash.json`.
5. Open imported dashboard in **draft/edit mode**, select the approved SQL warehouse for datasets, run **Refresh**, and review the six pages.
6. Use `sql/01_RECONCILIATION.sql` to compare 30-day totals with the Executive page. If warehouse permissions, dataset binding, or JSON compatibility errors occur, export the issue details; do not publish invalid figures.
7. Restrict viewer permissions to the approved platform/FinOps/governance groups before publishing. Employee identities appear in the underlying datasets. Set refresh schedule based on operational need and billing update frequency.
8. Optional, after confirming `system.billing.list_prices` SELECT access, import `IFBI_Genie_Usage_With_List_Price.lvdash.json` (seven pages). This adds **estimated list-price USD**, not invoice cost. It can be deployed as a separate draft or replace the core dashboard after verifying all datasets.

**No CREATE SCHEMA or CREATE VIEW access is needed for these dashboards.** No user-facing dashboard files contain personal data or credentials: employee names/emails are queried from IFBI Databricks at runtime.

## First-run checklist

- [ ] Approved SQL warehouse selected in dashboard (not a serverless warehouse unless explicitly approved)
- [ ] `system.billing.usage` readable
- [ ] 30-day meter total reconciled to system.billing.usage
- [ ] Genie Code / Genie One SKUs represented
- [ ] Existing IFBI workspaces and Databricks accounts reconciled to platform inventory
- [ ] People with dashboard access approved
- [ ] Source freshness reviewed and refresh schedule set
- [ ] USD dashboard remains unshared until price access and price reconciliation verified

## Troubleshooting

| Issue | Action |
|---|---|
| Import not recognized as dashboard | File must have `.lvdash.json` suffix; use Dashboards > Import dashboard from file, not an arbitrary workspace file upload. |
| Query fails due to permission | Ensure you can query `system.billing.usage` with the selected warehouse. Pricing requires separate `system.billing.list_prices` access. |
| Dashboard shows no data | Check the SQL warehouse and user permissions, record dates and system table account scope. |
| All DBUs appear free | Check time window, SKU grouping, billing latency and whether any paid SKU records exist. |
| Totals differ from raw query | Ensure matching 30-day date window and `usage_unit = 'DBU'`, and confirm recent usage hasn't arrived between runs. |
| Invalid JSON/schema import | Share the Visio/Databricks import error; file is schema-validated locally but has not been imported into the IFBI tenant. |
| Chart seems overestimated | Remember that a billing record is NOT a prompt count or inference session, and negative corrections can occur. |

## Honest scope

This release uses `system.billing.usage` only (plus optional `system.billing.list_prices` for USD). It **cannot** show actual questions/prompts, Genie Agent accuracy, SQL execution reliability, restricted-table access attempts, true team attribution, or warehouse infrastructure spend. Those require additional system-table permissions and governance approvals. Do not label this as a comprehensive security audit.
