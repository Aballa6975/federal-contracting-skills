"""Render /tmp/arch_matrix.html #capture element to PNG at 2x scale."""
import asyncio
import os
from playwright.async_api import async_playwright

OUT = os.path.expanduser("~/Downloads/architecture.png")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, channel="chrome")
        context = await browser.new_context(
            viewport={"width": 1820, "height": 1600},
            device_scale_factor=2,
        )
        page = await context.new_page()
        await page.goto(f"file:///tmp/arch_matrix.html", wait_until="networkidle")
        await asyncio.sleep(0.5)
        el = await page.query_selector("#capture")
        await el.screenshot(path=OUT, omit_background=False)
        await browser.close()
    print(f"Wrote {OUT} ({os.path.getsize(OUT)} bytes)")


if __name__ == "__main__":
    asyncio.run(main())
