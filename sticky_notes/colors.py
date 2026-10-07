"""Sticky-note color palettes."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NoteTheme:
    name: str
    body: str
    header: str
    text: str
    muted: str
    accent: str


THEMES: dict[str, NoteTheme] = {
    "yellow": NoteTheme("yellow", "#FFF4B8", "#F5E28A", "#3D3418", "#8A7A3A", "#C9A227"),
    "green": NoteTheme("green", "#D8F0C8", "#B9E0A4", "#1F3D1A", "#4A7040", "#5A9A3A"),
    "pink": NoteTheme("pink", "#F8D4E4", "#EFB4CE", "#4A1E33", "#8A4A68", "#C45A88"),
    "purple": NoteTheme("purple", "#E4D4F8", "#CDB4EF", "#2E1A4A", "#6A4A8A", "#7A5AC4"),
    "blue": NoteTheme("blue", "#D4E8F8", "#B4D4EF", "#1A2E4A", "#4A6A8A", "#3A7AC4"),
    "gray": NoteTheme("gray", "#EDEDED", "#D8D8D8", "#222222", "#666666", "#888888"),
}

DEFAULT_THEME = "yellow"


def theme_for(name: str) -> NoteTheme:
    return THEMES.get(name, THEMES[DEFAULT_THEME])
