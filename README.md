# query-patterns
Declare query access patterns in code and verify matching DB indexes.
Supports SQLAlchemy and Django.

## What it does
- Collects all @query_pattern declarations
- Extracts ORM indexes
  - SQLAlchemy: MetaData
  - Django: Model._meta.indexes
- Compares (table, columns) and reports [OK] or [MISSING]

### Example output
- [OK] users('email',)
- [MISSING] orders('user_id',)

## Install
```shell
pip install query-patterns
pip install "query-patterns[sqlalchemy]"
pip install "query-patterns[django]"
```

## Declare a pattern
```python
from query_patterns import query_pattern

class Repo:
    @query_pattern(table="users", columns=["email"])
    def find(self, email): ...
```

### SQLAlchemy
```shell
query-patterns sqlalchemy \
  --module myapp.repo \
  --metadata myapp.metadata.metadata
  
# or auto-discover modules
query-patterns sqlalchemy \
  --metadata myapp.metadata.metadata
```

### Django
```shell
query-patterns django \
  --settings config.settings \
  --module myapp.repo
  
# or auto-discover modules 
query-patterns django \
  --settings config.settings
 ```
