from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Recipe, BrewSession
from .forms import RecipeForm, BrewSessionForm


def recipe_list(request):
    recipes = Recipe.objects.all().order_by('-created_at')
    return render(request, 'brews/recipe_list.html', {'recipes': recipes})


def recipe_detail(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    return render(request, 'brews/recipe_detail.html', {'recipe': recipe})


def recipe_create(request):
    if request.method == 'POST':
        form = RecipeForm(request.POST)
        if form.is_valid():
            recipe = form.save()
            messages.success(request, f'Recipe "{recipe.name}" created successfully!')
            return redirect('recipe_detail', pk=recipe.pk)
    else:
        form = RecipeForm()
    return render(request, 'brews/recipe_form.html', {'form': form, 'title': 'New Recipe'})


def session_create(request, recipe_pk):
    recipe = get_object_or_404(Recipe, pk=recipe_pk)
    if request.method == 'POST':
        form = BrewSessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.recipe = recipe
            session.save()
            messages.success(request, f'Brew session logged for "{recipe.name}"!')
            return redirect('recipe_detail', pk=recipe.pk)
    else:
        form = BrewSessionForm()
    return render(request, 'brews/recipe_form.html', {'form': form, 'title': f'Log Brew Session - {recipe.name}'})