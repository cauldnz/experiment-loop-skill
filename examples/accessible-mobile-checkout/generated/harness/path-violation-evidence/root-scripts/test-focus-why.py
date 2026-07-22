import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        path = os.path.abspath('.experiments/accessible-mobile-checkout/generated/track-task-cards/loop-01/index.html')
        await page.goto(f'file:///{path}')
        
        info = await page.locator('#place-order').evaluate('''el => {
            el.focus();
            const s = getComputedStyle(el);
            return {
                active: document.activeElement === el,
                visibility: s.visibility,
                display: s.display,
                disabled: el.disabled,
                tabIndex: el.tabIndex,
                tagName: el.tagName,
                offsetHeight: el.offsetHeight,
                offsetWidth: el.offsetWidth
            };
        }''')
        print(info)
        await browser.close()

asyncio.run(main())
