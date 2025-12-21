from .exchange_error import ExchangeError


class InstrumentNotFoundError(ExchangeError):
    error_code = "INSTRUMENT_NOT_FOUND"

    def __init__(self, instrument: str):
        self.instrument = instrument
        super().__init__()

    def default_message(self) -> str:
        return f"Instrument '{self.instrument}' does not exist in the exchange."
