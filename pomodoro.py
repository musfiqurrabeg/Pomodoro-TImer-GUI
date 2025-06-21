# pomodoro_timer.py
# Dynamic, Smooth, and Interactive Pomodoro Timer

import tkinter as tk
from tkinter import messagebox
from datetime import date
import math
import json
import os
import threading
import time
import winsound  # Use cross-platform library like playsound if not on Windows

# --- Constants ---
CONFIG_FILE = "pomodoro_config.json"
BG_COLOR = "#1e272e"
FG_COLOR = "#d2dae2"
ACCENT_COLOR = "#34ace0"
WORK_COLOR = "#33d9b2"
BREAK_COLOR = "#706fd3"
LONG_BREAK_COLOR = "#ffb142"
PAUSE_COLOR = "#ff5252"
FONT_NAME = "Segoe UI"

# --- State Variables ---
timer_settings = {}
session_stats = {}
timer = None
reps = 0
is_paused = False
remaining_time = 0

# --- Utility Functions ---
def load_config():
    global timer_settings, session_stats
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
            timer_settings = data.get("timer_settings", {"work": 25, "short_break": 5, "long_break": 15})
            session_stats = data.get("session_stats", {})
    else:
        timer_settings = {"work": 25, "short_break": 5, "long_break": 15}
        session_stats = {}
        save_config()

def save_config():
    with open(CONFIG_FILE, "w") as f:
        json.dump({"timer_settings": timer_settings, "session_stats": session_stats}, f, indent=4)

def log_session():
    today = date.today().isoformat()
    session_stats[today] = session_stats.get(today, 0) + 1
    save_config()

def play_sound():
    threading.Thread(target=lambda: winsound.Beep(1000, 200)).start()

# --- Main Class ---
class UltraPomodoro(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🔥 Ultra Pomodoro")
        self.config(bg=BG_COLOR, padx=20, pady=20)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        load_config()

        self.timer_label = tk.Label(self, text="00:00", font=(FONT_NAME, 48, "bold"), fg=FG_COLOR, bg=BG_COLOR)
        self.timer_label.pack(pady=20)

        self.status_label = tk.Label(self, text="Ready?", font=(FONT_NAME, 20), fg=ACCENT_COLOR, bg=BG_COLOR)
        self.status_label.pack(pady=10)

        self.task_var = tk.StringVar()
        self.task_entry = tk.Entry(self, textvariable=self.task_var, font=(FONT_NAME, 14), justify='center', width=30)
        self.task_entry.insert(0, "What are you working on?")
        self.task_entry.pack(pady=5)

        self.progress = tk.Canvas(self, width=250, height=20, bg=BG_COLOR, highlightthickness=0)
        self.progress_bar = self.progress.create_rectangle(0, 0, 0, 20, fill=WORK_COLOR)
        self.progress.pack(pady=10)

        self.button_frame = tk.Frame(self, bg=BG_COLOR)
        self.button_frame.pack(pady=15)

        self.start_btn = self.create_button("Start", self.start_timer, WORK_COLOR)
        self.pause_btn = self.create_button("Pause", self.toggle_pause, PAUSE_COLOR, state="disabled")
        self.reset_btn = self.create_button("Reset", self.reset_timer, BREAK_COLOR)

        self.update_idletasks()
        self.center()
        self.reset_timer()

    def create_button(self, text, command, color, state="normal"):
        btn = tk.Button(self.button_frame, text=text, command=command, font=(FONT_NAME, 12, "bold"), bg=color,
                        fg="white", relief="flat", padx=15, pady=10, activebackground=self.shade(color), state=state)
        btn.pack(side="left", padx=10)
        return btn

    def center(self):
        self.update_idletasks()
        w = self.winfo_screenwidth()
        h = self.winfo_screenheight()
        self.geometry(f"+{(w - self.winfo_width()) // 2}+{(h - self.winfo_height()) // 2}")

    def shade(self, hex_color):
        r, g, b = (int(hex_color[i:i+2], 16) for i in (1, 3, 5))
        r, g, b = int(r * 0.85), int(g * 0.85), int(b * 0.85)
        return f"#{r:02x}{g:02x}{b:02x}"

    def start_timer(self):
        global reps
        if not self.task_var.get().strip() or self.task_var.get().strip() == "What are you working on?":
            messagebox.showwarning("Task Required", "Please enter a task before starting.")
            return

        self.start_btn.config(state="disabled")
        self.pause_btn.config(state="normal")
        self.task_entry.config(state="disabled")
        reps += 1

        if reps % 8 == 0:
            self.countdown(timer_settings["long_break"] * 60, LONG_BREAK_COLOR, "Long Break")
        elif reps % 2 == 0:
            self.countdown(timer_settings["short_break"] * 60, BREAK_COLOR, "Short Break")
        else:
            self.countdown(timer_settings["work"] * 60, WORK_COLOR, self.task_var.get())

    def countdown(self, count, color, label):
        global timer, remaining_time
        remaining_time = count
        self.status_label.config(text=label, fg=color)
        self.progress.itemconfig(self.progress_bar, fill=color)
        self.update_timer(count, color)

    def update_timer(self, count, color):
        global timer, remaining_time
        mins, secs = divmod(count, 60)
        self.title(f"⏳ {mins:02}:{secs:02} - Ultra Pomodoro")
        self.timer_label.config(text=f"{mins:02}:{secs:02}")
        self.progress.coords(self.progress_bar, 0, 0, (1 - count / self.get_total_seconds()) * 250, 20)
        remaining_time = count

        if count > 0 and not is_paused:
            timer = self.after(1000, self.update_timer, count - 1, color)
        elif count <= 0:
            self.end_session()

    def toggle_pause(self):
        global is_paused, timer
        is_paused = not is_paused
        self.pause_btn.config(text="Resume" if is_paused else "Pause")
        if not is_paused:
            self.update_timer(remaining_time, self.progress.itemcget(self.progress_bar, "fill"))
        else:
            if timer: self.after_cancel(timer)

    def reset_timer(self):
        global timer, reps, is_paused
        if timer: self.after_cancel(timer)
        reps = 0
        is_paused = False
        self.timer_label.config(text="00:00")
        self.status_label.config(text="Ready?", fg=ACCENT_COLOR)
        self.progress.coords(self.progress_bar, 0, 0, 0, 20)
        self.start_btn.config(state="normal")
        self.pause_btn.config(state="disabled", text="Pause")
        self.task_entry.config(state="normal")
        self.title("🔥 Ultra Pomodoro")

    def end_session(self):
        play_sound()
        if reps % 2 == 1:
            log_session()
        if messagebox.askyesno("Session Complete", "Start next session?"):
            self.start_timer()
        else:
            self.reset_timer()

    def get_total_seconds(self):
        if reps % 8 == 0:
            return timer_settings["long_break"] * 60
        elif reps % 2 == 0:
            return timer_settings["short_break"] * 60
        else:
            return timer_settings["work"] * 60

    def on_close(self):
        save_config()
        self.destroy()

if __name__ == "__main__":
    app = UltraPomodoro()
    app.mainloop()
