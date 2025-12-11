from dataclasses import dataclass
from typing import Tuple

@dataclass(frozen=True)
class QueryPattern:
    table: str
    columns: Tuple[str, ...]
