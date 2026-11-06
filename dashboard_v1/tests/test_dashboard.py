"""Static validation for portable AI/BI dashboard artifacts (no Databricks connection)."""
import json
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
MAIN=ROOT/'dashboard'/'IFBI_Genie_Usage_Core.lvdash.json'
USD=ROOT/'dashboard'/'IFBI_Genie_Usage_With_List_Price.lvdash.json'

class DashboardIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main=json.loads(MAIN.read_text())
        cls.usd=json.loads(USD.read_text())

    def check(self,doc):
        self.assertEqual(set(doc),{'datasets','pages','uiSettings'})
        ds={d['name'] for d in doc['datasets']}
        self.assertEqual(len(ds),len(doc['datasets']))
        self.assertEqual(len({p['name'] for p in doc['pages']}),len(doc['pages']))
        widget_names=set()
        for d in doc['datasets']:
            self.assertTrue(d['queryLines'])
            query=''.join(d['queryLines']).upper()
            self.assertIn('SYSTEM.BILLING.USAGE',query)
            self.assertIn("BILLING_ORIGIN_PRODUCT = 'GENIE'",query.replace('BILLING_ORIGIN_PRODUCT=','BILLING_ORIGIN_PRODUCT = '))
            self.assertNotIn('CREATE OR REPLACE',query)
            self.assertNotIn('GRANT ',query)
            self.assertNotIn('INSERT INTO',query)
        for p in doc['pages']:
            self.assertEqual(p['pageType'],'PAGE_TYPE_CANVAS')
            occupied=set()
            for item in p['layout']:
                widget=item['widget']; n=widget['name']
                self.assertNotIn(n,widget_names)
                widget_names.add(n)
                pos=item['position'];x,y,w,h=(pos[a] for a in ('x','y','width','height'))
                self.assertGreater(w,0); self.assertGreater(h,0);self.assertGreaterEqual(x,0)
                self.assertGreaterEqual(y,0);self.assertLessEqual(x+w,12)
                for i in range(x,x+w):
                    for j in range(y,y+h):
                        self.assertNotIn((i,j),occupied, f'overlap in page {p["name"]} at {(i,j)}')
                        occupied.add((i,j))
                if 'queries' in widget:
                    self.assertIn(widget['spec']['widgetType'],{'table','bar','counter','line'})
                    for q in widget['queries']:
                        self.assertIn(q['query']['datasetName'],ds)
                        self.assertGreater(len(q['query']['fields']),0)
                else:
                    self.assertIn('multilineTextboxSpec',widget)
        return len(widget_names)

    def test_core_structure(self):
        self.assertEqual(len(self.main['pages']),6)
        self.assertGreaterEqual(self.check(self.main),35)

    def test_priced_structure(self):
        self.assertEqual(len(self.usd['pages']),7)
        self.assertGreaterEqual(self.check(self.usd),42)

    def test_core_only_uses_verified_billing_source(self):
        all_sql='\n'.join(''.join(d['queryLines']) for d in self.main['datasets']).lower()
        self.assertNotIn('system.billing.list_prices',all_sql)
        self.assertNotIn('system.access.',all_sql)
        self.assertNotIn('ifbi_edw_',all_sql)

    def test_price_join_is_safe(self):
        price_sql='\n'.join(''.join(d['queryLines']) for d in self.usd['datasets'] if d['name'].startswith('cost_')).lower()
        self.assertIn('left join system.billing.list_prices',price_sql)
        self.assertIn('missing_price',price_sql)
        self.assertIn('price_start_time',price_sql)
        self.assertIn('price_end_time',price_sql)
        self.assertIn('partition by u.account_id,u.record_id',price_sql)

    def test_no_private_info_or_tracking(self):
        content=MAIN.read_text()+'\n'+USD.read_text()
        for forbidden in ['@infarmbureau.com','execute-api.us-west','http://','https://ppxrz','access_token','personal_access_token']:
            self.assertNotIn(forbidden,content.lower())

if __name__=='__main__': unittest.main()
