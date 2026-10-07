"""Application shell: hidden root, note windows, tray-like manager."""

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont

from sticky_notes.store import Note, load_notes, save_notes
from sticky_notes.window import StickyNoteWindow

WELCOME_TEXT = (
    "Sticky Notes\n\n"
    "Type here. Drag the top bar to move.\n"
    "+  new note   📌 pin on top\n"
    "Dots change color. 🗑 deletes this note."
)


class StickyNotesApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Sticky Notes")
        self.root.geometry("280x360+40+40")
        self.root.minsize(240, 280)
        self.root.configure(bg="#1f1f1f")

        self.notes: dict[str, Note] = {}
        self.windows: dict[str, StickyNoteWindow] = {}

        self._build_manager()
        self._load()
        self.root.protocol("WM_DELETE_WINDOW", self._quit)

    def _build_manager(self) -> None:
        title_font = tkfont.Font(family="Segoe UI Semibold", size=14)
        body_font = tkfont.Font(family="Segoe UI", size=10)

        header = tk.Frame(self.root, bg="#1f1f1f")
        header.pack(fill=tk.X, padx=16, pady=(16, 8))
        tk.Label(
            header,
            text="Sticky Notes",
            fg="#f3f3f3",
            bg="#1f1f1f",
            font=title_font,
        ).pack(side=tk.LEFT)

        add = tk.Button(
            header,
            text="+ New",
            command=self._new_from_manager,
            bg="#3a3a3a",
            fg="#f3f3f3",
            activebackground="#4a4a4a",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=10,
            pady=4,
            cursor="hand2",
        )
        add.pack(side=tk.RIGHT)

        self.listbox = tk.Listbox(
            self.root,
            bd=0,
            highlightthickness=0,
            bg="#2b2b2b",
            fg="#f3f3f3",
            selectbackground="#4a4a4a",
            font=body_font,
            activestyle="none",
        )
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 8))
        self.listbox.bind("<Double-Button-1>", self._open_selected)

        footer = tk.Frame(self.root, bg="#1f1f1f")
        footer.pack(fill=tk.X, padx=16, pady=(0, 16))
        tk.Label(
            footer,
            text="Double-click a note to show it again.",
            fg="#9a9a9a",
            bg="#1f1f1f",
            font=body_font,
        ).pack(side=tk.LEFT)

    def _load(self) -> None:
        loaded = load_notes()
        if not loaded:
            loaded = [Note.create(x=420, y=160)]
            loaded[0].text = WELCOME_TEXT
        for note in loaded:
            self.notes[note.id] = note
            self._open_window(note)
        self._refresh_list()
        self._save()

    def _preview(self, note: Note) -> str:
        line = note.text.strip().splitlines()[0] if note.text.strip() else "Untitled note"
        return line[:42] + ("…" if len(line) > 42 else "")

    def _refresh_list(self) -> None:
        self.listbox.delete(0, tk.END)
        for note in self.notes.values():
            self.listbox.insert(tk.END, self._preview(note))

    def _ordered_ids(self) -> list[str]:
        return list(self.notes.keys())

    def _open_selected(self, _event: tk.Event | None = None) -> None:
        selection = self.listbox.curselection()
        if not selection:
            return
        note_id = self._ordered_ids()[selection[0]]
        window = self.windows.get(note_id)
        if window is None or not window.winfo_exists():
            self._open_window(self.notes[note_id])
            return
        window.deiconify()
        window.lift()

    def _open_window(self, note: Note) -> StickyNoteWindow:
        existing = self.windows.get(note.id)
        if existing is not None and existing.winfo_exists():
            return existing
        window = StickyNoteWindow(
            self.root,
            note,
            on_change=self._on_change,
            on_new=self._new_near,
            on_delete=self._delete_note,
        )
        self.windows[note.id] = window
        return window

    def _new_from_manager(self) -> None:
        offset = 30 * (len(self.notes) % 8)
        self._add_note(x=160 + offset, y=160 + offset)

    def _new_near(self, source: Note) -> None:
        self._add_note(x=source.x + 28, y=source.y + 28, color=source.color)

    def _add_note(self, *, x: int, y: int, color: str = "yellow") -> None:
        note = Note.create(x=x, y=y, color=color)
        self.notes[note.id] = note
        self._open_window(note)
        self._refresh_list()
        self._save()

    def _on_change(self, note: Note) -> None:
        self.notes[note.id] = note
        self._refresh_list()
        self._save()

    def _delete_note(self, note: Note) -> None:
        self.notes.pop(note.id, None)
        self.windows.pop(note.id, None)
        self._refresh_list()
        self._save()
        if not self.notes:
            self._new_from_manager()

    def _save(self) -> None:
        save_notes(list(self.notes.values()))

    def _quit(self) -> None:
        for window in list(self.windows.values()):
            if window.winfo_exists():
                window._flush()
        self._save()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()
