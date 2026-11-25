"""Check the research workflow with bounded official-shaped API fixtures."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import datetime
import json
import os
import shutil
import tempfile
import threading
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
CHANNEL='UCabcdefghijklmnopqrstuv'; PLAYLIST='UUabcdefghijklmnopqrstuv'
IDS=['abcdefghijk','ABCDEFGHIJK','123456789_-']
def video(id):
    i=IDS.index(id)
    return {'id':id,'snippet':{'title':['Network basics','A longer lecture','Young learners'][i],'channelTitle':'Learning channel','description':'Public lesson metadata'},'contentDetails':{'duration':['PT20M','PT90M','PT10M'][i]},'status':{'embeddable':True,'madeForKids':i==2}}
class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
def main():
    screenshots=ROOT/'browser-checks';screenshots.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        shutil.copytree(ROOT/'dist',Path(temporary)/'channelqueue')
        server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=temporary))
        threading.Thread(target=server.serve_forever,daemon=True).start()
        try:
            with sync_playwright() as p:
                opts={'executable_path':os.environ['CHROMIUM_PATH']} if os.environ.get('CHROMIUM_PATH') else {}
                browser=p.chromium.launch(**opts);page=browser.new_page(viewport={'width':1280,'height':1000})
                errors=[];requests=[];page.on('pageerror',lambda e:errors.append(str(e)))
                def gateway(route):
                    url=urlparse(route.request.url);q=parse_qs(url.query);requests.append(route.request.url)
                    path=url.path.rsplit('/',1)[-1]
                    if path=='search': data={'items':[{'id':{'channelId':CHANNEL},'snippet':{'title':'Learning channel','description':'Networks and ideas'}}]}
                    elif path=='channel':data={'items':[{'id':CHANNEL,'snippet':{'title':'Learning channel'},'contentDetails':{'relatedPlaylists':{'uploads':PLAYLIST}}}]}
                    elif path=='playlist':data={'items':[{'contentDetails':{'videoId':id}} for id in (IDS[2:] if q.get('pageToken') else IDS[:2])]};data.update({} if q.get('pageToken') else {'nextPageToken':'next'})
                    else:data={'items':[video(id) for id in q.get('ids',[''])[0].split(',') if id in IDS]}
                    route.fulfill(json={'fetched_at':datetime.datetime.now(datetime.UTC).isoformat(),'data':data})
                page.route('https://coolcode-visitor-api.jeffdyer.workers.dev/api/channelqueue/**',gateway)
                page.route('https://www.youtube-nocookie.com/**',lambda r:r.fulfill(body='<html><body>Official player fixture</body></html>',content_type='text/html'))
                page.goto(f'http://127.0.0.1:{server.server_port}/channelqueue/')
                assert page.locator('#desk').is_hidden();assert not requests
                page.locator('#agree').check();page.locator('#start').click()
                page.locator('.search-details summary').click();page.locator('#query').fill('Urban gardening');page.locator('#search-form button').click()
                page.locator('#results').get_by_role('button',name='Open channel').click()
                page.locator('#results .video-card').nth(1).wait_for();assert any('q=Urban+gardening' in u for u in requests)
                page.locator('#save-source').click();assert page.locator('#source-count').inner_text()=='1'
                page.locator('#load-more').click();page.locator('#results .video-card').nth(2).wait_for()
                page.locator('#max-minutes').fill('25');assert page.locator('#results .video-card').count()==2
                page.locator('#results .video-card').first.get_by_role('button',name='Add to learning queue').click()
                assert page.locator('#queue-count').inner_text()=='1';assert page.locator('#player-container iframe').count()==0
                page.locator('#bookmark-label').fill('My home lab lesson');page.locator('#bookmark-topic').fill('Home lab');page.locator('#bookmark-topic').press('Tab')
                page.locator('#note-time').fill('2:15');page.locator('#note-text').fill('<img src=x onerror=alert(1)>My VLAN question');page.locator('#note-form button').click()
                assert 'My VLAN question' in page.locator('#note-list').inner_text();assert page.locator('#note-list img').count()==0
                page.locator('#resume-time').fill('3:20');page.locator('#save-position').click()
                assert page.evaluate("localStorage.getItem('coolcode:channelqueue:workspace:v1')") is None
                page.locator('#load-player').click();page.locator('#player-container iframe').wait_for()
                assert 'start=200' in page.locator('#player-container iframe').get_attribute('src')
                page.locator('#remember').check();saved=json.loads(page.evaluate("localStorage.getItem('coolcode:channelqueue:workspace:v1')"))
                assert saved['bookmarks'][0]['label']=='My home lab lesson';assert 'title' not in saved['bookmarks'][0];assert 'description' not in saved['bookmarks'][0]
                page.reload();page.locator('#agree').check();page.locator('#start').click();page.locator('[data-tab="queue"]').click()
                page.get_by_role('heading',name='My home lab lesson',exact=True).wait_for()
                assert 'not loaded' in page.locator('#queue-list').inner_text()
                with page.expect_download() as download:page.locator('#export-json').click()
                data=json.loads(Path(download.value.path()).read_text());assert data['bookmarks'][0]['notes'][0]['time']==135;assert 'Network basics' not in json.dumps(data)
                page.screenshot(path=str(screenshots/'desktop.png'),full_page=True)
                page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
                page.screenshot(path=str(screenshots/'mobile.png'),full_page=True)
                page.locator('[data-tab="discover"]').click();page.locator('#source-input').fill(IDS[2]);page.locator('#open-form button').click()
                page.locator('#results .video-card').get_by_role('button',name='Add to learning queue').click()
                page.locator('#load-player').click();page.get_by_text('This app does not embed child-directed videos or videos whose child-directed status is unavailable. Use Watch on YouTube.',exact=True).wait_for()
                assert page.locator('#player-container iframe').count()==0
                page.locator('#remember').uncheck();assert page.evaluate("localStorage.getItem('coolcode:channelqueue:workspace:v1')") is None
                assert not errors,errors;browser.close()
            print('Browser checks passed: consent, arbitrary channel search, pagination, queue, notes, metadata-free persistence, export, embed status and mobile layout')
        finally:server.shutdown()
if __name__=='__main__':main()
