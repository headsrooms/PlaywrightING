import asyncio
from pathlib import Path

from playwright.async_api import (
    async_playwright,
    Error,
    TimeoutError as PlayWrightTimeout,
)

from accounts import Position
from config import config
from constants import (
    BEFORE_TIMEOUT_SCREENSHOT_PATH,
    BEFORE_ERROR_SCREENSHOT_PATH,
)
from navigation.login import login


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(downloads_path=Path(config.downloads_path))
        page = await browser.new_page(accept_downloads=True)

        try:
            await login(page)
            overall_position = await Position.get_position(page)
            transactions_downloads_path = Path(config.downloads_path)

            print(overall_position)
            await overall_position.get_transactions(page, transactions_downloads_path)

        except PlayWrightTimeout as e:
            await page.screenshot(path=BEFORE_TIMEOUT_SCREENSHOT_PATH)
            print(e)
        except Error as e:
            await page.screenshot(path=BEFORE_ERROR_SCREENSHOT_PATH)
            print(e)
        finally:
            await browser.close()


asyncio.run(main())
