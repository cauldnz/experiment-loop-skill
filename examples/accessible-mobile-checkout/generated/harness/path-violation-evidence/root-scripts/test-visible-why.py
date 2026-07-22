import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 390, "height": 844})
        page = await context.new_page()
        path = os.path.abspath('.experiments/accessible-mobile-checkout/generated/track-task-cards/loop-01/index.html')
        await page.goto(f'file:///{path}')
        
        hooks = ("cart", "subtotal", "tax", "total")
        for hook in hooks:
            loc = page.locator(f'[data-hook="{hook}"]')
            count = await loc.count()
            try:
                vis = await loc.is_visible()
                print(f"{hook}: count={count}, is_visible={vis}")
            except Exception as e:
                print(f"{hook}: Exception {e}")
        await browser.close()

asyncio.run(main())
