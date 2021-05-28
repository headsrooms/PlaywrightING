from playwright.async_api import TimeoutError as PlayWrightTimeout

from playwrighting.page_selectors import (
    DISABLED_PREVIOUS_MONTH_BUTTON,
    VER_MAS_BUTTON,
    VALID_OPERATION_TEXT,
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


async def need_to_check_your_phone(page) -> bool:
    try:
        await page.wait_for_selector(f"text={VALID_OPERATION_TEXT}", timeout=1_000)
        return True
    except PlayWrightTimeout:
        return False
