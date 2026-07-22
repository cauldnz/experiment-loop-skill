import asyncio
from playwright.async_api import async_playwright
import os
import re

def _contrast_value(paint, prop="foreground") -> float:
    from math import pow
    def luminance(channels: tuple[float, float, float, float]) -> float:
        r, g, b, _ = channels
        return (
            0.2126 * (r / 12.92 if r <= 0.03928 else pow((r + 0.055) / 1.055, 2.4))
            + 0.7152 * (g / 12.92 if g <= 0.03928 else pow((g + 0.055) / 1.055, 2.4))
            + 0.0722 * (b / 12.92 if b <= 0.03928 else pow((b + 0.055) / 1.055, 2.4))
        )
    def rgb(value: str):
        if not value or value in ("transparent", "none"):
            return None
        match = re.fullmatch(
            r"rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)(?:[,\s/]+([\d.]+))?\s*\)",
            value.strip(),
            re.I,
        )
        if match:
            channels = tuple(float(match.group(i)) / 255 for i in range(1, 4))
            alpha = float(match.group(4)) if match.group(4) else 1.0
            if alpha > 1:
                alpha /= 255
            return (*channels, alpha)
        return None

    c1 = rgb(paint.get(prop, ""))
    c2 = rgb(paint.get("background", ""))
    if not c1 or not c2:
        return None
    l1 = luminance(c1)
    l2 = luminance(c2)
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        path = os.path.abspath('.experiments/accessible-mobile-checkout/generated/track-task-cards/loop-01/index.html')
        await page.goto(f'file:///{path}')
        
        samples = ("synthetic-banner", "cart", "subtotal", "tax", "total", "status", "error-summary")
        for hook in samples:
            loc = page.locator(f'[data-hook="{hook}"]')
            if await loc.is_visible():
                paint = await loc.evaluate('''el => {
                    const s = getComputedStyle(el);
                    return {
                        foreground: s.color,
                        background: s.backgroundColor,
                        fontSize: s.fontSize,
                        fontWeight: s.fontWeight
                    };
                }''')
                print(f"{hook}: {paint} -> {_contrast_value(paint)}")
        await browser.close()

asyncio.run(main())
