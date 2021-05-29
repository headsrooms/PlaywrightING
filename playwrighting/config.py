from pathlib import Path

from configclasses import configclass


@configclass
class Config:
    pass_code: str
    id_number: str
    birthday_day: str
    birthday_month: str
    birthday_year: str
    download_path: str


app_path = Path("~/playwrighting").expanduser()
app_path.mkdir(exist_ok=True)
config = Config.from_path(app_path / ".env")
screenshots_path = app_path / "screenshots"
screenshots_path.mkdir(exist_ok=True)
account_page_screenshot_path = screenshots_path / "account_page.png"
before_timeout_screenshot_path = screenshots_path / "before_timeout.png"
before_error_screenshot_path = screenshots_path / "before_error.png"
