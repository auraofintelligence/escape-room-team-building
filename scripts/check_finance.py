#!/usr/bin/env python3
"""Read-only audit of the published model and manuscript.

Run from any working directory with Python 3. This checks the current documented
model, including its published-price snapshot and illustrative calendar assumptions.
It never regenerates or changes finance.json, plan.json or other publications.
Prices still require the source and supplier checks described in the manuscript.
"""

import json
import re
import sys
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
D = Decimal
GST_FACTOR = D('1.1')
CARD_RATE = D('0.0165')
CARD_FIXED = D('0.30')
TOLERANCE = D('0.000002')
errors = []
checks = 0


def require(condition, label):
    global checks
    checks += 1
    if not condition:
        errors.append(label)


def equal(actual, expected, label, tolerance=TOLERANCE):
    require(abs(D(str(actual)) - D(str(expected))) <= tolerance,
            f'{label}: stored {actual}, calculated {expected}')


def load(name):
    return json.loads((ROOT / 'content' / name).read_text(encoding='utf-8'),
                      parse_float=Decimal)


def section(title):
    matches = [s for c in plan['chapters'] for s in c['sections']
               if s['title'] == title]
    require(len(matches) == 1, f'Manuscript section must be unique: {title}')
    return matches[0]['body'] if matches else ''


def table_row(body, label, expected):
    rows = [[cell.strip() for cell in line.strip().strip('|').split('|')]
            for line in body.splitlines() if line.strip().startswith('|')]
    matches = [row for row in rows if row[0].strip('*') == label]
    require(len(matches) == 1, f'Manuscript table row must be unique: {label}')
    if matches:
        require(matches[0][1:] == expected,
                f'Manuscript row {label}: {matches[0][1:]} != {expected}')


def money(value, places=2):
    return f'${value:,.{places}f}'


f = load('finance.json')
plan = load('plan.json')
sources = load('sources.json')

# Product mix and net admission yield. Shares refer to bookings, not people.
products = f['products']
equal(sum(x['booking_share'] for x in products), 1, 'Booking shares total')
participants = sum(x['booking_share'] * x['paid_players'] for x in products)
gross = sum(x['booking_share'] * x['paid_players'] * x['price_inc_gst']
            for x in products)
net = gross / GST_FACTOR
fee_cash = gross * CARD_RATE + CARD_FIXED
fee_net = fee_cash / GST_FACTOR
for key, value in [('average_players', participants), ('gross_per_team', gross),
                   ('net_per_team', net), ('domestic_card_fee_cash_per_team', fee_cash),
                   ('domestic_card_fee_net_per_team', fee_net)]:
    equal(f['unit_revenue'][key], value, f'Unit revenue {key}')
equal(f['unit_revenue']['transactions_per_team'], 1, 'One payment per team')

# Priced item extensions are kept on their published tax and scope bases.
for item in f['prototype_lines']:
    equal(item['line_total'], item['quantity'] * item['unit_price'], item['id'])
    require(bool(item['tax_basis']), f'{item["id"]} tax basis')
equal(f['prototype_displayed_price_subtotal'],
      sum(x['line_total'] for x in f['prototype_lines']), 'Prototype subtotal')
for size in ['two_room', 'four_room']:
    for item in f['furniture_lines']:
        equal(item[f'{size}_total'], item[f'quantity_{size}'] * item['unit_price'],
              f'{item["id"]} {size}')
    equal(f['furniture_displayed_subtotals'][size],
          sum(x[f'{size}_total'] for x in f['furniture_lines']), f'Furniture {size}')
    for item in f['trade_work_packages']:
        for end in ['low', 'high']:
            if item[f'rate_{end}'] is not None:
                expected = item[f'hours_{size}'] * item[f'rate_{end}']
            else:
                # Published electrical example: one 8-hour attendance per room.
                expected = D(item[f'hours_{size}']) / 8 * (235 + 7 * 135)
            equal(item[f'{size}_{end}'], expected, f'{item["id"]} {size} {end}')
    for end in ['low', 'high']:
        equal(f['trade_subtotals_ex_gst'][size][end],
              sum(x[f'{size}_{end}'] for x in f['trade_work_packages']),
              f'Trade subtotal {size} {end}')
equal(f['room_kit_displayed_benchmark_sum'],
      sum(x['price_aud'] for x in f['room_kit_benchmarks']), 'Catalogue room sum')
training = f['preopening_training']
equal(training['total_paid_hours'], training['people'] * training['hours_each'],
      'Preopening training hours')
equal(training['wages_plus_sg'], training['total_paid_hours'] *
      training['example_ordinary_wage'] * (1 + training['super_rate']),
      'Preopening wages and super')

# Capacity, renewal closures, wages and separately paid task hours.
w = f['wage_inputs']
op_by_name = {}
for op in f['operations']:
    label = op['name']
    op_by_name[label] = op
    # These are the worked calendars documented in the current manuscript.
    sunday_fraction = D(1) / 6 if op['rooms'] == 4 else D(0)
    rate_a = (w['ordinary_A'] * (1-sunday_fraction) +
              w['sunday_A'] * sunday_fraction) * (1+w['sg_rate'])
    rate_b = (w['ordinary_B'] * (1-sunday_fraction) +
              w['sunday_B'] * sunday_fraction) * (1+w['sg_rate'])
    equal(op['baseline_A_rate_plus_sg'], rate_a, f'{label} A rate')
    equal(op['baseline_B_rate_plus_sg'], rate_b, f'{label} B rate')
    nominal = op['rooms'] * op['starts_per_room_day'] * op['trading_days']
    blocked = op['rooms'] * op['extra_closed_days_per_room'] * op['starts_per_room_day']
    available = nominal - blocked
    equal(op['nominal_team_slots'], nominal, f'{label} nominal capacity')
    equal(op['renewal_blocked_slots'], blocked, f'{label} renewal closures')
    equal(op['available_team_slots'], available, f'{label} available capacity')
    require(op['baseline_roles'] == 2, f'{label} baseline positions')
    coverage_each = op['baseline_hours_per_role_day'] * op['trading_days']
    fixed_wages = coverage_each * (rate_a + rate_b)
    equal(op['baseline_total_coverage_hours'], coverage_each * 2, f'{label} coverage')
    equal(op['baseline_wages_plus_sg'], fixed_wages, f'{label} baseline wages')
    extra = op['extra_reset_minutes_per_team']
    require(extra == (5 if '75-minute' in label else 0), f'{label} extra reset minutes')
    a_hours = D(25 + extra) / 60
    b_hours = D(35) / 60
    premium_hours = D('0.2') * D('0.75')
    variable = a_hours * rate_a + (b_hours + premium_hours) * rate_b
    equal(op['delivery_wages_plus_sg_per_team'], variable, f'{label} variable wages')
    for case in op['cases']:
        name = f'{label} {case["sold_fraction"]}'
        teams = available * case['sold_fraction']
        equal(case['teams'], teams, name + ' teams')
        equal(case['paid_visits'], teams * participants, name + ' visits')
        equal(case['gross_receipts'], teams * gross, name + ' gross sales')
        equal(case['net_sales'], teams * net, name + ' net sales')
        wages = fixed_wages + teams * variable
        equal(case['wages_plus_sg'], wages, name + ' wages')
        equal(case['card_fees_ex_gst'], teams * fee_net, name + ' card fees')
        equal(case['remaining_for_all_other_costs'], teams * net - wages - teams * fee_net,
              name + ' remaining for other costs')
        hours = case['work_hours']
        for key, value in [('baseline_coverage', coverage_each * 2),
                           ('reset_handover_relief', teams * a_hours),
                           ('reflection_preparation_delivery_notes', teams * b_hours),
                           ('premium_workshop', teams * premium_hours),
                           ('total_before_roster_fragmentation', coverage_each * 2 +
                            teams * (a_hours + b_hours + premium_hours))]:
            equal(hours[key], value, name + ' hours ' + key)

# Asset-level renewal quantities, annual contribution and cash at 3/5/10 years.
for scope, group in f['renewal_schedules'].items():
    assets = [x for x in f['renewal_assets'] if x['scope'] == scope]
    annual = sum(D(x['purchase_cost_displayed']) / x['reserve_years'] for x in assets)
    equal(group['annual_reserve'], annual, scope + ' annual reserve')
    balance = D(0)
    for row in group['schedule']:
        replacements = [x for x in assets if row['year'] % x['reserve_years'] == 0]
        purchases = sum(x['purchase_cost_displayed'] for x in replacements)
        balance += annual - purchases
        equal(row['reserve_contribution'], annual, scope + ' annual contribution')
        equal(row['planned_purchase_at_current_prices'], purchases, scope + ' purchases')
        equal(row['balance'], balance, scope + ' reserve balance')
        require(balance >= 0, scope + ' reserve must cover scheduled replacements')
        require(row['items'] == [x['id'] for x in replacements], scope + ' replacement IDs')
    for year, value in group['horizons'].items():
        equal(value, sum(row['planned_purchase_at_current_prices'] for row in group['schedule']
                         if row['year'] <= int(year)), scope + f' horizon {year}')
room_reserve = f['room_renewal_benchmark']
equal(room_reserve['annual_displayed_price_reserve'],
      D(room_reserve['displayed_replacement_cost']) / room_reserve['proposed_reserve_years'],
      'Room-package annual reserve')

# Pass conservation: venue allocations never become central service revenue.
p = f['tourism_pass']
equal(p['price_per_person_inc_gst'], 3 * p['venue_allocation_each_visit_inc_gst'] +
      p['network_service_per_pass_inc_gst'], 'Pass allocation per person')
cash = p['passes_per_transaction'] * p['price_per_person_inc_gst']
service = p['passes_per_transaction'] * p['network_service_per_pass_inc_gst']
processor = cash * CARD_RATE + CARD_FIXED
equal(p['customer_cash'], cash, 'Pass receipts')
equal(p['venue_allocations_gross'], cash - service, 'Venue settlement liability')
equal(p['central_service_gross'], service, 'Central service gross')
equal(p['central_service_net'], D(service) / GST_FACTOR, 'Central service net')
equal(p['processor_fee_cash'], processor, 'Pass processing cash')
equal(p['processor_fee_net_if_credit_eligible'], processor / GST_FACTOR, 'Pass net fee')
equal(p['central_residual_before_other_costs'], (service - processor) / GST_FACTOR,
      'Central service amount after eligible fee credit')
equal(p['central_residual_without_processor_gst_credit'], service / GST_FACTOR - processor,
      'Central service without processor GST credit')

# Software uses USD; full submitted duration counts for every participant file.
software = f['software_ai_budget']
speech = software['transcription']
require('USD' in software['currency'], 'Software currency identified')
for case in speech['cases']:
    op = op_by_name[case['operation']]
    operating = next(x for x in op['cases'] if x['sold_fraction'] == case['sold_fraction'])
    equal(case['sold_teams'], operating['teams'], 'Audio sold teams')
    minutes = case['sold_teams'] * case['planning_recorded_participants_per_team'] * 45
    equal(case['chargeable_audio_minutes'], minutes, 'Submitted channel minutes')
    equal(case['file_transcription_usd'], minutes * speech['file_usd_per_audio_minute'],
          'File transcription USD')
    equal(case['live_transcription_usd'], minutes * speech['live_usd_per_audio_minute'],
          'Live transcription USD')
prices = software['token_unit_price_benchmark']
analysis_total = D(0)
for call in software['team_analysis_work_packages']:
    cost = call['calls_per_team'] * (call['uncached_input_token_budget'] *
           prices['usd_per_million_uncached_input_tokens'] + call['output_token_budget'] *
           prices['usd_per_million_output_tokens']) / D(1000000)
    equal(call['usd_per_team'], cost, call['task'])
    analysis_total += cost
equal(software['team_analysis_usd_per_team'], analysis_total, 'Analysis package USD')
reference = next(x for x in f['operations'] if x['rooms'] == 4 and x['starts_per_room_day'] == 8)
case50 = next(x for x in reference['cases'] if x['sold_fraction'] == D('0.5'))
equal(software['team_analysis_four_room_50_percent_usd'], analysis_total * case50['teams'],
      'Annual analysis package USD')

# Cross-check the published financial tables against the current data file.
turnover = section('Turnover and the amount available for remaining costs')
for label, key, currency in [('Sold team sessions', 'teams', False),
                             ('Paid visits', 'paid_visits', False),
                             ('Receipts including GST', 'gross_receipts', True),
                             ('Sales excluding GST', 'net_sales', True),
                             ('Example roster wages plus super', 'wages_plus_sg', True),
                             ('Domestic card processing, excluding recoverable GST', 'card_fees_ex_gst', True),
                             ('Available for all other costs and operating result', 'remaining_for_all_other_costs', True)]:
    table_row(turnover, label, [money(c[key], 0) if currency else f'{c[key]:,.0f}'
                               for c in reference['cases']])
slow = next(x for x in f['operations'] if x['rooms'] == 4 and x['starts_per_room_day'] == 7)
slow50 = next(x for x in slow['cases'] if x['sold_fraction'] == D('0.5'))
require(money(slow50['remaining_for_all_other_costs']) in turnover,
        'Manuscript corrected 75-minute amount')
pass_body = section('Tourism pass: settlement without double counting')
for label, key, places in [('Customer payment', 'customer_cash', 2),
                           ('Three-venue allocations, including GST', 'venue_allocations_gross', 2),
                           ('Network service component, including GST', 'central_service_gross', 2),
                           ('Network service revenue, excluding GST', 'central_service_net', 2),
                           ('Domestic-card processor cash charge', 'processor_fee_cash', 4),
                           ('Processor cost excluding GST if credit eligible', 'processor_fee_net_if_credit_eligible', 6),
                           ('Network amount after processing, before its other costs', 'central_residual_before_other_costs', 2)]:
    table_row(pass_body, label, [money(p[key], places)])
software_body = section('Software and AI unit-cost appendix')
for case in speech['cases']:
    if case['operation'] == reference['name']:
        table_row(software_body, f'{case["sold_fraction"]:.0%}',
                  [f'{case["sold_teams"]:,.1f}', f'{case["chargeable_audio_minutes"]:,.1f}',
                   f'{case["file_transcription_usd"]:,.2f}', f'{case["live_transcription_usd"]:,.2f}'])

# All unresolved packages stay explicit, and source IDs resolve locally.
require(f['financial_completion']['full_profit_available'] is False,
        'No fully quoted profit claim')
for item in f['quote_required']:
    require(item['status'] == 'quote_required' and item['cost'] is None,
            f'{item["id"]} unresolved scope must not be zero-priced')
source_map = {x['id']: x for group in sources.values() if isinstance(group, list)
              for x in group if isinstance(x, dict) and 'id' in x}
for source in f['source_registry']:
    require(source['id'] in source_map, f'Source exists: {source["id"]}')
    if source['id'] in source_map:
        require(source_map[source['id']].get('url') == source['url'],
                f'Source URL agrees: {source["id"]}')
for chapter in plan['chapters']:
    for item in chapter['sections']:
        for ref in item.get('refs', []):
            require(ref in source_map, f'Manuscript source exists: {ref}')

if errors:
    print(f'Financial audit failed: {len(errors)} of {checks} checks.', file=sys.stderr)
    for error in errors:
        print(f'- {error}', file=sys.stderr)
    sys.exit(1)
print(f'Financial audit passed: {checks} checks. No files changed.')
print('Verified priced extensions, capacity, wages, renewals, settlements, USD usage,')
print('published turnover/pass/software tables and source references.')
