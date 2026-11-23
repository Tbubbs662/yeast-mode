from django.shortcuts import render, get_object_or_404, redirect # type: ignore
from django.contrib import messages # type: ignore
from django.db import transaction # type: ignore
from .models import Recipe, BrewSession
from .forms import RecipeForm, RecipeAdjunctFormSet, RecipeGrainFormSet, RecipeHopFormSet, BrewSessionForm
from django.contrib.auth.forms import UserCreationForm # type: ignore
from django.contrib.auth import login # type: ignore
from django.contrib.auth.decorators import login_required # type: ignore

def landing(request):
    return render(request, 'brews/landing.html')

def sign_up(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Account has been created successfully!')
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'brews/sign_up.html', { 'form': form, 'title': 'Sign up'})

@login_required
def recipe_list(request):
    recipes = Recipe.objects.filter(owner=request.user).order_by('-created_at')
    return render(request, 'brews/recipe_list.html', {'recipes': recipes})

@login_required
def recipe_detail(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk, owner=request.user)
    return render(request, 'brews/recipe_detail.html', {'recipe': recipe})

# Ingredient sections on the recipe form, in brewing order:
# (formset prefix, formset class, heading, add-button label, help text)
INGREDIENT_SECTIONS = [
    ('grains', RecipeGrainFormSet, 'Grain bill', 'Add grain', ''),
    ('hops', RecipeHopFormSet, 'Hops', 'Add hop', 'Time is minutes for boil and whirlpool, days for dry hops.'),
    ('adjuncts', RecipeAdjunctFormSet, 'Adjuncts', 'Add adjunct', 'Sugars, fruit, spices and other additions.'),
]

def recipe_form_view(request, recipe, title, success_message):
    """Shared create/edit handling for a recipe and its ingredient formsets."""
    data = request.POST if request.method == 'POST' else None
    form = RecipeForm(data, instance=recipe)
    sections = [
        {
            'formset': formset_class(data, instance=recipe, prefix=prefix),
            'kind': prefix,
            'title': heading,
            'add_label': add_label,
            'help': help_text,
        }
        for prefix, formset_class, heading, add_label, help_text in INGREDIENT_SECTIONS
    ]
    formsets = [section['formset'] for section in sections]

    if request.method == 'POST':
        # Validate everything (not short-circuiting) so every error shows at once.
        valid = [form.is_valid()] + [formset.is_valid() for formset in formsets]
        if all(valid):
            with transaction.atomic():
                recipe = form.save()
                for formset in formsets:
                    formset.instance = recipe
                    formset.save()
            messages.success(request, success_message.format(name=recipe.name))
            return redirect('recipe_detail', pk=recipe.pk)

    return render(request, 'brews/recipe_form.html', {
        'form': form,
        'ingredient_sections': sections,
        'title': title,
    })

@login_required
def recipe_create(request):
    return recipe_form_view(
        request, Recipe(owner=request.user), 'New Recipe',
        'Recipe "{name}" created successfully!',
    )

@login_required
def recipe_edit(request, recipe_pk):
    recipe = get_object_or_404(Recipe, pk=recipe_pk, owner=request.user)
    return recipe_form_view(
        request, recipe, recipe.name,
        'Recipe "{name}" has been updated successfully!',
    )

@login_required
def recipe_delete(request,recipe_pk):
    recipe = get_object_or_404(Recipe, pk=recipe_pk, owner=request.user)
    if request.method == 'POST':
        recipe.delete()
        messages.success(request, f'Recipe "{recipe.name}" has been deleted successfully!')
        return redirect('recipe_list')
    else:
        return render(request, 'brews/recipe_confirm_delete.html', {'recipe': recipe})

@login_required
def session_create(request, recipe_pk):
    recipe = get_object_or_404(Recipe, pk=recipe_pk, owner=request.user)
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

@login_required
def session_edit(request, pk):
    session = get_object_or_404(BrewSession, pk=pk, recipe__owner=request.user)
    if request.method == 'POST':
        form = BrewSessionForm(request.POST, instance=session)
        if form.is_valid():
            session = form.save()
            messages.success(request, f'{session.recipe.name} batch {session.batch_number} has been updated successfully!')
            return redirect('session_detail', pk=pk)
    else:
        form = BrewSessionForm(instance=session)
    return render(request, 'brews/session_edit.html', {'form': form, 'title': session.batch_number, 'session': session})

@login_required
def session_delete(request, pk):
    session = get_object_or_404(BrewSession, pk=pk, recipe__owner=request.user)
    recipe_pk = session.recipe.pk
    if request.method == 'POST':
        session.delete()
        messages.success(request, f'{session.recipe.name} batch {session.batch_number} has been deleted successfully!')
        return redirect('recipe_detail', recipe_pk)
    else:
        return render(request, 'brews/session_confirm_delete.html', {'session': session})

@login_required
def session_detail(request, pk):
    session = get_object_or_404(BrewSession, pk=pk, recipe__owner=request.user)
    return render(request, 'brews/session_details.html', {'session': session})

@login_required
def dashboard(request):
    fermenting = BrewSession.objects.filter(status='fermenting').filter(recipe__owner=request.user).order_by('-brew_date')
    conditioning = BrewSession.objects.filter(status='conditioning').filter(recipe__owner=request.user).order_by('-brew_date')
    ready = BrewSession.objects.filter(status='ready').filter(recipe__owner=request.user).order_by('-brew_date')
    archived = BrewSession.objects.filter(status='archived').filter(recipe__owner=request.user).order_by('-brew_date')
    beer_count = Recipe.objects.filter(owner=request.user, brew_type='beer').count()
    mead_count = Recipe.objects.filter(owner=request.user, brew_type='mead').count()
    cider_count = Recipe.objects.filter(owner=request.user, brew_type='cider').count()
    other_count = Recipe.objects.filter(owner=request.user, brew_type='other').count()
    return render(request, 'brews/dashboard.html', {
        'fermenting': fermenting,
        'conditioning': conditioning,
        'ready': ready,
        'archived': archived,
        'beer': beer_count,
        'mead': mead_count,
        'cider': cider_count,
        'other': other_count
    })