"""Frameless sticky-note window."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from typing import Callable

import tkinter as tk
from tkinter import font as tkfont

from sticky_notes.colors import THEMES, NoteTheme, theme_for
from sticky_notes.store import Note

MIN_WIDTH = 220
MIN_HEIGHT = 180

DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMWCP_ROUND = 2


def _apply_rounded_corners(widget: tk.Misc) -> None:
    try:
        hwnd = wintypes.HWND(widget.winfo_id())
        preference = ctypes.c_int(DWMWCP_ROUND)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_WINDOW_CORNER_PREFERENCE,
            ctypes.byref(preference),
            ctypes.sizeof(preference),
        )
    except Exception:
        pass


class StickyNoteWindow(tk.Toplevel):
    def __init__(
        self,
        master: tk.Tk,
        note: Note,
        *,
        on_change: Callable[[Note], None],
        on_new: Callable[[Note], None],
        on_delete: Callable[[Note], None],
    ) -> None:
        super().__init__(master)
        self.note = note
        self._on_change = on_change
        self._on_new = on_new
        self._on_delete = on_delete
        self._drag_offset = (0, 0)
        self._save_job: str | None = None
        self._theme = theme_for(note.color)

        self.overrideredirect(True)
        self.geometry(f"{note.width}x{note.height}+{note.x}+{note.y}")
        self.minsize(MIN_WIDTH, MIN_HEIGHT)
        self.configure(bg=self._theme.body)
        self.attributes("-topmost", note.always_on_top)

        self._body_font = tkfont.Font(family="Segoe UI", size=12)
        self._chrome_font = tkfont.Font(family="Segoe UI", size=11)
        self._icon_font = tkfont.Font(family="Segoe UI", size=13)

        self._build()
        self.after(50, lambda: _apply_rounded_corners(self))
        self.protocol("WM_DELETE_WINDOW", self._hide)

    def _build(self) -> None:
        theme = self._theme
        self.header = tk.Frame(self, bg=theme.header, height=36)
        self.header.pack(fill=tk.X)
        self.header.pack_propagate(False)

        self.btn_new = self._chrome_button(self.header, "+", self._spawn_new)
        self.btn_new.pack(side=tk.LEFT, padx=(8, 2), pady=4)

        self.pin_var = tk.BooleanVar(value=self.note.always_on_top)
        self.btn_pin = self._chrome_button(self.header, "📌", self._toggle_pin)
        self.btn_pin.pack(side=tk.LEFT, padx=2, pady=4)

        self.btn_close = self._chrome_button(self.header, "✕", self._hide)
        self.btn_close.pack(side=tk.RIGHT, padx=(2, 8), pady=4)

        self.btn_delete = self._chrome_button(self.header, "🗑", self._delete)
        self.btn_delete.pack(side=tk.RIGHT, padx=2, pady=4)

        for event in ("<ButtonPress-1>", "<B1-Motion>", "<ButtonRelease-1>"):
            self.header.bind(event, self._on_header_event)
            for child in self.header.winfo_children():
                if child not in (self.btn_new, self.btn_pin, self.btn_close, self.btn_delete):
                    child.bind(event, self._on_header_event)

        # Color dots sit in header; skip drag on them.
        self.swatches = tk.Frame(self.header, bg=theme.header)
        self.swatches.pack(side=tk.LEFT, padx=8)
        for name in THEMES:
            dot = tk.Canvas(
                self.swatches,
                width=14,
                height=14,
                highlightthickness=0,
                bg=theme.header,
            )
            fill = THEMES[name].body
            outline = theme.accent if name == self.note.color else THEMES[name].header
            dot.create_oval(1, 1, 13, 13, fill=fill, outline=outline, width=2)
            dot.pack(side=tk.LEFT, padx=2)
            dot.bind("<Button-1>", lambda _e, n=name: self._set_color(n))

        self.text = tk.Text(
            self,
            wrap=tk.WORD,
            bd=0,
            highlightthickness=0,
            padx=12,
            pady=10,
            font=self._body_font,
            bg=theme.body,
            fg=theme.text,
            insertbackground=theme.text,
            undo=True,
        )
        self.text.pack(fill=tk.BOTH, expand=True)
        self.text.insert("1.0", self.note.text)
        self.text.bind("<<Modified>>", self._on_text_modified)

        self.grip = tk.Frame(self, bg=theme.body, cursor="size_nw_se", height=12)
        self.grip.pack(fill=tk.X, side=tk.BOTTOM)
        self.grip.bind("<ButtonPress-1>", self._start_resize)
        self.grip.bind("<B1-Motion>", self._do_resize)
        self.grip.bind("<ButtonRelease-1>", self._finish_move_or_resize)

        self._refresh_pin_look()

    def _chrome_button(self, parent: tk.Misc, label: str, command: Callable[[], None]) -> tk.Label:
        btn = tk.Label(
            parent,
            text=label,
            bg=self._theme.header,
            fg=self._theme.muted,
            font=self._icon_font,
            cursor="hand2",
            padx=6,
        )
        btn.bind("<Button-1>", lambda _e: command())
        btn.bind("<Enter>", lambda _e: btn.configure(fg=self._theme.text))
        btn.bind("<Leave>", lambda _e: btn.configure(fg=self._theme.muted))
        return btn

    def apply_theme(self, theme: NoteTheme) -> None:
        self._theme = theme
        self.configure(bg=theme.body)
        self.header.configure(bg=theme.header)
        self.swatches.configure(bg=theme.header)
        self.text.configure(bg=theme.body, fg=theme.text, insertbackground=theme.text)
        self.grip.configure(bg=theme.body)
        for widget in (self.btn_new, self.btn_pin, self.btn_close, self.btn_delete):
            widget.configure(bg=theme.header, fg=theme.muted)
        for child in self.swatches.winfo_children():
            child.configure(bg=theme.header)
        self._refresh_pin_look()
        self._redraw_swatches()

    def _redraw_swatches(self) -> None:
        names = list(THEMES)
        for canvas, name in zip(self.swatches.winfo_children(), names):
            canvas.delete("all")
            fill = THEMES[name].body
            outline = self._theme.accent if name == self.note.color else THEMES[name].header
            canvas.create_oval(1, 1, 13, 13, fill=fill, outline=outline, width=2)

    def _set_color(self, name: str) -> None:
        self.note.color = name
        self.apply_theme(theme_for(name))
        self._persist()

    def _toggle_pin(self) -> None:
        self.note.always_on_top = not self.note.always_on_top
        self.attributes("-topmost", self.note.always_on_top)
        self._refresh_pin_look()
        self._persist()

    def _refresh_pin_look(self) -> None:
        color = self._theme.accent if self.note.always_on_top else self._theme.muted
        self.btn_pin.configure(fg=color)

    def _spawn_new(self) -> None:
        self._on_new(self.note)

    def _hide(self) -> None:
        self._flush()
        self.withdraw()

    def _delete(self) -> None:
        self._on_delete(self.note)
        self.destroy()

    def _on_text_modified(self, _event: tk.Event | None = None) -> None:
        if not self.text.edit_modified():
            return
        self.text.edit_modified(False)
        self.note.text = self.text.get("1.0", "end-1c")
        self._schedule_save()

    def _schedule_save(self) -> None:
        if self._save_job is not None:
            self.after_cancel(self._save_job)
        self._save_job = self.after(350, self._persist)

    def _flush(self) -> None:
        if self._save_job is not None:
            self.after_cancel(self._save_job)
            self._save_job = None
        self.note.text = self.text.get("1.0", "end-1c")
        self._sync_geometry()
        self._persist()

    def _persist(self) -> None:
        self._save_job = None
        self._on_change(self.note)

    def _sync_geometry(self) -> None:
        self.update_idletasks()
        self.note.x = self.winfo_x()
        self.note.y = self.winfo_y()
        self.note.width = self.winfo_width()
        self.note.height = self.winfo_height()

    def _on_header_event(self, event: tk.Event) -> None:
        widget = event.widget
        if widget in (self.btn_new, self.btn_pin, self.btn_close, self.btn_delete):
            return
        if isinstance(widget, tk.Canvas):
            return
        if event.type == tk.EventType.ButtonPress:
            self._start_move(event)
        elif event.type == tk.EventType.Motion:
            self._do_move(event)
        else:
            self._finish_move_or_resize(event)

    def _start_move(self, event: tk.Event) -> None:
        self._drag_offset = (event.x_root - self.winfo_x(), event.y_root - self.winfo_y())

    def _do_move(self, event: tk.Event) -> None:
        x = event.x_root - self._drag_offset[0]
        y = event.y_root - self._drag_offset[1]
        self.geometry(f"+{x}+{y}")

    def _start_resize(self, event: tk.Event) -> None:
        self._resize_origin = (event.x_root, event.y_root, self.winfo_width(), self.winfo_height())

    def _do_resize(self, event: tk.Event) -> None:
        ox, oy, ow, oh = self._resize_origin
        width = max(MIN_WIDTH, ow + (event.x_root - ox))
        height = max(MIN_HEIGHT, oh + (event.y_root - oy))
        self.geometry(f"{width}x{height}")

    def _finish_move_or_resize(self, _event: tk.Event | None = None) -> None:
        self._sync_geometry()
        self._persist()
