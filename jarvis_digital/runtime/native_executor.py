"""Bounded native Maestri executor: original evidence -> canonical gate -> build -> browser QA -> independent reviewer."""
from pathlib import Path
import json,datetime,hashlib,time,re,subprocess,sys,shutil,threading,http.server,functools,urllib.parse,ipaddress,os
B=Path(__file__).resolve().parent.parent
ROOT=B.parents[2];QUEUE=B/'runtime/queue';OUT=B/'runtime/results'
CLI=r'C:\Users\Giorgio\AppData\Local\Programs\Maestri\resources\cli\maestri.exe'
NODE=r'C:\Program Files\nodejs\node.exe'
HUNTER='690a34da-5627-44f7-ae45-0da4dbccbb18';CREATOR='19d88dc0-c0bd-4d2c-8d87-1b08fe341c30';REVIEWER='daa7235d-92b3-4941-b48d-7bcd684dc453'
sys.path.insert(0,str(ROOT/'JARVIS-Orquestracao/ChatGPTBridge'))
sys.path.insert(0,str(B/'engine'))
import bridge
from orchestrator import PipelineOrchestrator
from pages_packager import PagesPackager
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');t.replace(p)
def path(v):
 p=(B/str(v)).resolve()
 if not p.is_relative_to(B.resolve()):raise ValueError('PATH_OUTSIDE_MISSION')
 return p
def slug(v):
 if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',v or ''):raise ValueError('INVALID_SLUG')
 return v
def public_url(v,instagram=False):
 u=urllib.parse.urlsplit(v);h=(u.hostname or '').lower()
 if u.scheme!='https' or not h or u.username or u.password or u.port not in (None,443) or h in ('localhost','metadata.google.internal') or '.' not in h:raise ValueError('PUBLIC_HTTPS_REQUIRED')
 try:
  ip=ipaddress.ip_address(h)
  if not ip.is_global:raise ValueError('PRIVATE_HOST')
 except ValueError:
  if re.fullmatch(r'[\d.:]+',h):raise ValueError('INVALID_IP')
 if any(x in u.path.lower() for x in ['/direct','/inbox','/accounts','/login','/settings','/logout']):raise ValueError('PRIVATE_OR_ACCOUNT_PATH')
 if instagram and (h not in ('instagram.com','www.instagram.com') or u.query or u.fragment):raise ValueError('EXACT_INSTAGRAM_PUBLIC_URL_REQUIRED')
 return v
def cli(*args):
 r=subprocess.run([CLI,*args],capture_output=True,text=True,encoding='utf8',errors='replace',timeout=45)
 if r.returncode:raise RuntimeError(r.stderr[-600:] or r.stdout[-600:])
 return r.stdout
def tell(t,text):
 return bridge.api_factory()('/api/terminals/'+t+'/prompt',{'text':text})
def hashes(folder):
 return {p.relative_to(folder).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file()}
def capture_public(job,dest):
 from playwright.sync_api import sync_playwright
 rows=[]
 with sync_playwright() as p:
  browser=p.firefox.launch()
  for i,url in enumerate(job['urls']):
   public_url(url);page=browser.new_page(viewport={'width':1440,'height':900})
   row={'requested_url':url,'captured_at':now(),'status':'ORIGINAL_BROWSER_CAPTURE'}
   try:
    r=page.goto(url,wait_until='domcontentloaded',timeout=25000);page.wait_for_timeout(2200)
    row.update(url=page.url,http=r.status if r else None,title=page.title(),text=page.locator('body').inner_text(timeout=4000),links=page.locator('a[href]').evaluate_all('(es)=>es.map(e=>({href:e.href,text:e.innerText}))'))
    if '/sorry/' in page.url or 'Our systems have detected unusual traffic' in row['text']:row['status']='CHALLENGE_NOT_SEARCH_RESULTS'
    (dest/(str(i)+'.html')).write_text(page.content(),encoding='utf8');page.screenshot(path=str(dest/(str(i)+'.png')),full_page='google.com/maps' not in page.url)
   except Exception as e:row.update(status='CAPTURE_FAILED',error=str(e)[:400])
   save(dest/(str(i)+'.json'),row);rows.append(row);page.close()
  browser.close()
 return {'captures':rows,'hashes':hashes(dest),'automatic_qualification':False}
def capture_instagram(job,dest):
 rows=[];portal='Instagram - Curadoria de Sites'
 for i,url in enumerate(job['urls']):
  public_url(url,True);cli('portal','navigate',portal,url);time.sleep(2)
  html=cli('portal','html',portal);snapshot=cli('portal','snapshot',portal)
  (dest/(str(i)+'.html')).write_text(html,encoding='utf8');(dest/(str(i)+'-snapshot.txt')).write_text(snapshot,encoding='utf8')
  try:shot=cli('portal','screenshot',portal)
  except Exception as e:shot='SCREENSHOT_UNAVAILABLE: '+str(e)
  (dest/(str(i)+'-screenshot-receipt.txt')).write_text(shot,encoding='utf8')
  for match in re.findall(r'[A-Za-z]:[\\/][^\r\n"]+?\.png',shot):
   f=Path(match.strip())
   if f.is_file():shutil.copy2(f,dest/(str(i)+'.png'));break
  rows.append({'url':url,'captured_at':now(),'screenshot_available':(dest/(str(i)+'.png')).exists(),'status':'SOURCE_UNAVAILABLE' if 'Esta página não está disponível' in snapshot else 'NATIVE_PORTAL_ORIGINAL','rights':'PUBLIC_REFERENCE_OR_OFFICIAL_EMBED_ONLY','private_data_accessed':False})
 return {'captures':rows,'hashes':hashes(dest),'automatic_qualification':False}
def evidence_preflight(candidate):
 def walk(value):
  if isinstance(value,dict):
   if all(k in value for k in ('file','url','sha256')):
    p=Path(value['file']);p=p if p.is_absolute() else ROOT/p;p=p.resolve()
    if not p.is_relative_to(ROOT.resolve()) or not p.is_file():raise ValueError('EVIDENCE_FILE_UNAVAILABLE')
    content=p.read_text(encoding='utf8',errors='replace').lower()
    blocked=['our systems have detected unusual traffic','esta página não está disponível','verify you are human','checking your browser before accessing']
    if any(marker in content for marker in blocked):raise ValueError('EVIDENCE_IS_CHALLENGE_OR_UNAVAILABLE: '+str(p))
    meta=p.with_suffix('.json')
    if p.suffix=='.html' and meta.is_file():
     m=json.loads(meta.read_text(encoding='utf8'));url=str(m.get('url',''))
     if '/sorry/' in url or m.get('status')=='CAPTURE_FAILED' or m.get('http',200) is None or m.get('http',200)>=400:raise ValueError('EVIDENCE_CAPTURE_FAILED: '+str(p))
   for v in value.values():walk(v)
  elif isinstance(value,list):
   for v in value:walk(v)
 walk(candidate.get('presence_audit',{}))
 import unicodedata
 def qnorm(v):return re.sub(r'[^a-z0-9]+',' ',''.join(c for c in unicodedata.normalize('NFKD',str(v)).lower() if not unicodedata.combining(c))).strip()
 for row in candidate.get('presence_audit',{}).get('name_searches',[]):
  evidence=row.get('evidence',{});p=Path(evidence.get('file',''));p=p if p.is_absolute() else ROOT/p
  actual=[]
  if p.suffix=='.json':
   data=json.loads(p.read_text(encoding='utf8'))
   if data.get('tool')=='search_service_web_run.system1_search_query' and data.get('original_response'):actual=data.get('queries',[])
  else:
   meta=p.with_suffix('.json')
   if meta.is_file():
    data=json.loads(meta.read_text(encoding='utf8'));u=urllib.parse.urlsplit(data.get('requested_url',''));params=urllib.parse.parse_qs(u.query)
    actual=params.get('q',[]) or params.get('query',[])
    if not actual and '/maps/search/' in u.path:actual=[urllib.parse.unquote_plus(u.path.split('/maps/search/',1)[1].strip('/'))]
  if qnorm(row.get('query','')) not in [qnorm(q) for q in actual]:raise ValueError('SEARCH_QUERY_NOT_EXECUTED_AS_CLAIMED: '+str(row.get('purpose')))


def qualify(job,dest):
 candidate=json.loads(path(job['candidate']).read_text(encoding='utf-8-sig'))
 evidence_preflight(candidate)
 g=PipelineOrchestrator(db_path=B/'state/pipeline.sqlite',workspace_root=ROOT,canonical_gate_path=B.parent/'automacoes/JARVIS-Propostas/lead_presence_gate.py').process_candidate(candidate)
 strict=g['eligible_for_production'] and any(r.get('criterion')=='SEM_SITE_CONFIRMADO' for r in g['verdict'].get('reasons',[]))
 g['mission_eligible']=strict;save(dest/'gate.json',g)
 if strict:
  tell(CREATOR,'LEAD QUALIFICADO POR EXECUTOR CANONICO: '+str(path(job['candidate']))+'. Veredito real: '+str(dest/'gate.json')+'. Comece agora curadoria/brief individual e desenvolvimento no piso aprovado. Use runtime/EXECUTOR_CONTRACT.md; escreva jobs BUILD_QA quando pronto. Nao aguarde novo pedido humano. Midia real com fontes e incorporacoes oficiais; nao invente fatos. Sem envio comercial.')
 return g
def qa_site(dist,dest,video_ids,url=None):
 from playwright.sync_api import sync_playwright
 class Handler(http.server.SimpleHTTPRequestHandler):
  def log_message(self,*a):pass
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(dist)))
 threading.Thread(target=server.serve_forever,daemon=True).start();rows=[]
 try:
  with sync_playwright() as p:
   browser=p.firefox.launch()
   for name,w,h in [('desktop',1440,900),('tablet',768,1024),('mobile',390,844)]:
    page=browser.new_page(viewport={'width':w,'height':h});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    response=page.goto(url or 'http://127.0.0.1:'+str(server.server_port),wait_until='domcontentloaded');page.wait_for_timeout(8000)
    page.screenshot(path=str(dest/(name+'_hero.png')));play=[]
    for vid in video_ids:
     frame=next((f for f in page.frames if vid in f.url),None)
     if not frame:play.append({'id':vid,'progressed':False});continue
     v=frame.locator('video').first
     try:
      v.scroll_into_view_if_needed(timeout=3000);before=v.evaluate('(v)=>v.currentTime')
      v.evaluate('(v)=>{v.muted=true;return v.play()}');page.wait_for_timeout(1800)
      after=v.evaluate('(v)=>v.currentTime');play.append({'id':vid,'progressed':after>before,'before':before,'after':after})
     except Exception as e:play.append({'id':vid,'progressed':False,'error':str(e)[:100]})
    state=page.evaluate('({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,h1:document.querySelectorAll("h1").length,brokenImages:[...document.images].filter(i=>!i.complete||i.naturalWidth===0).length})')
    imgs=[]
    for f in page.frames:
     if 'instagram.com/' in f.url:imgs.append(f.locator('img').evaluate_all('(es)=>es.filter(i=>i.complete&&i.naturalWidth>250).length'))
    page.screenshot(path=str(dest/(name+'_full.png')),full_page=True)
    body=page.locator('body').inner_text();robots=page.locator('meta[name=robots]').get_attribute('content') or '';policy='noindex' in robots.lower() and bool(re.search(r'demonstra[çc][ãa]o (?:conceitual )?n[ãa]o oficial',body,re.I))
    menu={'tested':False}
    if name=='mobile':
     button=page.get_by_role('button',name=re.compile('abrir menu',re.I))
     if button.count():
      button.first.click();page.keyboard.press('Escape');menu={'tested':True,'expanded_after_escape':button.first.get_attribute('aria-expanded')}
    masks=page.locator('.media-mask').evaluate_all('(es)=>es.map(e=>({overflow:getComputedStyle(e).overflow,iy:parseFloat(getComputedStyle(e).getPropertyValue("--iy")),width:e.clientWidth,height:e.clientHeight}))')
    broken_anchors=page.locator('a[href^="#"]').evaluate_all('(es)=>es.map(a=>a.getAttribute("href")).filter(h=>h.length>1&&!document.getElementById(h.slice(1)))')
    crop_pass=len(masks)>=3 and all(m['overflow']=='hidden' and m['iy'] is not None and m['iy']<=-50 for m in masks)
    menu_pass=name!='mobile' or (menu.get('tested') and menu.get('expanded_after_escape')=='false')
    rows.append({'name':name,'media_masks':masks,'crop_passed':crop_pass,'broken_anchors':broken_anchors,'demo_policy_passed':policy,'mobile_menu':menu,'state':state,'errors':errors,'http':response.status,'embed_images':imgs,'playback':play,'technical_passed':crop_pass and menu_pass and not broken_anchors and policy and response.status==200 and state['width']==state['scrollWidth'] and state['h1']==1 and state['brokenImages']==0 and not errors and bool(imgs) and all(i>0 for i in imgs) and bool(play) and all(v['progressed'] for v in play)})
    page.close()
   browser.close()
 finally:server.shutdown()
 return {'at':now(),'technical_passed':all(r['technical_passed'] for r in rows),'viewports':rows,'screenshots':hashes(dest),'visual_approved':False,'requires_independent_visual_review':True}
def build(job,dest):
 site=path(job['site'])
 if not site.is_relative_to((B/'sites').resolve()) or site.name=='studio-962-real-v3':raise ValueError('NEW_SITE_VERSION_REQUIRED')
 candidate=json.loads(path(job['candidate']).read_text(encoding='utf-8-sig'))
 evidence_preflight(candidate)
 gate=PipelineOrchestrator(db_path=B/'state/pipeline.sqlite',workspace_root=ROOT,canonical_gate_path=B.parent/'automacoes/JARVIS-Propostas/lead_presence_gate.py').process_candidate(candidate)
 if not gate['eligible_for_production'] or not any(r.get('criterion')=='SEM_SITE_CONFIRMADO' for r in gate['verdict']['reasons']):raise ValueError('CANONICAL_GATE_BLOCKED')
 base=B/'sites/studio-962-real-v3'
 if (site/'package-lock.json').read_bytes()!=(base/'package-lock.json').read_bytes():raise ValueError('REUSE_APPROVED_DEPENDENCIES; new dependencies require review')
 if not (site/'node_modules').exists():
  import _winapi
  _winapi.CreateJunction(str(base/'node_modules'),str(site/'node_modules'))
 logs=[]
 for args in [[NODE,str(base/'node_modules/typescript/bin/tsc')],[NODE,str(base/'node_modules/vite/bin/vite.js'),'build']]:
  r=subprocess.run(args,cwd=site,capture_output=True,text=True,encoding='utf8',errors='replace',timeout=120);logs.append(r.stdout+r.stderr)
  if r.returncode:(dest/'build.log').write_text('\\n'.join(logs),encoding='utf8');raise RuntimeError('BUILD_FAILED '+logs[-1][-1200:])
 (dest/'build.log').write_text('\\n'.join(logs),encoding='utf8')
 clean,errors,files=PagesPackager.audit_dist_files(site/'dist')
 if not clean:raise ValueError('DIST_AUDIT_FAILED '+str(errors))
 qa=qa_site(site/'dist',dest,job.get('video_ids',[]));qa['dist_hashes']={f['file']:f['sha256'] for f in files};qa['source_hashes']=hashes(site/'src');save(dest/'qa.json',qa)
 if qa['technical_passed']:
  tell(REVIEWER,'REVISAO INDEPENDENTE NECESSARIA AGORA: site '+str(site)+', candidato '+str(path(job['candidate']))+', QA real '+str(dest/'qa.json')+'. Inspecione 1440/768/390 e compare baseline aprovada. Execute ferramentas de imagem disponiveis. Nao dar nota por build, nao inventar hash. Grave '+str(site/'INDEPENDENT_REVIEW.json')+' com factual_approved,visual_approved,reviewed_by,verdict,dist_hashes atuais e arquivos de capturas inspecionados. Se aprovado, apos inspecao visual real, grave job PUBLISH conforme runtime/EXECUTOR_CONTRACT.md com site/candidate/qa/video_ids e informe baseline_compared:true, score fundamentado>=90. Se nao puder inspecionar imagens, registre pendente sem nota. Corrija via Criador se falhar. Nenhum envio comercial.')
 else:tell(CREATOR,'BUILD/QA executados. Corrija falhas reais em '+str(dest/'qa.json')+' e crie novo job BUILD_QA com ID novo; nao copiar QA anterior.')
 return qa
def publish(job,dest):
 site=path(job['site']);candidate=json.loads(path(job['candidate']).read_text(encoding='utf-8-sig'));s=slug(candidate['slug'])
 if s=='studio-962':raise ValueError('APPROVED_BASELINE_PRESERVED')
 gate=PipelineOrchestrator(db_path=B/'state/pipeline.sqlite',workspace_root=ROOT,canonical_gate_path=B.parent/'automacoes/JARVIS-Propostas/lead_presence_gate.py').process_candidate(candidate)
 if not gate['eligible_for_production'] or not any(r.get('criterion')=='SEM_SITE_CONFIRMADO' for r in gate['verdict']['reasons']):raise ValueError('GATE_BLOCKED')
 qa=json.loads(path(job['qa']).read_text(encoding='utf8'));review=json.loads((site/'INDEPENDENT_REVIEW.json').read_text(encoding='utf8'))
 current=hashes(site/'dist')
 if not qa.get('technical_passed') or qa.get('dist_hashes')!=current or qa.get('source_hashes')!=hashes(site/'src'):raise ValueError('STALE_OR_FAILED_QA')
 if review.get('verdict')!='APROVADO' or not review.get('visual_approved') or not review.get('factual_approved') or not review.get('reviewed_by') or not review.get('baseline_compared') or review.get('score',0)<90 or review.get('dist_hashes')!=current:raise ValueError('CURRENT_INDEPENDENT_REVIEW_REQUIRED')
 inspected=review.get('inspected_files',[])
 if not inspected:raise ValueError('INSPECTED_CAPTURES_REQUIRED')
 for item in inspected:
  f=Path(item['path']);f=f if f.is_absolute() else ROOT/f
  if not f.resolve().is_relative_to(ROOT.resolve()) or not f.is_file() or hashlib.sha256(f.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('REVIEW_EVIDENCE_HASH_MISMATCH')
 clean,errors,manifest=PagesPackager.audit_dist_files(site/'dist')
 if not clean:raise ValueError('DIST_FORBIDDEN_FILES '+str(errors))
 media=json.loads((site/'REAL_MEDIA_MANIFEST.json').read_text(encoding='utf8'))
 rights,errors=PagesPackager(workspace_root=ROOT).verify_media_manifest(manifest,media)
 if not rights:raise ValueError('MEDIA_FILE_RIGHTS_FAILED '+str(errors))
 previous=json.loads((B/'hosting/CURRENT_RELEASE.json').read_text(encoding='utf8'));old=Path(previous['release_dir'])
 text=(old/'_worker.js').read_text(encoding='utf8');registry=json.loads(re.search(r'const registry\s*=\s*(\{.*\});\s*export default',text,re.S).group(1))
 if s in registry:raise ValueError('SLUG_ALREADY_PUBLISHED; explicit revision required')
 version=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+s
 release=B/'hosting/releases'/version;release.mkdir()
 for oldslug,record in registry.items():
  for file,sha in record['files'].items():
   source=old/oldslug/file
   if hashlib.sha256(source.read_bytes()).hexdigest()!=sha:raise ValueError('PREVIOUS_RELEASE_HASH_MISMATCH')
   target=release/oldslug/file;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
 for file,sha in current.items():
  target=release/s/file;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(site/'dist'/file,target)
 expires=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(days=7)).isoformat()
 registry[s]={'active':True,'expires_at':expires,'files':current,'status':'INDEPENDENT_REVIEW_APPROVED'}
 (release/'_worker.js').write_text((B/'hosting/expiry_worker.mjs').read_text(encoding='utf8')+'\nconst registry='+json.dumps(registry)+';\nexport default {fetch:createFetch(registry)};',encoding='utf8')
 (release/'_routes.json').write_text(json.dumps({'version':1,'include':['/*'],'exclude':[]}),encoding='utf8')
 command=[os.environ.get('COMSPEC',r'C:\Windows\System32\cmd.exe'),'/d','/c',r'C:\Users\Giorgio\AppData\Roaming\npm\wrangler.cmd','pages','deploy',str(release),'--project-name','jarvis-digital','--branch','main']
 r=subprocess.run(command,capture_output=True,text=True,encoding='utf8',errors='replace',timeout=150)
 (dest/'deploy.log').write_text(r.stdout+r.stderr,encoding='utf8')
 if r.returncode:raise RuntimeError('DEPLOY_FAILED; inspect log before retry')
 previous.update(release_dir=str(release),composition_version=version,last_added_slug=s)
 save(B/'hosting/CURRENT_RELEASE.json',previous)
 url='https://jarvis-digital.pages.dev/'+s+'/'
 public=qa_site(site/'dist',dest,job['video_ids'],url=url);save(dest/'public_qa.json',public)
 receipt={'url':url,'release_dir':str(release),'expires_at':expires,'public_technical_passed':public['technical_passed'],'status':'PUBLISHED_TESTED' if public['technical_passed'] else 'PUBLISHED_QA_FAILED','no_outreach':True}
 save(site/'PUBLIC_RELEASE.json',receipt)
 return receipt
def run_job(job,dest):
 kind=job.get('kind');slug(job['job_id'])
 if kind.startswith('CAPTURE_'):
  if not isinstance(job.get('urls'),list) or not 1<=len(job['urls'])<=6:raise ValueError('1_TO_6_URLS_REQUIRED')
 if kind=='INIT_SITE':
  site=path(job['site']);base=B/'sites/studio-962-real-v3'
  if not site.is_relative_to((B/'sites').resolve()) or site.name.startswith('studio-962'):raise ValueError('NEW_SITE_ONLY')
  site.mkdir(parents=True,exist_ok=True);(site/'src').mkdir(exist_ok=True);copied=[]
  for name in ['package.json','package-lock.json','postcss.config.js','tsconfig.json','vite.config.ts','tailwind.config.js','index.html']:
   if not (site/name).exists():shutil.copy2(base/name,site/name);copied.append(name)
  if not (site/'node_modules').exists():
   import _winapi
   _winapi.CreateJunction(str(base/'node_modules'),str(site/'node_modules'))
  return {'site':str(site),'copied_approved_tooling_only':copied,'source_not_cloned':True}
 if kind=='PRIORITY_HANDOFF':
  names={'creator':(CREATOR,'JARVIS Criador de Sites'),'hunter':(HUNTER,'JARVIS - Renda Hunter'),'reviewer':(REVIEWER,'JARVIS - SENTINELA')}
  tid,name=names[job['target']];message=path(job['message_file']).read_text(encoding='utf8');reply=tell(tid,message)
  try:raw=cli('ask',name,'--raw',r'\em')
  except Exception as e:raw='PRIORITY_KEY_UNAVAILABLE: '+str(e)
  return {'dispatch':reply,'priority_result':raw[-300:],'no_process_restart':True}
 if kind=='CAPTURE_PUBLIC':return capture_public(job,dest)
 if kind=='CAPTURE_INSTAGRAM':return capture_instagram(job,dest)
 if kind=='QUALIFY':return qualify(job,dest)
 if kind=='BUILD_QA':return build(job,dest)
 if kind=='PUBLISH':return publish(job,dest)
 raise ValueError('UNSUPPORTED_JOB_KIND')
def main():
 QUEUE.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
 lock=B/'runtime/executor.lock'
 try:fd=os.open(str(lock),os.O_CREAT|os.O_EXCL|os.O_WRONLY)
 except FileExistsError:raise SystemExit('EXECUTOR_ALREADY_RUNNING_OR_STALE_LOCK; inspect before recovery')
 os.write(fd,str(os.getpid()).encode());os.close(fd)
 try:
  while not (B/'runtime/STOP').exists():
   save(B/'runtime/heartbeat.json',{'at':now(),'pid':os.getpid(),'status':'RUNNING','mode':'BOUNDED_NATIVE_EXECUTOR'})
   for request in sorted(QUEUE.glob('*.json')):
    result=OUT/(request.stem+'.json')
    if result.exists():continue
    
    try:job=json.loads(request.read_text(encoding='utf-8-sig'))
    except Exception as e:save(result,{'status':'INVALID_REQUEST','error':str(e)[:200],'finished_at':now()});continue
    if job.get('status')!='QUEUED':continue
    dest=OUT/slug(job['job_id']);dest.mkdir(exist_ok=True);job.update(status='RUNNING',started_at=now());save(request,job)
    try:out={'status':'COMPLETED','result':run_job(job,dest)}
    except Exception as e:out={'status':'FAILED','error_type':type(e).__name__,'error':str(e)[:1600]}
    if out['status']=='FAILED' and job.get('kind') in ('BUILD_QA','PUBLISH'):
     try:tell(CREATOR,'EXECUTOR FALHOU: '+str(dest)+' '+out.get('error','')+'. Corrija agora e crie job novo; nao aguarde supervisor. Contrato runtime/EXECUTOR_CONTRACT.md.')
     except Exception:pass
    out.update(job_id=job['job_id'],kind=job['kind'],finished_at=now());save(result,out);job.update(status=out['status'],finished_at=now());save(request,job);print(json.dumps({'job_id':job['job_id'],'status':out['status']}),flush=True)
    if job.get('notify_hunter'):
     try:tell(HUNTER,'EXECUTOR RESULTADO REAL '+str(result)+'. Leia arquivos originais em '+str(dest)+', reconcilie candidato/gate; nao aguarde supervisor. Escreva proximo job no contrato.')
     except Exception as e:save(dest/'notification-error.json',{'error':str(e)[:200],'status':'DO_NOT_RESEND_BLINDLY'})
    event={'event_id':'factory-executor-'+job['job_id'],'timestamp':now(),'mission_id':'jarvis-digital-20261103','agent':'native-executor','type':'FACTORY_JOB','status':out['status'],'entity':job['job_id'],'evidence':str(result),'next_action':'Follow executor contract; no outreach'}
    with (B.parent/'state/obsidian_events.jsonl').open('a',encoding='utf8') as f:f.write(json.dumps(event,ensure_ascii=False)+'\n')
   time.sleep(2)
 finally:lock.unlink(missing_ok=True)
if __name__=='__main__':main()