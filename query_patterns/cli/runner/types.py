from typing import NewType, Literal

TableName = NewType("TableName", str)
IndexColumns = tuple[str, ...]
IndexRecord = tuple[TableName, IndexColumns]
IndexSet = set[IndexRecord]
PatternSource = Literal["schema", "db"]
