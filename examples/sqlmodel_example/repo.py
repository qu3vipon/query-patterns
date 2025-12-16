from orm import User
from query_patterns import query_pattern


class Repo:
    @query_pattern(table=User, columns=[User.id])
    def find_by_id(self, email: str):
        pass

    @query_pattern(table="sm_users", columns=["nickname"])
    def find_by_nickname(self, email: str):
        pass

    @query_pattern(table="sm_users", columns=["email"])
    def find_by_email(self, email: str):
        pass

    @query_pattern(table="sm_users", columns=["age"])
    def find_by_age(self, email: str):
        pass
