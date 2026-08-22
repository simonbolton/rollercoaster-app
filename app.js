const coasters = [
  {name:'Steel Vengeance',park:'Cedar Point',country:'USA',type:'Hybrid',height:62,speed:119,drops:4,color:'#ff6848'},
  {name:'Fury 325',park:'Carowinds',country:'USA',type:'Steel',height:99,speed:153,drops:3,color:'#9cddff'},
  {name:'Zadra',park:'Energylandia',country:'Poland',type:'Hybrid',height:63,speed:121,drops:3,color:'#d8ff3e'},
  {name:'The Voyage',park:'Holiday World',country:'USA',type:'Wooden',height:49,speed:108,drops:5,color:'#ffc56b'},
  {name:'Taron',park:'Phantasialand',country:'Germany',type:'Launch',height:30,speed:117,drops:2,color:'#cab7ff'},
  {name:'VelociCoaster',park:'Islands of Adventure',country:'USA',type:'Launch',height:47,speed:113,drops:2,color:'#71e2be'},
  {name:'Hyperion',park:'Energylandia',country:'Poland',type:'Steel',height:77,speed:142,drops:3,color:'#ff9bc7'},
  {name:'Wicker Man',park:'Alton Towers',country:'UK',type:'Wooden',height:22,speed:70,drops:2,color:'#f0a466'},
  {name:'DC Rivals',park:'Warner Bros. Movie World',country:'Australia',type:'Steel',height:62,speed:115,drops:3,color:'#85a7ff'}
];

let activeType='All';
let saved=new Set(JSON.parse(localStorage.getItem('savedCoasters')||'[]'));
const grid=document.querySelector('#coasterGrid');
const filters=document.querySelector('#filters');
const search=document.querySelector('#search');

function renderFilters(){
  filters.innerHTML='';
  ['All',...new Set(coasters.map(c=>c.type))].forEach(type=>{
    const button=document.createElement('button');
    button.className=`filter ${type===activeType?'active':''}`;
    button.textContent=type;
    button.onclick=()=>{activeType=type;renderFilters();renderCards()};
    filters.appendChild(button);
  });
}

function renderCards(){
  const query=search.value.trim().toLowerCase();
  const shown=coasters.filter(c=>(activeType==='All'||c.type===activeType)&&`${c.name} ${c.park} ${c.country}`.toLowerCase().includes(query));
  grid.innerHTML=shown.map((c,index)=>`<article class="card">
    <div class="card-visual" style="--card-color:${c.color}"><span class="rank">${String(index+1).padStart(2,'0')}</span><button class="save ${saved.has(c.name)?'saved':''}" data-name="${c.name}" aria-label="Save ${c.name}">${saved.has(c.name)?'♥':'♡'}</button></div>
    <div class="card-body"><span class="type">${c.type} coaster</span><h3>${c.name}</h3><p class="location">${c.park} · ${c.country}</p>
    <div class="metrics"><div><strong>${c.height}m</strong><span>Height</span></div><div><strong>${c.speed}</strong><span>km/h</span></div><div><strong>${c.drops}</strong><span>Big drops</span></div></div></div>
  </article>`).join('');
  document.querySelector('#emptyState').hidden=shown.length>0;
  document.querySelectorAll('.save').forEach(button=>button.onclick=()=>toggleSave(button.dataset.name));
}

function toggleSave(name){saved.has(name)?saved.delete(name):saved.add(name);localStorage.setItem('savedCoasters',JSON.stringify([...saved]));updateSaved();renderCards()}
function updateSaved(){document.querySelector('#savedCount').textContent=saved.size}

search.addEventListener('input',renderCards);
document.querySelector('#savedButton').onclick=()=>{search.value='';activeType='All';grid.scrollIntoView({behavior:'smooth'});renderFilters();renderCards();document.querySelectorAll('.card').forEach(card=>{if(!saved.has(card.querySelector('h3').textContent))card.style.display='none'})};
document.querySelector('#rideCount').textContent=coasters.length;
document.querySelector('#countryCount').textContent=new Set(coasters.map(c=>c.country)).size;
document.querySelector('#year').textContent=new Date().getFullYear();
renderFilters();renderCards();updateSaved();
