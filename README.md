# PlaywrightING

Get your ING account data.

This works for ING ES (Spain), for another country page you need to change LOGIN_URL in constants.py and some selectors
like SETUP_COOKIES in selectors.py.

## Install

    poetry install
    poetry run playwright install

or

    scripts/install.sh


## Commands

Fill out a file like sample.env with your personal data and rename it as .env. 

### Init

    poetry run python pying.py init

or

    scripts/init.sh

### Download

Files with your accounts transactions will be downloaded in the specified download_path (.env) or supplied parameter.

    poetry run python pying.py download [--download_path PATH]

or

    scripts/download.sh [--download_path PATH]

### Show

    poetry run python pying.py show
