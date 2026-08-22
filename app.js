let coasters=[];
let activeCountry='All';
let saved=new Set(JSON.parse(localStorage.getItem('savedCoasters')||'[]'));
const grid=document.querySelector('#coasterGrid');
const filters=document.querySelector('#filters');
const search=document.querySelector('#search');
const suggestions=document.querySelector('#suggestions');
let suggestionResults=[];
let activeSuggestion=-1;
let searchTimer;

const display=(value,suffix='')=>value===null||value===undefined?'—':`${Number.isInteger(value)?value:Number(value).toFixed(1)}${suffix}`;
const colorFor=name=>['#ff6848','#9cddff','#d8ff3e','#ffc56b','#cab7ff','#71e2be','#ff9bc7','#f0a466','#85a7ff'][[...name].reduce((n,c)=>n+c.charCodeAt(0),0)%9];
const escapeHtml=value=>String(value).replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const youtubePovUrl=coaster=>`https://www.youtube.com/results?search_query=${encodeURIComponent(`${coaster.name} ${coaster.park||''} roller coaster POV front seat`)}`;

function renderFilters(){
  filters.innerHTML='';
  ['All',...[...new Set(coasters.map(c=>c.country).filter(Boolean))].sort((a,b)=>a.localeCompare(b))].forEach(country=>{
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
  grid.innerHTML=shown.slice(0,100).map((c,index)=>`<article class="card" tabindex="0" role="button" aria-label="Flip ${escapeHtml(c.name)} card" aria-pressed="false">
    <div class="card-inner">
      <div class="card-face card-front">
        <div class="card-visual" style="--card-color:${colorFor(c.name)}"><span class="rank">${String(index+1).padStart(2,'0')}</span><button class="save ${saved.has(c.wikidata_id)?'saved':''}" data-id="${c.wikidata_id}" aria-label="Save ${escapeHtml(c.name)}">${saved.has(c.wikidata_id)?'♥':'♡'}</button></div>
        <div class="card-body"><span class="type">${escapeHtml(c.manufacturer||'Manufacturer unknown')}</span><h3>${escapeHtml(c.name)}</h3><p class="location">${escapeHtml(c.park||'Park unknown')}${c.country?` · ${escapeHtml(c.country)}`:''}</p>
        <div class="metrics"><div><strong>${display(c.height_m,'m')}</strong><span>Height</span></div><div><strong>${display(c.length_m,'m')}</strong><span>Length</span></div><div><strong>${display(c.speed_kmh)}</strong><span>km/h</span></div><div><strong>${c.opened?.slice(0,4)||'—'}</strong><span>Opened</span></div></div>
        ${c.capacity?`<p class="capacity">Capacity: ${c.capacity.toLocaleString()} riders/hour</p>`:''}<span class="flip-hint">Click to see photo ↗</span></div>
      </div>
      <div class="card-face card-back" style="--card-color:${colorFor(c.name)}">
        ${c.image_url?`<img src="${escapeHtml(c.image_url)}" alt="${escapeHtml(c.name)} rollercoaster" loading="lazy">`:'<div class="photo-missing">Photo not available</div>'}
        <div class="photo-caption"><span>${escapeHtml(c.park||'Rollercoaster')}</span><h3>${escapeHtml(c.name)}</h3><div class="photo-links"><a class="pov-link" href="${escapeHtml(youtubePovUrl(c))}" target="_blank" rel="noopener">Watch POV on YouTube ▶</a>${c.image_source_url?`<a href="${escapeHtml(c.image_source_url)}" target="_blank" rel="noopener">Image source ↗</a>`:''}</div><small>Click to return</small></div>
      </div>
    </div>
  </article>`).join('');
  document.querySelector('#emptyState').hidden=shown.length>0;
  document.querySelectorAll('.save').forEach(button=>button.onclick=event=>{event.stopPropagation();toggleSave(button.dataset.id)});
  document.querySelectorAll('.card').forEach(card=>{
    const flip=()=>{card.classList.toggle('flipped');card.setAttribute('aria-pressed',String(card.classList.contains('flipped')))};
    card.onclick=event=>{if(!event.target.closest('a,button'))flip()};
    card.onkeydown=event=>{if(['Enter',' '].includes(event.key)&&!event.target.closest('a,button')){event.preventDefault();flip()}};
  });
}

function toggleSave(id){saved.has(id)?saved.delete(id):saved.add(id);localStorage.setItem('savedCoasters',JSON.stringify([...saved]));updateSaved();renderCards()}
function updateSaved(){document.querySelector('#savedCount').textContent=saved.size}

function closeSuggestions(){suggestions.hidden=true;search.setAttribute('aria-expanded','false');activeSuggestion=-1}
function showSuggestions(items){
  suggestionResults=items;
  suggestions.innerHTML=items.map((item,index)=>`<button class="suggestion" role="option" data-index="${index}"><span><strong>${escapeHtml(item.name)}</strong><span>${escapeHtml(item.park||item.country||'Park unknown')}</span></span><span class="suggestion-match">${item.matched_on==='name'?'Name match':`via ${escapeHtml(item.matched_on)}`}</span></button>`).join('');
  suggestions.hidden=items.length===0;
  search.setAttribute('aria-expanded',String(items.length>0));
  suggestions.querySelectorAll('.suggestion').forEach(button=>button.onclick=()=>selectSuggestion(Number(button.dataset.index)));
}
function selectSuggestion(index){
  const item=suggestionResults[index];
  if(!item)return;
  if(!coasters.some(coaster=>coaster.wikidata_id===item.wikidata_id))coasters.unshift(item);
  activeCountry='All';search.value=item.name;renderFilters();renderCards();closeSuggestions();
  grid.scrollIntoView({behavior:'smooth',block:'start'});
}
async function fetchSuggestions(){
  const query=search.value.trim();
  if(query.length<2)return closeSuggestions();
  try{
    const response=await fetch(`/api/search?q=${encodeURIComponent(query)}&limit=8`).then(result=>result.json());
    if(search.value.trim()===query)showSuggestions(response.items);
  }catch(error){closeSuggestions()}
}

async function load(){
  try{
    const [catalogue,stats]=await Promise.all([fetch('/api/coasters?limit=2000').then(r=>r.json()),fetch('/api/stats').then(r=>r.json())]);
    coasters=catalogue.items;
    document.querySelector('#rideCount').textContent=stats.coasters;
    document.querySelector('#parkCount').textContent=stats.parks;
    document.querySelector('#countryCount').textContent=stats.countries;
    renderFilters();renderCards();
  }catch(error){
    document.querySelector('#emptyState').hidden=false;
    document.querySelector('#emptyState').textContent='The coaster database is temporarily unavailable.';
  }
}

search.addEventListener('input',()=>{renderCards();clearTimeout(searchTimer);searchTimer=setTimeout(fetchSuggestions,180)});
search.addEventListener('keydown',event=>{
  const options=[...suggestions.querySelectorAll('.suggestion')];
  if(event.key==='Escape')return closeSuggestions();
  if(!options.length||!['ArrowDown','ArrowUp','Enter'].includes(event.key))return;
  event.preventDefault();
  if(event.key==='Enter'&&activeSuggestion>=0)return selectSuggestion(activeSuggestion);
  activeSuggestion=event.key==='ArrowDown'?Math.min(activeSuggestion+1,options.length-1):Math.max(activeSuggestion-1,0);
  options.forEach((option,index)=>option.classList.toggle('active',index===activeSuggestion));
});
document.addEventListener('click',event=>{if(!event.target.closest('.search-wrap'))closeSuggestions()});
document.querySelector('#savedButton').onclick=()=>{search.value='';activeCountry='All';grid.scrollIntoView({behavior:'smooth'});renderFilters();renderCards();document.querySelectorAll('.card').forEach(card=>{if(!saved.has(card.querySelector('.save').dataset.id))card.style.display='none'})};
document.querySelector('#year').textContent=new Date().getFullYear();
updateSaved();load();
