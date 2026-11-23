"""Seed the ingredient tables with common brewing ingredients.

The data lives in this file (rather than being imported from the app) so the
migration keeps working even if the app code changes later. Safe to re-run:
existing ingredients are matched by name and left untouched.
"""

from django.db import migrations

GRAINS = [
    ('2-Row Pale Malt', 'Versatile base malt for most beer styles, with a clean, lightly grainy flavor.'),
    ('Pilsner Malt', 'Very pale base malt with a soft, bready sweetness. The standard for lagers and many Belgian styles.'),
    ('Maris Otter', 'British pale base malt with a rich, biscuity character.'),
    ('Munich Malt', 'Kilned base malt that adds bready, malty depth and an amber color.'),
    ('Vienna Malt', 'Lightly kilned base malt with a toasty, malty sweetness.'),
    ('Wheat Malt', 'Adds body, a soft bready flavor and protein that helps head retention.'),
    ('Carapils (Dextrin Malt)', 'Adds body and head retention with very little color or flavor.'),
    ('Crystal 10L', 'Light caramel malt with a gentle, honey-like sweetness.'),
    ('Crystal 40L', 'Medium caramel malt with balanced caramel sweetness and a golden-amber color.'),
    ('Crystal 60L', 'Caramel malt with a fuller caramel flavor and an amber-red color.'),
    ('Crystal 120L', 'Dark caramel malt with burnt-sugar and dark-fruit notes.'),
    ('Biscuit Malt', 'Toasted malt with a dry biscuit and bread-crust flavor.'),
    ('Chocolate Malt', 'Dark roasted malt with chocolate and coffee notes.'),
    ('Roasted Barley', 'Unmalted roasted barley with a dry, coffee-like bitterness. Classic in stouts.'),
    ('Black Patent Malt', 'Very dark malt used mainly for color, with a sharp roasted bite.'),
    ('Flaked Oats', 'Unmalted oats that add a silky body and smooth mouthfeel.'),
]

HOPS = [
    ('Cascade', 'American aroma hop with floral, citrus and grapefruit notes.'),
    ('Centennial', 'Dual-purpose American hop with floral and lemony citrus character.'),
    ('Citra', 'American hop with intense tropical fruit and citrus aromas.'),
    ('Mosaic', 'American hop with complex blueberry, tropical fruit and pine notes.'),
    ('Simcoe', 'American hop with pine, passion fruit and earthy notes.'),
    ('Amarillo', 'American hop with orange citrus and floral notes.'),
    ('Chinook', 'American hop with pine, spice and grapefruit. A good bittering hop.'),
    ('Columbus (CTZ)', 'High-alpha American hop with a pungent, dank and earthy character.'),
    ('Magnum', 'Clean, high-alpha bittering hop.'),
    ('Galaxy', 'Australian hop with bold passion fruit and peach aromas.'),
    ('Saaz', 'Czech noble hop with a delicate earthy, herbal and spicy character. Classic in pilsners.'),
    ('Hallertau Mittelfrüh', 'German noble hop with a mild floral and spicy aroma.'),
    ('Tettnang', 'German noble hop with a mild herbal and spicy aroma.'),
    ('East Kent Goldings', 'English aroma hop with a gentle earthy, floral and honey character.'),
    ('Fuggle', 'English hop with a mild woody and earthy character.'),
]

YEASTS = [
    ('SafAle US-05', 'Dry American ale yeast with a clean, neutral profile.'),
    ('SafAle S-04', 'Dry English ale yeast. Fast fermenting and flocculating, slightly fruity.'),
    ('LalBrew Nottingham', 'Dry, neutral English-style ale yeast that tolerates a wide temperature range.'),
    ('White Labs WLP001 California Ale', 'Liquid American ale yeast with a clean, crisp profile.'),
    ('Wyeast 1056 American Ale', 'Liquid American ale yeast with a clean, crisp profile.'),
    ('SafLager W-34/70', 'Dry lager yeast with a clean, malty profile.'),
    ('SafAle WB-06', 'Dry wheat beer yeast with banana and clove character.'),
    ('LalBrew Belle Saison', 'Dry saison yeast with spicy, peppery notes and high attenuation.'),
    ('Voss Kveik', 'Norwegian farmhouse yeast that ferments very quickly at warm temperatures, with an orange-peel character.'),
    ('Lalvin EC-1118', 'Champagne yeast with a neutral profile and high alcohol tolerance. Popular for mead, cider and sparkling wine.'),
    ('Lalvin 71B', 'Wine yeast that keeps fruity aromas and softens acidity. Popular for mead and fruit wines.'),
    ('Lalvin D47', 'White wine yeast that gives a rounded mouthfeel. Popular for traditional mead at cooler temperatures.'),
    ('Lalvin K1-V1116', 'Robust wine yeast with high alcohol tolerance. Good for mead and country wines.'),
]

ADJUNCTS = [
    ('Honey', 'Fermentable sugar and the main ingredient in mead.'),
    ('Apple Juice', 'Fresh-pressed or store-bought juice. The base for cider.'),
    ('Lactose', 'Unfermentable milk sugar that adds sweetness and body, as in milk stouts.'),
    ('Corn Sugar (Dextrose)', 'Highly fermentable sugar for boosting alcohol, drying out the body or priming bottles.'),
    ('Belgian Candi Sugar', 'Adds fermentable sugar and, in darker grades, caramel and dark-fruit flavor to Belgian styles.'),
    ('Brown Sugar', 'Fermentable sugar with a light molasses character.'),
    ('Maple Syrup', 'Fermentable sugar with a subtle maple character.'),
    ('Raspberries', 'Fruit addition with a tart berry flavor and a red color.'),
    ('Cherries', 'Fruit addition with a tart cherry flavor, common in sour beers.'),
    ('Orange Peel', 'Citrus addition, common in Belgian witbiers.'),
    ('Coriander', 'Spice with a citrusy, peppery character, common in witbiers.'),
    ('Cinnamon', 'Warming spice for winter ales, ciders and metheglins.'),
    ('Vanilla Bean', 'Adds a rich vanilla flavor. Usually added in secondary.'),
    ('Cacao Nibs', 'Adds chocolate flavor without sweetness.'),
    ('Coffee', 'Adds roasted coffee flavor and aroma.'),
    ('Oak Chips', 'Adds oak, vanilla and tannin character, like barrel aging.'),
]


def seed_ingredients(apps, schema_editor):
    tables = [
        ('Grain', GRAINS),
        ('Hop', HOPS),
        ('Yeast', YEASTS),
        ('Adjunct', ADJUNCTS),
    ]
    for model_name, items in tables:
        model = apps.get_model('brews', model_name)
        for name, description in items:
            model.objects.get_or_create(name=name, defaults={'description': description})


class Migration(migrations.Migration):

    dependencies = [
        ('brews', '0005_unique_ingredient_names'),
    ]

    operations = [
        # Reversing is a no-op: we don't want to delete ingredients that
        # recipes may already be using.
        migrations.RunPython(seed_ingredients, migrations.RunPython.noop),
    ]
