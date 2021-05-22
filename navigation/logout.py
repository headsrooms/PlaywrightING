from playwright.async_api import Page

from page_selectors import LOGOUT_BUTTON, LOGOUT_CLOSE


async def logout(page: Page):
    await page.click(LOGOUT_BUTTON)
    await page.click(LOGOUT_CLOSE)
