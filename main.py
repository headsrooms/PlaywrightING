from pathlib import Path

import asyncclick as click
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


@click.group()
def cli():
    pass


@click.command()
async def init():
    async with async_playwright() as p:
        browser = await p.chromium.launch(downloads_path=Path(config.downloads_path))
        page = await browser.new_page(accept_downloads=True)

        try:
            await login(page)

            old_position = Position.load()
            new_position = await Position.create(page)

            if old_position != new_position:
                new_position = await new_position.update(page)
                new_position.save()

        except PlayWrightTimeout as e:
            await page.screenshot(path=BEFORE_TIMEOUT_SCREENSHOT_PATH)
            print(e)
        except Error as e:
            await page.screenshot(path=BEFORE_ERROR_SCREENSHOT_PATH)
            print(e)
        finally:
            await browser.close()


@click.command()
async def download():
    new_position = Position.load()

    if new_position:
        transactions_downloads_path = Path(config.downloads_path)
        await new_position.download(transactions_downloads_path)


cli.add_command(init)
cli.add_command(download)

if __name__ == "__main__":
    cli(_anyio_backend="asyncio")
