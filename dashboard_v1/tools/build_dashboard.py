#!/usr/bin/env python3
"""Build version controlled Databricks AI/BI Genie dashboard files.
No dependencies other than the Python 3 standard library. Does not contact Databricks.
"""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DASH=ROOT/'dashboard'

BASE = """WITH base AS (
 SELECT u.account_id, CAST(u.workspace_id AS STRING) AS workspace_id,
        u.record_id, u.usage_date, u.usage_end_time, u.cloud, u.usage_unit,
        LOWER(COALESCE(u.identity_metadata.run_as, 'UNATTRIBUTED')) AS user_identity,
        COALESCE(u.usage_metadata.genie.surface, 'UNKNOWN') AS genie_product,
        u.sku_name,
        CAST(u.usage_quantity AS DOUBLE) AS total_dbus,
        CASE WHEN u.sku_name = 'GENIE_FREE_USAGE'
             THEN CAST(u.usage_quantity AS DOUBLE) ELSE 0D END AS free_dbus,
        CASE WHEN u.sku_name <> 'GENIE_FREE_USAGE'
             THEN CAST(u.usage_quantity AS DOUBLE) ELSE 0D END AS billed_dbus
 FROM system.billing.usage u
 WHERE u.billing_origin_product = 'GENIE'
   AND u.usage_unit = 'DBU'
   AND u.usage_date >= DATE_SUB(CURRENT_DATE(), 89)
)
"""

DATASETS={
 'executive': BASE+"""SELECT ROUND(SUM(total_dbus),2) AS total_dbus_30d,
 ROUND(SUM(free_dbus),2) AS free_dbus_30d,
 ROUND(SUM(billed_dbus),2) AS billed_dbus_30d,
 COUNT(DISTINCT user_identity) AS identities_30d,
 COUNT(DISTINCT workspace_id) AS workspaces_30d,
 MAX(usage_date) AS latest_usage_date
 FROM base WHERE usage_date >= DATE_SUB(CURRENT_DATE(),29)""",
 'daily_trend':BASE+"""SELECT usage_date AS day,
 ROUND(SUM(total_dbus),2) AS total_dbus,
 ROUND(SUM(free_dbus),2) AS free_dbus,
 ROUND(SUM(billed_dbus),2) AS billed_dbus,
 COUNT(DISTINCT user_identity) AS identities
 FROM base WHERE usage_date >= DATE_SUB(CURRENT_DATE(),29)
 GROUP BY usage_date ORDER BY usage_date""",
 'surface_30d':BASE+"""SELECT genie_product,
 ROUND(SUM(total_dbus),2) AS total_dbus,
 ROUND(SUM(free_dbus),2) AS free_dbus,
 ROUND(SUM(billed_dbus),2) AS billed_dbus,
 COUNT(DISTINCT user_identity) AS identities
 FROM base WHERE usage_date >= DATE_SUB(CURRENT_DATE(),29)
 GROUP BY genie_product ORDER BY total_dbus DESC""",
 'top_users_30d':BASE+"""SELECT user_identity,
 ROUND(SUM(total_dbus),2) AS total_dbus,
 ROUND(SUM(free_dbus),2) AS free_dbus,
 ROUND(SUM(billed_dbus),2) AS billed_dbus,
 COUNT(DISTINCT usage_date) AS active_billing_days,
 COUNT(DISTINCT genie_product) AS products_used,
 MAX(usage_date) AS last_metered_day
 FROM base WHERE usage_date >= DATE_SUB(CURRENT_DATE(),29)
 GROUP BY user_identity ORDER BY billed_dbus DESC, total_dbus DESC LIMIT 200""",
 'users_mtd':BASE+"""SELECT user_identity, workspace_id,
 ROUND(SUM(total_dbus),2) AS mtd_total_dbus,
 ROUND(SUM(free_dbus),2) AS mtd_free_dbus,
 ROUND(SUM(billed_dbus),2) AS mtd_billed_dbus,
 ROUND(SUM(CASE WHEN genie_product = 'GENIE_CODE' THEN total_dbus ELSE 0 END),2) AS code_dbus,
 ROUND(SUM(CASE WHEN genie_product = 'GENIE_ONE' THEN total_dbus ELSE 0 END),2) AS one_dbus,
 ROUND(SUM(CASE WHEN genie_product = 'GENIE_AGENTS' THEN total_dbus ELSE 0 END),2) AS agents_dbus,
 COUNT(DISTINCT usage_date) AS active_billing_days,
 MAX(usage_date) AS last_metered_day
 FROM base WHERE usage_date >= DATE_TRUNC('MONTH', CURRENT_DATE())
 GROUP BY user_identity,workspace_id
 ORDER BY mtd_billed_dbus DESC,mtd_total_dbus DESC LIMIT 2000""",
 'activity_90d':BASE+"""SELECT user_identity, MIN(usage_date) AS first_seen_in_90d,
 MAX(usage_date) AS last_seen_in_90d,
 COUNT(DISTINCT usage_date) AS active_billing_days_90d,
 ROUND(SUM(total_dbus),2) AS total_dbus_90d,
 COUNT(DISTINCT genie_product) AS genie_products_used,
 COUNT(DISTINCT workspace_id) AS workspaces_used
 FROM base GROUP BY user_identity ORDER BY total_dbus_90d DESC LIMIT 2000""",
 'week_activity':BASE+"""SELECT CAST(DATE_TRUNC('WEEK',usage_date) AS DATE) AS week_start,
 COUNT(DISTINCT user_identity) AS active_metered_identities,
 ROUND(SUM(total_dbus),2) AS metered_dbus
 FROM base GROUP BY DATE_TRUNC('WEEK',usage_date) ORDER BY week_start""",
 'billing_sku_mtd':BASE+"""SELECT sku_name, genie_product,
 ROUND(SUM(total_dbus),2) AS dbus_mtd,
 ROUND(SUM(billed_dbus),2) AS billed_dbus_mtd,
 ROUND(SUM(free_dbus),2) AS free_dbus_mtd,
 COUNT(DISTINCT user_identity) AS identities,
 COUNT(*) AS billing_rows
 FROM base WHERE usage_date >= DATE_TRUNC('MONTH',CURRENT_DATE())
 GROUP BY sku_name,genie_product ORDER BY billed_dbus_mtd DESC,dbus_mtd DESC""",
 'monthly_cost_proxy':BASE+"""SELECT CAST(DATE_TRUNC('MONTH',usage_date) AS DATE) AS month,
 genie_product,
 ROUND(SUM(total_dbus),2) AS total_dbus,
 ROUND(SUM(billed_dbus),2) AS billed_dbus,
 ROUND(SUM(free_dbus),2) AS free_dbus
 FROM base GROUP BY DATE_TRUNC('MONTH',usage_date),genie_product
 ORDER BY month,genie_product""",
 'runrate_mtd':BASE+"""SELECT ROUND(SUM(billed_dbus),2) AS mtd_billed_dbus,
 ROUND(SUM(billed_dbus) * DAY(LAST_DAY(CURRENT_DATE())) /
       GREATEST(DAY(CURRENT_DATE()),1),2) AS indicative_month_end_billed_dbus,
 ROUND(SUM(total_dbus),2) AS mtd_total_dbus
 FROM base WHERE usage_date >= DATE_TRUNC('MONTH',CURRENT_DATE())""",
 'workspace_30d':BASE+"""SELECT account_id,workspace_id,genie_product,
 ROUND(SUM(total_dbus),2) AS total_dbus,
 ROUND(SUM(billed_dbus),2) AS billed_dbus,
 COUNT(DISTINCT user_identity) AS active_identities,
 MAX(usage_date) AS last_metered_day
 FROM base WHERE usage_date >= DATE_SUB(CURRENT_DATE(),29)
 GROUP BY account_id,workspace_id,genie_product
 ORDER BY total_dbus DESC""",
 'workspace_summary':BASE+"""SELECT workspace_id,ROUND(SUM(total_dbus),2) AS total_dbus,
 ROUND(SUM(billed_dbus),2) AS billed_dbus,
 COUNT(DISTINCT user_identity) AS identities
 FROM base WHERE usage_date >= DATE_SUB(CURRENT_DATE(),29)
 GROUP BY workspace_id ORDER BY total_dbus DESC""",
 'spikes':BASE+""" ,
 stats AS (
   SELECT user_identity,
   SUM(CASE WHEN usage_date >= DATE_SUB(CURRENT_DATE(),6) THEN total_dbus ELSE 0 END) AS last_7d_dbus,
   SUM(CASE WHEN usage_date >= DATE_SUB(CURRENT_DATE(),34)
                 AND usage_date < DATE_SUB(CURRENT_DATE(),6) THEN total_dbus ELSE 0 END) AS previous_28d_dbus,
   SUM(CASE WHEN usage_date >= DATE_SUB(CURRENT_DATE(),6) THEN billed_dbus ELSE 0 END) AS last_7d_paid,
   MAX(usage_date) AS last_metered_day
   FROM base WHERE usage_date >= DATE_SUB(CURRENT_DATE(),34)
   GROUP BY user_identity
 )
 SELECT user_identity,
 ROUND(last_7d_dbus,2) AS last_7d_dbus,
 ROUND(previous_28d_dbus,2) AS previous_28d_dbus,
 ROUND(last_7d_paid,2) AS last_7d_billed_dbus,
 CASE WHEN previous_28d_dbus > 0
      THEN ROUND((last_7d_dbus/7D)/(previous_28d_dbus/28D),2)
      ELSE NULL END AS rate_ratio,
 CASE WHEN previous_28d_dbus > 0 AND last_7d_dbus >= 15D
           AND (last_7d_dbus/7D) >= 3D*(previous_28d_dbus/28D) THEN 'REVIEW_INCREASE'
      WHEN previous_28d_dbus = 0 AND last_7d_dbus > 0 THEN 'NEW_IN_WINDOW'
      ELSE 'NO_SIGNAL' END AS review_signal,
 last_metered_day
 FROM stats ORDER BY
 CASE WHEN review_signal = 'REVIEW_INCREASE' THEN 0
      WHEN review_signal = 'NEW_IN_WINDOW' THEN 1 ELSE 2 END,
 last_7d_dbus DESC LIMIT 500""",
 'governance_coverage':BASE+"""SELECT account_id,workspace_id,genie_product,sku_name,
 COUNT(*) AS usage_records,
 COUNT(DISTINCT user_identity) AS distinct_billing_identities,
 SUM(CASE WHEN user_identity = 'unattributed' THEN 1 ELSE 0 END) AS unattributed_records,
 ROUND(SUM(total_dbus),2) AS total_dbus_30d,
 MAX(usage_date) AS last_metered_day
 FROM base WHERE usage_date >= DATE_SUB(CURRENT_DATE(),29)
 GROUP BY account_id,workspace_id,genie_product,sku_name
 ORDER BY total_dbus_30d DESC""",
 'data_freshness':BASE+"""SELECT MAX(usage_date) AS last_metered_day,
 DATEDIFF(CURRENT_DATE(), MAX(usage_date)) AS days_since_last_metered_usage,
 COUNT(DISTINCT account_id) AS databricks_accounts_observed,
 COUNT(DISTINCT workspace_id) AS workspaces_observed,
 COUNT(DISTINCT user_identity) AS identities_observed_90d,
 COUNT(*) AS billing_rows_90d
 FROM base""",
 'user_surface':BASE+"""SELECT user_identity,genie_product,
 ROUND(SUM(total_dbus),2) AS total_dbus,
 ROUND(SUM(billed_dbus),2) AS billed_dbus,
 ROUND(SUM(free_dbus),2) AS free_dbus,
 COUNT(DISTINCT usage_date) AS active_billing_days
 FROM base WHERE usage_date >= DATE_SUB(CURRENT_DATE(),29)
 GROUP BY user_identity,genie_product ORDER BY total_dbus DESC LIMIT 1000""",
 'code_free_mtd':BASE+"""SELECT user_identity,
 ROUND(SUM(CASE WHEN genie_product='GENIE_CODE' AND sku_name='GENIE_FREE_USAGE'
                 THEN total_dbus ELSE 0 END),2) AS recorded_code_free_dbus,
 ROUND(SUM(CASE WHEN genie_product='GENIE_CODE' AND sku_name<>'GENIE_FREE_USAGE'
                 THEN total_dbus ELSE 0 END),2) AS code_billed_dbus,
 COUNT(DISTINCT usage_date) AS active_billing_days
 FROM base WHERE usage_date >= DATE_TRUNC('MONTH',CURRENT_DATE())
 GROUP BY user_identity HAVING SUM(CASE WHEN genie_product='GENIE_CODE' THEN total_dbus ELSE 0 END) > 0
 ORDER BY recorded_code_free_dbus DESC LIMIT 2000""",
}

# Optional account-level dollar list-price estimate. Fail-safe: core dashboard never references this.
# In the event a paid SKU is unmatched, estimated_cost_usd is NULL rather than falsely showing zero.
COST_BASE="""WITH priced AS (
 SELECT u.account_id,CAST(u.workspace_id AS STRING) AS workspace_id,
        LOWER(COALESCE(u.identity_metadata.run_as,'UNATTRIBUTED')) AS user_identity,
        COALESCE(u.usage_metadata.genie.surface,'UNKNOWN') AS genie_product,
        u.usage_date,u.sku_name,u.usage_quantity,
        CASE WHEN u.sku_name='GENIE_FREE_USAGE' THEN 0D
             WHEN lp.pricing.effective_list.default IS NULL THEN NULL
             ELSE CAST(u.usage_quantity AS DOUBLE)*CAST(lp.pricing.effective_list.default AS DOUBLE)
        END AS estimated_cost_usd,
        CASE WHEN u.sku_name<>'GENIE_FREE_USAGE' AND lp.sku_name IS NULL THEN 1 ELSE 0 END AS missing_price,
        ROW_NUMBER() OVER (PARTITION BY u.account_id,u.record_id ORDER BY lp.price_start_time DESC NULLS LAST) AS price_rank
 FROM system.billing.usage u
 LEFT JOIN system.billing.list_prices lp
   ON u.sku_name=lp.sku_name AND u.cloud=lp.cloud AND u.usage_unit=lp.usage_unit
  AND u.usage_end_time>=lp.price_start_time
  AND (lp.price_end_time IS NULL OR u.usage_end_time<lp.price_end_time)
 WHERE u.billing_origin_product='GENIE' AND u.usage_unit='DBU'
   AND u.usage_date>=DATE_SUB(CURRENT_DATE(),89)
), clean AS (SELECT * FROM priced WHERE price_rank=1)
"""
COST_DATASETS={
 'cost_kpi':COST_BASE+"""SELECT
 CASE WHEN SUM(missing_price)>0 THEN NULL ELSE ROUND(SUM(estimated_cost_usd),2) END AS estimated_list_usd_30d,
 SUM(missing_price) AS unpriced_paid_rows_30d,
 COUNT(DISTINCT user_identity) AS identities_30d,
 ROUND(SUM(CASE WHEN sku_name<>'GENIE_FREE_USAGE' THEN usage_quantity ELSE 0 END),2) AS billed_dbus_30d
 FROM clean WHERE usage_date>=DATE_SUB(CURRENT_DATE(),29)""",
 'cost_user':COST_BASE+"""SELECT user_identity,genie_product,
 ROUND(SUM(CASE WHEN sku_name<>'GENIE_FREE_USAGE' THEN usage_quantity ELSE 0 END),2) AS billed_dbus,
 CASE WHEN SUM(missing_price)>0 THEN NULL ELSE ROUND(SUM(estimated_cost_usd),2) END AS estimated_list_usd,
 SUM(missing_price) AS unpriced_rows
 FROM clean WHERE usage_date>=DATE_SUB(CURRENT_DATE(),29)
 GROUP BY user_identity,genie_product ORDER BY billed_dbus DESC LIMIT 1000""",
 'cost_day':COST_BASE+"""SELECT usage_date AS day,
 CASE WHEN SUM(missing_price)>0 THEN NULL ELSE ROUND(SUM(estimated_cost_usd),2) END AS estimated_list_usd,
 SUM(missing_price) AS unpriced_rows
 FROM clean WHERE usage_date>=DATE_SUB(CURRENT_DATE(),29)
 GROUP BY usage_date ORDER BY usage_date"""
}

UI={"theme":{"canvasBackgroundColor":{"light":"#FFFFFF","dark":"#1F272D"},
 "widgetBackgroundColor":{"light":"#FFFFFF","dark":"#11171C"},
 "widgetBorderColor":{"light":"#E4E9F0","dark":"#2A343C"},
 "fontColor":{"light":"#172B4D","dark":"#E8ECF0"},
 "selectionColor":{"light":"#216AB4","dark":"#5BACF4"},
 "visualizationColors":["#1463A5","#00A899","#F3A85F","#6E84C8","#D97770","#56ADCC","#8C7AAE"],
 "widgetHeaderAlignment":"LEFT"},"applyModeEnabled":False}

class Dashboard:
 def __init__(self,priced=False):
  self.priced=priced;self.datasets=[];self.pages=[]
  for key,q in {**DATASETS,**(COST_DATASETS if priced else {})}.items():
   self.datasets.append({'name':key,'displayName':key.replace('_',' ').title(),'queryLines':[line+'\n' for line in q.splitlines()]})
 def page(self,slug,title):
  p={'name':slug,'displayName':title,'layout':[],'pageType':'PAGE_TYPE_CANVAS','layoutVersion':'GRID_V1'}
  self.pages.append(p);return p
 def add(self,p,name,widget,x,y,w,h):
  p['layout'].append({'widget':{'name':name,**widget},'position':{'x':x,'y':y,'width':w,'height':h}})
 def text(self,p,name,heading,subtitle,y=0,h=3):
  self.add(p,name,{'multilineTextboxSpec':{'lines':[f'## {heading}\n',f'{subtitle}\n']}},0,y,12,h)
 def query(self,dataset,cols):
  return [{'name':'main_query','query':{'datasetName':dataset,'fields':[{'name':c,'expression':f'`{c}`'} for c in cols],'disaggregated':True}}]
 def counter(self,p,name,title,dataset,col,x,y,w=3):
  self.add(p,name,{'queries':self.query(dataset,[col]),'spec':{'version':2,'widgetType':'counter','frame':{'title':title,'showTitle':True},'encodings':{'value':{'fieldName':col,'displayName':title}}}},x,y,w,4)
 def chart(self,p,name,title,dataset,xfield,yfield,x,y,w=6,h=7,kind='bar',temporal=False):
  self.add(p,name,{'queries':self.query(dataset,[xfield,yfield]),'spec':{'version':3,'widgetType':kind,'frame':{'title':title,'showTitle':True},'encodings':{'x':{'fieldName':xfield,'scale':{'type':'temporal' if temporal else 'categorical'},'displayName':xfield.replace('_',' ').title()},'y':{'fieldName':yfield,'scale':{'type':'quantitative'},'displayName':yfield.replace('_',' ').title()}}}},x,y,w,h)
 def table(self,p,name,title,dataset,cols,x,y,w=12,h=9):
  self.add(p,name,{'queries':self.query(dataset,cols),'spec':{'version':2,'widgetType':'table','frame':{'title':title,'showTitle':True},'rowsPerPage':15,'encodings':{'columns':[{'fieldName':c,'displayName':c.replace('_',' ').title()} for c in cols]}}},x,y,w,h)
 def result(self):
  return {'datasets':self.datasets,'pages':self.pages,'uiSettings':UI}

def populate(d):
 p=d.page('executive','01 • Executive Pulse')
 d.text(p,'intro','IFBI | Genie Usage & Governance','Rolling 30 days · Genie inference metering · SQL warehouse cost is separate.')
 for i,(title,key) in enumerate([('Total DBUs','total_dbus_30d'),('Free DBUs','free_dbus_30d'),('Billable DBUs','billed_dbus_30d'),('Metered identities','identities_30d')]): d.counter(p,'kpi_'+key,title,'executive',key,i*3,3)
 d.chart(p,'daily','Daily Genie DBUs','daily_trend','day','total_dbus',0,7,7,7,'line',True)
 d.chart(p,'byproduct','Consumption by Genie product','surface_30d','genie_product','total_dbus',7,7,5,7)
 d.table(p,'leaders','Highest billable usage (30d)','top_users_30d',['user_identity','total_dbus','free_dbus','billed_dbus','active_billing_days','last_metered_day'],0,14,12,10)
 d.text(p,'caveat','Interpretation','A billing identity is not necessarily the human who initiated a request. DBUs are not prompt counts. Billing data can arrive late.',24,3)

 p=d.page('adoption','02 • User Adoption')
 d.text(p,'adopt_text','Genie users and adoption','Current-month by user/workspace; 90-day lookback for new and returning activity.')
 d.chart(p,'weekly','Weekly active billing identities','week_activity','week_start','active_metered_identities',0,3,7,7,'line',True)
 d.chart(p,'product_users','Unique identities by product (30d)','surface_30d','genie_product','identities',7,3,5,7)
 d.table(p,'mtd_users','Month-to-date usage by billing identity','users_mtd',['user_identity','workspace_id','mtd_total_dbus','mtd_free_dbus','mtd_billed_dbus','code_dbus','one_dbus','agents_dbus','active_billing_days'],0,10,12,12)
 d.table(p,'last_seen','Observed activity during last 90 days','activity_90d',['user_identity','first_seen_in_90d','last_seen_in_90d','active_billing_days_90d','genie_products_used','workspaces_used','total_dbus_90d'],0,22,12,10)

 p=d.page('cost','03 • Free & Billed Usage')
 d.text(p,'cost_text','Free and billable consumption','Paid SKU DBUs are a cost signal—not USD expense. A priced edition is included separately.')
 d.counter(p,'mtd_billable','MTD billable DBUs','runrate_mtd','mtd_billed_dbus',0,3,4)
 d.counter(p,'forecast','Indicative month-end billed DBUs','runrate_mtd','indicative_month_end_billed_dbus',4,3,4)
 d.counter(p,'mtd_all','MTD total DBUs','runrate_mtd','mtd_total_dbus',8,3,4)
 d.chart(p,'paid_daily','Daily billed DBUs (30d)','daily_trend','day','billed_dbus',0,7,7,7,'line',True)
 d.chart(p,'paid_products','Billed DBUs by product','surface_30d','genie_product','billed_dbus',7,7,5,7)
 d.table(p,'sku_table','Billing SKU audit (month to date)','billing_sku_mtd',['sku_name','genie_product','dbus_mtd','free_dbus_mtd','billed_dbus_mtd','identities','billing_rows'],0,14,12,9)
 d.table(p,'allowance_table','Recorded Genie Code free DBUs (not entitlement verification)','code_free_mtd',['user_identity','recorded_code_free_dbus','code_billed_dbus','active_billing_days'],0,23,12,8)
 d.text(p,'cost_note','Forecast caveat','Linear billed-DBU forecast uses calendar days; early-month data, lag and traffic changes can affect accuracy.',31,3)

 p=d.page('workspaces','04 • Workspace & Product')
 d.text(p,'ws_text','Workspace and product coverage','Observed Databricks account and workspace consumption; deployment coverage must be confirmed separately.')
 d.counter(p,'workspaces_count','Workspaces observed (30d)','executive','workspaces_30d',0,3,4)
 d.counter(p,'last_meter','Most recent usage date','executive','latest_usage_date',4,3,4)
 d.counter(p,'90day_users','Identities in 90d','data_freshness','identities_observed_90d',8,3,4)
 d.chart(p,'workspace_chart','DBUs by workspace (30d)','workspace_summary','workspace_id','total_dbus',0,7,12,8)
 d.table(p,'ws_prod','Workspace / Genie product details','workspace_30d',['account_id','workspace_id','genie_product','total_dbus','billed_dbus','active_identities','last_metered_day'],0,15,12,10)

 p=d.page('governance','05 • Governance Watchlist')
 d.text(p,'gov_text','Usage patterns worth reviewing','Signals require human validation. Do not treat a spike or high consumption as misuse.')
 d.table(p,'spikes','Usage changes (7-day vs preceding 28 days)','spikes',['user_identity','review_signal','last_7d_dbus','previous_28d_dbus','rate_ratio','last_7d_billed_dbus','last_metered_day'],0,3,12,12)
 d.table(p,'paid_leaders','Cost-attribution review — highest paid DBUs','top_users_30d',['user_identity','billed_dbus','free_dbus','products_used','active_billing_days','last_metered_day'],0,15,12,9)
 d.table(p,'sku_identity','Genie product by user (30d)','user_surface',['user_identity','genie_product','total_dbus','billed_dbus','free_dbus','active_billing_days'],0,24,12,10)
 d.text(p,'gov_notes','Governance boundaries','No prompts, question text, SQL statement text, customer records or HR team mapping are captured by these dashboards. Access should be restricted.',34,3)

 p=d.page('quality','06 • Billing Quality & Coverage')
 d.text(p,'q_text','Data quality and completeness','System billing data is account scoped and delayed. A workspace observed here does not prove all IFBI workspaces are covered.')
 d.counter(p,'q_accounts','Accounts observed (90d)','data_freshness','databricks_accounts_observed',0,3,4)
 d.counter(p,'q_workspaces','Workspaces observed (90d)','data_freshness','workspaces_observed',4,3,4)
 d.counter(p,'q_delay','Days since last metered date','data_freshness','days_since_last_metered_usage',8,3,4)
 d.table(p,'q_details','Product / SKU coverage and missing identities','governance_coverage',['account_id','workspace_id','genie_product','sku_name','usage_records','distinct_billing_identities','unattributed_records','total_dbus_30d','last_metered_day'],0,7,12,12)
 d.table(p,'q_summary','Product usage and observed identities','surface_30d',['genie_product','total_dbus','free_dbus','billed_dbus','identities'],0,19,12,8)
 d.text(p,'q_note','Limitations','No inferred team, assistant prompt counts, generated-query costs, customer data access, or security violations. These require governed additional telemetry.',27,3)

 if d.priced:
  p=d.page('priced','07 • List-Price Estimates (Optional)')
  d.text(p,'usd_text','Estimated Databricks Genie list-price cost','Requires SELECT on system.billing.list_prices. Estimates are not invoices; unknown SKU prices cause NULL amounts.')
  d.counter(p,'usd_total','Estimated list USD (30d)','cost_kpi','estimated_list_usd_30d',0,3,4)
  d.counter(p,'unpriced','Paid records without price','cost_kpi','unpriced_paid_rows_30d',4,3,4)
  d.counter(p,'priced_dbus','Billed DBUs (30d)','cost_kpi','billed_dbus_30d',8,3,4)
  d.chart(p,'usd_daily','Estimated list USD by day','cost_day','day','estimated_list_usd',0,7,12,7,'line',True)
  d.table(p,'usd_people','Estimated USD by billing identity and product','cost_user',['user_identity','genie_product','billed_dbus','estimated_list_usd','unpriced_rows'],0,14,12,12)
  d.text(p,'usd_note','Cost limitations','This excludes SQL warehouse, AWS infrastructure and Fivetran charges. List rates may differ from IFBI contracted prices. Never label as invoice cost.',26,3)

 return d

def main():
 DASH.mkdir(parents=True,exist_ok=True)
 for is_priced,name in [(False,'IFBI_Genie_Usage_Core.lvdash.json'),(True,'IFBI_Genie_Usage_With_List_Price.lvdash.json')]:
  dashboard=populate(Dashboard(priced=is_priced)).result()
  (DASH/name).write_text(json.dumps(dashboard,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
  print(f'{name}: {len(dashboard["pages"])} pages, {len(dashboard["datasets"])} datasets, {sum(len(p["layout"]) for p in dashboard["pages"])} widgets')

if __name__=='__main__':main()
