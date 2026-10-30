/* Local arithmetic only. Inputs and rates are comparison values, never approvals. */
(function (root, factory) {
  const engine = factory();
  if (typeof module === 'object' && module.exports) module.exports = engine;
  else root.PlanCalculators = engine;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  function n(value, label, min = 0, max = 1e12, integer = false) {
    if (value === '' || value === null || value === undefined) throw Error('Enter ' + label + '.');
    const v = Number(value);
    if (!Number.isFinite(v) || v < min || v > max || (integer && !Number.isInteger(v)))
      throw Error(label + ' must be ' + (integer ? 'a whole number ' : '') + 'from ' + min + ' to ' + max + '.');
    return v;
  }
  const roundCash = x => Math.round((x + Number.EPSILON) * 100) / 100;
  const missing = (v) => v === '' || v === null || v === undefined;
  function throughput(x) {
    const rooms = n(x.rooms, 'rooms per location', 1, 10000, true);
    const locations = n(x.locations, 'locations', 1, 10000, true);
    const starts = n(x.starts, 'starts per room per day', 1, 1000, true);
    const days = n(x.days, 'trading days', 1, 366, true);
    const play = n(x.play, 'play minutes', 1, 1440);
    const reset = n(x.reset, 'reset minutes', 0, 1440);
    const buffer = n(x.buffer, 'buffer minutes', 0, 1440);
    const window = n(x.window, 'room window in hours', 0, 24) * 60;
    const cycle = play + reset + buffer;
    const maxStarts = window < play ? 0 : Math.floor((window - play) / cycle) + 1;
    if (starts > maxStarts) throw Error('The room window permits at most ' + maxStarts + ' starts at this cycle.');
    const totalRooms = rooms * locations;
    const closed = n(x.closed, 'blocked room-days', 0, totalRooms * days, true);
    const group = n(x.group, 'average paying group size', 0, 1000);
    const limit = n(x.limit, 'player limit per room', 1, 1000, true);
    if (group > limit) throw Error('Average group size exceeds the entered room limit.');
    const sold = n(x.sold, 'sold percentage', 0, 100) / 100;
    const price = n(x.price, 'price per person');
    const tax = n(x.tax, 'GST percentage', 0, 100) / 100;
    const available = (totalRooms * days - closed) * starts;
    const teams = available * sold;
    const visits = teams * group;
    const cash = visits * price;
    return {totalRooms, maxStarts, cycle, available, teams, visits, cash, net: cash / (1 + tax),
      perRoomCash: cash / totalRooms, perLocationCash: cash / locations,
      simultaneous: totalRooms * limit, dailyVisits: visits / days};
  }
  function cost(x) {
    if (!x.lines || !x.lines.length) throw Error('Add a priced item.');
    let itemCash = 0;
    for (let i=0; i<x.lines.length; i++) {
      const l=x.lines[i], label='item ' + (i+1);
      const q=n(l.quantity, label+' quantity', 0, 1e9);
      const p=n(l.price, label+' unit price');
      if (!['inc10','ex10','none'].includes(l.tax)) throw Error('Choose the tax basis for '+label+'.');
      itemCash += q*p*(l.tax==='ex10'?1.1:1);
    }
    const freight=n(x.freight,'freight cash cost');
    const repair=n(x.repair,'cleaning and repair cash cost');
    const install=n(x.install,'installation cash cost');
    const cash=itemCash+freight+repair+install;
    const credit=n(x.credit,'eligible input GST credit',0,cash);
    return {itemCash, cash, credit, net:cash-credit};
  }
  function labour(x) {
    let labour;
    if(x.mode==='hourly') {
      const people=n(x.people,'people',1,1e5,true);
      const hours=n(x.hours,'hours per person');
      const rate=n(x.rate,'hourly rate excluding GST');
      labour=people*hours*rate;
    } else if(x.mode==='attendance') {
      const visits=n(x.attendances,'attendances',0,1e6,true);
      const first=n(x.first,'attendance and first-hour charge excluding GST');
      const extra=n(x.extra,'total additional labour hours');
      const later=n(x.later,'additional hourly rate excluding GST');
      if(visits===0 && extra>0) throw Error('Additional hours require at least one attendance.');
      labour=visits*first+extra*later;
    } else throw Error('Choose hourly or attendance pricing.');
    return {labour, total:labour+n(x.materials,'materials excluding GST')+n(x.other,'other charges excluding GST')};
  }
  function operating(x) {
    const available=n(x.available,'available annual team sessions',0,1e10);
    const sold=n(x.sold,'sold percentage',0,100)/100;
    const group=n(x.group,'average paying group size',0,1000);
    const price=n(x.price,'price per person including GST');
    const tax=n(x.tax,'sales GST percentage',0,100)/100;
    const teams=available*sold, grossPerTeam=group*price, cash=teams*grossPerTeam;
    const out={available,teams,cash,net:cash/(1+tax),complete:false};
    const fields=['cardRate','cardFixed','payments','credit','variable','fixed','renewal'];
    if(fields.some(k=>missing(x[k]))) {out.note='Complete every cost and card field to calculate contribution and operating balance. Use 0 only where it applies.';return out;}
    const payments=n(x.payments,'payments per team',1,1000,true);
    const rate=n(x.cardRate,'processor percentage',0,100)/100;
    const fee=n(x.cardFixed,'processor fixed cash fee');
    const credit=n(x.credit,'recoverable share of processor GST',0,100)/100;
    // Card benchmark fees include 10% GST. A zero credit share deducts no input tax credit.
    const feePerPayment=roundCash(grossPerTeam/payments*rate+fee);
    const cardPerTeam=payments*feePerPayment*(1-credit/11);
    const variable=n(x.variable,'all other variable cost per team');
    const fixed=n(x.fixed,'annual fixed cost');
    const renewal=n(x.renewal,'annual renewal provision');
    const contribution=grossPerTeam/(1+tax)-cardPerTeam-variable;
    const balance=teams*contribution-fixed-renewal;
    const breakEven=available>0&&contribution>0?(fixed+renewal)/(available*contribution)*100:null;
    return {...out,complete:true,feePerPayment,cardPerTeam,cardTotal:cardPerTeam*teams,contribution,balance,breakEven};
  }
  function pass(x) {
    const passes=n(x.passes,'passes per transaction',1,1e6,true);
    const price=n(x.price,'pass price including GST');
    const visits=n(x.visits,'venue visits per pass',1,1000,true);
    const allocation=n(x.allocation,'venue allocation per visit including GST');
    const tax=n(x.tax,'service GST percentage',0,100)/100;
    const rate=n(x.cardRate,'processor percentage',0,100)/100;
    const fixed=n(x.cardFixed,'processor fixed cash fee');
    const credit=n(x.credit,'recoverable share of processor GST',0,100)/100;
    // Price and allocation are currency amounts rounded to cents before settlement.
    const cash=passes*roundCash(price), venue=passes*visits*roundCash(allocation);
    if(venue>cash+1e-8) throw Error('Venue allocations exceed customer receipts.');
    const service=cash-venue, processing=roundCash(cash*rate+fixed);
    const netProcessing=processing*(1-credit/11);
    const serviceNet=service/(1+tax), remaining=serviceNet-netProcessing;
    return {cash,venue,service,serviceNet,processing,netProcessing,remaining,perPass:remaining/passes};
  }
  function renewal(x) {
    const replacement=n(x.replacement,'total replacement cash cost');
    const years=n(x.years,'funding interval in years',1,100,true);
    const annual=replacement/years;
    const horizons={};for(const h of [3,5,10]) horizons[h]=Math.floor(h/years)*replacement;
    const slots=n(x.displaced,'displaced team sessions');
    const sold=n(x.sold,'expected sold percentage',0,100)/100;
    const contribution=n(x.contribution,'contribution per sold session',-1e12,1e12);
    return {annual,horizons,lost:slots*sold*contribution};
  }
  function software(x) {
    const sessions=n(x.sessions,'recorded sessions');
    const people=n(x.people,'average recorded people per session',0,1000);
    const minutes=n(x.minutes,'minutes per person');
    const submissions=n(x.submissions,'submissions per file including retries',1,1000);
    const rate=n(x.audioRate,'USD price per audio minute');
    const calls=n(x.calls,'model calls including repeats');
    const input=n(x.input,'input tokens per call');
    const output=n(x.output,'billable output tokens per call');
    const inputRate=n(x.inputRate,'USD input price per million');
    const outputRate=n(x.outputRate,'USD output price per million');
    const tools=n(x.tools,'other provider charges in USD');
    const audioMinutes=sessions*people*minutes*submissions;
    const audio=audioMinutes*rate;
    const tokens=calls*(input*inputRate+output*outputRate)/1e6;
    const usd=audio+tokens+tools;
    const out={audioMinutes,audio,tokens,usd};
    if(missing(x.fx)||missing(x.extraAud))return {...out,aud:null};
    return {...out,aud:usd*n(x.fx,'AUD per USD',0.000001,100000)+n(x.extraAud,'FX tax and other cash charges in AUD')};
  }
  return {throughput,cost,labour,operating,pass,renewal,software,roundCash};
});
