# velvet/core/interfaces/wallet.py
from __future__ import annotations
from abc import ABC, abstractmethod


class WalletInterface(ABC):
    """
    Abstract interface for Drive-Fi / token logic.
    """

    @abstractmethod
    def get_balance(self) -> float:
        raise NotImplementedError

    @abstractmethod
    def mint(self, amount: float, reason: str) -> None:
        raise NotImplementedError
