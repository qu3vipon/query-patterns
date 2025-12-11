from typing import Protocol, runtime_checkable, TypeAlias, Any


@runtime_checkable
class SQLAlchemyORMLike(Protocol):
    __tablename__: str


@runtime_checkable
class SQLAlchemyTableLike(Protocol):
    name: str
    columns: Any


@runtime_checkable
class DjangoModelLike(Protocol):
    class Meta:
        db_table: str


TableLike: TypeAlias = str | SQLAlchemyORMLike | SQLAlchemyTableLike | DjangoModelLike
