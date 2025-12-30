from __future__ import annotations
from abc import ABC
from .exchange_error import ExchangeError


class InvalidOrderError(ExchangeError, ABC):
    """
    Abstract base class for all invalid-order errors.
    """

    error_code = "INVALID_ORDER"

    def header_string(self) -> str:
        return "Invalid Order: "
