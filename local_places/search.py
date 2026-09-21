"""Typo-tolerant search + "Did you mean?" ranking for the public
`/local/places/` API (BE-1 + BE-8).

Reuses the normalize/fuzzy primitives already used by the Admin search
(`tybee_backend/search_utils.py`) so both surfaces behave consistently.
"""

import re
from difflib import SequenceMatcher

from django.utils.html import strip_tags

from tybee_backend.search_utils import fuzzy_match, normalize_text

# Below this length, fuzzy ratio comparisons produce noise (almost anything
# is "close enough" to a 1-2 char string), so only exact substring matches.
MIN_FUZZY_QUERY_LENGTH = 3

# "Did you mean?" only suggests a name at least this close to the query.
# Below it, the best fuzzy hit is usually just another place sharing a common
# word ("bar", "grill"), not what the user meant.
DID_YOU_MEAN_MIN_SIMILARITY = 0.75

_WORD_RE = re.compile(r"[^A-Za-z0-9]+")


def parse_id_list(value):
    """'1, 3,abc' -> [1, 3]. Ignores anything non-numeric instead of 500ing."""
    return [int(v) for v in (value or "").split(",") if v.strip().isdigit()]


def _words(text):
    return [w for w in _WORD_RE.split(text or "") if w]


def _place_haystack_fields(place):
    """Distinct field strings used for fuzzy matching (NOT description —
    that gets exact-only matching, see `_matches_term`)."""
    fields = [place.name, place.address]
    if place.category_id and place.category:
        fields.append(place.category.title)
    fields += [t.title for t in place.tags.all()]
    fields += [a.title for a in place.activities.all()]
    fields += [l.name for l in place.live_like_a_local.all()]
    return [f for f in fields if f]


def _matches_term(place, term):
    """Return (matched, is_exact, name_hit) for a single place."""
    normalized_query = normalize_text(term)
    if not normalized_query:
        return False, False, False

    haystack_fields = _place_haystack_fields(place)
    description_plain = strip_tags(place.description or "")

    # 1. Exact (punctuation/case-insensitive) substring anywhere, including
    #    the description — but no fuzzy ratio against the description, a
    #    long block of text produces meaningless similarity scores.
    exact = any(normalized_query in normalize_text(f) for f in haystack_fields)
    exact = exact or normalized_query in normalize_text(description_plain)
    name_hit = normalized_query in normalize_text(place.name or "")

    if exact:
        return True, True, name_hit

    if len(normalized_query) < MIN_FUZZY_QUERY_LENGTH:
        return False, False, False

    # 2. Whole query vs whole field — catches "Docks Bars" vs "Doc's Bar"
    #    (docksbars ~ docsbar), which per-word comparison alone would miss.
    for field in haystack_fields:
        if fuzzy_match(term, field):
            return True, False, field == place.name

    # 3. Word vs word — every query word must match some word of the place's
    #    fields ("kelpy" ~ "Kelpie" in "The Kelpie Pub"). Requiring all words
    #    keeps a common word like "bar" or "tybee" (in every address) from
    #    matching half the catalog.
    query_words = _words(term)
    field_words = [word for field in haystack_fields for word in _words(field)]
    if query_words and all(
        any(fuzzy_match(query_word, word) for word in field_words)
        for query_word in query_words
    ):
        name_words = _words(place.name)
        name_hit = all(
            any(fuzzy_match(query_word, word) for word in name_words)
            for query_word in query_words
        )
        return True, False, name_hit

    return False, False, False


def _name_similarity(term, name):
    """0..1, how close `term` is to `name`: the better of the whole query vs
    the whole name, and the average of each query word's best match among the
    name's words."""
    query, target = normalize_text(term), normalize_text(name)
    if not query or not target:
        return 0.0
    whole = SequenceMatcher(None, query, target).ratio()
    query_words = [w for w in (normalize_text(w) for w in _words(term)) if w]
    name_words = [w for w in (normalize_text(w) for w in _words(name)) if w]
    if not query_words or not name_words:
        return whole
    per_word = sum(
        max(SequenceMatcher(None, query_word, name_word).ratio() for name_word in name_words)
        for query_word in query_words
    ) / len(query_words)
    return max(whole, per_word)


def rank_places(queryset, term):
    """Fuzzy-filter and rank `queryset` by `term`.

    Returns (ordered_list_of_places, did_you_mean). `did_you_mean` is the
    name of the top result when nothing matched exactly (only fuzzy hits),
    and None otherwise (including when there are zero results).
    """
    term = (term or "").strip()
    if not term:
        return list(queryset), None

    scored = []
    any_exact = False
    for place in queryset:
        matched, exact, name_hit = _matches_term(place, term)
        if not matched:
            continue
        if exact:
            any_exact = True
        similarity = _name_similarity(term, place.name or "")
        # Name hits first, exact matches before fuzzy-only, then by how close
        # the name is to the query (alphabetical only breaks ties).
        rank = (
            0 if name_hit else 1,
            0 if exact else 1,
            -similarity,
            (place.name or "").lower(),
        )
        scored.append((rank, similarity, place))

    scored.sort(key=lambda item: item[0])
    ordered = [place for _, _, place in scored]

    did_you_mean = None
    if scored and not any_exact and scored[0][1] >= DID_YOU_MEAN_MIN_SIMILARITY:
        did_you_mean = scored[0][2].name
    return ordered, did_you_mean
