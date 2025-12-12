import os
import django
from django.core.management import call_command
from query_patterns.cli.main import main as cli_main


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    django.setup()

    call_command("migrate", run_syncdb=True, verbosity=1)

    cli_main(
        [
            "django",
            "--settings",
            "settings",
            "--source",
            "db",
        ]
    )


if __name__ == "__main__":
    main()
