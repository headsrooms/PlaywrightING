import asyncio
from pathlib import Path
from typing import Union, Iterable

from playwright.async_api import (
    async_playwright,
    Error,
    TimeoutError as PlayWrightTimeout,
    Page,
)

from accounts import Position, Account, Card
from config import config
from constants import (
    BEFORE_TIMEOUT_SCREENSHOT_PATH,
    BEFORE_ERROR_SCREENSHOT_PATH,
    LOGIN_URL,
)
from navigation.login import login
from page_selectors import (
    MY_PRODUCTS,
    EXCEL_BUTTON,
    NO_TRANSACTIONS_MESSAGE,
)


async def download_excel(page, download_path: Path):
    async with page.expect_download(timeout=120_000) as download_info:
        await page.click(EXCEL_BUTTON)
    download = await download_info.value
    await download.save_as(download_path)


async def has_transactions(page) -> bool:
    try:
        await page.wait_for_selector(NO_TRANSACTIONS_MESSAGE, timeout=1_000)
        return False
    except PlayWrightTimeout:
        return True


async def get_transactions(
    page: Page,
    accounts_or_cards: Union[Iterable[Account], Iterable[Card]],
    downloads_path: Path,
):
    for account_or_card in accounts_or_cards:
        await download_transactions_file(
            page, account_or_card.name, downloads_path / f"{account_or_card.name}.xlsx"
        )


async def download_transactions_file(
    page, account_or_card_name: str, download_path: Path
):
    print(f"Downloading data from {account_or_card_name}")
    await page.click(MY_PRODUCTS)
    await page.click(f"text={account_or_card_name}")
    if await has_transactions(page):
        await download_excel(page, download_path)


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(downloads_path=Path(config.downloads_path))
        page = await browser.new_page(accept_downloads=True)
        await page.goto(LOGIN_URL)

        try:
            await login(page)
            overall_position = await Position.get_position(page)
            transactions_downloads_path = Path(config.downloads_path)

            print(overall_position)
            accounts_and_cards = [
                *overall_position.accounts,
                *overall_position.accounts,
            ]
            download_tasks = [
                download_transactions_file(
                    page,
                    account_or_card.name,
                    transactions_downloads_path / f"{account_or_card.name}.xlsx",
                )
                for account_or_card in accounts_and_cards
            ]

            await asyncio.gather(*download_tasks)

        except PlayWrightTimeout as e:
            await page.screenshot(path=BEFORE_TIMEOUT_SCREENSHOT_PATH)
            print(e)
        except Error as e:
            await page.screenshot(path=BEFORE_ERROR_SCREENSHOT_PATH)
            print(e)
        finally:
            await browser.close()


async def download_all_transactions_files(
    overall_position, browser, transactions_downloads_path
):
    accounts_and_cards = [*overall_position.accounts, *overall_position.accounts]
    page = await browser.new_page(accept_downloads=True)
    await page.goto(LOGIN_URL)
    for account_or_card in accounts_and_cards:
        await download_transactions_file(
            page,
            account_or_card.name,
            transactions_downloads_path / f"{account_or_card.name}.xlsx",
        )


asyncio.run(main())
