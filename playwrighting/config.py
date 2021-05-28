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
config = Config.from_path(app_path / ".env")
