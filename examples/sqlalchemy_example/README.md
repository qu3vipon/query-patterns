# SQLAlchemy Example
```shell
# From schema (using SQLAlchemy MetaData)
query-patterns sqlalchemy --metadata orm.metadata --module repo

# From database (using a shared in-memory SQLite database via URI mode)
query-patterns sqlalchemy --source db --engine-url "sqlite:///file::memory:?cache=shared&uri=true"
```