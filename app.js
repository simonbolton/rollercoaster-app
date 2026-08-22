let coasters=[],parks=[],view='coasters',activeCountry='All';
let saved=new Set(JSON.parse(localStorage.getItem('savedCoasters')||'[]'));
const grid=document.querySelector('#coasterGrid'),filters=document.querySelector('#filters'),search=document.querySelector('#search'),suggestions=document.querySelector('#suggestions'),coastersTab=document.querySelector('#coastersTab'),parksTab=document.querySelector('#parksTab');
let suggestionResults=[],activeSuggestion=-1,searchTimer;
const display=(value,suffix='')=>value===null||value===undefined?'—':`${Number.isInteger(value)?value:Number(value).toFixed(1)}${suffix}`;
const feet=value=>value===null||value===undefined?'—':`${Math.round(value*3.28084).toLocaleString()}ft`;
const colorFor=name=>['#ff6848','#9cddff','#d8ff3e','#ffc56b','#cab7ff','#71e2be','#ff9bc7','#f0a466','#85a7ff'][[...name].reduce((n,c)=>n+c.charCodeAt(0),0)%9];
const escapeHtml=value=>String(value).replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const youtubePovUrl=c=>`https://www.youtube.com/results?search_query=${encodeURIComponent(`${c.name} ${c.park||''} roller coaster POV front seat`)}`;
const currentItems=()=>view==='coasters'?coasters:parks;

function setView(next){
  view=next;activeCountry='All';search.value='';closeSuggestions();clearTimeout(searchTimer);
  coastersTab.classList.toggle('active',view==='coasters');parksTab.classList.toggle('active',view==='parks');
  coastersTab.setAttribute('aria-selected',String(view==='coasters'));parksTab.setAttribute('aria-selected',String(view==='parks'));
  search.placeholder=view==='coasters'?'Search rides or parks…':'Search parks or countries…';
  search.setAttribute('aria-label',search.placeholder);document.querySelector('#savedButton').hidden=view==='parks';
  renderFilters();renderCards();
}
function renderFilters(){
  filters.innerHTML='';
  ['All',...[...new Set(currentItems().map(item=>item.country).filter(Boolean))].sort((a,b)=>a.localeCompare(b))].forEach(country=>{
    const button=document.createElement('button');button.className=`filter ${country===activeCountry?'active':''}`;button.textContent=country;
    button.onclick=()=>{activeCountry=country;search.value='';closeSuggestions();clearTimeout(searchTimer);renderFilters();renderCards()};filters.appendChild(button);
  });
}
function coasterCard(c,index){return `<article class="card" tabindex="0" role="button" aria-label="Flip ${escapeHtml(c.name)} card" aria-pressed="false"><div class="card-inner"><div class="card-face card-front">
  <div class="card-visual" style="--card-color:${colorFor(c.name)}"><span class="rank">${String(index+1).padStart(2,'0')}</span><button class="save ${saved.has(c.wikidata_id)?'saved':''}" data-id="${c.wikidata_id}" aria-label="Save ${escapeHtml(c.name)}">${saved.has(c.wikidata_id)?'♥':'♡'}</button></div>
  <div class="card-body"><span class="type">${escapeHtml(c.manufacturer||'Manufacturer unknown')}</span><h3>${escapeHtml(c.name)}</h3><p class="location">${escapeHtml(c.park||'Park unknown')}${c.country?` · ${escapeHtml(c.country)}`:''}</p>
  <div class="metrics"><div><strong>${feet(c.height_m)}</strong><span>Height</span></div><div><strong>${feet(c.length_m)}</strong><span>Length</span></div><div><strong>${display(c.speed_kmh)}</strong><span>km/h</span></div><div><strong>${c.opened?.slice(0,4)||'—'}</strong><span>Opened</span></div></div>
  ${c.capacity?`<p class="capacity">Capacity: ${c.capacity.toLocaleString()} riders/hour</p>`:''}<span class="flip-hint">Click to see photo ↗</span></div></div>
  <div class="card-face card-back" style="--card-color:${colorFor(c.name)}">${c.image_url?`<img src="${escapeHtml(c.image_url)}" alt="${escapeHtml(c.name)} rollercoaster" loading="lazy">`:'<div class="photo-missing">Photo not available</div>'}
  <div class="photo-caption"><span>${escapeHtml(c.park||'Rollercoaster')}</span><h3>${escapeHtml(c.name)}</h3><div class="photo-links"><a class="pov-link" href="${escapeHtml(youtubePovUrl(c))}" target="_blank" rel="noopener">Watch POV on YouTube ▶</a>${c.image_source_url?`<a href="${escapeHtml(c.image_source_url)}" target="_blank" rel="noopener">Image source ↗</a>`:''}</div><small>Click to return</small></div></div></div></article>`}
function parkCard(park,index){
  const years=park.first_coaster_year?`${park.first_coaster_year}${park.latest_coaster_year!==park.first_coaster_year?`–${park.latest_coaster_year}`:''}`:'—';
  return `<article class="card park-card" tabindex="0" role="button" aria-label="Flip ${escapeHtml(park.name)} card" aria-pressed="false"><div class="card-inner"><div class="card-face card-front">
  <div class="card-visual" style="--card-color:${colorFor(park.name)}"><span class="rank">${String(index+1).padStart(2,'0')}</span></div>
  <div class="card-body"><span class="type">Amusement park</span><h3>${escapeHtml(park.name)}</h3><p class="location">${escapeHtml(park.country||'Country unknown')}</p>
  <div class="metrics"><div><strong>${park.coaster_count}</strong><span>Coasters</span></div><div><strong>${feet(park.tallest_m)}</strong><span>Tallest</span></div><div><strong>${display(park.fastest_kmh)}</strong><span>km/h max</span></div><div><strong>${years}</strong><span>Ride years</span></div></div>
  <span class="flip-hint">Click to see park photo ↗</span></div></div><div class="card-face card-back" style="--card-color:${colorFor(park.name)}">
  ${park.image_url?`<img src="${escapeHtml(park.image_url)}" alt="${escapeHtml(park.name)}" loading="lazy">`:'<div class="photo-missing">Photo not available</div>'}
  <div class="photo-caption"><span>${escapeHtml(park.country||'Amusement park')}</span><h3>${escapeHtml(park.name)}</h3><div class="photo-links"><button class="pov-link show-park" data-park="${escapeHtml(park.name)}">See its coasters →</button>${park.image_source_url?`<a href="${escapeHtml(park.image_source_url)}" target="_blank" rel="noopener">Image source ↗</a>`:''}</div><small>Click to return</small></div></div></div></article>`;
}
function renderCards(){
  const query=search.value.trim().toLowerCase();
  const shown=currentItems().filter(item=>(activeCountry==='All'||item.country===activeCountry)&&(view==='coasters'?`${item.name} ${item.park||''} ${item.manufacturer||''}`:`${item.name} ${item.country||''}`).toLowerCase().includes(query));
  grid.innerHTML=shown.slice(0,100).map((item,index)=>view==='coasters'?coasterCard(item,index):parkCard(item,index)).join('');
  const empty=document.querySelector('#emptyState');empty.hidden=shown.length>0;empty.textContent=view==='coasters'?'No rides match that search. Try another track.':'No parks match that search.';
  document.querySelectorAll('.save').forEach(button=>button.onclick=event=>{event.stopPropagation();toggleSave(button.dataset.id)});
  document.querySelectorAll('.show-park').forEach(button=>button.onclick=event=>{event.stopPropagation();const park=button.dataset.park;setView('coasters');search.value=park;renderCards();grid.scrollIntoView({behavior:'smooth',block:'start'})});
  document.querySelectorAll('.card').forEach(card=>{const flip=()=>{card.classList.toggle('flipped');card.setAttribute('aria-pressed',String(card.classList.contains('flipped')))};card.onclick=event=>{if(!event.target.closest('a,button'))flip()};card.onkeydown=event=>{if(['Enter',' '].includes(event.key)&&!event.target.closest('a,button')){event.preventDefault();flip()}}});
}
function toggleSave(id){saved.has(id)?saved.delete(id):saved.add(id);localStorage.setItem('savedCoasters',JSON.stringify([...saved]));updateSaved();renderCards()}
function updateSaved(){document.querySelector('#savedCount').textContent=saved.size}
function closeSuggestions(){suggestions.hidden=true;search.setAttribute('aria-expanded','false');activeSuggestion=-1}
function showSuggestions(items){suggestionResults=items;suggestions.innerHTML=items.map((item,index)=>`<button class="suggestion" role="option" data-index="${index}"><span><strong>${escapeHtml(item.name)}</strong><span>${escapeHtml(item.park||item.country||'Park unknown')}</span></span><span class="suggestion-match">${item.matched_on==='name'?'Name match':`via ${escapeHtml(item.matched_on)}`}</span></button>`).join('');suggestions.hidden=items.length===0;search.setAttribute('aria-expanded',String(items.length>0));suggestions.querySelectorAll('.suggestion').forEach(button=>button.onclick=()=>selectSuggestion(Number(button.dataset.index)))}
function selectSuggestion(index){const item=suggestionResults[index];if(!item)return;if(!coasters.some(c=>c.wikidata_id===item.wikidata_id))coasters.unshift(item);activeCountry='All';search.value=item.name;renderFilters();renderCards();closeSuggestions();grid.scrollIntoView({behavior:'smooth',block:'start'})}
async function fetchSuggestions(){if(view!=='coasters')return closeSuggestions();const query=search.value.trim();if(query.length<2)return closeSuggestions();try{const response=await fetch(`/api/search?q=${encodeURIComponent(query)}&limit=8`).then(result=>result.json());if(search.value.trim()===query)showSuggestions(response.items)}catch(error){closeSuggestions()}}
async function load(){try{const [catalogue,parkCatalogue,stats]=await Promise.all([fetch('/api/coasters?limit=2000').then(r=>r.json()),fetch('/api/parks?limit=2000').then(r=>r.json()),fetch('/api/stats').then(r=>r.json())]);coasters=catalogue.items;parks=parkCatalogue.items;document.querySelector('#rideCount').textContent=stats.coasters;document.querySelector('#parkCount').textContent=stats.parks;document.querySelector('#countryCount').textContent=stats.countries;renderFilters();renderCards()}catch(error){const empty=document.querySelector('#emptyState');empty.hidden=false;empty.textContent='The catalogue is temporarily unavailable.'}}
search.addEventListener('input',()=>{renderCards();clearTimeout(searchTimer);searchTimer=setTimeout(fetchSuggestions,180)});
search.addEventListener('keydown',event=>{const options=[...suggestions.querySelectorAll('.suggestion')];if(event.key==='Escape')return closeSuggestions();if(!options.length||!['ArrowDown','ArrowUp','Enter'].includes(event.key))return;event.preventDefault();if(event.key==='Enter'&&activeSuggestion>=0)return selectSuggestion(activeSuggestion);activeSuggestion=event.key==='ArrowDown'?Math.min(activeSuggestion+1,options.length-1):Math.max(activeSuggestion-1,0);options.forEach((option,index)=>option.classList.toggle('active',index===activeSuggestion))});
document.addEventListener('click',event=>{if(!event.target.closest('.search-wrap'))closeSuggestions()});
coastersTab.onclick=()=>setView('coasters');parksTab.onclick=()=>setView('parks');
document.querySelector('#savedButton').onclick=()=>{setView('coasters');grid.scrollIntoView({behavior:'smooth'});document.querySelectorAll('.card').forEach(card=>{if(!saved.has(card.querySelector('.save').dataset.id))card.style.display='none'})};
document.querySelector('#year').textContent=new Date().getFullYear();updateSaved();load();
