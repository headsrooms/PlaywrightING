from datetime import datetime
from pathlib import Path

from configclasses import configclass
from configclasses.configclasses import dump
from configclasses.exceptions import ConfigFilePathDoesNotExist
from rich import print
from rich.prompt import Prompt


@configclass
class Config:
    pass_code: str
    id_number: str
    birthday_day: str
    birthday_month: str
    birthday_year: str
    download_path: str

    @classmethod
    def ask_for_config_parameters(cls, root_path: Path) -> "Config":
        print(
            f"Configuration file doesn't exist in the expected path {root_path / '.env'}"
        )
        config_parameters = {
            "pass_code": Prompt.ask("Enter your security code"),
            "id_number": Prompt.ask("Enter your ID number"),
            "birthday": Prompt.ask("Enter your birthday date (e.g: 31/05/1994)"),
            "download_path": Prompt.ask(
                "Enter a default download path", default=str(root_path / "downloads")
            ),
        }
        birthday = datetime.strptime(config_parameters["birthday"], "%d/%m/%Y")
        config_parameters["birthday_day"] = str(birthday.day).zfill(2)
        config_parameters["birthday_month"] = str(birthday.month).zfill(2)
        config_parameters["birthday_year"] = str(birthday.year)
        config_parameters.pop("birthday")

        return cls(**config_parameters)


app_path = Path("~/playwrighting").expanduser()
app_path.mkdir(exist_ok=True)
config_path = app_path / ".env"

try:
    config = Config.from_path(config_path)
except ConfigFilePathDoesNotExist:
    config = Config.ask_for_config_parameters(app_path)
    dump(config, config_path)

screenshots_path = app_path / "screenshots"
screenshots_path.mkdir(exist_ok=True)
account_page_screenshot_path = screenshots_path / "account_page.png"
before_timeout_screenshot_path = screenshots_path / "before_timeout.png"
before_error_screenshot_path = screenshots_path / "before_error.png"
