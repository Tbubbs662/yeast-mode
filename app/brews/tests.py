from django.test import TestCase # type: ignore
import importlib

from django.apps import apps as django_apps # type: ignore
from decimal import Decimal

from django.core.exceptions import ValidationError # type: ignore
from django.db import IntegrityError, transaction # type: ignore
from django.db.models import ProtectedError # type: ignore
from brews.models import ( # type: ignore
    Adjunct, BrewSession, Grain, Hop, Recipe, RecipeAdjunct, RecipeGrain, RecipeHop, Yeast,
)
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


class RecipeIngredientAmountTest(TestCase):
    def setUp(self):
        owner = User.objects.create_user(username='brewer', password='brewer123')
        self.recipe = Recipe.objects.create(name='Pale Ale', owner=owner)
        self.cascade = Hop.objects.get(name='Cascade')
        self.two_row = Grain.objects.get(name='2-Row Pale Malt')
        self.honey = Adjunct.objects.get(name='Honey')

    def test_hop_addition(self):
        bittering = RecipeHop.objects.create(recipe=self.recipe, hop=self.cascade, amount=Decimal('1.00'), time=60)
        dry_hop = RecipeHop.objects.create(recipe=self.recipe, hop=self.cascade, amount=Decimal('2.5'), use=RecipeHop.DRY_HOP, time=3)
        flameout = RecipeHop.objects.create(recipe=self.recipe, hop=self.cascade, amount=Decimal('1'), use=RecipeHop.WHIRLPOOL)
        self.assertEqual(str(bittering), '1 oz Cascade (Boil, 60 min)')
        self.assertEqual(str(dry_hop), '2.5 oz Cascade (Dry hop, 3 days)')
        self.assertEqual(str(flameout), '1 oz Cascade (Whirlpool)')
        # The same hop can be added more than once, in the order entered.
        self.assertEqual(list(self.recipe.hop_additions.all()), [bittering, dry_hop, flameout])

    def test_grain_bill(self):
        grain = RecipeGrain.objects.create(recipe=self.recipe, grain=self.two_row, amount=Decimal('10'))
        self.assertEqual(str(grain), '10 lb 2-Row Pale Malt')
        self.assertEqual(list(self.recipe.grain_bill.all()), [grain])

    def test_adjunct_addition(self):
        adjunct = RecipeAdjunct.objects.create(recipe=self.recipe, adjunct=self.honey, amount=Decimal('3'), added_when=RecipeAdjunct.SECONDARY)
        self.assertEqual(str(adjunct), '3 lb Honey (Secondary)')
        self.assertEqual(list(self.recipe.adjunct_additions.all()), [adjunct])

    def test_yeast_and_amount(self):
        self.recipe.yeast = Yeast.objects.get(name='SafAle US-05')
        self.recipe.yeast_amount = Decimal('2')
        self.recipe.full_clean()
        self.recipe.save()
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.yeast.name, 'SafAle US-05')
        self.assertEqual(self.recipe.yeast_amount, Decimal('2'))

    def test_amounts_must_be_positive(self):
        for line in (
            RecipeHop(recipe=self.recipe, hop=self.cascade, amount=Decimal('0')),
            RecipeGrain(recipe=self.recipe, grain=self.two_row, amount=Decimal('-1')),
            RecipeAdjunct(recipe=self.recipe, adjunct=self.honey, amount=Decimal('0')),
        ):
            with self.subTest(line=type(line).__name__):
                with self.assertRaises(ValidationError):
                    line.full_clean()
        self.recipe.yeast_amount = Decimal('0')
        with self.assertRaises(ValidationError):
            self.recipe.full_clean()

    def test_ingredient_in_use_cannot_be_deleted(self):
        RecipeHop.objects.create(recipe=self.recipe, hop=self.cascade, amount=Decimal('1'))
        RecipeGrain.objects.create(recipe=self.recipe, grain=self.two_row, amount=Decimal('10'))
        RecipeAdjunct.objects.create(recipe=self.recipe, adjunct=self.honey, amount=Decimal('1'))
        for ingredient in (self.cascade, self.two_row, self.honey):
            with self.subTest(ingredient=str(ingredient)):
                with self.assertRaises(ProtectedError):
                    ingredient.delete()

    def test_deleting_recipe_removes_its_line_items(self):
        RecipeHop.objects.create(recipe=self.recipe, hop=self.cascade, amount=Decimal('1'))
        RecipeGrain.objects.create(recipe=self.recipe, grain=self.two_row, amount=Decimal('10'))
        RecipeAdjunct.objects.create(recipe=self.recipe, adjunct=self.honey, amount=Decimal('1'))
        self.recipe.delete()
        self.assertEqual(RecipeHop.objects.count(), 0)
        self.assertEqual(RecipeGrain.objects.count(), 0)
        self.assertEqual(RecipeAdjunct.objects.count(), 0)
        self.assertTrue(Hop.objects.filter(pk=self.cascade.pk).exists())

    def test_admin_recipe_page_shows_ingredient_inlines(self):
        admin_user = User.objects.create_superuser(username='admin', password='admin123')
        self.client.force_login(admin_user)
        response = self.client.get(f'/admin/brews/recipe/{self.recipe.pk}/change/')
        self.assertEqual(response.status_code, 200)
        for prefix in ('grain_bill', 'hop_additions', 'adjunct_additions', 'yeast_amount'):
            self.assertContains(response, prefix)


class RecipeHopFormViewTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='brewer', password='brewer123')
        self.client.force_login(self.owner)
        self.cascade = Hop.objects.get(name='Cascade')
        self.citra = Hop.objects.get(name='Citra')

    def post_data(self, hops, initial=0, **recipe_fields):
        data = {
            'name': 'Pale Ale', 'brew_type': 'beer', 'style': '', 'target_gravity': '',
            'target_final_gravity': '', 'description': '', 'notes': '',
            'hops-TOTAL_FORMS': str(len(hops)), 'hops-INITIAL_FORMS': str(initial),
            'hops-MIN_NUM_FORMS': '0', 'hops-MAX_NUM_FORMS': '1000',
        }
        data.update(recipe_fields)
        for i, hop in enumerate(hops):
            for key, value in hop.items():
                data[f'hops-{i}-{key}'] = value
        return data

    def test_form_pages_render_hop_formset(self):
        recipe = Recipe.objects.create(name='Pale Ale', owner=self.owner)
        for url in ('/recipe/new/', f'/recipe/{recipe.pk}/edit/'):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(response, 'name="hops-TOTAL_FORMS"')
                self.assertContains(response, 'data-formset-empty')
                self.assertContains(response, 'Cascade')

    def test_session_form_has_no_hop_section(self):
        recipe = Recipe.objects.create(name='Pale Ale', owner=self.owner)
        response = self.client.get(f'/recipe/{recipe.pk}/session/new/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'hops-TOTAL_FORMS')

    def test_create_recipe_with_hops(self):
        response = self.client.post('/recipe/new/', self.post_data([
            {'hop': self.cascade.pk, 'amount': '1', 'unit': 'oz', 'use': 'boil', 'time': '60'},
            {'hop': self.citra.pk, 'amount': '2', 'unit': 'oz', 'use': 'dry_hop', 'time': '3'},
        ]))
        recipe = Recipe.objects.get(name='Pale Ale')
        self.assertRedirects(response, f'/recipe/{recipe.pk}/')
        self.assertEqual(recipe.owner, self.owner)
        self.assertEqual(
            [str(h) for h in recipe.hop_additions.all()],
            ['1 oz Cascade (Boil, 60 min)', '2 oz Citra (Dry hop, 3 days)'],
        )

    def test_blank_extra_row_is_ignored(self):
        response = self.client.post('/recipe/new/', self.post_data([
            {'hop': '', 'amount': '', 'unit': 'oz', 'use': 'boil', 'time': ''},
        ]))
        recipe = Recipe.objects.get(name='Pale Ale')
        self.assertRedirects(response, f'/recipe/{recipe.pk}/')
        self.assertEqual(recipe.hop_additions.count(), 0)

    def test_invalid_hop_row_saves_nothing(self):
        response = self.client.post('/recipe/new/', self.post_data([
            {'hop': self.cascade.pk, 'amount': '1', 'unit': 'oz', 'use': 'boil', 'time': '60'},
            {'hop': self.citra.pk, 'amount': '0', 'unit': 'oz', 'use': 'boil', 'time': ''},
        ]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Amount: Ensure this value is greater than or equal to 0.01.')
        self.assertFalse(Recipe.objects.exists())
        self.assertFalse(RecipeHop.objects.exists())

    def test_edit_updates_adds_and_removes_hops(self):
        recipe = Recipe.objects.create(name='Pale Ale', owner=self.owner)
        keep = RecipeHop.objects.create(recipe=recipe, hop=self.cascade, amount=Decimal('1'), time=60)
        remove = RecipeHop.objects.create(recipe=recipe, hop=self.citra, amount=Decimal('1'), time=10)
        response = self.client.post(f'/recipe/{recipe.pk}/edit/', self.post_data([
            {'id': keep.pk, 'hop': self.cascade.pk, 'amount': '1.5', 'unit': 'oz', 'use': 'boil', 'time': '45'},
            {'id': remove.pk, 'hop': self.citra.pk, 'amount': '1', 'unit': 'oz', 'use': 'boil', 'time': '10', 'DELETE': 'on'},
            {'hop': self.citra.pk, 'amount': '28', 'unit': 'g', 'use': 'whirlpool', 'time': ''},
        ], initial=2))
        self.assertRedirects(response, f'/recipe/{recipe.pk}/')
        self.assertEqual(
            [str(h) for h in recipe.hop_additions.all()],
            ['1.5 oz Cascade (Boil, 45 min)', '28 g Citra (Whirlpool)'],
        )

    def test_cannot_edit_another_recipes_hop_row(self):
        other_owner = User.objects.create_user(username='other', password='other123')
        other_recipe = Recipe.objects.create(name='Theirs', owner=other_owner)
        their_hop = RecipeHop.objects.create(recipe=other_recipe, hop=self.cascade, amount=Decimal('1'))
        recipe = Recipe.objects.create(name='Pale Ale', owner=self.owner)
        response = self.client.post(f'/recipe/{recipe.pk}/edit/', self.post_data([
            {'id': their_hop.pk, 'hop': self.citra.pk, 'amount': '5', 'unit': 'oz', 'use': 'boil', 'time': ''},
        ], initial=1))
        # Django ignores rows whose id isn't part of this recipe.
        self.assertRedirects(response, f'/recipe/{recipe.pk}/')
        self.assertEqual(recipe.hop_additions.count(), 0)
        their_hop.refresh_from_db()
        self.assertEqual(their_hop.recipe, other_recipe)
        self.assertEqual(their_hop.hop, self.cascade)
        self.assertEqual(their_hop.amount, Decimal('1'))
