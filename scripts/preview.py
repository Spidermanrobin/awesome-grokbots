#!/usr/bin/env python3
"""Optional Playwright smoke checks and a reproducible 1440×1000 preview."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import json
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(ROOT/'site')))
    Thread(target=server.serve_forever,daemon=True).start()
    url=f'http://127.0.0.1:{server.server_port}/'
    catalog=json.loads((ROOT/'site/data/catalog.json').read_text())
    total=len(catalog['entries'])
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
            context=browser.new_context(viewport={'width':1440,'height':1000},device_scale_factor=1,locale='en-US')
            page=context.new_page();errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
            page.goto(url);page.wait_for_selector('.card')
            assert page.locator('.card').count()==total
            page.locator('[data-category=finance].category-button').click()
            assert page.locator('.card').count()==sum(e['category']=='finance' for e in catalog['entries'])
            page.locator('#tier').select_option('tested');assert page.locator('#empty').is_visible()
            page.locator('#empty-reset').click();assert page.locator('.card').count()==total
            page.keyboard.press('/');assert page.locator('#search').evaluate('(e)=>e===document.activeElement')
            page.locator('#search').fill('paperknife');assert page.locator('.card').count()==1
            page.keyboard.press('Escape');assert page.locator('.card').count()==total
            page.locator('[data-kind=skills]').click();assert page.locator('.card').count()==catalog['counts']['skills']
            page.locator('#tag').select_option('mcp');assert page.locator('.card').count()==sum(e['kind']=='skills' and 'mcp' in e['tags'] for e in catalog['entries'])
            page.locator('#reset').click()
            for lang in ['zh-CN','ja']:
                page.locator('#language').select_option(lang);assert page.locator('html').get_attribute('lang')==lang
                page.locator('#search').fill('paperknife');assert page.locator('.card-review').inner_text()==next(e['review_i18n'][lang] for e in catalog['entries'] if e['id']=='paperknife')
                page.reload();page.wait_for_selector('.card');assert page.locator('html').get_attribute('lang')==lang
            page.locator('#language').select_option('en');page.locator('#search').fill('imagine-mcp')
            page.locator('.source-details summary').click();assert page.get_by_text('ZeroPointRepo/awesome-grok-bot contributors',exact=True).is_visible()
            assert page.locator('.source-content a').nth(1).get_attribute('href')=='https://creativecommons.org/licenses/by/4.0/'
            page.locator('#reset').click();page.locator('#sort').select_option('new');assert page.locator('.card').count()==total
            page.locator('#sort').select_option('name')
            for width in [390,768,1440]:
                page.set_viewport_size({'width':width,'height':1000})
                assert not page.evaluate('document.documentElement.scrollWidth>innerWidth'),f'Overflow at {width}px'
            page.evaluate('window.scrollTo(0,0)');page.screenshot(path=str(ROOT/'docs-preview.png'),full_page=False)
            # Exercise future weekly picks without changing the editorial data.
            picked={**catalog,'picks':[{'week':'2026-10-19','entries':['paperknife']}]}
            page.route('**/data/catalog.json',lambda route:route.fulfill(json=picked))
            page.reload();page.wait_for_selector('.pick-list a');assert page.locator('.pick-list a').inner_text()=='Paperknife'
            assert not errors,errors
            browser.close()
    finally:
        server.shutdown();server.server_close()
    print(f'Browser checks passed ({total} entries, 3 locales, desktop + mobile). Saved docs-preview.png (1440×1000).')


if __name__=='__main__':
    main()
