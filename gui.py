"""Desktop GUI for Pomodoro Tracker using tkinter."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from threading import Thread
from queue import Queue, Empty

from timer import format_time
from categorizer import categorize_task, CATEGORIES
from storage import load_config, load_sessions, save_session

# States
IDLE = "IDLE"
FOCUS = "FOCUS"
BREAK = "BREAK"
PAUSED = "PAUSED"

# Duration presets (minutes)
DURATIONS = [5, 15, 25, 50]

# Theme colors
THEMES = {
    IDLE: {"bg": "#2b2b2b", "fg": "#ffffff", "accent": "#888888", "bar": "#555555"},
    FOCUS: {"bg": "#3b1c1c", "fg": "#ffffff", "accent": "#e74c3c", "bar": "#e74c3c"},
    BREAK: {"bg": "#1c3b2a", "fg": "#ffffff", "accent": "#2ecc71", "bar": "#2ecc71"},
    PAUSED: {"bg": "#3b351c", "fg": "#ffffff", "accent": "#f39c12", "bar": "#f39c12"},
}


class PomodoroGUI:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Pomodoro Tracker")
        self.root.resizable(False, False)

        self.config = load_config()
        self.state = IDLE
        self.remaining = 0
        self.total = 0
        self.elapsed = 0
        self.timer_id: str | None = None
        self.category_queue: Queue[str] = Queue()
        self.current_task = ""
        self.current_category = ""
        self._paused_from = IDLE

        self._build_ui()
        self._refresh_history()
        self._apply_theme(IDLE)
        self.root.bind("<Return>", lambda e: self._on_start())

    def _build_ui(self) -> None:
        # --- Title ---
        title_frame = ttk.Frame(self.root, padding=(20, 10))
        title_frame.pack(fill="x")
        ttk.Label(
            title_frame, text="POMODORO TRACKER", font=("Helvetica", 16, "bold")
        ).pack()

        ttk.Separator(self.root, orient="horizontal").pack(fill="x", padx=10)

        # --- Task entry ---
        task_frame = ttk.Frame(self.root, padding=(20, 10))
        task_frame.pack(fill="x")

        ttk.Label(task_frame, text="Task:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.task_entry = ttk.Entry(task_frame, width=30)
        self.task_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8))

        category_options = ["Auto-detect"] + CATEGORIES
        self.category_var = tk.StringVar(value="Auto-detect")
        self.category_combo = ttk.Combobox(
            task_frame,
            textvariable=self.category_var,
            values=category_options,
            state="readonly",
            width=14,
        )
        self.category_combo.grid(row=0, column=2, padx=(0, 8))

        self.duration_var = tk.StringVar(value="25")
        self.duration_spin = ttk.Spinbox(
            task_frame,
            textvariable=self.duration_var,
            values=[str(d) for d in DURATIONS],
            wrap=True,
            width=5,
        )
        self.duration_spin.grid(row=0, column=3, padx=(0, 4))
        ttk.Label(task_frame, text="min").grid(row=0, column=4, sticky="w")

        self.duration_var.trace_add("write", self._on_duration_changed)

        task_frame.columnconfigure(1, weight=1)

        ttk.Separator(self.root, orient="horizontal").pack(fill="x", padx=10)

        # --- Timer display ---
        self.timer_frame = tk.Frame(self.root, padx=20, pady=15)
        self.timer_frame.pack(fill="x")

        self.mode_label = tk.Label(
            self.timer_frame, text="READY", font=("Helvetica", 14, "bold")
        )
        self.mode_label.pack()

        self.time_label = tk.Label(
            self.timer_frame,
            text=format_time(self._get_duration_minutes() * 60),
            font=("Helvetica", 48, "bold"),
        )
        self.time_label.pack(pady=(5, 10))

        self.progress = ttk.Progressbar(
            self.timer_frame, orient="horizontal", length=350, mode="determinate"
        )
        self.progress.pack()

        # --- Control buttons ---
        btn_frame = ttk.Frame(self.root, padding=(20, 10))
        btn_frame.pack()

        self.start_btn = ttk.Button(btn_frame, text="Start", command=self._on_start)
        self.start_btn.grid(row=0, column=0, padx=5)

        self.pause_btn = ttk.Button(
            btn_frame, text="Pause", command=self._on_pause, state="disabled"
        )
        self.pause_btn.grid(row=0, column=1, padx=5)

        self.reset_btn = ttk.Button(
            btn_frame, text="Reset", command=self._on_reset, state="disabled"
        )
        self.reset_btn.grid(row=0, column=2, padx=5)

        ttk.Separator(self.root, orient="horizontal").pack(fill="x", padx=10)

        # --- History Treeview ---
        history_frame = ttk.Frame(self.root, padding=(20, 10))
        history_frame.pack(fill="both", expand=True)

        ttk.Label(history_frame, text="Recent Sessions", font=("Helvetica", 11, "bold")).pack(
            anchor="w"
        )

        columns = ("id", "task", "category", "duration", "status", "date")
        self.tree = ttk.Treeview(
            history_frame, columns=columns, show="headings", height=8
        )
        self.tree.heading("id", text="#")
        self.tree.heading("task", text="Task")
        self.tree.heading("category", text="Category")
        self.tree.heading("duration", text="Duration")
        self.tree.heading("status", text="Status")
        self.tree.heading("date", text="Date")

        self.tree.column("id", width=35, anchor="center")
        self.tree.column("task", width=140)
        self.tree.column("category", width=95, anchor="center")
        self.tree.column("duration", width=70, anchor="center")
        self.tree.column("status", width=65, anchor="center")
        self.tree.column("date", width=110, anchor="center")

        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    # --- Theme ---

    def _apply_theme(self, state: str) -> None:
        theme = THEMES[state]
        self.timer_frame.configure(bg=theme["bg"])
        self.mode_label.configure(bg=theme["bg"], fg=theme["accent"])
        self.time_label.configure(bg=theme["bg"], fg=theme["fg"])

        style = ttk.Style()
        style.configure(
            "Timer.Horizontal.TProgressbar",
            troughcolor="#444444",
            background=theme["bar"],
        )
        self.progress.configure(style="Timer.Horizontal.TProgressbar")

    # --- Duration helpers ---

    def _get_duration_minutes(self) -> int:
        try:
            val = int(self.duration_var.get())
            return val if val > 0 else 25
        except (ValueError, tk.TclError):
            return 25

    def _on_duration_changed(self, *_args) -> None:
        if self.state == IDLE:
            self.time_label.configure(
                text=format_time(self._get_duration_minutes() * 60)
            )

    # --- Timer logic ---

    def _tick(self) -> None:
        if self.state not in (FOCUS, BREAK):
            return

        self.remaining -= 1
        self.elapsed += 1
        self._update_display()

        if self.remaining <= 0:
            self._on_timer_complete()
            return

        self.timer_id = self.root.after(1000, self._tick)

    def _update_display(self) -> None:
        self.time_label.configure(text=format_time(self.remaining))
        progress_val = ((self.total - self.remaining) / self.total * 100) if self.total > 0 else 0
        self.progress["value"] = progress_val

    def _on_timer_complete(self) -> None:
        self.root.bell()

        if self.state == FOCUS:
            # Save the focus session
            save_session(self.current_task, self.current_category, self.total, True)
            self._refresh_history()

            # Determine break length
            sessions = load_sessions()
            focus_count = sum(
                1 for s in sessions if s["completed"] and s["category"] != "break"
            )
            if focus_count % self.config["sessions_before_long_break"] == 0:
                break_len = self.config["long_break_minutes"]
                self.mode_label.configure(text="LONG BREAK")
            else:
                break_len = self.config["short_break_minutes"]
                self.mode_label.configure(text="SHORT BREAK")

            # Auto-start break
            self.state = BREAK
            self.total = break_len * 60
            self.remaining = self.total
            self.elapsed = 0
            self._apply_theme(BREAK)
            self._update_display()
            self.timer_id = self.root.after(1000, self._tick)

        elif self.state == BREAK:
            # Break finished, go back to idle
            self.state = IDLE
            self._apply_theme(IDLE)
            self.mode_label.configure(text="READY")
            self.time_label.configure(
                text=format_time(self._get_duration_minutes() * 60)
            )
            self.progress["value"] = 0
            self.start_btn.configure(state="normal")
            self.pause_btn.configure(state="disabled")
            self.reset_btn.configure(state="disabled")
            self.task_entry.configure(state="normal")
            self.category_combo.configure(state="readonly")
            self.duration_spin.configure(state="normal")

    # --- Button handlers ---

    def _on_start(self) -> None:
        task = self.task_entry.get().strip()
        if not task:
            self.task_entry.focus_set()
            return

        self.current_task = task
        self.state = FOCUS
        self.total = self._get_duration_minutes() * 60
        self.remaining = self.total
        self.elapsed = 0

        # Handle category
        cat_choice = self.category_var.get()
        if cat_choice == "Auto-detect":
            self.current_category = "Other"  # temporary until async finishes
            self._start_async_categorize(task)
        else:
            self.current_category = cat_choice

        self.mode_label.configure(text="FOCUS MODE")
        self._apply_theme(FOCUS)
        self._update_display()

        self.start_btn.configure(state="disabled")
        self.pause_btn.configure(state="normal")
        self.reset_btn.configure(state="normal")
        self.task_entry.configure(state="disabled")
        self.category_combo.configure(state="disabled")
        self.duration_spin.configure(state="disabled")

        self.timer_id = self.root.after(1000, self._tick)

    def _on_pause(self) -> None:
        if self.state in (FOCUS, BREAK):
            self._paused_from = self.state
            self.state = PAUSED
            if self.timer_id is not None:
                self.root.after_cancel(self.timer_id)
                self.timer_id = None
            self.pause_btn.configure(text="Resume")
            self.mode_label.configure(text="PAUSED")
            self._apply_theme(PAUSED)

        elif self.state == PAUSED:
            self.state = self._paused_from
            self._apply_theme(self.state)
            mode_text = "FOCUS MODE" if self.state == FOCUS else "BREAK"
            self.mode_label.configure(text=mode_text)
            self.pause_btn.configure(text="Pause")
            self.timer_id = self.root.after(1000, self._tick)

    def _on_reset(self) -> None:
        if self.timer_id is not None:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None

        # If we were in focus and had some elapsed time, save as incomplete
        if self.state in (FOCUS, PAUSED) and self._paused_from != BREAK and self.elapsed > 0:
            save_session(self.current_task, self.current_category, self.elapsed, False)
            self._refresh_history()

        self.state = IDLE
        self._apply_theme(IDLE)
        self.mode_label.configure(text="READY")
        self.time_label.configure(
            text=format_time(self._get_duration_minutes() * 60)
        )
        self.progress["value"] = 0
        self.start_btn.configure(state="normal")
        self.pause_btn.configure(state="disabled", text="Pause")
        self.reset_btn.configure(state="disabled")
        self.task_entry.configure(state="normal")
        self.category_combo.configure(state="readonly")
        self.duration_spin.configure(state="normal")

    # --- Async categorization ---

    def _start_async_categorize(self, task: str) -> None:
        def _worker():
            result = categorize_task(task)
            self.category_queue.put(result)

        Thread(target=_worker, daemon=True).start()
        self._poll_category()

    def _poll_category(self) -> None:
        try:
            category = self.category_queue.get_nowait()
            self.current_category = category
        except Empty:
            self.root.after(200, self._poll_category)

    # --- History ---

    def _refresh_history(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        sessions = load_sessions()
        for s in sessions[-10:]:
            m, sec = divmod(s["duration_seconds"], 60)
            status = "Done" if s["completed"] else "Stopped"
            # Parse date simply
            date_str = s["started_at"][:16].replace("T", " ")
            self.tree.insert(
                "",
                "end",
                values=(s["id"], s["task"], s["category"], f"{m}m {sec}s", status, date_str),
            )

    # --- Run ---

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    app = PomodoroGUI()
    app.run()


if __name__ == "__main__":
    main()
