# htf_engine/errors.py
from __future__ import annotations
from abc import ABC, abstractmethod


class ExchangeError(Exception, ABC):
    """
    Abstract base class for all exchange-related errors.

    This class MUST NOT be instantiated directly.
    """

    @property
    @abstractmethod
    def error_code(self) -> str:
        """Machine-readable error code (must be implemented)."""
        ...

    @abstractmethod
    def default_message(self) -> str:
        """Default human-readable message."""
        ...

    def __init__(self, message: str | None = None):
        if type(self) is ExchangeError:
            raise TypeError("ExchangeError is abstract and cannot be instantiated directly")

        self.message = message or self.default_message()
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"
