# query-patterns
Declare query-access patterns in code and verify matching DB indexes.
Supports SQLAlchemy and Django, both schema-based and database introspection modes.

## What it does
- Collects all @query_pattern declarations from your Python modules
- Extracts index definitions from:
  - SQLAlchemy 
    - ORM schema (MetaData)
    - Actual DB (Inspector)
  - Django 
    - ORM schema (Model._meta.indexes)
    - Actual DB (connection.introspection)
- Compares (table, columns) tuples
- Reports:
  - [OK] — index exists
  - [MISSING] — index missing
- Can be integrated into CI to enforce index coverage

### Example output
- [OK] users('email',)
- [MISSING] orders('user_id',)

## Install
```shell
pip install query-patterns
```

## Declare a pattern
```python
from query_patterns import query_pattern

class Repo:
    @query_pattern(table="users", columns=["email"])
    def find(self, email): ...
```

### 1. SQLAlchemy Command
```shell
# Reads indexes from MetaData
query-patterns sqlalchemy \
  --metadata myapp.db.metadata \
  --module myapp.repo
  
# Auto-discover modules
query-patterns sqlalchemy \
  --metadata myapp.db.metadata
  
# Reads actual indexes from the database
query-patterns sqlalchemy \
  --source db \
  --engine-url postgresql://user:pass@localhost/mydb \
  --module myapp.repo
```

### 2. Django Command
```shell
# Reads Model._meta.indexes from installed apps
query-patterns django \
  --settings config.settings \
  --module myapp.repo
  
# Auto-discover modules 
query-patterns django \
  --settings config.settings
  
# Reads actual DB indexes using Django introspection
query-patterns django \
  --source db \
  --settings config.settings \
  --module myapp.repo
 ```
