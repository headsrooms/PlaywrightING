from playwright.async_api import Page

from navigation.transactions import (
    has_previous_month,
    has_ver_mas_button,
    need_to_check_your_phone,
)
from page_selectors import (
    VER_MAS_BUTTON,
    PREVIOUS_MONTH_BUTTON,
    TRANSACTIONS_TABLE,
    CARD_DATE_NAVIGATOR_BUTTON,
    THIS_MONTH_BUTTON,
)
from utils import HashableDataFrame


def process_transactions_dataframe(
    transactions: HashableDataFrame,
) -> HashableDataFrame:
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
    return transactions


async def download_transaction_data(
    page: Page, is_credit_card: bool = False
) -> HashableDataFrame:
    transactions = HashableDataFrame()

    # credit card page need additional steps
    if is_credit_card:
        await page.click(CARD_DATE_NAVIGATOR_BUTTON)
        await page.click(THIS_MONTH_BUTTON)

    while await has_previous_month(page):
        while await has_ver_mas_button(page):
            if await need_to_check_your_phone(page):
                await page.click(VER_MAS_BUTTON)

                print("Check your phone and accept the notification")
                while input("Have you accepted the notification? (y/n) ") not in (
                    "y",
                    "Y",
                    "yes",
                    "Yes",
                ):
                    print("Please accept the notification to continue")
            else:
                await page.click(VER_MAS_BUTTON)

        transactions = HashableDataFrame.concat(
            [await get_transactions_from_page(page), transactions]
        )

        await page.click(PREVIOUS_MONTH_BUTTON)

    return transactions


async def get_transactions_from_page(page: Page) -> HashableDataFrame:
    content = await page.inner_html(TRANSACTIONS_TABLE)
    transactions = HashableDataFrame.read_html(content, thousands=".", decimal=",")[0]
    transactions = process_transactions_dataframe(transactions)
    return transactions
