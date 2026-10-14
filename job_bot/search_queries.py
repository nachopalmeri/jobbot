"""Build bounded, diverse query batches without discarding profile keywords."""

from typing import Iterable, List


def build_search_queries(
    personal_keywords: Iterable[str],
    broad_keywords: Iterable[str],
    limit: int,
    include_broad: bool = True,
) -> List[str]:
    """Prefer broad role-family coverage, then fill remaining slots with user terms."""
    personal = list(personal_keywords)
    broad = list(broad_keywords)
    ordered_keywords = []
    if include_broad:
        personal_slots = min(2, len(personal))
        broad_slots = max(0, limit - personal_slots)
        ordered_keywords.extend(broad[:broad_slots])
    ordered_keywords.extend(personal)
    if include_broad:
        ordered_keywords.extend(broad[broad_slots:])

    selected = []
    seen = set()
    for keyword in ordered_keywords:
        clean_keyword = str(keyword or "").strip()
        normalized = clean_keyword.casefold()
        if not clean_keyword or normalized in seen:
            continue
        seen.add(normalized)
        selected.append(clean_keyword)
        if len(selected) >= max(0, limit):
            break
    return selected
