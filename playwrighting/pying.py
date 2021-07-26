import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from shutil import copy
from string import ascii_letters
from typing import Optional, Dict

import asyncclick as click
import pandas as pd
from playwright.async_api import (
    async_playwright,
    Error,
    TimeoutError as PlayWrightTimeout,
)
from rich import print
from rich.console import Console
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
from playwrighting.exceptions import (
    StateFileAlreadyExists,
    NotAValidChoice,
    ParentDirectoryDoesNotExist,
    StateFileDoesNotExist,
)
from playwrighting.navigation.login import login


def exist_state_file() -> bool:
    return Path(app_path / STATE_FILE_NAME).exists()


@click.group(chain=True)
def cli():
    pass


@click.command()
@click.option("--force", is_flag=True, default=False)
async def init(force):
    if exist_state_file():
        state_file_path = Path(app_path / STATE_FILE_NAME)
        if not force:
            raise StateFileAlreadyExists(
                f"State file already exists. Remove it, add --force flag or execute update command instead. "
                f"Path is {state_file_path}"
            )
        state_file_path.unlink()

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
                new_position = (
                    await new_position.update(page)
                    if old_position != new_position
                    else new_position.touch()
                )
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
@click.option("--create_parents", is_flag=True, default=False)
async def download(download_path: Optional[str], create_parents: bool):
    new_position = Position.load()

    if new_position:
        download_path = Path(download_path or config.download_path)
        if create_parents:
            download_path.mkdir(parents=True, exist_ok=True)

        try:
            await new_position.download(download_path)
        except FileNotFoundError:
            raise ParentDirectoryDoesNotExist(
                f"Parent directory/ies of your download_path {download_path} doesn't exist, create it or use "
                f"--create_parents flag "
            )


class ShowOptions(str, Enum):
    position: str = "position"
    account: str = "accounts"
    transactions: str = "transactions"


def get_account_or_card_selection_choices(
    position: Position,
) -> Dict[str, pd.DataFrame]:
    cards_choices = {
        f"{i + 1}.{ascii_letters[j]}": account.transactions
        for i, account in enumerate(position.accounts)
        for j, _ in enumerate(account.cards)
    }
    accounts_choices = {
        f"{i + 1}": account.transactions for i, account in enumerate(position.accounts)
    }

    return cards_choices | accounts_choices


@click.command()
@click.option("--option", default=None)
async def show(option):
    if not option:
        option = Prompt.ask(
            "What do you want to show?",
            choices=list(ShowOptions),
            default=ShowOptions.position,
        )
    else:
        if option not in list(ShowOptions):
            raise NotAValidChoice("Selected option is not a valid choice")

    position = Position.load()

    if position:
        if option == "position":
            print(str(position))
        elif option == "accounts":
            message = f"""Accounts:
        {"".join([f"{i + 1}) {account.position()}" for i, account in enumerate(position.accounts)])}
        """
            print(message)
        elif option == "transactions":
            cards_lines = "".join(
                [
                    f"{i + 1}) {account.transactions_menu(i + 1)}"
                    for i, account in enumerate(position.accounts)
                ]
            )
            message = f"""Choose an account or card:
        {cards_lines}
        """

            account_or_card_selection_choices = get_account_or_card_selection_choices(
                position
            )
            account_or_card_selection = Prompt.ask(
                message,
                choices=list(account_or_card_selection_choices.keys()),
                default=list(account_or_card_selection_choices.keys())[0],
            )

            console = Console()
            with console.pager():
                console.print(
                    account_or_card_selection_choices[account_or_card_selection]
                )


@click.command()
@click.option("--destiny_name", default=None, help="destiny backup file name")
async def backup(destiny_name: str):
    origin_state = app_path / STATE_FILE_NAME
    now = datetime.now().strftime("%d%b%y-%H%M")
    destiny_file_name = f"{destiny_name or now}.pkl"
    destiny_state = app_path / destiny_file_name

    if not origin_state.exists():
        raise StateFileDoesNotExist("Cannot backup because state file doesn't exist")

    copy(origin_state, destiny_state)


install()
cli.add_command(init)
cli.add_command(update)
cli.add_command(download)
cli.add_command(show)
cli.add_command(backup)

if __name__ == "__main__":
    cli(_anyio_backend="asyncio")
