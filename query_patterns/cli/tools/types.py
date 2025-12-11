from typing import NewType

TableName = NewType("TableName", str)
IndexColumns = tuple[str, ...]
IndexRecord = tuple[TableName, IndexColumns]
IndexSet = set[IndexRecord]
