import click
from .command.sqlalchemy import sqlalchemy_cmd
from .command.django import django_cmd


@click.group()
def main():
    pass


main.add_command(sqlalchemy_cmd)
main.add_command(django_cmd)
