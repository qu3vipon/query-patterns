# query-patterns
Declare query-access patterns in code and verify matching DB indexes.
Supports SQLAlchemy and Django, both schema-based and database introspection modes.

## Motivation
As projects grow, the number and variety of database queries increase. 
Over time, it becomes difficult to maintain a consistent set of query-access patterns across the codebase, and even harder to verify whether each pattern is backed by an appropriate database index.
Relying on manual checks or memory often leads to:
- Missing or outdated indexes that cause silent performance regressions
- Inconsistent query patterns across teams or modules
- Schema changes that unintentionally break previously optimized queries
- Performance issues that surface only in production traffic

query-patterns addresses these problems by allowing you to declare expected query patterns in code and validate them against either your ORM schema or a running database instance — all via a simple CLI command.

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
- Can be integrated into CI to enforce index coverage

## Install
```shell
pip install query-patterns
```

## Declare a pattern
```python
from query_patterns import query_pattern


# Declare query pattern using table/column names
class RepoA:
    @query_pattern(table="users", columns=["email"])
    def find(self, email): ...


# Declare query pattern using ORM models(works with both SQLAlchemy and Django models)
from models import User

class RepoB:
    @query_pattern(table=User, columns=[User.email])
    def find(self, email): ...
```

### a. SQLAlchemy Command
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

### b. Django Command
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
