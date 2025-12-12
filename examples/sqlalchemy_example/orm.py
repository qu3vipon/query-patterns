from sqlalchemy import MetaData, Table, Column, Integer, String, Index, create_engine

engine_url = "sqlite:///file::memory:?cache=shared&uri=true"

engine = create_engine(engine_url)
metadata = MetaData()

Table(
    "sa_users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String),
    Index("ix_sa_users_email", "email"),
)

metadata.create_all(engine)
