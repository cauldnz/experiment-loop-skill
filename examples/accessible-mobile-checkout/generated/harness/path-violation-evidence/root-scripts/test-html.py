import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 390, "height": 844}, reduced_motion="reduce", forced_colors="active")
        page = await context.new_page()
        path = os.path.abspath('.experiments/accessible-mobile-checkout/generated/track-task-cards/loop-01/index.html')
        await page.goto(f'file:///{path}')
        
        html = await page.locator('[data-hook="cart"]').evaluate('el => el.outerHTML')
        print("CART HTML:", html)
        vis = await page.locator('[data-hook="cart"]').is_visible()
        print("CART VISIBLE:", vis)
        await browser.close()

asyncio.run(main())
