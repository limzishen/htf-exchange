from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class UserAction:
    timestamp: datetime
    user_id: str
    username: str
    action: str

    def __str__(self):
        ts = self.timestamp.isoformat().replace("+00:00", "Z")
        return f"{ts} | {self.user_id} | {self.username} | {self.action}"

