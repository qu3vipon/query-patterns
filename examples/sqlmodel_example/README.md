# SQLModel Example
```shell
# From schema (using SQLModel MetaData)
query-patterns sqlmodel --metadata orm.metadata --module repo

# From database (using a shared in-memory SQLite database via URI mode)
query-patterns sqlmodel --source db --engine-url "sqlite:///file::memory:?cache=shared&uri=true"
```