"""Streamlit page for one ingredient-list photo.

The NOVA group comes from the scanner package in the original project, through
the same server.scan_image the plain Python page uses. This file only draws
the card that card.py builds.
"""

from __future__ import annotations

import html
from typing import Any

import streamlit as st

import server
from card import announcement

GROUP_COLORS = {1: "#3F8F5B", 2: "#6F8F3A", 3: "#B7801A", 4: "#7A3E6E"}
DEFAULT_COLOR = "#1B2A2F"
PUNCTUATION = "\\`*_{}[]()#+-.!|<>~$:&"


@st.cache_resource(show_spinner="Loading the scanner")
def connect() -> bool:
    server.connect_scanner()
    return True


def plain(text: str) -> str:
    """Show scanner text as written, not as markdown."""
    return "".join("\\" + ch if ch in PUNCTUATION else ch for ch in str(text))


def ingredient_markdown(item: dict[str, Any], depth: int = 0) -> str:
    name = plain(item.get("name") or "")
    if item.get("marker"):
        category = plain(item["category"]) if item.get("category") else ""
        name = f"**{name}**" + (f" │ {category}" if category else "")
    lines = ["    " * depth + "- " + name]
    for child in item.get("children") or []:
        lines.append(ingredient_markdown(child, depth + 1))
    return "\n".join(lines)


def show_form() -> None:
    st.title("Check a food label")
    st.caption("Choose a photo that shows the ingredient list.")
    photo = st.file_uploader(
        "Choose a photo",
        type=["jpg", "jpeg", "png", "webp"],
        key=f"photo-{st.session_state.round}",
    )
    if photo is None:
        return
    image = photo.getvalue()
    st.image(image)
    if len(image) > server.MAX_BYTES:
        st.error("That file is too large. Choose a smaller photo.")
        return
    if st.button("Check this photo", type="primary", use_container_width=True):
        with st.spinner("Reading the ingredient list."):
            code, payload = server.scan_image(image)
        if code == 200:
            st.session_state.card = payload
            st.session_state.image = image
        else:
            st.session_state.error = payload.get("error") or "The scan did not finish."
        st.rerun()


def show_card(card: dict[str, Any], image: bytes) -> None:
    color = GROUP_COLORS.get(card.get("group"), DEFAULT_COLOR)
    st.image(image)
    st.markdown(
        f'<h2 style="color:{color}">{html.escape(card["title"])}</h2>',
        unsafe_allow_html=True,
    )
    if card.get("announcement") and card.get("group"):
        st.caption(card["announcement"])
    if card.get("notice"):
        st.write(plain(card["notice"]))
    items = card.get("ingredients") or []
    if items:
        st.markdown("\n".join(ingredient_markdown(item) for item in items))
    if st.button("Okay", type="primary", use_container_width=True):
        st.session_state.card = None
        st.session_state.image = None
        st.session_state.round += 1
        st.rerun()


def main() -> None:
    st.set_page_config(page_title="Ultra-processed food", layout="centered")
    st.session_state.setdefault("round", 0)
    st.session_state.setdefault("card", None)
    st.session_state.setdefault("image", None)
    try:
        connect()
    except SystemExit as stop:
        st.error(str(stop))
        return
    error = st.session_state.pop("error", None)
    if st.session_state.card:
        show_card(st.session_state.card, st.session_state.image)
        return
    show_form()
    if error:
        st.error(error)


main()
