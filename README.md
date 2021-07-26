# PlaywrightING

Get your ING bank account data.

This works for ING ES (Spain), for another country page you will have to change some values in constants.py and some and
selectors.py.

## Install

    pip install playwrighting

## Commands

To inspect all CLI commands use:

    pying

### Init

This command will initialize the app, scraping your bank data from your account and creating an internal file that will
have your global position (cards, accounts and transactions).

    pying init

### Update

This command will try to update your account info, if there are some changes. You can force the update with parameter
--force.

    pying update [--force]

### Download

Files (csv) with your accounts transactions will be downloaded in the specified download_path or supplied parameter
--download path.

    pying download [--download_path PATH]

### Show

Interactive prompt to show position, accounts or transactions information.

    pying show

## Build

    poetry build