from typing import List

from playwright.async_api import Page, TimeoutError as PlayWrightTimeout
from selectolax.parser import HTMLParser


def get_number_from_string_with_dot_and_comma(amount) -> float:
    return float(amount.replace(".", "").replace(",", ".").replace("€", ""))


async def get_texts_within_css_selector(page: Page, selector: str):
    page_content = await page.content()
    tree = HTMLParser(page_content)

    if tree.body:
        return tree.body.css(selector)[0].text(separator="\n", strip=True).split()


async def click_on_selectors_list(
    page: Page, selectors: List[str], timeout: int = None
):
    for selector in selectors:
        try:
            print(f"Before clicking {selector}")
            await page.click(selector, timeout=timeout)
        except PlayWrightTimeout:
            print(f"Error clicking {selector}")
            continue
        else:
            print(f"After clicking {selector}")
            break
