from configclasses import configclass


@configclass
class Config:
    pass_code: str
    id_number: str
    birthday_day: str
    birthday_month: str
    birthday_year: str
    downloads_path: str


config = Config.from_path(".env")
