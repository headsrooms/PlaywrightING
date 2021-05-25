from pathlib import Path

import pandas as pd

from navigation.transactions import (
    has_previous_month,
    has_ver_mas_button,
    need_to_check_your_phone,
)
from page_selectors import (
    VER_MAS_BUTTON,
    PREVIOUS_MONTH_BUTTON,
    TRANSACTIONS_TABLE,
    MY_PRODUCTS,
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
                await page.click(VER_MAS_BUTTON)

                print("Check your phone and accept the notification")
                while input("Have you accepted the notification? (y/n)") not in (
                    "y",
                    "Y",
                    "yes",
                    "Yes",
                ):
                    print("Please accept the notification to continue")
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
