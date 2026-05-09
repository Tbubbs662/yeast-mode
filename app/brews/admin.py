from django.contrib import admin # type: ignore
from .models import Recipe, BrewSession

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ['name', 'brew_type', 'style', 'created_at']
    list_filter = ['brew_type']
    search_fields = ['name', 'style']

@admin.register(BrewSession)
class BrewSessionAdmin(admin.ModelAdmin):
    list_display = ['recipe', 'batch_number', 'status', 'brew_date', 'original_gravity', 'final_gravity', 'abv']
    list_filter = ['status']
    search_fields = ['recipe__name']
