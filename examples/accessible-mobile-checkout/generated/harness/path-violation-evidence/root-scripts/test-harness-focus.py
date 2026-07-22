import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        path = os.path.abspath('.experiments/accessible-mobile-checkout/generated/track-task-cards/loop-01/index.html')
        await page.goto(f'file:///{path}')
        
        style = await page.locator('#place-order').evaluate('''el => {
            el.focus();
            const s = getComputedStyle(el);
            return {
                active: document.activeElement === el,
                outlineColor: s.outlineColor,
                outlineWidth: s.outlineWidth,
                outlineStyle: s.outlineStyle,
                boxShadow: s.boxShadow,
                borderColor: s.borderColor
            };
        }''')
        print(style)
        await browser.close()

asyncio.run(main())
