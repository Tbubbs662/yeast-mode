from django.core.management.base import BaseCommand # type: ignore
from django.core.management import call_command # type: ignore

class Command(BaseCommand):
    help = 'This command is to run the migrate commands, seed data, and superuser all in one go.'

    def handle(self, *args, **options):
        call_command("makemigrations")
        call_command("migrate")
        call_command("createsuperuser")
        call_command("create_seed_data")
        self.stdout.write(self.style.SUCCESS('Systems initiated!'))
