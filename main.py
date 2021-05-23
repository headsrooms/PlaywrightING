import asyncio
from pathlib import Path
from typing import Union, Iterable

import pandas as pd
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
)
from navigation.login import login
from page_selectors import (
    MY_PRODUCTS,
    TRANSACTIONS_TABLE,
    DISABLED_PREVIOUS_MONTH_BUTTON,
    PREVIOUS_MONTH_BUTTON,
    VER_MAS_BUTTON,
)


def process_transactions_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    days = "|".join(
        [
            "Lunes",
            "Martes",
            "Miércoles",
            "Jueves",
            "Viernes",
            "Sábado",
            "Domingo",
            "Ayer",
            "Hoy",
        ]
    )
    df["Fecha"] = df["Fecha"].str.replace(days, "", regex=True)
    return df


async def has_previous_month(page) -> bool:
    try:
        await page.wait_for_selector(DISABLED_PREVIOUS_MONTH_BUTTON, timeout=1_000)
        return False
    except PlayWrightTimeout:
        return True


async def has_ver_mas_button(page) -> bool:
    try:
        await page.wait_for_selector(VER_MAS_BUTTON, timeout=1_000)
        return True
    except PlayWrightTimeout:
        return False


async def download_transaction_data(page, file_path: Path):
    df = pd.DataFrame()
    while True:
        if await has_ver_mas_button(page):
            await page.click(VER_MAS_BUTTON)

        df = pd.concat([await get_transactions_from_page(page), df])

        if await has_previous_month(page):
            await page.click(PREVIOUS_MONTH_BUTTON)
        else:
            break

    df.to_csv(file_path)


async def get_transactions_from_page(page):
    content = await page.inner_html(TRANSACTIONS_TABLE)
    df = pd.read_html(content, thousands=".", decimal=",")[0]
    df = process_transactions_dataframe(df)
    return df


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
    page, account_or_card_name: str, downloads_path: Path
):
    print(f"Downloading data from {account_or_card_name}")
    file_path = downloads_path / f"{account_or_card_name}.csv"

    await page.click(MY_PRODUCTS)
    await page.click(f"text={account_or_card_name}")
    await download_transaction_data(page, file_path)


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(downloads_path=Path(config.downloads_path))
        page = await browser.new_page(accept_downloads=True)

        try:
            await login(page)
            overall_position = await Position.get_position(page)
            transactions_downloads_path = Path(config.downloads_path)

            print(overall_position)
            accounts_and_cards = [
                *overall_position.accounts,
                *overall_position.cards,
            ]

            for account_or_card in accounts_and_cards:
                await download_transactions_file(
                    page,
                    account_or_card.name,
                    transactions_downloads_path,
                )

        except PlayWrightTimeout as e:
            await page.screenshot(path=BEFORE_TIMEOUT_SCREENSHOT_PATH)
            print(e)
        except Error as e:
            await page.screenshot(path=BEFORE_ERROR_SCREENSHOT_PATH)
            print(e)
        finally:
            await browser.close()


asyncio.run(main())
