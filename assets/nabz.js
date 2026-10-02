/* NABZ Tools shared UI: theme, copy, toast, digit helpers */
(function(){
var d=document,b=d.body,K='nabz-theme';
function apply(m){b.classList.toggle('dark',m==='dark');b.classList.toggle('light',m==='light');var t=d.getElementById('themeToggle');if(t){t.textContent=m==='dark'?'☀':'☾';t.setAttribute('aria-pressed',m==='dark'?'true':'false')}}
var s=null;try{s=localStorage.getItem(K)}catch(e){}
apply(s||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'));
var tg=d.getElementById('themeToggle');if(tg)tg.addEventListener('click',function(){var m=b.classList.contains('dark')?'light':'dark';apply(m);try{localStorage.setItem(K,m)}catch(e){}});
var box;function toast(msg){if(!box){box=d.createElement('div');box.className='nz-toast';box.setAttribute('role','status');b.appendChild(box)}box.textContent=msg;box.classList.add('show');clearTimeout(box._t);box._t=setTimeout(function(){box.classList.remove('show')},1800)}
function copy(txt){if(!txt){toast('چیزی برای کپی نیست');return}(navigator.clipboard?navigator.clipboard.writeText(txt):Promise.reject()).then(function(){toast('کپی شد ✓')},function(){var a=d.createElement('textarea');a.value=txt;b.appendChild(a);a.select();try{d.execCommand('copy');toast('کپی شد ✓')}catch(e){toast('کپی نشد')}a.remove()})}
d.addEventListener('click',function(e){var x=e.target.closest('[data-copy]');if(!x)return;var el=d.querySelector(x.getAttribute('data-copy'));copy(el?(el.value!==undefined&&el.tagName!=='DIV'&&el.tagName!=='STRONG'&&el.tagName!=='P'?el.value:el.textContent).trim():'')});
var FA='۰۱۲۳۴۵۶۷۸۹',AR='٠١٢٣٤٥٦٧٨٩';
function en(v){return String(v==null?'':v).replace(/[۰-۹]/g,function(c){return FA.indexOf(c)}).replace(/[٠-٩]/g,function(c){return AR.indexOf(c)})}
function num(v){var x=parseFloat(en(v).replace(/[,٬،\s]/g,''));return isFinite(x)?x:NaN}
function fa(v){return String(v).replace(/\d/g,function(c){return FA[c]})}
function money(v,dec){if(!isFinite(v))return '—';return fa(Number(v).toLocaleString('en-US',{maximumFractionDigits:dec==null?0:dec}))}
window.NZ={toast:toast,copy:copy,en:en,num:num,fa:fa,money:money};
d.querySelectorAll('input[data-money]').forEach(function(i){i.addEventListener('input',function(){var raw=en(i.value).replace(/[^\d.]/g,'');if(!raw){i.value='';return}var p=raw.split('.');i.value=Number(p[0]).toLocaleString('en-US')+(p.length>1?'.'+p[1]:'')})});
})();
