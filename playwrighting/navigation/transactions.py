from datetime import datetime, date, timedelta

import dateparser
from playwright.async_api import TimeoutError as PlayWrightTimeout

from playwrighting.page_selectors import (
    DISABLED_PREVIOUS_MONTH_BUTTON,
    VER_MAS_BUTTON,
    VALID_OPERATION_TEXT,
    CARD_DATE_NAVIGATOR_BUTTON,
)


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


async def previous_month_not_obtained(page, last_update: datetime) -> bool:
    if not last_update:
        return True
    try:
        current_month = await page.inner_text(CARD_DATE_NAVIGATOR_BUTTON, timeout=1_000)
        previous_month = get_previous_month(current_month)
        last_update_date = last_update.date()

        return previous_month >= last_update_date
    except PlayWrightTimeout:
        return False


def get_previous_month(current_month: str) -> date:
    parsed_month = dateparser.parse(current_month)

    # with savings account the format is different and dateparser fails parsing
    if not parsed_month:
        lower_month, rest = current_month.split("-")
        upper_month, year = rest.split()

        parsed_month = dateparser.parse(f"{lower_month} {year}")

    current_month = parsed_month.date()
    return current_month - timedelta(days=30)


async def need_to_check_your_phone(page) -> bool:
    try:
        await page.wait_for_selector(f"text={VALID_OPERATION_TEXT}", timeout=1_000)
        return True
    except PlayWrightTimeout:
        return False
