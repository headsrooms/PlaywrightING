# PlaywrightING

Get your ING account data. WIP

This works for ING ES (Spain), for another country page you need to change LOGIN_URL in constants.py and some selectors
like SETUP_COOKIES in selectors.py.

## Install

    poetry install
    poetry run playwright install

## Run

Fill out a file like sample.env with your personal data and rename it as .env. Then:

    poetry run python main.py

## Downloads

Files with your accounts transactions will be downloaded in the specified downloads_path.
