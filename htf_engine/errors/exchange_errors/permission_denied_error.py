from .exchange_error import ExchangeError


class PermissionDeniedError(ExchangeError):
    error_code = "PERMISSION_DENIED"

    def __init__(self, user_id: str, required_level: int, actual_level: int):
        self.user_id = user_id
        self.required_level = required_level
        self.actual_level = actual_level
        super().__init__()

    def default_message(self) -> str:
        return (
            f"User '{self.user_id}' does not have sufficient permissions "
            f"(required={self.required_level}, actual={self.actual_level})."
        )
