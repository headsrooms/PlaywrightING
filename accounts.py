import dataclasses
import pickle
from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Union, Tuple, Optional

import pandas as pd
from more_itertools import pairwise
from playwright.async_api import Page
from selectolax.parser import HTMLParser

from constants import IS_ACTIVATED, ACCOUNT_DELIMITER, CARD_DELIMITER
from page_selectors import (
    OVERALL_POSITION_AMOUNT,
    NORMAL_ACCOUNTS,
    SAVINGS_ACCOUNTS,
    MY_PRODUCTS,
)
from transactions import download_transaction_data
from utils import (
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

    @staticmethod
    def create(name: str, remaining_info: Union[str, float]):
        if remaining_info == IS_ACTIVATED:
            return DebitCard(name, transactions=None, is_activated=True)
        return CreditCard(
            name,
            transactions=None,
            expense=get_number_from_string_with_dot_and_comma(remaining_info),
        )

    @abstractmethod
    async def update(self, page: Page) -> "Card":
        raise NotImplementedError

    async def download(self, downloads_path: Path):
        file_path = downloads_path / f"{self.name}.csv"

        if self.transactions is not None:
            self.transactions.to_csv(file_path)


@dataclass(frozen=True)
class CreditCard(Card):
    expense: float

    async def update(self, page: Page) -> Card:
        print(f"Obtaining transactions of {self.name}")
        await page.click(MY_PRODUCTS)
        await page.click(f"text={self.name}")
        transactions = await download_transaction_data(page, is_credit_card=True)

        return dataclasses.replace(self, transactions=transactions)


@dataclass(frozen=True)
class DebitCard(Card):
    is_activated: bool

    async def update(self, page: Page) -> Card:
        print(f"Obtaining transactions of {self.name}")

        await page.click(MY_PRODUCTS)
        await page.click(f"text={self.name}")
        transactions = await download_transaction_data(page)

        return dataclasses.replace(self, transactions=transactions)


@dataclass(frozen=True)
class Account:
    name: str
    balance: float
    transactions: Optional[pd.DataFrame] = None

    @classmethod
    def create(cls, name: str, raw_balance: str):
        return cls(name, balance=get_number_from_string_with_dot_and_comma(raw_balance))

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
    ) -> Tuple[Tuple["Account", ...], Union[Tuple[Card, ...], Tuple]]:
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

        accounts = [account[0:4] for account in accounts]
        accounts = tuple(
            Account.create(name=" ".join(account[:3]), raw_balance=account[-1])
            for account in accounts
        )

        return accounts, cards

    @staticmethod
    async def parse_account(
        page, account_selector: str, account_type: AccountType
    ) -> Tuple[Tuple["Account", ...], Tuple[Card, ...]]:
        accounts = await get_texts_within_css_selector(
            page,
            account_selector,
        )
        return Account.get_account_info(accounts, account_type)

    async def update(self, page: Page) -> "Account":
        print(f"Obtaining transactions of {self.name}")

        await page.click(MY_PRODUCTS)
        await page.click(f"text={self.name}")
        transactions = await download_transaction_data(page)

        return dataclasses.replace(self, transactions=transactions)

    async def download(self, downloads_path: Path):
        file_path = downloads_path / f"{self.name}.csv"

        if self.transactions is not None:
            self.transactions.to_csv(file_path)


@dataclass(frozen=True)
class Position:
    balance: float
    accounts: Tuple[Account, ...]
    cards: Tuple[Card, ...]

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
        normal_accounts, cards = await Account.parse_account(
            page, NORMAL_ACCOUNTS, AccountType.normal
        )
        savings_accounts, _ = await Account.parse_account(
            page, SAVINGS_ACCOUNTS, AccountType.savings
        )
        overall_position = Position(
            total_balance, (*normal_accounts, *savings_accounts), cards
        )
        return overall_position

    async def update(self, page: Page) -> "Position":
        accounts = tuple([await account.update(page) for account in self.accounts])
        cards = tuple([await card.update(page) for card in self.cards])

        return dataclasses.replace(self, accounts=accounts, cards=cards)

    async def download(self, download_path: Path):
        accounts_and_cards = [
            *self.accounts,
            *self.cards,
        ]
        for account_or_card in accounts_and_cards:
            await account_or_card.download(download_path)

    def __eq__(self, other):
        # simplicity works
        # I don't use the autogenerated method because at the beginning we don't have transactions to compare between
        # positions

        if other:
            return self.balance == other.balance

    def save(self):
        with open("state.pkl", "wb") as state_file:
            pickle.dump(self, state_file)

    @staticmethod
    def load() -> Optional["Position"]:
        try:
            with open("state.pkl", "rb") as state_file:
                pickle_data = pickle.load(state_file)
                return pickle_data
        except FileNotFoundError:
            pass
