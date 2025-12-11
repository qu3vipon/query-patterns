def collect_sqlalchemy_indexes(metadata: "MetaData"):
    """
    Returns:
        set of (table_name, (col1, col2, ...))
    """
    indexes = set()

    for table in metadata.tables.values():
        for index in table.indexes:
            indexes.add(
                (table.name, tuple(index.columns.keys()))
            )

    return indexes
