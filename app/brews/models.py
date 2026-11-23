from django.db import models # type: ignore
from decimal import Decimal

from django.contrib.auth.models import User # type: ignore
from django.core.validators import MinValueValidator # type: ignore

class Hop(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name}"

class Grain(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name}"

class Adjunct(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name}"

class Yeast(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name}"

class Recipe(models.Model):
    BEER = 'beer'
    MEAD = 'mead'
    CIDER = 'cider'
    OTHER = 'other'

    BREW_TYPE_CHOICES = [
        (BEER, 'Beer'),
        (MEAD, 'Mead'),
        (CIDER, 'Cider'),
        (OTHER, 'Other')
    ]

    name = models.CharField(max_length=200)
    brew_type = models.CharField(max_length=20, choices=BREW_TYPE_CHOICES, default=BEER)
    target_gravity = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    target_final_gravity = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    style = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recipes')
    yeast = models.ForeignKey(Yeast, on_delete=models.SET_NULL, null=True, blank=True)
    yeast_amount = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Number of packets or vials.',
    )

    @property
    def abv(self):
        if self.target_gravity and self.target_final_gravity:
            return round((float(self.target_gravity) - float(self.target_final_gravity)) * 131.25, 2)
        return None
    
    def __str__(self):
        return self.name
    
def format_amount(amount):
    """Show 1.00 as '1' and 1.50 as '1.5'."""
    return f"{amount.normalize():f}"


def positive_amount_field():
    return models.DecimalField(
        max_digits=7, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )


class RecipeHop(models.Model):
    OZ, G = 'oz', 'g'
    UNIT_CHOICES = [(OZ, 'oz'), (G, 'g')]

    BOIL, WHIRLPOOL, DRY_HOP = 'boil', 'whirlpool', 'dry_hop'
    USE_CHOICES = [(BOIL, 'Boil'), (WHIRLPOOL, 'Whirlpool'), (DRY_HOP, 'Dry hop')]

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='hop_additions')
    hop = models.ForeignKey(Hop, on_delete=models.PROTECT)
    amount = positive_amount_field()
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default=OZ)
    use = models.CharField(max_length=20, choices=USE_CHOICES, default=BOIL)
    time = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Minutes for boil and whirlpool additions, days for dry hops.',
    )

    class Meta:
        ordering = ['pk']

    @property
    def time_unit(self):
        return 'days' if self.use == self.DRY_HOP else 'min'

    def __str__(self):
        text = f"{format_amount(self.amount)} {self.unit} {self.hop} ({self.get_use_display()}"
        if self.time is not None:
            text += f", {self.time} {self.time_unit}"
        return text + ")"


class RecipeGrain(models.Model):
    LB, OZ, KG, G = 'lb', 'oz', 'kg', 'g'
    UNIT_CHOICES = [(LB, 'lb'), (OZ, 'oz'), (KG, 'kg'), (G, 'g')]

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='grain_bill')
    grain = models.ForeignKey(Grain, on_delete=models.PROTECT)
    amount = positive_amount_field()
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default=LB)

    class Meta:
        ordering = ['pk']

    def __str__(self):
        return f"{format_amount(self.amount)} {self.unit} {self.grain}"


class RecipeAdjunct(models.Model):
    UNIT_CHOICES = [
        ('lb', 'lb'), ('oz', 'oz'), ('kg', 'kg'), ('g', 'g'),
        ('gal', 'gal'), ('l', 'L'), ('tsp', 'tsp'), ('tbsp', 'tbsp'),
        ('each', 'each'),
    ]

    MASH, BOIL, PRIMARY, SECONDARY, BOTTLING = 'mash', 'boil', 'primary', 'secondary', 'bottling'
    ADDED_WHEN_CHOICES = [
        (MASH, 'Mash'), (BOIL, 'Boil'), (PRIMARY, 'Primary'),
        (SECONDARY, 'Secondary'), (BOTTLING, 'Bottling'),
    ]

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='adjunct_additions')
    adjunct = models.ForeignKey(Adjunct, on_delete=models.PROTECT)
    amount = positive_amount_field()
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='lb')
    added_when = models.CharField(max_length=20, choices=ADDED_WHEN_CHOICES, default=BOIL)

    class Meta:
        ordering = ['pk']

    def __str__(self):
        return f"{format_amount(self.amount)} {self.unit} {self.adjunct} ({self.get_added_when_display()})"


class BrewSession(models.Model):
    FERMENTING = 'fermenting'
    CONDITIONING = 'conditioning'
    READY = 'ready'
    ARCHIVED = 'archived'

    STATUS_CHOICES = [
        (FERMENTING, 'Fermenting'),
        (CONDITIONING, 'Conditioning'),
        (READY, 'Ready'),
        (ARCHIVED, 'Archived')
    ]

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='sessions')
    batch_number = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=FERMENTING)
    brew_date = models.DateField()
    original_gravity = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    final_gravity = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def abv(self):
        if self.original_gravity and self.final_gravity:
            return round((float(self.original_gravity) - float(self.final_gravity)) * 131.25, 2)
        return None
    
    def __str__(self):
        return f"{self.recipe.name} - Batch #{self.batch_number}"
