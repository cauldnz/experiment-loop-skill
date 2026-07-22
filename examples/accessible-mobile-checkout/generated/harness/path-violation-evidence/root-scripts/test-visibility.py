import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        path = os.path.abspath('.experiments/accessible-mobile-checkout/generated/track-task-cards/loop-01/index.html')
        await page.goto(f'file:///{path}')
        
        samples = ("synthetic-banner", "cart", "subtotal", "tax", "total", "status", "error-summary")
        for hook in samples:
            visible = await page.locator(f'[data-hook="{hook}"]').is_visible()
            print(f"{hook}: visible={visible}")
        await browser.close()

asyncio.run(main())
