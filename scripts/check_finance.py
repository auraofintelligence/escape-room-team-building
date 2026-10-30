"""Read-only source, unit, market-total and printed-summary checks."""
import json
from pathlib import Path
from decimal import Decimal as D
ROOT=Path(__file__).resolve().parents[1]
def read(name):return json.loads((ROOT/'content'/name).read_text(encoding='utf-8'),parse_float=D)
f=read('finance.json');p=read('plan.json');s=read('sources.json');m=read('market-data.json')
checks=0
def require(ok,message):
    global checks
    checks+=1
    if not ok:raise AssertionError(message)
refs={e['id']:e for key in ['documents','links','research'] for e in s[key]}
for ch in p['chapters']:
    for section in ch['sections']:
        for sid in section.get('refs',[]):require(sid in refs,'Missing reference '+sid)
        require('\u2014' not in section['body'],'Em dash in manuscript')
for sub in m['operator_subtotals']:
    rows=[v for v in m['venues'] if v['operator']==sub['operator'] and v['venue'] in sub['included_venues']]
    require(len(rows)==len(sub['included_venues']),'Duplicate/missing venue')
    require(sum(x['rooms'] for x in rows)==sub['rooms'],'Room subtotal')
    require(sum(x['players'] for x in rows)==sub['players'],'Player subtotal')
market=p['chapters'][1]['sections'][0]['body']
for v in m['venues']:
    require(f'| {v["operator"]} | {v["venue"]} | {v["rooms"]} | {v["players"]} | {v["source"]} |' in market,'Printed venue mismatch')
for b in f['benchmarks']:
    require(b['source'] in refs,'Missing benchmark source')
    require(refs[b['source']]['verification_status'] in ['page_rechecked','corrected_page_rechecked'],'Unverified active benchmark')
    require(b['quote_date'] is None,'Invented quotation date')
    require(b['value']>=0,'Negative benchmark')
require(not any(b['source']=='R112' for b in f['benchmarks']),'Unverified used chair retained')
for q in f['quote_required']:require(q['cost'] is None,'Unpriced scope silently given a cost')
for value in f['founder_decisions'].values():require(value is None,'Unmade decision recorded')
for rent in f['rent_comparables']:
    require(D(rent['annual_rent_ex_gst'])/rent['area_m2']==rent['rent_per_m2_year'],'Rent unit mismatch')
base=f['summary_comparison'];summary=p['chapters'][0]['sections'][1]['body']
for rooms,locations,expected in [(1,1,210000),(4,1,840000),(4,5,4200000)]:
    available=rooms*locations*base['starts_per_room_day']*base['trading_days']
    gross=available*D(base['sold_percent'])/100*base['average_players']*base['price_per_person']
    require(gross==expected,'Summary receipt calculation')
    require(f'${expected:,}' in summary,'Summary printed receipts')
    require(f'${gross/D("1.1"):,.0f}' in summary,'Summary printed ex-GST sales')
require(base['price_source']=='M18' and base['price_per_person']==42,'Summary price citation')
require('operations' not in f and 'trade_work_packages' not in f,'Unsupported old quantities retained')
require(f['financial_completion']['full_profit_available'] is False,'Full-profit claim')
print(f'Source and manuscript audit passed: {checks} checks. Run check_calculators.cjs for arithmetic and edge cases.')
