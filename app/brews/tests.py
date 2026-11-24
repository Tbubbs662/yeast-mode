from django.test import TestCase # type: ignore
import importlib

from django.apps import apps as django_apps # type: ignore
from decimal import Decimal

from django.core.exceptions import ValidationError # type: ignore
from django.db import IntegrityError, connection, transaction # type: ignore
from django.test.utils import CaptureQueriesContext # type: ignore
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


class RecipeFormPostMixin:
    """Builds POST data for the recipe form and its three ingredient formsets."""

    def post_data(self, hops=(), initial=0, grains=(), adjuncts=(), grain_initial=0, adjunct_initial=0, **recipe_fields):
        data = {
            'name': 'Pale Ale', 'brew_type': 'beer', 'style': '', 'target_gravity': '',
            'target_final_gravity': '', 'description': '', 'notes': '',
        }
        data.update(recipe_fields)
        for prefix, rows, initial_forms in (
            ('hops', hops, initial),
            ('grains', grains, grain_initial),
            ('adjuncts', adjuncts, adjunct_initial),
        ):
            data.update({
                f'{prefix}-TOTAL_FORMS': str(len(rows)), f'{prefix}-INITIAL_FORMS': str(initial_forms),
                f'{prefix}-MIN_NUM_FORMS': '0', f'{prefix}-MAX_NUM_FORMS': '1000',
            })
            for i, row in enumerate(rows):
                for key, value in row.items():
                    data[f'{prefix}-{i}-{key}'] = value
        return data


class RecipeHopFormViewTest(RecipeFormPostMixin, TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='brewer', password='brewer123')
        self.client.force_login(self.owner)
        self.cascade = Hop.objects.get(name='Cascade')
        self.citra = Hop.objects.get(name='Citra')

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


class RecipeGrainAdjunctFormViewTest(RecipeFormPostMixin, TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='brewer', password='brewer123')
        self.client.force_login(self.owner)
        self.two_row = Grain.objects.get(name='2-Row Pale Malt')
        self.crystal = Grain.objects.get(name='Crystal 40L')
        self.honey = Adjunct.objects.get(name='Honey')
        self.orange_peel = Adjunct.objects.get(name='Orange Peel')
        self.cascade = Hop.objects.get(name='Cascade')

    def test_form_renders_all_sections_in_brewing_order(self):
        response = self.client.get('/recipe/new/')
        html = response.content.decode()
        for prefix in ('grains', 'hops', 'adjuncts'):
            self.assertIn(f'name="{prefix}-TOTAL_FORMS"', html)
        self.assertLess(html.index('data-formset="grains"'), html.index('data-formset="hops"'))
        self.assertLess(html.index('data-formset="hops"'), html.index('data-formset="adjuncts"'))
        self.assertContains(response, 'Add grain')
        self.assertContains(response, 'Add adjunct')

    def test_create_recipe_with_all_ingredient_types(self):
        response = self.client.post('/recipe/new/', self.post_data(
            grains=[
                {'grain': self.two_row.pk, 'amount': '10', 'unit': 'lb'},
                {'grain': self.crystal.pk, 'amount': '8', 'unit': 'oz'},
            ],
            hops=[{'hop': self.cascade.pk, 'amount': '1', 'unit': 'oz', 'use': 'boil', 'time': '60'}],
            adjuncts=[{'adjunct': self.honey.pk, 'amount': '2', 'unit': 'lb', 'added_when': 'secondary'}],
        ))
        recipe = Recipe.objects.get(name='Pale Ale')
        self.assertRedirects(response, f'/recipe/{recipe.pk}/')
        self.assertEqual([str(g) for g in recipe.grain_bill.all()], ['10 lb 2-Row Pale Malt', '8 oz Crystal 40L'])
        self.assertEqual([str(h) for h in recipe.hop_additions.all()], ['1 oz Cascade (Boil, 60 min)'])
        self.assertEqual([str(a) for a in recipe.adjunct_additions.all()], ['2 lb Honey (Secondary)'])

    def test_blank_extra_rows_are_ignored(self):
        response = self.client.post('/recipe/new/', self.post_data(
            grains=[{'grain': '', 'amount': '', 'unit': 'lb'}],
            adjuncts=[{'adjunct': '', 'amount': '', 'unit': 'lb', 'added_when': 'boil'}],
        ))
        recipe = Recipe.objects.get(name='Pale Ale')
        self.assertRedirects(response, f'/recipe/{recipe.pk}/')
        self.assertEqual(recipe.grain_bill.count(), 0)
        self.assertEqual(recipe.adjunct_additions.count(), 0)

    def test_invalid_row_in_any_section_saves_nothing(self):
        response = self.client.post('/recipe/new/', self.post_data(
            grains=[{'grain': self.two_row.pk, 'amount': '10', 'unit': 'lb'}],
            hops=[{'hop': self.cascade.pk, 'amount': '1', 'unit': 'oz', 'use': 'boil', 'time': '60'}],
            adjuncts=[{'adjunct': self.honey.pk, 'amount': '', 'unit': 'lb', 'added_when': 'boil'}],
        ))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Amount: This field is required.')
        self.assertFalse(Recipe.objects.exists())
        self.assertFalse(RecipeGrain.objects.exists())
        self.assertFalse(RecipeHop.objects.exists())

    def test_errors_show_in_every_invalid_section(self):
        response = self.client.post('/recipe/new/', self.post_data(
            grains=[{'grain': self.two_row.pk, 'amount': '0', 'unit': 'lb'}],
            adjuncts=[{'adjunct': self.honey.pk, 'amount': '', 'unit': 'lb', 'added_when': 'boil'}],
        ))
        self.assertContains(response, 'Amount: Ensure this value is greater than or equal to 0.01.')
        self.assertContains(response, 'Amount: This field is required.')

    def test_edit_updates_adds_and_removes_grains_and_adjuncts(self):
        recipe = Recipe.objects.create(name='Pale Ale', owner=self.owner)
        grain = RecipeGrain.objects.create(recipe=recipe, grain=self.two_row, amount=Decimal('10'))
        adjunct = RecipeAdjunct.objects.create(recipe=recipe, adjunct=self.honey, amount=Decimal('1'))
        response = self.client.post(f'/recipe/{recipe.pk}/edit/', self.post_data(
            grains=[
                {'id': grain.pk, 'grain': self.two_row.pk, 'amount': '11', 'unit': 'lb'},
                {'grain': self.crystal.pk, 'amount': '1', 'unit': 'lb'},
            ],
            grain_initial=1,
            adjuncts=[
                {'id': adjunct.pk, 'adjunct': self.honey.pk, 'amount': '1', 'unit': 'lb', 'added_when': 'boil', 'DELETE': 'on'},
                {'adjunct': self.orange_peel.pk, 'amount': '1', 'unit': 'oz', 'added_when': 'boil'},
            ],
            adjunct_initial=1,
        ))
        self.assertRedirects(response, f'/recipe/{recipe.pk}/')
        self.assertEqual([str(g) for g in recipe.grain_bill.all()], ['11 lb 2-Row Pale Malt', '1 lb Crystal 40L'])
        self.assertEqual([str(a) for a in recipe.adjunct_additions.all()], ['1 oz Orange Peel (Boil)'])


class RecipeYeastFormViewTest(RecipeFormPostMixin, TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='brewer', password='brewer123')
        self.client.force_login(self.owner)
        self.us05 = Yeast.objects.get(name='SafAle US-05')

    def test_yeast_section_comes_after_ingredients(self):
        response = self.client.get('/recipe/new/')
        html = response.content.decode()
        self.assertContains(response, 'No yeast chosen yet')
        self.assertContains(response, 'Lalvin EC-1118')
        self.assertLess(html.index('data-formset="adjuncts"'), html.index('name="yeast"'))
        self.assertLess(html.index('name="notes"'), html.index('name="yeast"'))

    def test_session_form_has_no_yeast_section(self):
        recipe = Recipe.objects.create(name='Pale Ale', owner=self.owner)
        response = self.client.get(f'/recipe/{recipe.pk}/session/new/')
        self.assertNotContains(response, 'name="yeast"')
        self.assertContains(response, 'name="batch_number"')

    def test_create_recipe_with_yeast(self):
        response = self.client.post('/recipe/new/', self.post_data(yeast=self.us05.pk, yeast_amount='2'))
        recipe = Recipe.objects.get(name='Pale Ale')
        self.assertRedirects(response, f'/recipe/{recipe.pk}/')
        self.assertEqual(recipe.yeast, self.us05)
        self.assertEqual(recipe.yeast_amount, Decimal('2'))

    def test_yeast_is_optional(self):
        response = self.client.post('/recipe/new/', self.post_data(yeast='', yeast_amount=''))
        recipe = Recipe.objects.get(name='Pale Ale')
        self.assertRedirects(response, f'/recipe/{recipe.pk}/')
        self.assertIsNone(recipe.yeast)

    def test_amount_without_yeast_is_rejected(self):
        response = self.client.post('/recipe/new/', self.post_data(yeast='', yeast_amount='1'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Yeast: Choose a yeast for this amount.')
        self.assertFalse(Recipe.objects.exists())

    def test_edit_changes_and_clears_yeast(self):
        recipe = Recipe.objects.create(name='Pale Ale', owner=self.owner, yeast=self.us05, yeast_amount=Decimal('1'))
        response = self.client.get(f'/recipe/{recipe.pk}/edit/')
        self.assertContains(response, f'<option value="{self.us05.pk}" selected>SafAle US-05</option>', html=True)

        ec1118 = Yeast.objects.get(name='Lalvin EC-1118')
        self.client.post(f'/recipe/{recipe.pk}/edit/', self.post_data(yeast=ec1118.pk, yeast_amount='1.5'))
        recipe.refresh_from_db()
        self.assertEqual((recipe.yeast, recipe.yeast_amount), (ec1118, Decimal('1.5')))

        self.client.post(f'/recipe/{recipe.pk}/edit/', self.post_data(yeast='', yeast_amount=''))
        recipe.refresh_from_db()
        self.assertEqual((recipe.yeast, recipe.yeast_amount), (None, None))


class RecipeDetailIngredientsTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='brewer', password='brewer123')
        self.client.force_login(self.owner)
        self.recipe = Recipe.objects.create(name='Pale Ale', owner=self.owner)
        self.url = f'/recipe/{self.recipe.pk}/'

    def add_ingredients(self, count):
        hops = list(Hop.objects.all()[:count])
        grains = list(Grain.objects.all()[:count])
        adjuncts = list(Adjunct.objects.all()[:count])
        for hop, grain, adjunct in zip(hops, grains, adjuncts):
            RecipeHop.objects.create(recipe=self.recipe, hop=hop, amount=Decimal('1'), time=30)
            RecipeGrain.objects.create(recipe=self.recipe, grain=grain, amount=Decimal('5'))
            RecipeAdjunct.objects.create(recipe=self.recipe, adjunct=adjunct, amount=Decimal('1'))

    def test_shows_all_ingredients(self):
        RecipeGrain.objects.create(recipe=self.recipe, grain=Grain.objects.get(name='2-Row Pale Malt'), amount=Decimal('10'))
        RecipeHop.objects.create(recipe=self.recipe, hop=Hop.objects.get(name='Cascade'), amount=Decimal('1.5'), time=60)
        RecipeAdjunct.objects.create(recipe=self.recipe, adjunct=Adjunct.objects.get(name='Honey'), amount=Decimal('2'), added_when=RecipeAdjunct.SECONDARY)
        self.recipe.yeast = Yeast.objects.get(name='SafAle US-05')
        self.recipe.yeast_amount = Decimal('1')
        self.recipe.save()

        response = self.client.get(self.url)
        self.assertContains(response, '<span class="qty">10 lb</span><span class="name">2-Row Pale Malt</span>', html=True)
        self.assertContains(response, '<span class="qty">1.5 oz</span><span class="name">Cascade</span><span class="meta">Boil, 60 min</span>', html=True)
        self.assertContains(response, '<span class="qty">2 lb</span><span class="name">Honey</span><span class="meta">Secondary</span>', html=True)
        self.assertContains(response, '<span class="qty">1 pack</span><span class="name">SafAle US-05</span>', html=True)
        self.assertNotContains(response, 'added yet')
        self.assertNotContains(response, 'No yeast chosen yet.')

    def test_empty_sections_show_placeholders(self):
        response = self.client.get(self.url)
        for text in ('No grains added yet.', 'No hops added yet.', 'No adjuncts added yet.', 'No yeast chosen yet.'):
            self.assertContains(response, text)

    def test_hop_schedule_order(self):
        cascade = Hop.objects.get(name='Cascade')
        for use, time in ((RecipeHop.DRY_HOP, 3), (RecipeHop.BOIL, 15), (RecipeHop.WHIRLPOOL, None), (RecipeHop.BOIL, 60), (RecipeHop.BOIL, None)):
            RecipeHop.objects.create(recipe=self.recipe, hop=cascade, amount=Decimal('1'), use=use, time=time)
        response = self.client.get(self.url)
        self.assertEqual(
            [hop.schedule for hop in response.context['hop_schedule']],
            ['Boil, 60 min', 'Boil, 15 min', 'Boil', 'Whirlpool', 'Dry hop, 3 days'],
        )

    def test_quantity_formatting(self):
        vanilla = RecipeAdjunct(recipe=self.recipe, adjunct=Adjunct.objects.get(name='Vanilla Bean'), amount=Decimal('2.00'), unit='each')
        juice = RecipeAdjunct(recipe=self.recipe, adjunct=Adjunct.objects.get(name='Apple Juice'), amount=Decimal('5'), unit='l')
        self.assertEqual(vanilla.quantity, '2')
        self.assertEqual(juice.quantity, '5 L')
        self.recipe.yeast_amount = Decimal('1.50')
        self.assertEqual(self.recipe.yeast_quantity, '1.5 packs')
        self.recipe.yeast_amount = None
        self.assertEqual(self.recipe.yeast_quantity, '')

    def test_yeast_without_amount(self):
        self.recipe.yeast = Yeast.objects.get(name='Lalvin 71B')
        self.recipe.save()
        response = self.client.get(self.url)
        self.assertContains(response, '<span class="qty">—</span><span class="name">Lalvin 71B</span>', html=True)

    def test_query_count_does_not_grow_with_ingredients(self):
        self.add_ingredients(1)
        with CaptureQueriesContext(connection) as one_each:
            self.client.get(self.url)
        self.add_ingredients(3)
        with CaptureQueriesContext(connection) as four_each:
            self.client.get(self.url)
        self.assertEqual(len(one_each), len(four_each))


class CacheBustingStaticFilesStorageTest(TestCase):
    """Development static URLs carry the file's modified time so browsers refetch changed files."""

    def setUp(self):
        from yeastmode.storage import CacheBustingStaticFilesStorage # type: ignore
        self.storage = CacheBustingStaticFilesStorage()

    def test_url_includes_modified_time(self):
        from unittest import mock
        with mock.patch('yeastmode.storage.os.path.getmtime', return_value=1732400000.7):
            url = self.storage.url('brews/css/app.css')
        self.assertTrue(url.endswith('brews/css/app.css?v=1732400000'))

    def test_url_changes_when_file_changes(self):
        from unittest import mock
        with mock.patch('yeastmode.storage.os.path.getmtime', return_value=1000):
            before = self.storage.url('brews/css/app.css')
        with mock.patch('yeastmode.storage.os.path.getmtime', return_value=2000):
            after = self.storage.url('brews/css/app.css')
        self.assertNotEqual(before, after)

    def test_missing_file_gets_plain_url(self):
        self.assertTrue(self.storage.url('brews/css/does-not-exist.css').endswith('brews/css/does-not-exist.css'))


class CancelLinkTest(TestCase):
    """Every form's Cancel button links to a real page instead of the browser history."""

    def setUp(self):
        from django.urls import reverse # type: ignore
        self.reverse = reverse
        self.user = User.objects.create_user(username='brewer', password='brewer-pass-123')
        self.recipe = Recipe.objects.create(name='Saison', brew_type='beer', owner=self.user)
        self.session = BrewSession.objects.create(
            recipe=self.recipe, batch_number='1', status='fermenting', brew_date='2026-07-14',
        )

    def assertCancelLinksTo(self, page_url, expected_url):
        response = self.client.get(page_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'<a href="{expected_url}" class="btn btn-ghost">Cancel</a>', html=True)
        self.assertNotContains(response, 'history.back')

    def test_logged_in_pages(self):
        self.client.force_login(self.user)
        recipe_page = self.reverse('recipe_detail', args=[self.recipe.pk])
        session_page = self.reverse('session_detail', args=[self.session.pk])
        cases = [
            (self.reverse('recipe_create'), self.reverse('recipe_list')),
            (self.reverse('recipe_edit', args=[self.recipe.pk]), recipe_page),
            (self.reverse('recipe_delete', args=[self.recipe.pk]), recipe_page),
            (self.reverse('session_create', args=[self.recipe.pk]), recipe_page),
            (self.reverse('session_edit', args=[self.session.pk]), session_page),
            (self.reverse('session_delete', args=[self.session.pk]), session_page),
        ]
        for page_url, expected_url in cases:
            with self.subTest(page=page_url):
                self.assertCancelLinksTo(page_url, expected_url)

    def test_auth_pages_cancel_to_landing(self):
        for name in ('login', 'signup'):
            with self.subTest(page=name):
                self.assertCancelLinksTo(self.reverse(name), self.reverse('landing'))

    def test_cancel_link_survives_failed_save(self):
        """After a failed save, Cancel still leaves the form instead of reloading it."""
        self.client.force_login(self.user)
        response = self.client.post(self.reverse('session_edit', args=[self.session.pk]), {})
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            f'<a href="{self.reverse("session_detail", args=[self.session.pk])}" class="btn btn-ghost">Cancel</a>',
            html=True,
        )


class RecipeListFilterTest(TestCase):
    """Search, brew-type filter and sort on the recipe list, all driven by the query string."""

    def setUp(self):
        from django.urls import reverse # type: ignore
        self.url = reverse('recipe_list')
        self.user = User.objects.create_user(username='brewer', password='brewer-pass-123')
        self.client.force_login(self.user)

        make = lambda **kw: Recipe.objects.create(owner=self.user, **kw)
        self.ipa = make(name='Hazy IPA', style='New England IPA', brew_type='beer',
                        target_gravity='1.065', target_final_gravity='1.012')  # 6.96%
        self.stout = make(name='Oatmeal Stout', style='Stout', brew_type='beer',
                          target_gravity='1.055', target_final_gravity='1.015')  # 5.25%
        self.mead = make(name='Orange Blossom', style='Traditional', brew_type='mead',
                         target_gravity='1.110', target_final_gravity='1.010')  # 13.13%
        self.cider = make(name='apple Cider', brew_type='cider')  # no ABV
        for n in range(2):
            BrewSession.objects.create(recipe=self.stout, batch_number=str(n), brew_date='2026-07-14')
        BrewSession.objects.create(recipe=self.cider, batch_number='1', brew_date='2026-07-14')

        # Someone else's recipe never shows up.
        other = User.objects.create_user(username='other', password='other-pass-123')
        Recipe.objects.create(owner=other, name='Other IPA', style='IPA')

    def names(self, **params):
        response = self.client.get(self.url, params)
        self.assertEqual(response.status_code, 200)
        return [r.name for r in response.context['recipes']]

    def test_search_matches_name_and_style_case_insensitively(self):
        self.assertEqual(self.names(q='ipa'), ['Hazy IPA'])
        self.assertEqual(self.names(q='stout'), ['Oatmeal Stout'])
        self.assertEqual(self.names(q='TRADITIONAL'), ['Orange Blossom'])

    def test_filter_by_brew_type(self):
        self.assertCountEqual(self.names(type='beer'), ['Hazy IPA', 'Oatmeal Stout'])
        self.assertEqual(self.names(type='mead'), ['Orange Blossom'])
        self.assertEqual(self.names(type='other'), [])

    def test_search_and_type_combine(self):
        self.assertEqual(self.names(q='o', type='mead'), ['Orange Blossom'])

    def test_sort_by_name(self):
        self.assertEqual(self.names(sort='name'), ['apple Cider', 'Hazy IPA', 'Oatmeal Stout', 'Orange Blossom'])

    def test_sort_by_abv_puts_missing_abv_last(self):
        self.assertEqual(self.names(sort='abv'), ['Orange Blossom', 'Hazy IPA', 'Oatmeal Stout', 'apple Cider'])

    def test_sort_by_most_brewed(self):
        self.assertEqual(self.names(sort='brewed')[:2], ['Oatmeal Stout', 'apple Cider'])

    def test_default_sort_is_recently_updated(self):
        self.stout.notes = 'Bumped'
        self.stout.save()
        self.assertEqual(self.names()[0], 'Oatmeal Stout')

    def test_unknown_values_fall_back(self):
        response = self.client.get(self.url, {'type': 'wine', 'sort': 'bogus'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['recipes']), 4)
        self.assertEqual(response.context['sort'], 'updated')
        self.assertFalse(response.context['is_filtered'])

    def test_form_reflects_current_filters(self):
        response = self.client.get(self.url, {'q': 'stout', 'type': 'beer', 'sort': 'abv'})
        self.assertContains(response, 'value="stout"')
        self.assertContains(response, '<option value="beer" selected>Beer</option>', html=True)
        self.assertContains(response, '<option value="abv" selected>Sort: ABV</option>', html=True)
        self.assertContains(response, '1 of 4 recipes')

    def test_no_matches_state_links_to_cleared_list(self):
        response = self.client.get(self.url, {'q': 'lager', 'sort': 'name'})
        self.assertContains(response, 'No matching recipes')
        self.assertContains(response, f'href="{self.url}?sort=name"')
        self.assertNotContains(response, 'No recipes yet')

    def test_brand_new_user_sees_first_recipe_prompt_without_filters(self):
        newbie = User.objects.create_user(username='newbie', password='newbie-pass-123')
        self.client.force_login(newbie)
        response = self.client.get(self.url)
        self.assertContains(response, 'No recipes yet')
        self.assertNotContains(response, 'id="recipe-filters"')

    def test_card_shows_abv_once_without_percent_icon(self):
        response = self.client.get(self.url)
        self.assertContains(response, '6.96% ABV')
        self.assertNotContains(response, 'bi-percent')

    def test_batch_counts_do_not_add_queries_per_recipe(self):
        with CaptureQueriesContext(connection) as ctx:
            self.client.get(self.url)
        baseline = len(ctx)
        for n in range(3):
            r = Recipe.objects.create(owner=self.user, name=f'Extra {n}')
            BrewSession.objects.create(recipe=r, batch_number='1', brew_date='2026-07-14')
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(self.url)
        self.assertEqual(len(ctx), baseline)
        self.assertContains(response, '2 batches')


class SiteChromeTest(TestCase):
    """Favicon links and the site footer appear on every page."""

    def setUp(self):
        from django.urls import reverse # type: ignore
        self.reverse = reverse
        self.user = User.objects.create_user(username='brewer', password='brewer-pass-123')

    def assertChrome(self, response):
        self.assertEqual(response.status_code, 200)
        # static() gives the right URL for whichever storage is active
        # (?v= stamps in dev, hashed filenames when DEBUG is off).
        from django.templatetags.static import static # type: ignore
        self.assertContains(response, f'rel="icon" href="{static("brews/img/favicon.svg")}"')
        self.assertContains(response, f'rel="icon" href="{static("brews/img/favicon-32.png")}"')
        self.assertContains(response, f'rel="apple-touch-icon" href="{static("brews/img/apple-touch-icon.png")}"')
        self.assertContains(response, '<footer class="site-footer">')
        self.assertContains(response, 'href="https://github.com/Tbubbs662/yeast-mode"')

    def test_logged_out_pages(self):
        for name in ('landing', 'login', 'signup'):
            with self.subTest(page=name):
                self.assertChrome(self.client.get(self.reverse(name)))

    def test_logged_in_pages(self):
        self.client.force_login(self.user)
        for name in ('dashboard', 'recipe_list'):
            with self.subTest(page=name):
                self.assertChrome(self.client.get(self.reverse(name)))

    def test_favicon_ico_redirects_to_static_icon(self):
        response = self.client.get('/favicon.ico')
        self.assertEqual(response.status_code, 302)
        from django.templatetags.static import static # type: ignore
        self.assertEqual(response['Location'], static('brews/img/favicon.ico'))

    def test_icon_files_exist(self):
        from django.contrib.staticfiles import finders # type: ignore
        for path in ('favicon.svg', 'favicon-32.png', 'favicon.ico', 'apple-touch-icon.png'):
            with self.subTest(file=path):
                self.assertIsNotNone(finders.find(f'brews/img/{path}'))


class StatusChangedAtTest(TestCase):
    """BrewSession.status_changed_at follows status changes and nothing else."""

    def setUp(self):
        self.user = User.objects.create_user(username='brewer', password='brewer-pass-123')
        self.recipe = Recipe.objects.create(name='Saison', brew_type='beer', owner=self.user)
        self.session = BrewSession.objects.create(
            recipe=self.recipe, batch_number=1, status='fermenting', brew_date='2026-07-14',
        )

    def backdate(self):
        from django.utils import timezone # type: ignore
        import datetime
        past = timezone.now() - datetime.timedelta(days=30)
        BrewSession.objects.filter(pk=self.session.pk).update(status_changed_at=past)
        self.session.refresh_from_db()
        return past

    def test_set_on_create(self):
        self.assertIsNotNone(self.session.status_changed_at)

    def test_changing_status_updates_it(self):
        past = self.backdate()
        self.session.status = 'conditioning'
        self.session.save()
        self.session.refresh_from_db()
        self.assertGreater(self.session.status_changed_at, past)

    def test_editing_other_fields_leaves_it(self):
        past = self.backdate()
        self.session.notes = 'Smells great'
        self.session.original_gravity = Decimal('1.060')
        self.session.save()
        self.session.refresh_from_db()
        self.assertEqual(self.session.status_changed_at, past)

    def test_update_fields_status_also_saves_timestamp(self):
        past = self.backdate()
        self.session.status = 'ready'
        self.session.save(update_fields=['status'])
        self.session.refresh_from_db()
        self.assertGreater(self.session.status_changed_at, past)

    def test_edit_form_status_change_updates_it(self):
        past = self.backdate()
        self.client.force_login(self.user)
        self.client.post(f'/session/{self.session.pk}/edit/', {
            'batch_number': 1, 'status': 'conditioning', 'brew_date': '2026-07-14',
        })
        self.session.refresh_from_db()
        self.assertEqual(self.session.status, 'conditioning')
        self.assertGreater(self.session.status_changed_at, past)


class StatusChangedAtBackfillTest(TestCase):
    """The 0008 data migration's best guesses for existing batches."""

    def test_backfill(self):
        import datetime
        from django.utils import timezone # type: ignore
        migration = importlib.import_module('brews.migrations.0008_brewsession_status_changed_at')
        user = User.objects.create_user(username='brewer', password='brewer-pass-123')
        recipe = Recipe.objects.create(name='Saison', owner=user)
        fermenting = BrewSession.objects.create(recipe=recipe, status='fermenting', brew_date='2026-07-14')
        ready = BrewSession.objects.create(recipe=recipe, status='ready', brew_date='2026-07-14')

        migration.backfill_status_changed_at(django_apps, None)

        fermenting.refresh_from_db()
        ready.refresh_from_db()
        self.assertEqual(fermenting.status_changed_at,
                         datetime.datetime(2026, 7, 14, tzinfo=timezone.get_current_timezone()))
        self.assertEqual(ready.status_changed_at, ready.updated_at)


class NeedsAttentionTest(TestCase):
    """The dashboard's attention rules and the strip that shows them."""

    def setUp(self):
        import datetime
        from django.utils import timezone # type: ignore
        self.today = timezone.localdate()
        self.days_ago = lambda n: self.today - datetime.timedelta(days=n)
        self.user = User.objects.create_user(username='brewer', password='brewer-pass-123')
        self.recipe = Recipe.objects.create(name='Hazy IPA', owner=self.user)

    def make(self, status, brewed_days_ago, status_days_ago=None):
        import datetime
        from django.utils import timezone # type: ignore
        session = BrewSession.objects.create(
            recipe=self.recipe, status=status, brew_date=self.days_ago(brewed_days_ago),
        )
        if status_days_ago is not None:
            changed = datetime.datetime.combine(
                self.days_ago(status_days_ago), datetime.time(12), tzinfo=timezone.get_current_timezone(),
            )
            BrewSession.objects.filter(pk=session.pk).update(status_changed_at=changed)
            session.refresh_from_db()
        return session

    def attention(self, *sessions):
        from brews.attention import needs_attention # type: ignore
        return [(item.session, item.kind, item.days) for item in needs_attention(sessions, today=self.today)]

    def test_fermenting_threshold(self):
        early = self.make('fermenting', 13)
        due = self.make('fermenting', 14)
        self.assertEqual(self.attention(early, due), [(due, 'check_gravity', 14)])

    def test_fermenting_counts_from_brew_day_even_if_logged_later(self):
        logged_late = self.make('fermenting', 20)  # status_changed_at is "now"
        self.assertEqual(self.attention(logged_late), [(logged_late, 'check_gravity', 20)])

    def test_conditioning_threshold_uses_status_change(self):
        early = self.make('conditioning', 60, status_days_ago=20)
        due = self.make('conditioning', 60, status_days_ago=21)
        self.assertEqual(self.attention(early, due), [(due, 'probably_ready', 21)])

    def test_ready_and_archived_never_flagged(self):
        self.assertEqual(self.attention(
            self.make('ready', 90, status_days_ago=60),
            self.make('archived', 90, status_days_ago=60),
        ), [])

    def test_longest_waiting_first(self):
        a = self.make('fermenting', 15)
        b = self.make('conditioning', 60, status_days_ago=30)
        c = self.make('fermenting', 20)
        self.assertEqual([s for s, _, _ in self.attention(a, b, c)], [b, c, a])

    def test_dashboard_strip(self):
        self.make('fermenting', 14)
        self.make('conditioning', 60, status_days_ago=22)
        self.client.force_login(self.user)
        response = self.client.get('/dashboard/')
        self.assertContains(response, 'Needs attention')
        self.assertContains(response, '<strong>day 14</strong> of fermentation')
        self.assertContains(response, 'conditioning for 3 weeks')

    def test_dashboard_hides_strip_when_nothing_needs_attention(self):
        self.make('fermenting', 2)
        self.client.force_login(self.user)
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Needs attention')
