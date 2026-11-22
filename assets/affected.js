// Renders the curated "papers that use the affected data" list on an entry page.
(function(){
  const box=document.getElementById('affected'); if(!box) return;
  const id=box.dataset.entry, esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  fetch('/data/affected.json').then(r=>r.json()).then(d=>{
    const a=(d.entries||{})[id]; if(!a||!(a.papers||[]).length) return;
    const ps=[...a.papers].sort((x,y)=>y.year-x.year);
    const search='https://openalex.org/works?filter='+encodeURIComponent('title_and_abstract.search:'+a.query+',publication_year:'+a.years);
    box.innerHTML=`<h2>Papers that use the affected data (${ps.length})</h2>
<p class="meta" style="display:block">Listed because the paper uses the affected data for the affected region and period: ${esc(a.criterion)} <b>The effect on each paper has not been assessed</b>, and its conclusions may well hold. Authors are welcome to comment below or <a href="/report.html?kind=response">write to us</a>. Selected from a literature search (<a href="${esc(search)}">run it on OpenAlex</a>); reviewed ${esc(a.reviewed)}. Know of another paper? <a href="/report.html?kind=comment">Tell us</a>.</p>
${ps.map(p=>`<article class="entry"><h3><a href="/doi.html?doi=${encodeURIComponent(p.doi)}">${esc(p.title)}</a></h3>
<div class="meta"><span>${esc(p.authors)}</span><span>${esc(p.year)}</span><span>${esc(p.venue)}</span><a href="https://doi.org/${esc(p.doi)}">doi:${esc(p.doi)}</a></div>
<p style="margin:8px 0 0"><b>Uses:</b> ${esc(p.uses)}. <b>Period:</b> ${esc(p.period)}. <span class="meta" style="display:inline">Effect not assessed.</span></p></article>`).join('')}`;
  }).catch(()=>{});
})();
