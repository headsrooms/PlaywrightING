from typing import List

from playwright.async_api import Page

from config import config
from page_selectors import (
    INPUT_YEAR,
    INPUT_MONTH,
    INPUT_DAY,
    ID_NUMBER as ID_NUMBER_SELECTOR,
    CLOSE_COOKIES_BUTTON,
    SETUP_COOKIES,
    PIN_PAD_MARKERS,
    PIN_PAD_SELECTABLE,
    PIN_PAD_SELECTABLE_CURRENT,
    PIN_PAD_POSITIONS,
    WAIT_AFTER_FILLING_PASS_CODE,
    PIN_PAD,
    NEXT_BUTTON,
    WAIT_BEFORE_FILLING_ID_AND_BIRTHDAY,
)


async def login(page: Page):
    await remove_cookies_banner(page)
    await page.wait_for_selector(WAIT_BEFORE_FILLING_ID_AND_BIRTHDAY)
    await fill_id_number(page, config.id_number)
    await fill_birthday(
        page, config.birthday_day, config.birthday_month, config.birthday_year
    )
    await page.click(NEXT_BUTTON)
    await page.wait_for_selector(PIN_PAD)
    await fill_pass_code(page)
    await page.wait_for_selector(WAIT_AFTER_FILLING_PASS_CODE)


async def remove_cookies_banner(page: Page):
    await page.click(SETUP_COOKIES)
    await page.click(CLOSE_COOKIES_BUTTON)


async def fill_id_number(page: Page, id_number: str):
    await page.fill(ID_NUMBER_SELECTOR, id_number)


async def fill_birthday(
    page: Page, birthday_day: str, birthday_month: str, birthday_year: str
):
    await page.fill(INPUT_DAY, birthday_day)
    await page.fill(INPUT_MONTH, birthday_month)
    await page.fill(INPUT_YEAR, birthday_year)


async def pin_pad_is_refillable(inner_html: str):
    if PIN_PAD_SELECTABLE_CURRENT in inner_html or PIN_PAD_SELECTABLE in inner_html:
        return True


async def detect_unfilled_positions(page: Page) -> List[int]:
    pin_pad = await page.query_selector(PIN_PAD_POSITIONS)
    pin_pad = await pin_pad.inner_html()
    pin_pad_numbers = pin_pad.split("<div")[1:]

    pin_pad_positions = [
        i
        for i, pin_pad in enumerate(pin_pad_numbers)
        if await pin_pad_is_refillable(pin_pad)
    ]
    return pin_pad_positions


async def click_on_number(page: Page, number: int):
    await page.click(f"{PIN_PAD_MARKERS}('{number}')")


async def fill_pass_code(page: Page):
    positions = await detect_unfilled_positions(page)

    for position in positions:
        await click_on_number(page, config.pass_code[position])
