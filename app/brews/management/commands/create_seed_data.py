from django.core.management.base import BaseCommand # type: ignore
from django.contrib.auth.models import User # type: ignore
from brews.models import Recipe, BrewSession

class Command(BaseCommand):
    help = 'This command is to create seed data for the database. Creates a demo user that has a few recipes and a few batches for those recipes'

    def handle(self, *args, **options):
        demoUser = User.objects.create_user(username='demoUser', password='demoUser123', email='demoUser@yeastmode.com')
        demoRecipe1 = Recipe.objects.create(name='Saison', brew_type='beer', target_gravity='1.060', target_final_gravity='1.012', style='Saison', description='This is a mild saison.', owner=demoUser) 
        demoSession1 = BrewSession.objects.create(recipe=demoRecipe1, batch_number='1', status='fermenting', brew_date='2026-07-14', original_gravity='1.058')
        demoRecipe2 = Recipe.objects.create(name='Cyber Red', brew_type='beer', target_gravity='1.058', target_final_gravity='1.015', style='Red Ale', description='This is an Irish Red Ale.', owner=demoUser)
        demoSession2 = BrewSession.objects.create(recipe=demoRecipe2, batch_number='1', status='fermenting', brew_date='2026-07-14', original_gravity='1.062')
        self.stdout.write(self.style.SUCCESS('Seed data created successfully!')) 
        
