import dataclasses
import pickle
from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Union, Tuple, Optional

import pandas as pd
from more_itertools import pairwise
from playwright.async_api import Page
from rich import print
from selectolax.parser import HTMLParser

from playwrighting.config import app_path
from playwrighting.constants import (
    IS_ACTIVATED,
    ACCOUNT_DELIMITER,
    CARD_DELIMITER,
    STATE_FILE_NAME,
)
from playwrighting.page_selectors import (
    OVERALL_POSITION_AMOUNT,
    NORMAL_ACCOUNTS,
    SAVINGS_ACCOUNTS,
    MY_PRODUCTS,
)
from playwrighting.transactions import get_new_transactions
from playwrighting.utils import (
    get_number_from_string_with_dot_and_comma,
    get_texts_within_css_selector,
)


class AccountType(Enum):
    normal = "normal"
    savings = "savings"


@dataclass(frozen=True)
class Card:
    name: str
    transactions: Optional[pd.DataFrame]
    last_update: Optional[datetime]

    @staticmethod
    def create(name: str, remaining_info: Union[str, float]):
        if remaining_info == IS_ACTIVATED:
            return DebitCard(
                name, transactions=None, is_activated=True, last_update=None
            )
        return CreditCard(
            name,
            transactions=None,
            expense=get_number_from_string_with_dot_and_comma(remaining_info),
            last_update=None,
        )

    @abstractmethod
    async def update(self, page: Page) -> "Card":
        raise NotImplementedError

    async def download(self, download_path: Path):
        file_path = download_path / f"{self.name}.csv"

        if self.transactions is not None:
            self.transactions.to_csv(file_path)

        print(f"The card transactions have been downloaded as {file_path.resolve()}")


@dataclass(frozen=True)
class CreditCard(Card):
    expense: float

    async def update(self, page: Page) -> Card:
        print(f"Obtaining transactions of {self.name}")
        await page.click(MY_PRODUCTS)
        await page.click(f"text={self.name}")
        transactions = await get_new_transactions(
            page, self.last_update, is_credit_card=True
        )
        transactions = (
            pd.concat([self.transactions, transactions])
            .drop_duplicates()
            .sort_index(ascending=False)
        )

        return dataclasses.replace(
            self, transactions=transactions, last_update=datetime.now()
        )


@dataclass(frozen=True)
class DebitCard(Card):
    is_activated: bool

    async def update(self, page: Page) -> Card:
        print(f"Obtaining new transactions of {self.name}")

        await page.click(MY_PRODUCTS)
        await page.click(f"text={self.name}")
        transactions = await get_new_transactions(page, self.last_update)
        transactions = (
            pd.concat([self.transactions, transactions])
            .drop_duplicates()
            .sort_index(ascending=False)
        )

        return dataclasses.replace(
            self, transactions=transactions, last_update=datetime.now()
        )


@dataclass(frozen=True)
class Account:
    name: str
    balance: float
    cards: Tuple[Card, ...]
    transactions: Optional[pd.DataFrame] = None
    last_update: Optional[datetime] = None

    @classmethod
    def create(cls, name: str, raw_balance: str, cards: Tuple[Card, ...]):
        return cls(
            name,
            balance=get_number_from_string_with_dot_and_comma(raw_balance),
            cards=cards,
        )

    @staticmethod
    def get_cards(accounts: List[List[str]]):
        cards_indexes = [
            [i for i, chunk in enumerate(account) if chunk == CARD_DELIMITER]
            for account in accounts
        ]
        cards_indexes = [
            card_index + [len(account)]
            for account, card_index in zip(accounts, cards_indexes)
        ]
        cards_indexes = [
            [pairs for pairs in list(pairwise(card_index))]
            for card_index in cards_indexes
        ]

        return [
            account[beginning:end]
            for account, pairs in zip(accounts, cards_indexes)
            for beginning, end in pairs
        ]

    @staticmethod
    def get_account_info(
        info: List[str], account_type: AccountType
    ) -> Tuple["Account", ...]:
        account_indexes = [
            i for i, chunk in enumerate(info) if chunk == ACCOUNT_DELIMITER
        ]
        account_indexes.append(len(info))
        account_indexes = pairwise(account_indexes)

        accounts = [info[beginning:end] for beginning, end in account_indexes]

        if account_type == AccountType.normal:
            cards = Account.get_cards(accounts)
            cards = tuple(
                Card.create(name=" ".join(card[:3]), remaining_info=card[-1])
                for card in cards
            )
        else:
            cards = ()

        accounts_cards = [" ".join(account) for account in accounts]
        accounts = [account[0:4] for account in accounts]

        accounts_with_cards = []
        for i, account in enumerate(accounts):
            cards_in_this_account = tuple(
                [card for card in cards if card.name in accounts_cards[i]]
            )
            accounts_with_cards.append(
                Account.create(
                    name=" ".join(account[:3]),
                    raw_balance=account[-1],
                    cards=cards_in_this_account,
                )
            )
        return tuple(accounts_with_cards)

    @staticmethod
    async def parse_account(
        page, account_selector: str, account_type: AccountType
    ) -> Tuple["Account", ...]:
        accounts = await get_texts_within_css_selector(
            page,
            account_selector,
        )
        return Account.get_account_info(accounts, account_type)

    async def update(self, page: Page) -> "Account":
        print(f"Obtaining transactions of {self.name}")

        cards = tuple([await card.update(page) for card in self.cards])

        await page.click(MY_PRODUCTS)
        await page.click(f"text={self.name}")
        transactions = await get_new_transactions(page, self.last_update)
        transactions = (
            pd.concat([self.transactions, transactions])
            .drop_duplicates()
            .sort_index(ascending=False)
        )

        return dataclasses.replace(
            self, transactions=transactions, cards=cards, last_update=datetime.now()
        )

    async def download(self, download_path: Path):
        file_path = download_path / f"{self.name}.csv"

        if self.transactions is not None:
            self.transactions.to_csv(file_path)

        for card in self.cards:
            await card.download(download_path)

        print(f"The account transactions have been downloaded as {file_path.resolve()}")


@dataclass(frozen=True)
class Position:
    balance: float
    accounts: Tuple[Account, ...]
    last_update: datetime

    @staticmethod
    async def parse_balance(page: Page) -> Tuple[float, str]:
        page_content = await page.content()
        tree = HTMLParser(page_content)

        if tree.body:
            amount, currency = (
                tree.body.css(OVERALL_POSITION_AMOUNT)[0]
                .text(separator="\n", strip=True)
                .split()
            )
            return get_number_from_string_with_dot_and_comma(amount), currency

    @staticmethod
    async def create(page: Page):
        total_balance, currency = await Position.parse_balance(page)
        await page.click(MY_PRODUCTS)
        normal_accounts = await Account.parse_account(
            page, NORMAL_ACCOUNTS, AccountType.normal
        )
        savings_accounts = await Account.parse_account(
            page, SAVINGS_ACCOUNTS, AccountType.savings
        )
        overall_position = Position(
            total_balance,
            (*normal_accounts, *savings_accounts),
            last_update=datetime.now(),
        )
        return overall_position

    async def update(self, page: Page) -> "Position":
        accounts = tuple([await account.update(page) for account in self.accounts])

        return dataclasses.replace(self, accounts=accounts)

    async def download(self, download_path: Path):
        for account in self.accounts:
            await account.download(download_path)

    def __eq__(self, other):
        # simplicity works
        # I don't use the autogenerated method because at the beginning we don't have transactions to compare between
        # positions

        if other:
            return self.balance == other.balance

    def save(self):
        with open(app_path / STATE_FILE_NAME, "wb") as state_file:
            pickle.dump(self, state_file)

    @staticmethod
    def load() -> Optional["Position"]:
        try:
            with open(app_path / STATE_FILE_NAME, "rb") as state_file:
                pickle_data = pickle.load(state_file)
                return pickle_data
        except FileNotFoundError:
            pass
