/* No framework, remote scripts, trackers, or HTML interpolation of catalog data. */
'use strict';
const $ = (id) => document.getElementById(id);
const symbols = {all:'▦', finance:'↗', research:'◎', content:'✎', video:'▷', skills:'⌘', guides:'▤'};
const licenseUrls = {'CC0-1.0':'https://creativecommons.org/publicdomain/zero/1.0/','CC-BY-4.0':'https://creativecommons.org/licenses/by/4.0/'};
let catalog, translations, lang = 'en';
const state = {category:'all', kind:'all', tier:'all', tag:'all', query:'', sort:'name'};
const t = (key) => translations[lang][key];
const note = (entry) => entry.review_i18n[lang] || entry.review;
function element(tag, className, text) { const node=document.createElement(tag); if(className) node.className=className; if(text!==undefined) node.textContent=text; return node; }
function link(text, url, className='') {const a=element('a',className,text); a.href=url; a.target='_blank'; a.rel='noopener noreferrer'; return a;}
function option(value,label) {const node=element('option','',label);node.value=value;return node;}
function localStore(value) {try {if(value) localStorage.setItem('grok-language',value);else return localStorage.getItem('grok-language');} catch {return null;}}
function setLanguage(value) {
  lang=translations[value]?value:'en';localStore(lang);$('language').value=lang;document.documentElement.lang=lang;
  document.querySelectorAll('[data-i18n]').forEach(node=>{node.textContent=t(node.dataset.i18n);});
  document.querySelectorAll('[data-i18n-aria]').forEach(node=>{node.setAttribute('aria-label',t(node.dataset.i18nAria));});
  $('search').placeholder=t('search');$('search').setAttribute('aria-label',t('search'));
  $('total-count').textContent=catalog.entries.length;$('locale-count').textContent=Object.keys(translations).length;
  $('tier').replaceChildren(option('all',t('all_tiers')),...['listed','tested','featured'].map(x=>option(x,t(x))));$('tier').value=state.tier;
  $('tag').replaceChildren(option('all',t('all_tags')),...[...new Set(catalog.entries.flatMap(x=>x.tags))].sort().map(x=>option(x,x)));$('tag').value=state.tag;
  $('sort').replaceChildren(option('name',t('sort_name')),option('new',t('sort_new')));$('sort').value=state.sort;
  $('categories').replaceChildren(...['all',...Object.keys(t('categories'))].map(key=>{
    const button=element('button','category-button');button.type='button';button.dataset.category=key;
    button.append(element('span','category-icon',symbols[key]),element('span','',key==='all'?t('all'):t('categories')[key]),element('span','category-count',catalog.entries.filter(e=>key==='all'||e.category===key).length));
    button.addEventListener('click',()=>{state.category=key;render();});return button;
  }));
  $('kinds').replaceChildren(...['all','bots','skills','guides'].map(key=>{const button=element('button','',key==='all'?t('all'):t('kinds')[key]);button.type='button';button.dataset.kind=key;button.append(element('span','tab-count',key==='all'?catalog.entries.length:catalog.counts[key]));button.addEventListener('click',()=>{state.kind=key;render();});return button;}));
  renderPicks();render();
}
function card(entry) {
  const node=element('article','card');node.dataset.category=entry.category;
  const top=element('div','card-top');const icon=element('span','card-icon',symbols[entry.category]);icon.setAttribute('aria-hidden','true');const pill=element('span','tier-pill',t(entry.tier));pill.title=t('policy_text');top.append(icon,pill);
  const title=element('h3');title.append(link(entry.name,entry.url));
  const tags=element('div','card-tags');entry.tags.forEach(tag=>{const button=element('button','tag-button',tag);button.type='button';button.setAttribute('aria-label',`${t('tag')}: ${tag}`);button.addEventListener('click',()=>{state.tag=tag;$('tag').value=tag;render();$('collection').scrollIntoView({block:'start'});});tags.append(button);});
  const bottom=element('div','card-bottom');const author=element('span','author',`${t('by')} ${entry.author.name}`);author.title=entry.author.name;
  const details=element('details','source-details');details.append(element('summary','',t('source')));const content=element('div','source-content');content.append(link(entry.source.repo,`https://github.com/${entry.source.repo}`),element('br'),link(entry.source.license,licenseUrls[entry.source.license]));
  if(entry.source.attribution) content.append(element('p','',entry.source.attribution),element('p','',entry.source.changes));
  content.append(element('p','',`${t('checked')}: ${entry.last_checked}`),element('p','',entry.language.includes('und')?t('unknown_language'):entry.language.join(', ')));
  details.append(content);bottom.append(author,details);node.append(top,title,element('p','card-review',note(entry)),tags,bottom);return node;
}
function render() {
  const query=state.query.trim().toLocaleLowerCase(lang);
  const entries=catalog.entries.filter(e=>(state.category==='all'||e.category===state.category)&&(state.kind==='all'||e.kind===state.kind)&&(state.tier==='all'||e.tier===state.tier)&&(state.tag==='all'||e.tags.includes(state.tag))&&(!query||[e.id,e.name,e.review,...Object.values(e.review_i18n),e.author.name,e.author.handle,...e.tags,t('categories')[e.category]].join(' ').toLocaleLowerCase(lang).includes(query)));
  entries.sort((a,b)=>state.sort==='new'?(b.added.localeCompare(a.added)||a.name.localeCompare(b.name,lang)):a.name.localeCompare(b.name,lang));
  $('cards').replaceChildren(...entries.map(card));$('empty').hidden=entries.length>0;$('result-count').textContent=t('results').replace('{count}',entries.length);
  $('reset').hidden=!query&&['category','kind','tier','tag'].every(key=>state[key]==='all');
  document.querySelectorAll('[data-category].category-button').forEach(node=>node.setAttribute('aria-pressed',String(node.dataset.category===state.category)));
  document.querySelectorAll('[data-kind]').forEach(node=>node.setAttribute('aria-pressed',String(node.dataset.kind===state.kind)));
}
function reset() {Object.assign(state,{category:'all',kind:'all',tier:'all',tag:'all',query:''});$('search').value='';$('tier').value='all';$('tag').value='all';render();}
function renderPicks() {
  const box=$('picks');box.replaceChildren();
  if(!catalog.picks.length) {box.append(element('h3','',t('picks_empty')),element('p','',t('picks_text')));return;}
  const latest=[...catalog.picks].sort((a,b)=>b.week.localeCompare(a.week))[0];box.append(element('h3','',latest.week));const list=element('div','pick-list');latest.entries.forEach(id=>{const e=catalog.entries.find(x=>x.id===id);if(e)list.append(link(e.name,e.url));});box.append(list);
}
async function init() {
  try {
    const responses=await Promise.all(['data/catalog.json','data/ui.json'].map(url=>fetch(url)));
    if(responses.some(r=>!r.ok)) throw new Error('Catalog request failed');
    [catalog,translations]=await Promise.all(responses.map(r=>r.json()));
    $('language').replaceChildren(...Object.entries(translations).map(([key,ui])=>option(key,ui.language_name)));
    const saved=localStore();const preferred=navigator.language;setLanguage(saved|| (translations[preferred]?preferred:preferred.startsWith('zh')?'zh-CN':preferred.startsWith('ja')?'ja':'en'));
    $('language').addEventListener('change',e=>setLanguage(e.target.value));
    $('search').addEventListener('input',e=>{state.query=e.target.value;render();});
    ['tier','tag','sort'].forEach(key=>$(key).addEventListener('change',e=>{state[key]=e.target.value;render();}));
    $('reset').addEventListener('click',reset);$('empty-reset').addEventListener('click',reset);
    document.addEventListener('keydown',e=>{if(e.key==='/'&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName)){e.preventDefault();$('search').focus();}if(e.key==='Escape'&&document.activeElement===$('search')){state.query='';$('search').value='';render();}});
  } catch(error) {
    $('load-error').hidden=false;$('load-error').textContent=translations?t('load_error'):'The catalog could not load. Refresh or browse the GitHub README.';$('result-count').textContent='';console.error(error);
  }
}
init();
