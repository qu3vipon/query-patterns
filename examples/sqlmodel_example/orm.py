from typing import Optional
from sqlmodel import Field
from sqlalchemy import Index, UniqueConstraint
from sqlmodel import SQLModel, create_engine


class User(SQLModel, table=True):
    __tablename__ = "sm_users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True)
    nickname: str

    __table_args__ = (
        UniqueConstraint("nickname", name="uq_sm_users_nickname"),
    )

engine = create_engine("sqlite:///file::memory:?cache=shared&uri=true")
SQLModel.metadata.create_all(engine)

metadata = SQLModel.metadata
