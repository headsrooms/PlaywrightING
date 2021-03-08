import asyncio

from playwright.async_api import (
    async_playwright,
    Error,
    TimeoutError as PlayWrightTimeout,
)

from constants import BEFORE_TIMEOUT_SCREENSHOT_PATH, BEFORE_ERROR_SCREENSHOT_PATH, LOGIN_URL
from navigation.login import login


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(LOGIN_URL)
        try:
            await login(page)
        except PlayWrightTimeout:
            await page.screenshot(path=BEFORE_TIMEOUT_SCREENSHOT_PATH)
        except Error:
            await page.screenshot(path=BEFORE_ERROR_SCREENSHOT_PATH)

        await browser.close()


asyncio.run(main())
