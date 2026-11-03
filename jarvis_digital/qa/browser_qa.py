"""Real browser QA. Never grants independent factual or visual approval."""
import argparse,datetime,hashlib,json,pathlib,urllib.parse
from playwright.sync_api import sync_playwright
VIEWPORTS={'desktop':(1440,900),'tablet':(768,1024),'mobile':(390,844)}
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def run(url,output):
 target=urllib.parse.urlsplit(url)
 if target.scheme not in ('http','https') or target.username or target.password:raise ValueError('Invalid test URL')
 if target.hostname not in ('127.0.0.1','localhost','jarvis-digital.pages.dev'):raise ValueError('QA scope is local build or Jarvis Digital only')
 output.mkdir(parents=True,exist_ok=True)
 report={'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'url':url,'mode':'REAL_BROWSER','viewports':[],'visual_approved':False,'factual_approved':False,'verdict':'PENDENTE_REVISAO_INDEPENDENTE'}
 with sync_playwright() as p:
  browser=p.firefox.launch(headless=True)
  for name,(width,height) in VIEWPORTS.items():
   context=browser.new_context(viewport={'width':width,'height':height},reduced_motion='reduce')
   page=context.new_page();errors=[];failed=[]
   page.on('pageerror',lambda error:errors.append(str(error)))
   page.on('console',lambda msg:errors.append(msg.text) if msg.type=='error' else None)
   page.on('response',lambda response:failed.append({'url':response.url,'status':response.status}) if response.status>=400 else None)
   response=page.goto(url,wait_until='networkidle',timeout=30000)
   total_height=page.evaluate('() => document.documentElement.scrollHeight')
   for y in range(0,total_height,max(200,height//2)):
    page.evaluate('(y) => window.scrollTo(0,y)',y)
    page.wait_for_timeout(60)
   for img in page.locator('img').all():
    if img.is_visible():
     img.scroll_into_view_if_needed()
     img.evaluate('(i) => i.decode().catch(() => null)')
   page.evaluate('() => window.scrollTo(0,0)')
   state=page.evaluate('''() => ({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,h1:document.querySelectorAll('h1').length,lang:document.documentElement.lang,images:[...document.images].map(i=>({src:i.currentSrc,loaded:i.complete&&i.naturalWidth>0,alt:i.getAttribute('alt')})),links:[...document.querySelectorAll('a[href]')].map(a=>({href:a.getAttribute('href'),label:a.textContent.trim()||a.getAttribute('aria-label')||'',targetExists:!a.getAttribute('href').startsWith('#')||a.getAttribute('href')==='#'||!!document.getElementById(a.getAttribute('href').slice(1))})),navigationMs:performance.getEntriesByType('navigation')[0]?.duration||null})''')
   page.keyboard.press('Tab');state['keyboard_focus']=page.evaluate('() => ({tag:document.activeElement.tagName,label:document.activeElement.textContent.trim().slice(0,100)})')
   page.evaluate('() => { if (document.activeElement instanceof HTMLElement) document.activeElement.blur(); }')
   shot=output/('screenshot_home_'+name+'.png');page.screenshot(path=str(shot),full_page=True)
   issues=[]
   if not response or response.status!=200:issues.append('HTTP_NOT_200')
   if state['scrollWidth']>width+1:issues.append('HORIZONTAL_OVERFLOW')
   if state['h1']!=1:issues.append('H1_COUNT')
   if not state['lang']:issues.append('MISSING_LANGUAGE')
   for i in state['images']:
    if not i['loaded']:issues.append('BROKEN_IMAGE')
    if i['alt'] is None:issues.append('MISSING_IMAGE_ALT')
   for link in state['links']:
    if not link['label']:issues.append('UNNAMED_LINK')
    if not link['targetExists']:issues.append('MISSING_ANCHOR')
    if not link['href'] or link['href']=='#' or 'instagram.com/https' in link['href']:issues.append('INVALID_LINK')
   if errors:issues.append('BROWSER_ERRORS')
   if failed:issues.append('FAILED_RESOURCES')
   report['viewports'].append({'name':name,'actual_width':state['width'],'height':height,'status':'PASS' if not issues else 'FAIL','issues':sorted(set(issues)),'console_errors':errors,'failed_resources':failed,'state':state,'screenshot':shot.name,'screenshot_sha256':digest(shot)})
   context.close()
  browser.close()
 report['technical_passed']=all(v['status']=='PASS' for v in report['viewports'])
 if not report['technical_passed']:report['verdict']='REPROVADO_TECNICO'
 (output/'browser_qa.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
 print(json.dumps({'technical_passed':report['technical_passed'],'verdict':report['verdict'],'viewports':len(report['viewports'])}))
 return 0 if report['technical_passed'] else 2
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('url');parser.add_argument('output',type=pathlib.Path);args=parser.parse_args();raise SystemExit(run(args.url,args.output))