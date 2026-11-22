from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User  # type: ignore
from django.core.management.base import BaseCommand  # type: ignore
from django.db import transaction  # type: ignore

from brews.models import BrewSession, Recipe

DEMO_USER = {
    'username': 'demoUser',
    'password': 'demoUser123',
    'email': 'demoUser@yeastmode.com',
}

# Each recipe lists the brew sessions (batches) to create for it.
DEMO_RECIPES = [
    {
        'name': 'Saison',
        'brew_type': Recipe.BEER,
        'target_gravity': Decimal('1.060'),
        'target_final_gravity': Decimal('1.012'),
        'style': 'Saison',
        'description': 'This is a mild saison.',
        'sessions': [
            {
                'batch_number': 1,
                'status': BrewSession.FERMENTING,
                'brew_date': date(2026, 7, 14),
                'original_gravity': Decimal('1.058'),
            },
        ],
    },
    {
        'name': 'Cyber Red',
        'brew_type': Recipe.BEER,
        'target_gravity': Decimal('1.058'),
        'target_final_gravity': Decimal('1.015'),
        'style': 'Red Ale',
        'description': 'This is an Irish Red Ale.',
        'sessions': [
            {
                'batch_number': 1,
                'status': BrewSession.FERMENTING,
                'brew_date': date(2026, 7, 14),
                'original_gravity': Decimal('1.062'),
            },
        ],
    },
]


class Command(BaseCommand):
    help = (
        'Creates seed data for the database: a demo user with a few recipes '
        'and brew sessions. Safe to run more than once.'
    )

    @transaction.atomic
    def handle(self, *args, **options):
        user = self.create_demo_user()
        for recipe_data in DEMO_RECIPES:
            self.create_recipe(user, recipe_data)
        self.stdout.write(self.style.SUCCESS('Seed data created successfully!'))

    def create_demo_user(self):
        user, created = User.objects.get_or_create(
            username=DEMO_USER['username'],
            defaults={'email': DEMO_USER['email']},
        )
        if created:
            user.set_password(DEMO_USER['password'])
            user.save()
        return user

    def create_recipe(self, owner, recipe_data):
        recipe_data = dict(recipe_data)
        sessions = recipe_data.pop('sessions', [])
        name = recipe_data.pop('name')

        recipe, _ = Recipe.objects.get_or_create(
            owner=owner,
            name=name,
            defaults=recipe_data,
        )
        for session_data in sessions:
            session_data = dict(session_data)
            BrewSession.objects.get_or_create(
                recipe=recipe,
                batch_number=session_data.pop('batch_number'),
                defaults=session_data,
            )
        return recipe
