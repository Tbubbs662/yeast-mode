from django.shortcuts import render, get_object_or_404, redirect # type: ignore
from django.contrib import messages # type: ignore
from django.core.paginator import Paginator # type: ignore
from django.db import transaction # type: ignore
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Max, Prefetch, Q # type: ignore
from django.db.models.functions import Lower # type: ignore
from django.templatetags.static import static # type: ignore
from django.urls import reverse # type: ignore
from .attention import needs_attention
from .stats import dashboard_stats, monthly_activity
from .models import BrewSession, Recipe, RecipeAdjunct, RecipeGrain, RecipeHop
from .forms import RecipeForm, RecipeAdjunctFormSet, RecipeGrainFormSet, RecipeHopFormSet, BrewSessionForm
from django.contrib.auth.forms import UserCreationForm # type: ignore
from django.contrib.auth import login # type: ignore
from django.contrib.auth.decorators import login_required # type: ignore
from django.http import HttpResponseBadRequest, JsonResponse # type: ignore
from django.template.loader import render_to_string # type: ignore
from django.views.decorators.http import require_POST # type: ignore

def favicon(request):
    # Built per request: the production manifest storage can't resolve
    # static URLs until collectstatic has run. Not permanent, because the
    # target carries a version stamp that changes when the icon does.
    return redirect(static('brews/img/favicon.ico'))

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

# Recipe list sort options: (query value, label, ordering).
RECIPE_SORTS = [
    ('updated', 'Recently updated', [F('updated_at').desc()]),
    ('name', 'Name', [Lower('name')]),
    ('abv', 'ABV', [F('abv_value').desc(nulls_last=True)]),
    ('brewed', 'Most brewed', [F('batch_count').desc()]),
]
RECIPE_SORT_ORDERING = {key: ordering for key, _, ordering in RECIPE_SORTS}


@login_required
def recipe_list(request):
    """The user's recipes, narrowed by the ?q=, ?type= and ?sort= query string.

    Unknown filter values are ignored rather than raising, so a stale
    bookmark still shows the list.
    """
    query = request.GET.get('q', '').strip()
    brew_type = request.GET.get('type', '')
    if brew_type not in dict(Recipe.BREW_TYPE_CHOICES):
        brew_type = ''
    sort = request.GET.get('sort', '')
    if sort not in RECIPE_SORT_ORDERING:
        sort = 'updated'

    all_recipes = Recipe.objects.filter(owner=request.user)
    recipes = all_recipes.annotate(
        batch_count=Count('sessions'),
        abv_value=ExpressionWrapper(
            (F('target_gravity') - F('target_final_gravity')) * 131.25,
            output_field=DecimalField(),
        ),
    )
    if query:
        recipes = recipes.filter(Q(name__icontains=query) | Q(style__icontains=query))
    if brew_type:
        recipes = recipes.filter(brew_type=brew_type)
    recipes = recipes.order_by(*RECIPE_SORT_ORDERING[sort], Lower('name'), 'pk')

    # Clearing the filters keeps the chosen sort.
    clear_url = reverse('recipe_list')
    if sort != 'updated':
        clear_url += f'?sort={sort}'

    return render(request, 'brews/recipe_list.html', {
        'recipes': recipes,
        'clear_url': clear_url,
        'total_count': all_recipes.count(),
        'query': query,
        'brew_type': brew_type,
        'sort': sort,
        'is_filtered': bool(query or brew_type),
        'brew_type_choices': Recipe.BREW_TYPE_CHOICES,
        'sort_choices': [(key, label) for key, label, _ in RECIPE_SORTS],
    })

@login_required
def recipe_detail(request, pk):
    # Load every ingredient up front so the page runs a fixed number of
    # queries however many line items the recipe has.
    recipes = Recipe.objects.select_related('yeast').prefetch_related(
        Prefetch('grain_bill', queryset=RecipeGrain.objects.select_related('grain')),
        Prefetch('hop_additions', queryset=RecipeHop.objects.select_related('hop')),
        Prefetch('adjunct_additions', queryset=RecipeAdjunct.objects.select_related('adjunct')),
    )
    recipe = get_object_or_404(recipes, pk=pk, owner=request.user)
    return render(request, 'brews/recipe_detail.html', {
        'recipe': recipe,
        'hop_schedule': sorted(recipe.hop_additions.all(), key=RecipeHop.schedule_key),
    })

# Ingredient sections on the recipe form, in brewing order:
# (formset prefix, formset class, heading, add-button label, help text)
INGREDIENT_SECTIONS = [
    ('grains', RecipeGrainFormSet, 'Grain bill', 'Add grain', ''),
    ('hops', RecipeHopFormSet, 'Hops', 'Add hop', 'Time is minutes for boil and whirlpool, days for dry hops.'),
    ('adjuncts', RecipeAdjunctFormSet, 'Adjuncts', 'Add adjunct', 'Sugars, fruit, spices and other additions.'),
]

def recipe_form_view(request, recipe, title, success_message, cancel_url):
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
        'cancel_url': cancel_url,
    })

@login_required
def recipe_create(request):
    return recipe_form_view(
        request, Recipe(owner=request.user), 'New Recipe',
        'Recipe "{name}" created successfully!',
        cancel_url=reverse('recipe_list'),
    )

@login_required
def recipe_edit(request, recipe_pk):
    recipe = get_object_or_404(Recipe, pk=recipe_pk, owner=request.user)
    return recipe_form_view(
        request, recipe, recipe.name,
        'Recipe "{name}" has been updated successfully!',
        cancel_url=reverse('recipe_detail', args=[recipe.pk]),
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
        form = BrewSessionForm(initial={'batch_number': recipe.next_batch_number})
    return render(request, 'brews/recipe_form.html', {
        'form': form,
        'title': f'Log Brew Session - {recipe.name}',
        'cancel_url': reverse('recipe_detail', args=[recipe.pk]),
    })

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
@require_POST
def session_status(request, pk):
    """Move a batch to another status.

    The board's "Move to …" form posts here and is redirected back. Drag and
    drop asks for JSON (Accept: application/json) and gets the re-rendered
    card instead, so the page can update without reloading.
    """
    session = get_object_or_404(
        BrewSession.objects.select_related('recipe'), pk=pk, recipe__owner=request.user,
    )
    wants_json = 'application/json' in request.headers.get('Accept', '')
    status = request.POST.get('status')
    if status not in dict(BrewSession.STATUS_CHOICES):
        if wants_json:
            return JsonResponse({'error': 'Unknown status.'}, status=400)
        return HttpResponseBadRequest('Unknown status.')

    changed = status != session.status
    if changed:
        session.status = status
        session.save()
    message = f'{session.recipe.name} batch {session.batch_number} moved to {session.get_status_display()}.'

    if wants_json:
        return JsonResponse({
            'status': session.status,
            'message': message,
            'card': render_to_string('brews/partials/brew_card.html', {'session': session}, request=request),
        })
    if changed:
        messages.success(request, message)
    return redirect('dashboard')

@login_required
def session_detail(request, pk):
    session = get_object_or_404(BrewSession, pk=pk, recipe__owner=request.user)
    return render(request, 'brews/session_details.html', {'session': session})

@login_required
def dashboard(request):
    sessions = BrewSession.objects.filter(recipe__owner=request.user).select_related('recipe').order_by('-brew_date')
    fermenting = list(sessions.filter(status='fermenting'))
    conditioning = list(sessions.filter(status='conditioning'))
    ready = sessions.filter(status='ready')
    archived_count = sessions.filter(status='archived').count()
    activity = monthly_activity(request.user)
    return render(request, 'brews/dashboard.html', {
        'stats': dashboard_stats(request.user),
        'activity': activity,
        'activity_chart': {
            'labels': [month.strftime('%b') for month, _ in activity],
            'titles': [month.strftime('%B %Y') for month, _ in activity],
            'counts': [count for _, count in activity],
        },
        'activity_total': sum(count for _, count in activity),
        'attention': needs_attention(fermenting + conditioning),
        'board_columns': [
            ('fermenting', 'Fermenting', fermenting),
            ('conditioning', 'Conditioning', conditioning),
            ('ready', 'Ready', ready),
        ],
        'fermenting': fermenting,
        'conditioning': conditioning,
        'ready': ready,
        'archived_count': archived_count,
    })


HISTORY_PAGE_SIZE = 20


@login_required
def brew_history(request):
    """Every batch the user has brewed, newest first, filtered by the
    ?q= (recipe name), ?status=, ?type= and ?year= query string."""
    sessions = BrewSession.objects.filter(recipe__owner=request.user)
    years = [d.year for d in sessions.dates('brew_date', 'year', order='DESC')]

    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    if status not in dict(BrewSession.STATUS_CHOICES):
        status = ''
    brew_type = request.GET.get('type', '')
    if brew_type not in dict(Recipe.BREW_TYPE_CHOICES):
        brew_type = ''
    year = request.GET.get('year', '')
    if not year.isdigit() or int(year) not in years:
        year = ''

    filtered = sessions.select_related('recipe')
    if query:
        filtered = filtered.filter(recipe__name__icontains=query)
    if status:
        filtered = filtered.filter(status=status)
    if brew_type:
        filtered = filtered.filter(recipe__brew_type=brew_type)
    if year:
        filtered = filtered.filter(brew_date__year=int(year))
    filtered = filtered.order_by('-brew_date', '-batch_number', '-pk')

    page = Paginator(filtered, HISTORY_PAGE_SIZE).get_page(request.GET.get('page'))

    # Page links keep the filters; the Clear link drops them.
    params = request.GET.copy()
    params.pop('page', None)

    return render(request, 'brews/brew_history.html', {
        'page': page,
        'total_count': sessions.count(),
        'query': query,
        'status': status,
        'brew_type': brew_type,
        'year': year,
        'years': years,
        'is_filtered': bool(query or status or brew_type or year),
        'status_choices': BrewSession.STATUS_CHOICES,
        'brew_type_choices': Recipe.BREW_TYPE_CHOICES,
        'filter_query': params.urlencode(),
    })


@login_required
def batch_new(request):
    """Pick the recipe for a new batch: recently brewed first, then the rest.

    ?q= filters by name or style for browsers without JavaScript; with it,
    the page filters as you type.
    """
    recipes = Recipe.objects.filter(owner=request.user).annotate(
        last_brewed=Max('sessions__brew_date'),
        batch_count=Count('sessions'),
    )
    total_count = recipes.count()
    query = request.GET.get('q', '').strip()
    if query:
        recipes = recipes.filter(Q(name__icontains=query) | Q(style__icontains=query))
    recent = recipes.filter(last_brewed__isnull=False).order_by('-last_brewed', Lower('name'))
    others = recipes.filter(last_brewed__isnull=True).order_by(Lower('name'))
    sections = [
        (title, list(section))
        for title, section in (('Recently brewed', recent), ('Other recipes', others))
    ]
    return render(request, 'brews/batch_new.html', {
        'sections': [(title, rows) for title, rows in sections if rows],
        'total_count': total_count,
        'query': query,
    })

