from django.test import TestCase # type: ignore
import importlib

from django.apps import apps as django_apps # type: ignore
from django.db import IntegrityError, transaction # type: ignore
from brews.models import Adjunct, BrewSession, Grain, Hop, Recipe, Yeast # type: ignore
from django.contrib.auth.models import User # type: ignore


# Create your tests here.

class RecipeModelTest(TestCase):
    def setUp(self):
        demoUser = User.objects.create_user(username='demoUser', password='demoUser123', email='demoUser@yeastmode.com')
        self.recipe = Recipe.objects.create(name='Saison', brew_type='beer', target_gravity='1.060', target_final_gravity='1.012', style='Saison', description='This is a mild saison.', owner=demoUser) 
        
    def test_fields(self):
        self.assertEqual(self.recipe.name, 'Saison')
        self.assertEqual(self.recipe.brew_type, 'beer')
        self.assertEqual(self.recipe.target_gravity, '1.060')
        self.assertEqual(self.recipe.target_final_gravity, '1.012')
        self.assertEqual(self.recipe.style, 'Saison') 
        self.assertEqual(self.recipe.description, 'This is a mild saison.')         
            
    def test_abv(self):
        "Testing to make sure that the abv is calculated correctly for the recipe"
        self.assertEqual(self.recipe.abv, 6.3)

    def test_string(self):
        self.assertEqual(str(self.recipe), 'Saison')


class BrewSessionModelTest(TestCase):
    def setUp(self):
        demoUser = User.objects.create_user(username='demoUser', password='demoUser123', email='demoUser@yeastmode.com')
        self.recipe = Recipe.objects.create(name='Saison', brew_type='beer', target_gravity='1.060', target_final_gravity='1.012', style='Saison', description='This is a mild saison.', owner=demoUser)
        self.session = BrewSession.objects.create(recipe=self.recipe, batch_number='1', status='conditioning', brew_date='2026-07-14', original_gravity='1.058', final_gravity='1.012')

    def test_fields(self):
        self.assertEqual(self.session.recipe, self.recipe)
        self.assertEqual(self.session.batch_number, '1')
        self.assertEqual(self.session.status, 'conditioning')
        self.assertEqual(self.session.brew_date, '2026-07-14')
        self.assertEqual(self.session.original_gravity, '1.058') 
        self.assertEqual(self.session.final_gravity, '1.012')

    def test_abv(self):
        "Testing the abv calculation on the BrewSession."
        self.assertEqual(self.session.abv, 6.04)

    def test_string(self):
        self.assertEqual(str(self.session), 'Saison - Batch #1')

class RecipeViewTest(TestCase):
    def setUp(self):
        demoUser = User.objects.create_user(username='demoUser', password='demoUser123', email='demoUser@yeastmode.com')
        self.recipe = Recipe.objects.create(name='Saison', brew_type='beer', target_gravity='1.060', target_final_gravity='1.012', style='Saison', description='This is a mild saison.', owner=demoUser) 
        self.demoUser2 = User.objects.create_user(username='demoUser2', password='demoUser123', email='demoUser2@yeastmode.com')

    def test_authentication(self):
        response = self.client.get('/dashboard/')
        self.assertRedirects(response, '/login/?next=/dashboard/', status_code=302, target_status_code=200)

    def test_data_isolation(self):
        logged_in = self.client.login(username='demoUser2', password='demoUser123')
        self.assertTrue(logged_in)

        response = self.client.get(f'/recipe/{self.recipe.pk}/')
        self.assertEqual(response.status_code, 404)

class IngredientSeedTest(TestCase):
    """The 0006_seed_ingredients migration runs when the test DB is built."""

    def setUp(self):
        self.migration = importlib.import_module('brews.migrations.0006_seed_ingredients')
        self.tables = [
            (Grain, self.migration.GRAINS),
            (Hop, self.migration.HOPS),
            (Yeast, self.migration.YEASTS),
            (Adjunct, self.migration.ADJUNCTS),
        ]

    def test_seed_populates_all_tables(self):
        for model, items in self.tables:
            with self.subTest(model=model.__name__):
                names = set(model.objects.values_list('name', flat=True))
                self.assertTrue(items)
                self.assertTrue({name for name, _ in items} <= names)

    def test_includes_mead_and_cider_ingredients(self):
        self.assertTrue(Yeast.objects.filter(name='Lalvin EC-1118').exists())
        self.assertTrue(Adjunct.objects.filter(name='Honey').exists())
        self.assertTrue(Adjunct.objects.filter(name='Apple Juice').exists())

    def test_seed_is_idempotent(self):
        before = [model.objects.count() for model, _ in self.tables]
        self.migration.seed_ingredients(django_apps, None)
        after = [model.objects.count() for model, _ in self.tables]
        self.assertEqual(before, after)

    def test_seed_keeps_existing_descriptions(self):
        Hop.objects.filter(name='Cascade').update(description='My notes')
        self.migration.seed_ingredients(django_apps, None)
        self.assertEqual(Hop.objects.get(name='Cascade').description, 'My notes')

    def test_ingredient_names_are_unique(self):
        for model, items in self.tables:
            with self.subTest(model=model.__name__):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    model.objects.create(name=items[0][0])

    def test_ingredients_ordered_by_name(self):
        names = list(Hop.objects.values_list('name', flat=True))
        self.assertEqual(names, sorted(names))
