from __future__ import annotations
from abc import ABC
from .exchange_error import ExchangeError


class RejectedOrderError(ExchangeError, ABC):
    """
    Abstract base class for all rejected-order errors.
    """

    error_code = "REJECTED_ORDER"

    def header_string(self) -> str:
        return "Rejected Order: "
