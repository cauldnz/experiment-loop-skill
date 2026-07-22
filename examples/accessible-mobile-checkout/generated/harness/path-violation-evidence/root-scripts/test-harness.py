import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        path = os.path.abspath('.experiments/accessible-mobile-checkout/generated/track-task-cards/loop-01/index.html')
        await page.goto(f'file:///{path}')
        await page.focus('#place-order')
        
        # Copied from harness
        focus = await page.evaluate('''() => {
            const el = document.querySelector('#place-order');
            const style = window.getComputedStyle(el);
            return {
                outlineStyle: style.getPropertyValue('outline-style'),
                outlineColor: style.getPropertyValue('outline-color'),
                outlineWidth: style.getPropertyValue('outline-width'),
            };
        }''')
        print(focus)
        await browser.close()

asyncio.run(main())
