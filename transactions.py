import asyncio
from pathlib import Path

import pandas as pd
from playwright.async_api import TimeoutError as PlayWrightTimeout

from page_selectors import (
    DISABLED_PREVIOUS_MONTH_BUTTON,
    VER_MAS_BUTTON,
    PREVIOUS_MONTH_BUTTON,
    TRANSACTIONS_TABLE,
    MY_PRODUCTS,
    VALID_OPERATION_TEXT,
    CARD_DATE_NAVIGATOR_BUTTON,
    THIS_MONTH_BUTTON,
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


async def need_to_check_your_phone(page) -> bool:
    try:
        await page.wait_for_selector(f"text={VALID_OPERATION_TEXT}", timeout=1_000)
        return True
    except PlayWrightTimeout:
        return False


async def download_transaction_data(
    page, file_path: Path, is_credit_card: bool = False
):
    df = pd.DataFrame()

    # credit card page need additional steps
    if is_credit_card:
        await page.click(CARD_DATE_NAVIGATOR_BUTTON)
        await page.click(THIS_MONTH_BUTTON)

    while await has_previous_month(page):
        while await has_ver_mas_button(page):
            if await need_to_check_your_phone(page):
                # give 60 seconds to accept a notification sent to your phone
                await page.click(VER_MAS_BUTTON)
                print("Check your phone and accept the notification")
                await asyncio.sleep(60)
            else:
                await page.click(VER_MAS_BUTTON)

        df = pd.concat([await get_transactions_from_page(page), df])

        await page.click(PREVIOUS_MONTH_BUTTON)

    df.to_csv(file_path)


async def get_transactions_from_page(page):
    content = await page.inner_html(TRANSACTIONS_TABLE)
    df = pd.read_html(content, thousands=".", decimal=",")[0]
    df = process_transactions_dataframe(df)
    return df


async def download_transactions_file(
    page, account_or_card_name: str, downloads_path: Path, is_credit_card: bool = False
):
    print(f"Downloading data from {account_or_card_name}")
    file_path = downloads_path / f"{account_or_card_name}.csv"

    await page.click(MY_PRODUCTS)
    await page.click(f"text={account_or_card_name}")
    await download_transaction_data(page, file_path, is_credit_card)
