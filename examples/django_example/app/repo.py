from query_patterns import query_pattern


class Repo:
    @query_pattern(table="django_users", columns=["email"])
    def find_by_email(self):
        pass

    @query_pattern(table="django_users", columns=["nickname"])
    def find_by_nickname(self, email: str):
        pass

    @query_pattern(table="django_users", columns=["nickname"])
    def find_by_nickname2(self, email: str):
        pass
