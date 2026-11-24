"""What on the dashboard needs the brewer's attention today."""
from dataclasses import dataclass

from django.utils import timezone # type: ignore

from .models import BrewSession

# Starting thresholds; tune once there's real brewing data.
FERMENTING_CHECK_DAYS = 14
CONDITIONING_READY_DAYS = 21

CHECK_GRAVITY = 'check_gravity'
PROBABLY_READY = 'probably_ready'


@dataclass
class AttentionItem:
    session: BrewSession
    kind: str
    days: int

    @property
    def weeks(self):
        return self.days // 7


def needs_attention(sessions, today=None):
    """Attention items for the given sessions, longest-waiting first.

    - Fermenting for FERMENTING_CHECK_DAYS or more: check gravity.
    - Conditioning for CONDITIONING_READY_DAYS or more: probably ready.
    """
    today = today or timezone.localdate()
    items = []
    for session in sessions:
        if session.status == BrewSession.FERMENTING:
            # Fermentation starts on brew day, which also covers batches
            # that were logged after the fact.
            days = session.days_since_brewed(today)
            if days >= FERMENTING_CHECK_DAYS:
                items.append(AttentionItem(session, CHECK_GRAVITY, days))
        elif session.status == BrewSession.CONDITIONING:
            days = session.days_in_status(today)
            if days >= CONDITIONING_READY_DAYS:
                items.append(AttentionItem(session, PROBABLY_READY, days))
    items.sort(key=lambda item: item.days, reverse=True)
    return items
