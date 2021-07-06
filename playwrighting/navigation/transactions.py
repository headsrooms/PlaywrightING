from datetime import datetime

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
        return False
    try:
        current_month = await page.inner_text(CARD_DATE_NAVIGATOR_BUTTON, timeout=1_000)
        current_month = dateparser.parse(current_month).date()
        previous_month = current_month.replace(month=current_month.month - 1)
        last_update_date = last_update.date()

        return (
            previous_month.year >= last_update_date.year
            and previous_month.month >= last_update_date.month
        )
    except PlayWrightTimeout:
        return False


async def need_to_check_your_phone(page) -> bool:
    try:
        await page.wait_for_selector(f"text={VALID_OPERATION_TEXT}", timeout=1_000)
        return True
    except PlayWrightTimeout:
        return False
