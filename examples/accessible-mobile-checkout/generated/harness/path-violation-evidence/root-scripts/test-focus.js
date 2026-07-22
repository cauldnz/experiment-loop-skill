const { chromium } = require('playwright');
(async () => {
    const browser = await chromium.launch();
    const page = await browser.newPage();
    await page.goto('file:///' + require('path').resolve('.experiments/accessible-mobile-checkout/generated/track-task-cards/loop-01/index.html').replace(/\\/g, '/'));
    await page.focus('#place-order');
    const style = await page.$eval('#place-order', el => ({
        outline: getComputedStyle(el).outline,
        outlineStyle: getComputedStyle(el).outlineStyle,
        outlineColor: getComputedStyle(el).outlineColor,
        outlineWidth: getComputedStyle(el).outlineWidth
    }));
    console.log(style);
    await browser.close();
})();
