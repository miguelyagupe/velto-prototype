"""Record an actual controlled integration run of our original local CSV tool.

This is a real browser recording of actual calculations, not a mocked third-party
interface. Its intentionally invalid input is a negative test, not an AI failure.
"""
import argparse, asyncio, hashlib, json, shutil, time
from datetime import datetime, timezone
from pathlib import Path
from playwright.async_api import async_playwright

ROOT=Path(__file__).resolve().parents[1]
async def main(duration=78):
    out=ROOT/'episodes/EP001';out.mkdir(parents=True,exist_ok=True)
    recorded=out/'recording';recorded.mkdir(exist_ok=True)
    events=[]
    async with async_playwright() as p:
        browser=await p.chromium.launch(executable_path=shutil.which('chromium') or None,headless=True,args=['--no-sandbox'])
        context=await browser.new_context(viewport={'width':1920,'height':1080},record_video_dir=str(recorded),record_video_size={'width':1920,'height':1080},color_scheme='dark')
        page=await context.new_page();video=page.video;start=time.monotonic()
        async def mark(action):
            events.append({'seconds':round(time.monotonic()-start,3),'action':action,'visible_result':await page.locator('#status').inner_text(),'total':await page.locator('#total').inner_text(),'mean':await page.locator('#mean').inner_text(),'rows':await page.locator('#count').inner_text()})
        async def pause(n):await asyncio.sleep(n)
        await page.goto((ROOT/'demo/index.html').as_uri());await mark('Open original CSV analyzer; synthetic sample loaded')
        await pause(5)
        await page.locator('#csv').click();await pause(3)
        await page.locator('#run').click();await mark('Analyze six synthetic rows')
        assert await page.locator('#total').inner_text()=='12,000'
        assert await page.locator('#mean').inner_text()=='2,000'
        await pause(8)
        await page.locator('#csv').fill('month,sales\nJan,1200\nFeb,1800\nMar,1500\nApr,2400\nMay,2100\nJun,4500');await mark('Change June input from 3000 to 4500; result not recomputed yet')
        await pause(5)
        await page.locator('#run').click();await mark('Recompute after changing June')
        assert await page.locator('#total').inner_text()=='13,500'
        await pause(8)
        await page.locator('#csv').fill('month,sales\nJan,1200\nFeb,invalid');await pause(3)
        await page.locator('#run').click();await mark('Intentional invalid-input test; validation rejects non-numeric sales')
        assert 'non-negative number' in await page.locator('#status').inner_text()
        await pause(7)
        await page.locator('#reset').click();await mark('Restore known valid sample')
        assert await page.locator('#total').inner_text()=='12,000'
        await pause(4)
        await page.locator('#sort').select_option('desc');await mark('Sort real calculated bars highest first')
        assert await page.locator('.name').first.inner_text()=='Jun'
        await pause(7)
        await page.locator('#minimum').fill('2000');await pause(2)
        await page.locator('#filter').click();await mark('Filter rows below 2000 and recalculate visible totals')
        assert await page.locator('#total').inner_text()=='7,500'
        assert await page.locator('#count').inner_text()=='3'
        await pause(7)
        await page.locator('#reset').click();await mark('Reset completes controlled experiment')
        await page.screenshot(path=str(out/'capture_verified.png'))
        await pause(max(1,duration-(time.monotonic()-start)))
        await mark('End capture')
        await context.close();await video.save_as(str(out/'capture.webm'));await browser.close()
    report={'recorded_at':datetime.now(timezone.utc).isoformat(),'capture_type':'Actual Playwright viewport video of original local app','claims_scope':'Functional demo rerun, not a screen recording of the agent writing code','negative_test':'Deliberately invalid input; do not portray as unexpected agent defect','data':'Synthetic; no accounts, private data or network requests','events':events,'source_sha256':hashlib.sha256((ROOT/'demo/index.html').read_bytes()).hexdigest(),'capture_sha256':hashlib.sha256((out/'capture.webm').read_bytes()).hexdigest()}
    (out/'capture_events.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'capture':str(out/'capture.webm'),'events':len(events),'elapsed':events[-1]['seconds'],'checks':'passed'}))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--duration',type=float,default=78);args=ap.parse_args();asyncio.run(main(args.duration))
