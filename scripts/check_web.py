from playwright.sync_api import sync_playwright
from pathlib import Path
import json
import shutil
root=Path(__file__).resolve().parents[1]
checks=[]
with sync_playwright() as p:
 browser_path=shutil.which('chromium') or shutil.which('google-chrome')
 b=p.chromium.launch(executable_path=browser_path,headless=True)
 page=b.new_page(viewport={'width':1440,'height':1100},device_scale_factor=1)
 errors=[];external=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.on('request',lambda r:external.append(r.url) if r.url.startswith(('https://','http://')) else None)
 page.set_content((root/'web/index.html').read_text(), wait_until='load')
 def check(name,condition):
  assert condition,name
  checks.append(name)
 check('initial add disabled',page.locator('#add').is_disabled())
 page.click('#start');check('start updates recording state',page.locator('#mode').inner_text()=='演示采集中')
 page.click('#add');check('new fragment queued',page.locator('#queued').inner_text()=='1')
 page.click('#network');page.click('#add');page.click('#sync')
 check('offline queue retained',page.locator('#queued').inner_text()=='2')
 check('offline does not stop capture',page.locator('#mode').inner_text()=='演示采集中')
 page.click('#network');page.click('#sync')
 check('online sync drains queue',page.locator('#queued').inner_text()=='0')
 check('sync increments stored counter',page.locator('#stored').inner_text()=='2')
 check('stored is not read',page.locator('#readCount').inner_text()=='0')
 page.click('#read');check('explicit simulated read',page.locator('#readCount').inner_text()=='2')
 page.click('#interrupt');check('interrupt visible',page.locator('#gap').inner_text().startswith('1'))
 page.click('#start');page.click('#add')
 page.wait_for_timeout(2600)
 page.screenshot(path=str(root/'evidence/desktop-demo.png'),full_page=True)
 page.click('#sleep');check('sleep gates capture',page.locator('#add').is_disabled() and page.locator('#start').is_disabled())
 page.click('#pause');check('pause cannot bypass sleep',page.locator('#mode').inner_text().startswith('睡眠'))
 page.click('#wake');check('wake does not start recording',page.locator('#mode').inner_text()=='尚未开始' and page.locator('#add').is_disabled())
 page.click('#delete');check('delete leaves tombstone','已删 / 下游删除未知' in page.locator('#transcripts').inner_text())
 with page.expect_download() as dl:
  page.click('#export')
 obj=json.loads(Path(dl.value.path()).read_text())
 check('export explicitly synthetic',obj['real_audio'] is False and obj['dot_connected'] is False)
 check('export removes deleted text',obj['fragments'][-1]['text'] is None)
 check('wake advances synthetic calendar day',obj['event']['timestamp'].startswith('2026-10-22T'))
 check('desktop no horizontal overflow',page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
 page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(root/'evidence/mobile-demo.png'),full_page=True)
 check('mobile no horizontal overflow',page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
 page.click('#reset');check('reset removes fragments',page.locator('#countLabel').inner_text()=='0 个合成片段')
 check('no JavaScript errors',not errors)
 check('no external network requests',not external)
 b.close()
report={'surface':'synthetic browser demo, not a device or dot test','checks_passed':len(checks),'checks':checks,'javascript_errors':errors,'external_requests':external,'viewports':[[1440,1100],[390,844]]}
(root/'evidence/browser-checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
