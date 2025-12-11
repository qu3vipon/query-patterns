from __future__ import annotations

import os


def setup_django(settings_module: str | None = None) -> None:
    """
    Initialize Django so that model metadata is available.

    If `settings_module` is provided, use it as the DJANGO_SETTINGS_MODULE.
    Otherwise, fall back to the environment variable.

    This function ensures:
      - Django is installed
      - settings are configured
      - django.setup() is called
    """
    try:
        import django  # noqa: F401
    except ImportError as e:
        raise RuntimeError(
            "Django support requires installing the 'django' extra "
            "(e.g. 'pip install query-patterns[django]')"
        ) from e

    # Set Django settings module if provided
    if settings_module:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)

    # Ensure settings are available
    if not os.environ.get("DJANGO_SETTINGS_MODULE"):
        raise RuntimeError(
            "DJANGO_SETTINGS_MODULE is not set. Use --settings option "
            "or set the environment variable."
        )

    # Initialize Django
    import django  # noqa
    django.setup()


def collect_django_indexes():
    """
    Collect all indexes defined on Django models.

    Returns:
        A set of (table_name, (field1, field2, ...)) representing indexes.
    """
    from django.apps import apps

    indexes: set[tuple[str, tuple[str, ...]]] = set()

    # Iterate over all registered Django models
    for model in apps.get_models():
        table = model._meta.db_table

        # Collect index definitions explicitly declared on the model
        for index in model._meta.indexes:
            cols = tuple(index.fields)
            indexes.add((table, cols))

        # NOTE:
        # unique_together, constraints, or implicit PK indexes are not included
        # here yet. They can be added later depending on desired behavior.

    return indexes
