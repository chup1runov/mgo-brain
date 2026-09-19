"""Real Chromium smoke: catches runtime failures that HTML substring tests miss."""
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
    page=browser.new_page(viewport={'width':1280,'height':900})
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.goto(url, wait_until='networkidle')
    page.wait_for_timeout(1500)
    print('BROWSER_ERRORS',json.dumps(errors,ensure_ascii=False))
    assert not errors,errors
    assert page.locator('html').get_attribute('lang')=='ru'
    assert page.locator('#healthHome .health-item').count()==5
    page.screenshot(path=str(out/'dashboard-ru.png'), full_page=True)
    page.locator('[data-view="lab"]').click()
    page.wait_for_timeout(500)
    assert page.locator('#lab').is_visible()
    page.screenshot(path=str(out/'lab-ru.png'),full_page=True)
    page.locator('#langToggle').click()
    page.wait_for_load_state('networkidle')
    assert page.locator('html').get_attribute('lang')=='en'
    assert not errors,errors
    browser.close()
print('BROWSER_SMOKE_OK')
