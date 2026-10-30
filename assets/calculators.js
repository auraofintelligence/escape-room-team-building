/* UI for local calculations. No input is transmitted or saved. */
(() => {
  'use strict';
  const config=JSON.parse(document.getElementById('calculator-data')?.textContent||'{}');
  const money=v=>new Intl.NumberFormat('en-AU',{style:'currency',currency:'AUD'}).format(v);
  const usd=v=>'US'+money(v);
  const count=v=>new Intl.NumberFormat('en-AU',{maximumFractionDigits:2}).format(v);
  const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const row=(label,value)=>'<div><dt>'+esc(label)+'</dt><dd>'+esc(value)+'</dd></div>';
  const values=form=>Object.fromEntries([...form.querySelectorAll('[data-key]')].map(e=>[e.dataset.key,e.value]));
  function addItem(form) {
    const box=document.createElement('fieldset');box.className='calc-item';
    box.innerHTML='<legend>Cost item</legend><label>Source benchmark<select data-benchmark><option value="">Enter your own item</option>'+config.benchmarks.map(x=>'<option value="'+esc(x.id)+'">'+esc(x.label+' · $'+x.value+' · '+x.source)+'</option>').join('')+'</select></label><div class="calc-fields"><label>Item<input data-name type="text"></label><label>Quantity<input data-quantity type="number" min="0" step="any"></label><label>Quoted unit price AUD<input data-price type="number" min="0" step="any"></label><label>Invoice tax basis<select data-tax><option value="">Choose</option><option value="inc10">Includes 10% GST</option><option value="ex10">Add 10% GST</option><option value="none">No GST</option></select></label></div><p class="calc-note" data-source></p><button type="button" data-remove>Remove item</button>';
    box.querySelector('[data-benchmark]').addEventListener('change',e=>{
      const b=config.benchmarks.find(b=>b.id===e.target.value);
      if(!b)return;
      box.querySelector('[data-name]').value=b.label;
      box.querySelector('[data-price]').value=b.value;
      box.querySelector('[data-tax]').value=b.tax_basis==='inc_gst'?'inc10':'';
      box.querySelector('[data-source]').innerHTML='<a href="sources.html#'+b.source+'">'+b.source+'</a> · Checked 30 Oct 2026 · Advertised price';
      calculate(form);
    });
    box.querySelector('[data-remove]').addEventListener('click',()=>{box.remove();calculate(form);});
    form.querySelector('[data-cost-lines]').append(box);
  }
  function calculate(form) {
    const kind=form.dataset.calculator,x=values(form),target=form.querySelector('[data-results]');
    if(kind==='cost')x.lines=[...form.querySelectorAll('.calc-item')].map(e=>({quantity:e.querySelector('[data-quantity]').value,price:e.querySelector('[data-price]').value,tax:e.querySelector('[data-tax]').value}));
    try {
      const r=PlanCalculators[kind](x);let output='';
      if(kind==='throughput') output=row('Total physical rooms',count(r.totalRooms))+row('Maximum starts per room per day',count(r.maxStarts))+row('Available team sessions per year',count(r.available))+row('Expected sold team sessions per year',count(r.teams))+row('Expected paid visits per year',count(r.visits))+row('Annual ticket receipts per room',money(r.perRoomCash))+row('Annual ticket receipts per location',money(r.perLocationCash))+row('Annual ticket receipts all locations',money(r.cash))+row('Annual sales excluding entered GST',money(r.net));
      if(kind==='cost')output=row('Item cash subtotal',money(r.itemCash))+row('Delivered cash cost',money(r.cash))+row('Eligible GST credit entered',money(r.credit))+row('Cost after entered credit',money(r.net));
      if(kind==='labour')output=row('Labour excluding GST',money(r.labour))+row('Work package excluding GST',money(r.total));
      if(kind==='operating') {
        output=row('Expected sold teams',count(r.teams))+row('Ticket receipts',money(r.cash))+row('Sales excluding entered GST',money(r.net));
        if(r.complete)output+=row('Processor cash fee per payment',money(r.feePerPayment))+row('Processing cost per team after credit',money(r.cardPerTeam))+row('Contribution per sold team',money(r.contribution))+row('Operating balance before depreciation finance and income tax',money(r.balance))+row('Break-even share of available sessions',r.breakEven===null?'No positive contribution or no available capacity':count(r.breakEven)+'%'+(r.breakEven>100?' · exceeds entered capacity':''));
        else output+='</dl><p>'+esc(r.note)+'</p><dl>';
      }
      if(kind==='pass')output=row('Customer payment',money(r.cash))+row('Venue allocations',money(r.venue))+row('Service component including GST',money(r.service))+row('Service component excluding entered GST',money(r.serviceNet))+row('Processor cash charge',money(r.processing))+row('Service amount after processing before other costs',money(r.remaining))+row('Amount per pass before other costs',money(r.perPass));
      if(kind==='renewal')output=row('Annual cash provision',money(r.annual))+row('Replacement cash through year 3',money(r.horizons[3]))+row('Replacement cash through year 5',money(r.horizons[5]))+row('Replacement cash through year 10',money(r.horizons[10]))+row('Contribution displaced by closure',money(r.lost));
      if(kind==='software')output=row('Submitted audio minutes',count(r.audioMinutes))+row('Transcription',usd(r.audio))+row('Token use',usd(r.tokens))+row('Total provider charges entered',usd(r.usd))+row('AUD cash after entered FX and charges',r.aud===null?'Enter FX and additional AUD charges':money(r.aud));
      target.innerHTML='<dl>'+output+'</dl>';
      target.classList.remove('calc-error');
    } catch(e) {target.textContent=e.message;target.classList.add('calc-error');}
  }
  for(const form of document.querySelectorAll('[data-calculator]')) {
    const set=(key,v)=>{const e=form.querySelector('[data-key="'+key+'"]');if(e)e.value=v;};
    form.addEventListener('submit',e=>{e.preventDefault();calculate(form);});
    form.addEventListener('input',()=>calculate(form));
    form.addEventListener('change',()=>{
      for(const panel of form.querySelectorAll('[data-mode]'))panel.hidden=panel.dataset.mode!==values(form).mode;
      calculate(form);
    });
    form.querySelector('[data-clear]').addEventListener('click',()=>{
      for(const e of form.querySelectorAll('input,select'))e.value='';
      for(const p of form.querySelectorAll('[data-source]'))p.textContent='';
      for(const panel of form.querySelectorAll('[data-mode]'))panel.hidden=panel.dataset.mode!=='hourly';
      calculate(form);
    });
    form.querySelector('[data-add-item]')?.addEventListener('click',()=>{addItem(form);calculate(form);});
    form.querySelector('[data-use-card]')?.addEventListener('click',()=>{set('cardRate',config.verified_rates.card.rate_percent);set('cardFixed',config.verified_rates.card.fixed_aud);calculate(form);});
    form.querySelector('[data-use-token]')?.addEventListener('click',()=>{set('inputRate',config.verified_rates.tokens.input_usd_per_million);set('outputRate',config.verified_rates.tokens.output_usd_per_million);calculate(form);});
    for(const button of form.querySelectorAll('[data-audio]'))button.addEventListener('click',()=>{set('audioRate',config.verified_rates.transcription[button.dataset.audio+'_usd_per_minute']);calculate(form);});
    if(form.dataset.calculator==='cost')addItem(form);
    calculate(form);
  }
})();
