from django.db import models


class User(models.Model):
    email = models.CharField(max_length=255)

    class Meta:
        db_table = "django_users"
        indexes = [
            models.Index(fields=["email"]),
        ]
