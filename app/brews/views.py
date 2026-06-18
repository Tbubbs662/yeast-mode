from django.shortcuts import render, get_object_or_404, redirect # type: ignore
from django.contrib import messages # type: ignore
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

def recipe_edit(request, recipe_pk):
    recipe = get_object_or_404(Recipe, pk=recipe_pk)
    if request.method == 'POST':
        form = RecipeForm(request.POST, instance=recipe)
        if form.is_valid():
            recipe = form.save()
            messages.success(request, f'Recipe "{recipe.name}" has been updated successfully!')
            return redirect('recipe_detail', pk=recipe.pk)
    else:
        form = RecipeForm(instance=recipe)
    return render(request, 'brews/recipe_form.html', {'form': form, 'title': recipe.name})

def recipe_delete(request,recipe_pk):
    recipe = get_object_or_404(Recipe, pk=recipe_pk)
    if request.method == 'POST':
        recipe.delete()
        messages.success(request, f'Recipe "{recipe.name}" has been deleted successfully!')
        return redirect('recipe_list')
    else:
        return render(request, 'brews/recipe_confirm_delete.html', {'recipe': recipe})


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

def session_detail(request, pk):
    session = get_object_or_404(BrewSession, pk=pk)
    return render(request, 'brews/session_details.html', {'session': session})

def dashboard(request):
    fermenting = BrewSession.objects.filter(status='fermenting').order_by('-brew_date')
    conditioning = BrewSession.objects.filter(status='conditioning').order_by('-brew_date')
    ready = BrewSession.objects.filter(status='ready').order_by('-brew_date')
    archived = BrewSession.objects.filter(status='archived').order_by('-brew_date')
    return render(request, 'brews/dashboard.html', {
        'fermenting': fermenting,
        'conditioning': conditioning,
        'ready': ready,
        'archived': archived,
    })