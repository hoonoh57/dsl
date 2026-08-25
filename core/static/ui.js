document.addEventListener('DOMContentLoaded',()=>{
  const top=document.querySelector('.top'), title=document.getElementById('artifact-name');
  if(!top||!title||document.getElementById('artifact-type'))return;
  const type=document.createElement('select');
  type.id='artifact-type';type.className='control artifact-type';
  type.innerHTML='<option value="indicator">지표</option><option value="signal">신호</option><option value="strength">강세·약세</option><option value="strategy" selected>전략</option><option value="drawing">사용자형식</option>';
  top.insertBefore(type,title);
  ['validate','save','discard'].forEach(id=>{const button=document.getElementById(id);if(button){button.classList.add('top-action');top.appendChild(button)}});
  const validate=document.getElementById('validate');if(validate)validate.textContent='DSL 검증 · 차트 적용';
  const save=document.getElementById('save');if(save)save.textContent='검증본 저장';
  const discard=document.getElementById('discard');if(discard)discard.textContent='후보 폐기';
  type.addEventListener('change',()=>{
    document.querySelectorAll('.cat-title').forEach(node=>node.classList.toggle('active',node.textContent.includes(type.options[type.selectedIndex].text)))
  });
  const labels={'지표':'indicator','신호':'signal','강세·약세':'strength','전략':'strategy','사용자형식':'drawing'};
  document.getElementById('tree')?.addEventListener('click',event=>{
    const category=event.target.closest('.cat-title');if(!category)return;
    const label=category.textContent.replace('▾','').trim();if(labels[label])type.value=labels[label];
  });
  const draftKey='quant-dsl-last-workspace';
  const fields=['artifact-name','artifact-type','source-type','request','prompt','response','source-code'];
  const persist=()=>localStorage.setItem(draftKey,JSON.stringify(Object.fromEntries(fields.map(id=>[id,document.getElementById(id)?.value||'']))));
  try{const saved=JSON.parse(localStorage.getItem(draftKey)||'{}');fields.forEach(id=>{const node=document.getElementById(id);if(node&&saved[id])node.value=saved[id]})}catch{}
  fields.forEach(id=>document.getElementById(id)?.addEventListener('input',persist));
  document.getElementById('generate')?.addEventListener('click',()=>setTimeout(persist,500));
  document.getElementById('validate')?.addEventListener('click',()=>setTimeout(persist,500));
});
