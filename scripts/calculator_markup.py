"""Accessible forms for the local comparison calculators."""
from html import escape
import json

def field(key,label,value='',step='any',minimum='0',maximum=None):
    return f'<label>{escape(label)}<input data-key="{key}" type="number" inputmode="decimal" min="{minimum}" '+(f'max="{maximum}" ' if maximum else '')+f'step="{step}" value="{value}"></label>'
def select(key,label,options):
    return f'<label>{label}<select data-key="{key}">'+''.join(f'<option value="{v}">{t}</option>' for v,t in options)+'</select></label>'
def grid(*items):return '<div class="calc-fields">'+''.join(items)+'</div>'
def options(key,label,items):return select(key,label,[('','Choose')]+items)

def calculator_markup(kind,finance):
    extra=''
    if kind=='throughput':
        d=finance['summary_comparison']
        content=grid(field('rooms','Rooms per location',d['rooms'],'1'),field('locations','Locations',d['locations'],'1'),field('price','Price per person AUD',d['price_per_person']),field('group','Average paying players',d['average_players']),field('sold','Sessions sold %',d['sold_percent'],maximum='100'),field('starts','Starts per room each day',d['starts_per_room_day'],'1'),field('days','Trading days per year',d['trading_days'],'1',maximum='366'))
        content+='<details><summary>Timing room limits and GST</summary>'+grid(field('play','Game minutes',60),field('reset','Reset minutes',15),field('buffer','Buffer minutes',0),field('window','Room window hours',10),field('limit','Player limit per room',6,'1'),field('closed','Blocked room-days across all sites',0,'1'),field('tax','Sales GST %',10))+'</details>'
        extra='<p class="calc-note">Comparison starts at Puzzled’s $42 group price. All timing, demand and scale inputs are assumptions. Totals count admissions, not unique people. Final reset, briefing and reflection sit outside the room-window limit.</p>'
    elif kind=='cost':
        opts=[('','Enter your own item')]+[(x['id'],x['label']+' · $'+str(x['value'])+' · '+x['source']) for x in finance['benchmarks']]
        content='<div data-cost-lines></div><button type="button" class="calc-add" data-add-item>Add item</button>'+grid(field('freight','Freight or collection cash AUD'),field('repair','Cleaning and repairs cash AUD'),field('install','Installation cash AUD'),field('credit','Eligible input GST credit AUD'))
        extra='<p class="calc-note">Choose the invoice tax basis for every line. Extra costs are cash amounts including any tax. Enter the eligible GST credit from those invoices separately.</p>'
    elif kind=='labour':
        content=options('mode','Rate type',[('hourly','Hourly person-hours'),('attendance','Attendance includes first hour')])
        content+='<div data-mode="hourly">'+grid(field('people','People','','1'),field('hours','Hours per person'),field('rate','Hourly charge AUD ex GST'))+'</div>'
        content+='<div data-mode="attendance" hidden>'+grid(field('attendances','Attendance count','','1'),field('first','Attendance and first hour AUD ex GST'),field('extra','Total additional hours'),field('later','Additional hourly rate AUD ex GST'))+'</div>'
        content+=grid(field('materials','Materials AUD ex GST'),field('other','Other charges AUD ex GST'))
        extra='<p class="calc-note">Enter an actual charge rate or a dated benchmark from the table. Include every person’s hours. Do not add a second call-out when attendance is included.</p>'
    elif kind=='operating':
        content=grid(field('available','Available team sessions per year'),field('sold','Sold %',maximum='100'),field('group','Average paying players per team'),field('price','Price per person AUD inc GST'),field('tax','Sales GST %'))
        content+='<details open><summary>Payment and operating costs</summary><button type="button" data-use-card>Use Stripe domestic online benchmark</button>'+grid(field('cardRate','Processor % of cash'),field('cardFixed','Fixed processor fee AUD'),field('payments','Payments per team','','1'),field('credit','Recoverable processor GST %',maximum='100'),field('variable','All other variable cost AUD per team'),field('fixed','Annual fixed costs AUD'),field('renewal','Annual renewal provision AUD'))+'</details>'
        extra='<p class="calc-note">Costs exclude recoverable GST. Include paid delivery work in variable or fixed costs once. The processor benchmark includes 10% GST; enter 0 or 100 for the recoverable share, or the actual partial share. Equal-size payments are assumed within a team.</p>'
    elif kind=='pass':
        content=grid(field('passes','Passes in this transaction','','1'),field('price','Pass price AUD inc GST'),field('visits','Visits per pass','','1'),field('allocation','Allocation AUD per venue visit'),field('tax','Service GST %'))
        content+='<button type="button" data-use-card>Use Stripe domestic online benchmark</button>'+grid(field('cardRate','Processor % of cash'),field('cardFixed','Fixed processor cash fee AUD'),field('credit','Recoverable processor GST %',maximum='100'))
        extra='<p class="calc-note">One payment transaction. Allocations and pass prices are rounded to cents. Other distribution and service costs are additional. Processor fees include 10% GST under the displayed benchmark.</p>'
    elif kind=='renewal':
        content=grid(field('replacement','Replacement cash cost AUD'),field('years','Funding interval years','','1'),field('displaced','Team sessions displaced by closure'),field('sold','Expected sold %',maximum='100'),field('contribution','Contribution AUD per sold session',minimum='-1000000000000'))
        extra='<p class="calc-note">Constant-price comparison with replacement at each interval end, starting from a newly installed asset. Add freight, paid work and other replacement costs to the entered amount. Existing used assets need their remaining interval.</p>'
    elif kind=='software':
        content=grid(field('sessions','Recorded sessions'),field('people','Average recorded people'),field('minutes','Submitted minutes per person'),field('submissions','Submissions per file with retries'),field('audioRate','USD per audio minute'))
        content+='<div class="calc-buttons"><button type="button" data-audio="file">Use file rate $0.0045</button><button type="button" data-audio="live">Use live rate $0.017</button></div>'
        content+='<details open><summary>Model usage and other provider charges</summary><button type="button" data-use-token>Use Standard short-context $2 / $10 rates</button>'+grid(field('calls','Total model calls'),field('input','Input tokens per call'),field('output','Billable output tokens per call'),field('inputRate','USD input rate per million'),field('outputRate','USD output rate per million'),field('tools','Other provider charges USD'))+'</details>'
        content+='<details><summary>Convert to AUD cash</summary>'+grid(field('fx','AUD actually paid per USD'),field('extraAud','Other FX tax and cash charges AUD'))+'</details>'
        extra='<p class="calc-note">Recorded headcount includes anyone whose audio is submitted and excludes recording opt-outs. Estimate prices do not include hosting or human review. Enter 0 for unused categories.</p>'
    else:raise ValueError(kind)
    return f'<form class="calculator" data-calculator="{kind}" novalidate><p class="calc-label">Editable comparison calculator</p>{content}<div class="calc-buttons"><button type="submit">Calculate</button><button type="button" data-clear>Clear inputs</button></div><div class="calc-results" data-results aria-live="polite"></div>{extra}<noscript>JavaScript is needed for live calculation. The formulas above remain available.</noscript></form>'
