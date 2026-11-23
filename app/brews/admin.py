from django.contrib import admin # type: ignore
from .models import Hop, Grain, Adjunct, Yeast, Recipe, BrewSession, RecipeHop, RecipeGrain, RecipeAdjunct

@admin.register(Hop)
class HopAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    list_filter = []
    search_fields = ['name']

@admin.register(Grain)
class GrainAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    list_filter = []
    search_fields = ['name']

@admin.register(Adjunct)
class AdjunctAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    list_filter = []
    search_fields = ['name']

@admin.register(Yeast)
class YeastAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    list_filter = []
    search_fields = ['name']        

class RecipeGrainInline(admin.TabularInline):
    model = RecipeGrain
    extra = 0
    autocomplete_fields = ['grain']

class RecipeHopInline(admin.TabularInline):
    model = RecipeHop
    extra = 0
    autocomplete_fields = ['hop']

class RecipeAdjunctInline(admin.TabularInline):
    model = RecipeAdjunct
    extra = 0
    autocomplete_fields = ['adjunct']

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = [RecipeGrainInline, RecipeHopInline, RecipeAdjunctInline]
    autocomplete_fields = ['yeast']
    list_display = ['name', 'brew_type', 'style', 'created_at']
    list_filter = ['brew_type']
    search_fields = ['name', 'style']

@admin.register(BrewSession)
class BrewSessionAdmin(admin.ModelAdmin):
    list_display = ['recipe', 'batch_number', 'status', 'brew_date', 'original_gravity', 'final_gravity', 'abv']
    list_filter = ['status']
    search_fields = ['recipe__name']
