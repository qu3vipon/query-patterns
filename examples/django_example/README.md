# Django Example

# From schema (using Django models)
PYTHONPATH=. query-patterns django --settings settings

# From database (migrate first, then inspect db)
PYTHONPATH=. python bootstrap_and_run.py
