import pandas as pd
from playwright.async_api import Page, TimeoutError as PlayWrightTimeout
from rich import print
from rich.prompt import Prompt

from playwrighting.navigation.transactions import (
    has_previous_month,
    has_ver_mas_button,
    need_to_check_your_phone,
)
from playwrighting.page_selectors import (
    VER_MAS_BUTTON,
    PREVIOUS_MONTH_BUTTON,
    TRANSACTIONS_TABLE,
    CARD_DATE_NAVIGATOR_BUTTON,
    THIS_MONTH_BUTTON,
)


def clean(transactions: pd.DataFrame) -> pd.DataFrame:
    columns = transactions.columns.values

    # Remove unnamed columns
    columns = [column for column in columns if "Unnamed" not in column]

    return transactions[columns].dropna()


def style(transactions: pd.DataFrame) -> pd.DataFrame:
    return transactions.set_index("Fecha").sort_index(ascending=False)


def process_transactions_dataframe(
    transactions: pd.DataFrame,
) -> pd.DataFrame:
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
    transactions["Fecha"] = transactions["Fecha"].str.replace(days, "", regex=True)
    transactions["Fecha"] = pd.to_datetime(
        transactions["Fecha"], format="%d/%m/%Y", errors="coerce"
    )
    return transactions


async def download_transaction_data(
    page: Page, is_credit_card: bool = False
) -> pd.DataFrame:
    transactions = pd.DataFrame()

    # credit card page need additional steps
    if is_credit_card:
        await page.click(CARD_DATE_NAVIGATOR_BUTTON)
        await page.click(THIS_MONTH_BUTTON)

    while await has_previous_month(page):
        while await has_ver_mas_button(page):
            if await need_to_check_your_phone(page):
                await page.click(VER_MAS_BUTTON)

                print("Check your phone and accept the notification")
                Prompt.ask(
                    "Have you accepted the notification? Check your phone and accept the notification",
                    choices=[
                        "y",
                        "Y",
                        "yes",
                        "Yes",
                    ],
                    default="y",
                )
            else:
                await page.click(VER_MAS_BUTTON)

        transactions = pd.concat([await get_transactions_from_page(page), transactions])
        await page.click(PREVIOUS_MONTH_BUTTON)

    transactions = clean(transactions)
    transactions = style(transactions)
    return transactions


async def get_transactions_from_page(page: Page) -> pd.DataFrame:
    try:
        content = await page.inner_html(TRANSACTIONS_TABLE, timeout=1_000)
    except PlayWrightTimeout:
        content = await page.inner_html(TRANSACTIONS_TABLE_ALTERNATIVE)

    transactions = pd.read_html(content, thousands=".", decimal=",")[0]
    transactions = process_transactions_dataframe(transactions)
    return transactions
