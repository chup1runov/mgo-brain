"""Real Chromium checks: page startup, Russian/English, local AI and disconnection."""
import json
import time
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

url='http://127.0.0.1:8080/'
for _ in range(120):
    try:
        urllib.request.urlopen(url+'health',timeout=1).close()
        break
    except OSError:
        time.sleep(0.5)
else:
    raise SystemExit('Backend did not start')
errors=[]
out=Path('audit-output');out.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch()
    context=browser.new_context(viewport={'width':1280,'height':900})
    page=context.new_page()
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.goto(url, wait_until='networkidle')
    page.wait_for_timeout(1500)
    assert not errors,errors
    assert page.locator('html').get_attribute('lang')=='ru'
    assert page.locator('#healthHome .health-item').count()==5
    assert 'ДЕМОНСТРАЦИЯ' in page.locator('#dataOrigin').inner_text()
    page.screenshot(path=str(out/'dashboard-ru.png'), full_page=True)
    page.locator('[data-view="lab"]').click()
    page.wait_for_timeout(500)
    assert page.locator('#lab').is_visible()
    page.screenshot(path=str(out/'lab-ru.png'),full_page=True)
    page.locator('#langToggle').click()
    page.wait_for_load_state('networkidle')
    assert page.locator('html').get_attribute('lang')=='en'
    response=context.request.post(url+'api/v1/ai/ask',data={'question':'How is the engine?','language':'en'})
    assert response.ok,response.text()
    assert 'Local evidence report' in response.json()['answer']
    # Close the actual page's socket and block reconnection while HTTP remains live.
    page.evaluate("() => { ws.onclose=null; ws.close(); }")
    page.wait_for_timeout(3600)
    assert page.locator('[data-sig="engine.rpm"]').first.inner_text()=='–'
    assert page.locator('#conn').inner_text()=='offline'
    assert not errors,errors
    # A separate phone-size layout must remain usable, without JS failures.
    mobile=browser.new_page(viewport={'width':390,'height':844},is_mobile=True,device_scale_factor=1)
    mobile.on('pageerror',lambda error:errors.append(str(error)))
    mobile.goto(url+'?lang=ru',wait_until='networkidle')
    mobile.wait_for_timeout(500)
    assert mobile.locator('#home').is_visible()
    assert not errors,errors
    browser.close()
print('BROWSER_ERRORS',json.dumps(errors,ensure_ascii=False))
print('BROWSER_SMOKE_OK: RU EN AI-language stale-values desktop mobile')
