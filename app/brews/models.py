from django.db import models # type: ignore
from django.contrib.auth.models import User # type: ignore

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

    @property
    def abv(self):
        if self.target_gravity and self.target_final_gravity:
            return round((float(self.target_gravity) - float(self.target_final_gravity)) * 131.25, 2)
        return None
    
    def __str__(self):
        return self.name
    
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

