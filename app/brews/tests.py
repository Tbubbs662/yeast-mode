from django.test import TestCase # type: ignore
from brews.models import Recipe, BrewSession # type: ignore
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