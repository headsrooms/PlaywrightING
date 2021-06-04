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
from rich.prompt import Prompt
from rich.traceback import install

from playwrighting.accounts import Position
from playwrighting.config import (
    config,
    app_path,
    before_timeout_screenshot_path,
    before_error_screenshot_path,
)
from playwrighting.constants import (
    STATE_FILE_NAME,
)
from playwrighting.exceptions import StateFileAlreadyExists, NotAValidChoice
from playwrighting.navigation.login import login


def exist_state_file() -> bool:
    return Path(app_path / STATE_FILE_NAME).exists()


@click.group(chain=True)
def cli():
    pass


@click.command()
async def init():
    if exist_state_file():
        raise StateFileAlreadyExists(
            "State file already exists. Remove it or execute update command instead"
        )

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        try:
            await login(page)

            position = await Position.create(page)
            position = await position.update(page)
            position.save()

        except PlayWrightTimeout as e:
            await page.screenshot(path=before_timeout_screenshot_path)
            logging.exception(e)
        except Error as e:
            await page.screenshot(path=before_error_screenshot_path)
            logging.exception(e)
        finally:
            await browser.close()


@click.command()
@click.option("--force", is_flag=True, default=False)
async def update(force):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        try:
            await login(page)

            new_position = await Position.create(page)

            if force:
                new_position = await new_position.update(page)
                new_position.save()

            else:
                old_position = Position.load()
                if old_position != new_position:
                    new_position = await new_position.update(page)
                    new_position.save()

        except PlayWrightTimeout as e:
            await page.screenshot(path=before_timeout_screenshot_path)
            logging.exception(e)
        except Error as e:
            await page.screenshot(path=before_error_screenshot_path)
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
@click.option("--option", default=None)
async def show(option):
    # TODO move to enum
    options = ["position", "accounts", "cards"]
    if not option:
        option = Prompt.ask(
            "What do you want to show?", choices=options, default="position"
        )
    else:
        if option not in options:
            raise NotAValidChoice("Selected option is not a valid choice")

    position = Position.load()

    # TODO create repr and str of all classes

    if position:
        if option == "position":
            print(position)
        elif option == "accounts":
            print(position.accounts)
        elif option == "cards":
            for account in position.accounts:
                print(account.cards)


install()
cli.add_command(init)
cli.add_command(update)
cli.add_command(download)
cli.add_command(show)

if __name__ == "__main__":
    cli(_anyio_backend="asyncio")
