"""Dedicated read-only Instagram curation queue. Uses only the explicitly created JARVIS Digital profile."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import json,datetime,time,hashlib,re,urllib.parse,os
ROOT=Path(__file__).resolve().parent
PROFILE=ROOT/'browser_profile_jarvis_digital'
QUEUE=ROOT/'queue';OUTPUT=ROOT/'curation';STATUS=ROOT/'browser_session_status.json'
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(path,value):
 temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8');temp.replace(path)
def allowed(url):
 u=urllib.parse.urlsplit(str(url))
 if u.scheme!='https' or u.hostname not in ['www.instagram.com','instagram.com'] or u.username or u.password or u.query or u.fragment:return False
 parts=[x for x in u.path.split('/') if x]
 if len(parts)==1:return bool(re.fullmatch(r'[A-Za-z0-9._]{1,30}',parts[0])) and parts[0].lower() not in ['direct','accounts','explore','stories','reels','p','reel']
 return (len(parts)==2 and parts[0] in ['p','reel'] and bool(re.fullmatch(r'[A-Za-z0-9_-]+',parts[1]))) or (len(parts)==3 and parts[1] in ['p','reel'] and bool(re.fullmatch(r'[A-Za-z0-9._]{1,30}',parts[0])) and bool(re.fullmatch(r'[A-Za-z0-9_-]+',parts[2])))
def collect(page,job):
 urls=job.get('urls',[])
 if not isinstance(urls,list) or not 1<=len(urls)<=4 or not all(allowed(u) for u in urls):raise ValueError('Only1..4 exact public Instagram profile/post URLs; no private paths')
 jobid=job['job_id']
 if not re.fullmatch(r'[a-z0-9-]{3,80}',jobid):raise ValueError('Invalid job ID')
 dest=OUTPUT/jobid;dest.mkdir(parents=True,exist_ok=True);results=[]
 for i,url in enumerate(urls):
  response=page.goto(url,wait_until='domcontentloaded',timeout=25000);page.wait_for_timeout(1800)
  main=page.locator('main')
  blocked='/accounts/' in page.url or main.count()==0 or page.locator('input[type=password]').count()>0
  if blocked:
   results.append({'requested_url':url,'resolved_url':page.url.split('?')[0],'at':now(),'status':'LOGIN_OR_UNAVAILABLE','rights':'REFERENCE_ONLY'})
   break
  title=page.title();html=main.first.inner_html(timeout=4000);text=main.first.inner_text(timeout=4000)
  links=main.locator('a[href]').evaluate_all('(es)=>es.map(e=>({href:e.getAttribute("href"),alt:e.querySelector("img")?.alt})).filter(x=>/\\/(p|reel)\\//.test(x.href||""))')
  file=dest/(str(i)+'-main.html');file.write_text(html,encoding='utf8')
  record={'requested_url':url,'resolved_url':page.url.split('?')[0],'at':now(),'http':response.status if response else None,'title':title,'main_text':text,'public_post_links':links,'main_html_file':file.name,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'rights':'REFERENCE_ONLY; no download/rehosting authorization inferred','status':'OBSERVED_PUBLIC_MAIN','identity_verified':False,'website_absence_verified':False}
  save(dest/(str(i)+'-observation.json'),record);results.append(record)
  page.wait_for_timeout(1200)
 status='COLLECTED_REFERENCES' if len(results)==len(urls) and all(r['status']=='OBSERVED_PUBLIC_MAIN' for r in results) else 'PENDING_LOGIN_OR_SOURCE'
 return {'job_id':jobid,'at':now(),'status':status,'results':results,'no_dm':True,'no_follow':True,'no_media_download':True,'no_automatic_qualification':True}
def main():
 QUEUE.mkdir(exist_ok=True);OUTPUT.mkdir(exist_ok=True)
 with sync_playwright() as p:
  browser=p.chromium.launch_persistent_context(user_data_dir=str(PROFILE),headless=False,viewport={'width':1200,'height':850},args=['--no-first-run'])
  page=browser.pages[0] if browser.pages else browser.new_page();page.goto('https://www.instagram.com/',wait_until='domcontentloaded',timeout=25000)
  state={'created_at':now(),'purpose':'JARVIS DIGITAL BUSINESS RESEARCH','browser_profile':str(PROFILE),'independent_from_dronehub_social':True,'authentication':'NOT_VERIFIED','mode':'PUBLIC_CURATION_QUEUE; NO DM; NO FOLLOW; NO NATIVE DOWNLOAD','queue_ready':True}
  save(STATUS,state);print('JARVIS Digital independent Instagram curation queue ready.',flush=True)
  try:
   while browser.pages:
    if (ROOT/'STOP_WORKER').exists():break
    for path in sorted(QUEUE.glob('*.json')):
     if path.name.endswith('.result.json'):continue
     job=json.loads(path.read_text(encoding='utf8'));result=QUEUE/(path.stem+'.result.json')
     if result.exists():continue
     if job.get('status') not in ['QUEUED']:continue
     job['status']='RUNNING';job['started_at']=now();save(path,job)
     try:outcome=collect(page,job)
     except Exception as e:outcome={'job_id':job.get('job_id'),'status':'ERROR','at':now(),'error_type':type(e).__name__,'error':str(e)[:250]}
     save(result,outcome);job['status']=outcome['status'];job['finished_at']=now();save(path,job)
     state.update(last_job=job.get('job_id'),last_result=outcome['status'],heartbeat=now());save(STATUS,state)
     print(json.dumps({'job_id':job.get('job_id'),'status':outcome['status']},ensure_ascii=True),flush=True)
    page.wait_for_timeout(1000)
  finally:browser.close()
if __name__=='__main__':main()
