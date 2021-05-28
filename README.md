# PlaywrightING

Get your ING account data.

This works for ING ES (Spain), for another country page you need to change LOGIN_URL in constants.py and some selectors
like SETUP_COOKIES in selectors.py.

## Install

    pip install playwrighting

## Commands

Fill out a file like sample.env with your personal data and rename it as .env.

### Init

    pying init

### Update

    pying update [--force]


### Download

Files with your accounts transactions will be downloaded in the specified download_path (.env) or supplied parameter.

    pying download [--download_path PATH]

### Show

    pying show
