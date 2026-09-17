"""Punctuation/typo-tolerant search helpers shared across admin classes.

Standard Django admin search only does a case-sensitive-ish SQL `icontains`
per configured field. It does not tolerate punctuation differences
("O'Learys" vs "OLearys"), nor minor spelling mistakes ("Restaurent" vs
"Restaurant"). This module normalizes text (lowercase, strip punctuation
and spaces) before comparing, and falls back to a similarity ratio so
close-but-not-exact spellings still match.
"""

import re
from difflib import SequenceMatcher

_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def normalize_text(text):
    """Lowercase and strip everything but letters/digits."""
    return _NON_ALNUM_RE.sub("", (text or "").lower())


def fuzzy_match(query, target, threshold=0.6):
    """True if `query` is a (normalized) substring of `target`, or close
    enough to it (spelling variations) per `SequenceMatcher` ratio."""
    normalized_query = normalize_text(query)
    normalized_target = normalize_text(target)
    if not normalized_query or not normalized_target:
        return False
    if normalized_query in normalized_target:
        return True
    return SequenceMatcher(None, normalized_query, normalized_target).ratio() >= threshold


class FuzzySearchAdminMixin:
    """Mixin for `unfold.admin.ModelAdmin` subclasses that replaces the
    admin search box behaviour with punctuation/typo-tolerant matching.

    Subclasses must:
      - keep a non-empty `search_fields` tuple (Django only renders the
        search box in the changelist template when this is truthy — the
        actual lookup logic below ignores its contents).
      - override `get_search_haystack(obj)` to return the list of strings
        that should be searchable for that row (e.g. name, address,
        related category/tag titles).
    """

    fuzzy_search_threshold = 0.6

    def get_search_haystack(self, obj):
        return [str(obj)]

    def get_search_results(self, request, queryset, search_term):
        search_term = (search_term or "").strip()
        if not search_term:
            return queryset, False

        # Every whitespace-separated token must match at least one haystack
        # string, so "beach rest" still finds "Beachside Restaurant".
        tokens = search_term.split()
        matched_ids = []
        for obj in queryset:
            haystacks = [h for h in self.get_search_haystack(obj) if h]
            if all(
                any(fuzzy_match(token, h, self.fuzzy_search_threshold) for h in haystacks)
                for token in tokens
            ):
                matched_ids.append(obj.pk)

        return queryset.filter(pk__in=matched_ids), False
