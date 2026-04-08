from dataclasses import dataclass
from typing import Optional


@dataclass
class Transaction:
    id: Optional[int]
    tx_type: str
    from_account: str
    to_account: str
    amount: int
    note: Optional[str] = None
    created_at: Optional[str] = None
