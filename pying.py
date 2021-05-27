import logging
from pathlib import Path
from typing import Optional

import asyncclick as click
from playwright.async_api import (
    async_playwright,
    Error,
    TimeoutError as PlayWrightTimeout,
)
from rich import print

from accounts import Position
from config import config
from constants import (
    BEFORE_TIMEOUT_SCREENSHOT_PATH,
    BEFORE_ERROR_SCREENSHOT_PATH,
)
from navigation.login import login


@click.group(chain=True)
def cli():
    pass


@click.command()
async def init():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        try:
            await login(page)

            old_position = Position.load()
            new_position = await Position.create(page)

            if old_position != new_position:
                new_position = await new_position.update(page)
                new_position.save()

        except PlayWrightTimeout as e:
            await page.screenshot(path=BEFORE_TIMEOUT_SCREENSHOT_PATH)
            logging.exception(e)
        except Error as e:
            await page.screenshot(path=BEFORE_ERROR_SCREENSHOT_PATH)
            logging.exception(e)
        finally:
            await browser.close()


@click.command()
async def update():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        try:
            await login(page)

            new_position = await Position.create(page)
            new_position = await new_position.update(page)
            new_position.save()

        except PlayWrightTimeout as e:
            await page.screenshot(path=BEFORE_TIMEOUT_SCREENSHOT_PATH)
            logging.exception(e)
        except Error as e:
            await page.screenshot(path=BEFORE_ERROR_SCREENSHOT_PATH)
            logging.exception(e)
        finally:
            await browser.close()


@click.command()
@click.option(
    "--download_path", default=None, help="path where files will be downloaded"
)
async def download(download_path: Optional[str]):
    new_position = Position.load()

    if new_position:
        download_path = Path(download_path or config.download_path)
        await new_position.download(download_path)


@click.command()
@click.option("--what")
async def show(what):
    new_position = Position.load()
    print(new_position.accounts)

    if new_position:
        print(new_position)


cli.add_command(init)
cli.add_command(update)
cli.add_command(download)
cli.add_command(show)

if __name__ == "__main__":
    cli(_anyio_backend="asyncio")
