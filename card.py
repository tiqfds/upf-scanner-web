"""Turn one phone scan response into the card on the page.

This file does not decide a NOVA group. The scanner package does that.
"""

from __future__ import annotations

from typing import Any

TITLES = {
    1: "Group 1: Unprocessed or minimally processed foods",
    2: "Group 2: Processed culinary ingredients",
    3: "Group 3: Processed foods",
    4: "Group 4: Ultra-processed foods",
}

LIKELY = "Likely ultra-processed, being verified."
RETAKE = "Fit the whole ingredient list in the frame, then try again."

PHRASE = {
    1: "unprocessed or minimally processed food",
    2: "processed culinary ingredient",
    3: "processed food",
    4: "ultra-processed food",
}


def _state(scan: dict[str, Any]) -> str:
    state = scan.get("verdict_state")
    if state in ("confirmed", "provisional", "cannot_determine"):
        return state
    if scan.get("nova_group") is None:
        return "cannot_determine"
    return "confirmed"


def _line(part: dict[str, Any]) -> dict[str, Any]:
    marker = bool(part.get("marker"))
    kind = (part.get("kind") or "").strip()
    return {
        "name": part.get("name") or "",
        "marker": marker,
        "category": kind if marker else "",
        "children": [],
    }


def ingredient_lines(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lines = []
    for row in rows:
        parts = row.get("parts") or []
        if not parts:
            marker = bool(row.get("marker"))
            kind = (row.get("kind") or "").strip()
            lines.append({
                "name": row.get("name") or "",
                "marker": marker,
                "category": kind if marker else "",
                "children": [],
            })
            continue
        parent = next((part for part in parts if not part.get("nested")), parts[0])
        line = _line(parent)
        line["children"] = [_line(part) for part in parts if part.get("nested")]
        lines.append(line)
    return lines


def _text(scan: dict[str, Any], *keys: str) -> str:
    for key in keys:
        text = scan.get(key)
        if isinstance(text, str) and text.strip():
            return text.strip()
    return ""


def card_from_scan(scan: dict[str, Any]) -> dict[str, Any]:
    """The title, notice, group, and ingredient lines for one scan.

    The scanner has already decided. This only picks the words the phone
    card uses:

    - confirmed: Group 1, 2, 3, or 4
    - provisional: "Likely ultra-processed, being verified."
    - cannot_determine: the scanner's own sentence, then the retake line,
      and no group. That covers a screenshot, a photo with no food, a
      missing or cut-off list, a paper bag, a tray with no list, and a
      product that is not a food or a drink.
    """
    state = _state(scan)
    ingredients = ingredient_lines(scan.get("ingredients") or [])
    if state == "cannot_determine":
        return {
            "title": _text(scan, "retake_reason", "reason", "notice") or "Could not read this label",
            "notice": RETAKE,
            "group": None,
            "ingredients": ingredients,
        }
    if state == "provisional":
        return {
            "title": LIKELY,
            "notice": None,
            "group": None,
            "ingredients": ingredients,
        }
    group = scan.get("nova_group")
    if group not in TITLES:
        return {
            "title": "Could not read this label",
            "notice": RETAKE,
            "group": None,
            "ingredients": [],
        }
    return {
        "title": TITLES[group],
        "notice": None,
        "group": group,
        "ingredients": ingredients,
    }


def marker_count(items: list[dict[str, Any]]) -> int:
    total = 0
    for item in items:
        if item.get("marker"):
            total += 1
        total += marker_count(item.get("children") or [])
    return total


def announcement(card: dict[str, Any]) -> str:
    group = card.get("group")
    if group not in PHRASE:
        return card.get("title") or ""
    count = marker_count(card.get("ingredients") or [])
    markers = "1 marker found" if count == 1 else f"{count} markers found"
    return f"NOVA {group}, {PHRASE[group]}, {markers}"
