'use strict';
const state = {sddOnly:false, differences:false, details:true, query:''};
const escapeHTML = value => String(value).replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const normalize = value => value.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
const total = SECTIONS.reduce((sum,s)=>sum+s.rows.length,0);
const sourceLink = s => s.url ? `<a href="${s.url}" ${s.url.startsWith('#')?'':'target="_blank" rel="noopener noreferrer"'}>${escapeHTML(s.title)} ↗</a>` : `<span>${escapeHTML(s.title)}</span>`;
const nav = document.querySelector('.section-nav');
nav.innerHTML = SECTIONS.map((s,i)=>`<a href="#${s.id}" ${i===0?'class="active" aria-current="location"':''}><span>${String(i+1).padStart(2,'0')}</span>${s.nav}</a>`).join('');
document.getElementById('total-count').textContent = `${total} aspectos`;
document.getElementById('source-links').innerHTML = Object.values(SOURCES).map(sourceLink).join('');
function updateNavigation(){
 const sections=[...document.querySelectorAll('.dimension:not([hidden])')];
 const threshold=Math.max(180,document.querySelector('.explorer-bar').getBoundingClientRect().bottom+50);
 const current=sections.filter(section=>section.getBoundingClientRect().top<=threshold).at(-1)||sections[0];
 nav.querySelectorAll('a').forEach(a=>{const selected=current&&a.hash==='#'+current.id;a.classList.toggle('active',!!selected);if(selected)a.setAttribute('aria-current','location');else a.removeAttribute('aria-current');});
}
let navigationFrame=0;
function scheduleNavigation(){if(navigationFrame)return;navigationFrame=requestAnimationFrame(()=>{navigationFrame=0;updateNavigation();});}
window.addEventListener('scroll',scheduleNavigation,{passive:true});
window.addEventListener('resize',scheduleNavigation);
function render(){
 const indices = FRAMEWORKS.map((_,i)=>i).filter(i=>!state.sddOnly || FRAMEWORKS[i].className!=='control');
 let count=0;
 document.body.classList.toggle('sdd-only',state.sddOnly);
 document.body.classList.toggle('hide-details',!state.details);
 document.getElementById('tables').innerHTML=SECTIONS.map((s,index)=>{
  const rows=s.rows.filter(r=>{
   // Differences compare the primary value, keeping parenthetical nuances separate.
   const differs=new Set(indices.map(i=>r.values[i].text)).size>1;
   const text=normalize([r.label,...indices.map(i=>r.values[i].text+' '+r.values[i].note)].join(' '));
   return (!state.differences||differs)&&(!state.query||text.includes(normalize(state.query)));
  });
  count+=rows.length;
  const isHidden=!rows.length;
  const headers=indices.map(i=>{const f=FRAMEWORKS[i];return `<th scope="col" class="${f.className}"><div class="framework-heading">${f.logo?`<img class="framework-logo ${f.className}" src="${f.logo}" alt="Logo ${i===2?'GitHub':f.short}" width="29" height="29">`:`<span class="framework-glyph" aria-hidden="true">${f.glyph}</span>`}<div><div class="framework-name">${f.name}</div><div class="framework-type">${f.type}</div></div></div></th>`;}).join('');
  const body=rows.map(r=>`<tr><th scope="row">${escapeHTML(r.label)}</th>${indices.map(i=>{const c=r.values[i];return `<td class="kind-${c.kind} ${i>2?'control-cell':''}"><span class="mobile-framework" aria-hidden="true">${escapeHTML(FRAMEWORKS[i].name)}</span><span class="cell-main">${c.kind==='yes'?'<span class="cell-marker" aria-hidden="true">✓</span>':c.kind==='partial'?'<span class="cell-marker" aria-hidden="true">◒</span>':''}${escapeHTML(c.text)}</span>${c.note?`<span class="cell-note">(${escapeHTML(c.note)})</span>`:''}</td>`;}).join('')}</tr>`).join('');
  return `<section class="dimension" id="${s.id}" aria-labelledby="title-${s.id}" ${isHidden?'hidden':''}><div class="dimension-heading"><div class="dimension-title"><span class="dimension-number" aria-hidden="true">${String(index+1).padStart(2,'0')}</span><div><h2 id="title-${s.id}">${s.title}</h2><p class="dimension-question">${s.question}</p></div></div><span class="row-count">${rows.length} ASPECTOS</span></div><p class="swipe-hint">${FRAMEWORKS.length===2?'Ambos enfoques, lado a lado en cada aspecto.':'Desliza la tabla para comparar los enfoques <span aria-hidden="true">↔</span>'}</p><div class="table-scroll" role="region" aria-label="Tabla: ${s.title}.${FRAMEWORKS.length>2?' Desplazamiento horizontal disponible.':''}" tabindex="0"><table class="comparison-table"><caption>${s.title} — comparación de ${indices.length} enfoques</caption><colgroup><col class="criterion-col">${indices.map(()=>'<col>').join('')}</colgroup><thead><tr><th scope="col" class="criterion-heading">Aspecto a comparar</th>${headers}</tr></thead><tbody>${body}</tbody></table></div><div class="insights"><div class="insights-label">3 IDEAS CLAVE</div><div class="insights-grid">${s.insights.map(([title,body])=>`<article class="insight"><h3>${title}</h3><p>${body}</p></article>`).join('')}</div></div><div class="section-sources"><span>Fuentes:</span>${FRAMEWORKS.length>2?'<span>Análisis del plugin LKS-SDD</span>':''}${s.sources.slice(0,3).map(key=>sourceLink(SOURCES[key])).join('')}</div></section>`;
 }).join('');
 document.getElementById('result-count').textContent=`${count} de ${total} aspectos`;
 document.getElementById('empty').hidden=count>0;
 nav.querySelectorAll('a').forEach(a=>{const section=document.querySelector(a.getAttribute('href'));a.hidden=section.hidden;});
 scheduleNavigation();
}
function setMode(sddOnly){state.sddOnly=sddOnly;document.getElementById('all-mode')?.setAttribute('aria-pressed',String(!sddOnly));document.getElementById('sdd-mode')?.setAttribute('aria-pressed',String(sddOnly));render();}
document.getElementById('all-mode')?.addEventListener('click',()=>setMode(false));
document.getElementById('sdd-mode')?.addEventListener('click',()=>setMode(true));
document.getElementById('differences').addEventListener('change',event=>{state.differences=event.target.checked;render();});
document.getElementById('details').addEventListener('change',event=>{state.details=event.target.checked;document.body.classList.toggle('hide-details',!state.details);});
document.getElementById('search').addEventListener('input',event=>{state.query=event.target.value.trim();render();});
document.getElementById('reset').addEventListener('click',()=>{state.query='';state.differences=false;document.getElementById('search').value='';document.getElementById('differences').checked=false;setMode(false);});
document.getElementById('print').addEventListener('click',()=>window.print());
render();
document.querySelector('.hero').classList.add('reveal');
