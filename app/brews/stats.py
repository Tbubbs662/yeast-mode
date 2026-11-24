"""Numbers for the dashboard's stat tiles and brewing activity chart.

Everything is aggregated in the database rather than per row in Python.
"""
import datetime

from django.db.models import Avg, Count, DecimalField, ExpressionWrapper, F # type: ignore
from django.db.models.functions import TruncMonth # type: ignore
from django.utils import timezone # type: ignore

from .models import BrewSession, Recipe

ABV_FACTOR = 131.25  # same formula as BrewSession.abv


def _brewed(user, today):
    """The user's batches up to today (planned future brews don't count yet)."""
    return BrewSession.objects.filter(recipe__owner=user, brew_date__lte=today)


def dashboard_stats(user, today=None):
    """Values for the stat tiles. A tile's value is None when there's no data for it yet."""
    today = today or timezone.localdate()
    brewed = _brewed(user, today)

    measured = brewed.filter(original_gravity__isnull=False, final_gravity__isnull=False)
    abv = measured.aggregate(
        average=Avg(ExpressionWrapper(
            (F('original_gravity') - F('final_gravity')) * ABV_FACTOR,
            output_field=DecimalField(),
        )),
        count=Count('pk'),
    )

    type_counts = dict(
        Recipe.objects.filter(owner=user).values_list('brew_type').annotate(n=Count('pk')).order_by()
    )
    recipe_types = [
        (label, type_counts[value])
        for value, label in Recipe.BREW_TYPE_CHOICES
        if type_counts.get(value)
    ]

    return {
        'batches_this_year': brewed.filter(brew_date__year=today.year).count(),
        'batches_total': brewed.count(),
        'average_abv': round(float(abv['average']), 1) if abv['average'] is not None else None,
        'abv_batch_count': abv['count'],
        'recipe_count': sum(type_counts.values()),
        'recipe_types': recipe_types,
    }


def monthly_activity(user, today=None, months=12):
    """Batches brewed per month for the last `months` months, oldest first.

    Returns [(first day of month, count), ...] including months with no batches.
    """
    today = today or timezone.localdate()
    month_index = today.year * 12 + today.month - 1 - (months - 1)
    start = datetime.date(month_index // 12, month_index % 12 + 1, 1)

    counts = dict(
        _brewed(user, today)
        .filter(brew_date__gte=start)
        .annotate(month=TruncMonth('brew_date'))
        .values_list('month')
        .annotate(n=Count('pk'))
        .order_by()
    )

    result = []
    for offset in range(months):
        index = month_index + offset
        month = datetime.date(index // 12, index % 12 + 1, 1)
        result.append((month, counts.get(month, 0)))
    return result
