let coasters=[];
let activeCountry='All';
let saved=new Set(JSON.parse(localStorage.getItem('savedCoasters')||'[]'));
const grid=document.querySelector('#coasterGrid');
const filters=document.querySelector('#filters');
const search=document.querySelector('#search');

const display=(value,suffix='')=>value===null||value===undefined?'—':`${Number.isInteger(value)?value:Number(value).toFixed(1)}${suffix}`;
const colorFor=name=>['#ff6848','#9cddff','#d8ff3e','#ffc56b','#cab7ff','#71e2be','#ff9bc7','#f0a466','#85a7ff'][[...name].reduce((n,c)=>n+c.charCodeAt(0),0)%9];

function renderFilters(){
  filters.innerHTML='';
  ['All',...new Set(coasters.map(c=>c.country).filter(Boolean))].slice(0,9).forEach(country=>{
    const button=document.createElement('button');
    button.className=`filter ${country===activeCountry?'active':''}`;
    button.textContent=country;
    button.onclick=()=>{activeCountry=country;renderFilters();renderCards()};
    filters.appendChild(button);
  });
}

function renderCards(){
  const query=search.value.trim().toLowerCase();
  const shown=coasters.filter(c=>(activeCountry==='All'||c.country===activeCountry)&&`${c.name} ${c.park||''} ${c.manufacturer||''}`.toLowerCase().includes(query));
  grid.innerHTML=shown.slice(0,100).map((c,index)=>`<article class="card">
    <div class="card-visual" style="--card-color:${colorFor(c.name)}"><span class="rank">${String(index+1).padStart(2,'0')}</span><button class="save ${saved.has(c.wikidata_id)?'saved':''}" data-id="${c.wikidata_id}" aria-label="Save ${c.name}">${saved.has(c.wikidata_id)?'♥':'♡'}</button></div>
    <div class="card-body"><span class="type">${c.manufacturer||'Manufacturer unknown'}</span><h3>${c.name}</h3><p class="location">${c.park||'Park unknown'}${c.country?` · ${c.country}`:''}</p>
    <div class="metrics"><div><strong>${display(c.height_m,'m')}</strong><span>Height</span></div><div><strong>${display(c.length_m,'m')}</strong><span>Length</span></div><div><strong>${display(c.speed_kmh)}</strong><span>km/h</span></div><div><strong>${c.opened?.slice(0,4)||'—'}</strong><span>Opened</span></div></div>
    ${c.capacity?`<p class="capacity">Capacity: ${c.capacity.toLocaleString()} riders/hour</p>`:''}</div>
  </article>`).join('');
  document.querySelector('#emptyState').hidden=shown.length>0;
  document.querySelectorAll('.save').forEach(button=>button.onclick=()=>toggleSave(button.dataset.id));
}

function toggleSave(id){saved.has(id)?saved.delete(id):saved.add(id);localStorage.setItem('savedCoasters',JSON.stringify([...saved]));updateSaved();renderCards()}
function updateSaved(){document.querySelector('#savedCount').textContent=saved.size}

async function load(){
  try{
    const [catalogue,stats]=await Promise.all([fetch('/api/coasters?limit=500').then(r=>r.json()),fetch('/api/stats').then(r=>r.json())]);
    coasters=catalogue.items;
    document.querySelector('#rideCount').textContent=stats.coasters;
    document.querySelector('#countryCount').textContent=stats.countries;
    renderFilters();renderCards();
  }catch(error){
    document.querySelector('#emptyState').hidden=false;
    document.querySelector('#emptyState').textContent='The coaster database is temporarily unavailable.';
  }
}

search.addEventListener('input',renderCards);
document.querySelector('#savedButton').onclick=()=>{search.value='';activeCountry='All';grid.scrollIntoView({behavior:'smooth'});renderFilters();renderCards();document.querySelectorAll('.card').forEach(card=>{if(!saved.has(card.querySelector('.save').dataset.id))card.style.display='none'})};
document.querySelector('#year').textContent=new Date().getFullYear();
updateSaved();load();
