"""Log in as the demo account and screenshot the pages shown in the README.

Runs inside a throwaway Playwright container; see take.sh.
"""
import os

from playwright.sync_api import sync_playwright

BASE = os.environ.get('BASE_URL', 'http://localhost:8000')
OUT = os.environ.get('OUT_DIR', '/work')
PASSWORD = os.environ['DEMO_PASSWORD']

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1280, 'height': 860}, device_scale_factor=1.5, color_scheme='dark')
    page.goto(f'{BASE}/login/')
    page.fill('input[name=username]', 'demo')
    page.fill('input[name=password]', PASSWORD)
    page.click('form button[type=submit]')
    page.wait_for_url('**/dashboard/')

    def shot(url, name, height=860):
        # Short pages get a short window so the footer sits under the content.
        page.set_viewport_size({'width': 1280, 'height': height})
        page.goto(BASE + url, wait_until='networkidle')
        page.mouse.move(0, 0)
        page.evaluate('document.fonts.ready')
        page.wait_for_timeout(800)  # let the charts finish animating
        page.screenshot(path=f'{OUT}/{name}.png', full_page=True)
        print('saved', name)

    shot('/dashboard/', 'dashboard')
    shot('/recipes/', 'recipe-list')
    page.goto(BASE + '/dashboard/', wait_until='networkidle')
    session_url = page.get_attribute('a.stretched-link:has-text("Farmhouse Saison")', 'href')
    shot(session_url, 'session-detail', height=520)
    browser.close()
