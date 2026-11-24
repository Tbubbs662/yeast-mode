"""Create (or reset) the `demo` account used for the README screenshots.

Run inside the web container; see take.sh. Wipes and rebuilds the demo
user's recipes and batches only; other accounts are untouched.
"""
import datetime
import os
from decimal import Decimal
from django.contrib.auth.models import User
from django.utils import timezone
from brews.models import BrewSession, Recipe, Hop, Grain, Yeast, RecipeHop, RecipeGrain

password = os.environ['DEMO_PASSWORD']
user, _ = User.objects.get_or_create(username='demo')
user.set_password(password); user.save()
Recipe.objects.filter(owner=user).delete()

today = timezone.localdate()
ago = lambda n: today - datetime.timedelta(days=n)

def recipe(name, brew_type, style, og, fg, description):
    return Recipe.objects.create(owner=user, name=name, brew_type=brew_type, style=style,
        target_gravity=Decimal(og), target_final_gravity=Decimal(fg), description=description)

ipa = recipe('Hazy IPA', 'beer', 'New England IPA', '1.065', '1.012', 'Soft, juicy and loaded with Citra and Mosaic in the whirlpool and dry hop.')
stout = recipe('Oatmeal Stout', 'beer', 'Oatmeal Stout', '1.058', '1.016', 'Silky body from flaked oats with roast, chocolate and a little coffee.')
saison = recipe('Farmhouse Saison', 'beer', 'Saison', '1.060', '1.006', 'Bone-dry and peppery, fermented warm with a classic Belgian saison yeast.')
red = recipe('Irish Red', 'beer', 'Irish Red Ale', '1.052', '1.012', 'Toffee malt, a touch of roast for color, and a clean finish.')
mead = recipe('Orange Blossom Mead', 'mead', 'Traditional Mead', '1.110', '1.010', 'Orange blossom honey, staggered nutrient additions, aged three months.')
cider = recipe('Dry Apple Cider', 'cider', 'English Cider', '1.055', '1.000', 'Fresh-pressed apples fermented dry with a champagne yeast.')

def batch(r, n, status, brewed, og=None, fg=None, in_status=None, notes=''):
    s = BrewSession.objects.create(recipe=r, batch_number=n, status=status, brew_date=ago(brewed),
        original_gravity=og and Decimal(og), final_gravity=fg and Decimal(fg), notes=notes)
    changed = timezone.now() - datetime.timedelta(days=brewed if in_status is None else in_status)
    BrewSession.objects.filter(pk=s.pk).update(status_changed_at=changed)
    return s

batch(ipa, 3, 'fermenting', 16, '1.066')
batch(stout, 2, 'fermenting', 5, '1.059')
batch(mead, 2, 'fermenting', 2, '1.112')
batch(saison, 1, 'conditioning', 45, '1.061', '1.005', in_status=24,
      notes='Pitched at 68°F and let it free-rise to 82°F. Finished very dry with lots of pepper and citrus. Bottled with priming sugar for high carbonation.')
batch(cider, 1, 'conditioning', 30, '1.054', '1.000', in_status=9)
batch(red, 2, 'ready', 60, '1.053', '1.013', in_status=6)
batch(mead, 1, 'ready', 150, '1.108', '1.012', in_status=20)
batch(ipa, 2, 'archived', 120, '1.064', '1.013', in_status=70)
batch(ipa, 1, 'archived', 200, '1.062', '1.014', in_status=150)
batch(stout, 1, 'archived', 260, '1.057', '1.017', in_status=200)
batch(red, 1, 'archived', 300, '1.051', '1.012', in_status=240)

# A few ingredients so the recipe page isn't bare.
def first(model, *names):
    for n in names:
        obj = model.objects.filter(name__icontains=n).first()
        if obj: return obj
for grain, amt in (('Pale', '11'), ('Oats', '1.5'), ('Wheat', '1')):
    g = first(Grain, grain)
    if g: RecipeGrain.objects.create(recipe=ipa, grain=g, amount=Decimal(amt), unit='lb')
for hop, amt, use, time in (('Citra', '1', 'whirlpool', 20), ('Mosaic', '1', 'whirlpool', 20), ('Citra', '2', 'dry_hop', 3)):
    h = first(Hop, hop)
    if h: RecipeHop.objects.create(recipe=ipa, hop=h, amount=Decimal(amt), unit='oz', use=use, time=time)
y = first(Yeast, 'London Ale III', 'Verdant', 'Juicy', 'Ale')
if y: ipa.yeast = y; ipa.yeast_amount = 1; ipa.save()
print('seeded', Recipe.objects.filter(owner=user).count(), 'recipes', BrewSession.objects.filter(recipe__owner=user).count(), 'batches')
