import contextlib
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

import windows_launcher as core


APP_NAME = "Chino Bot Launcher"
PRIMARY = "#2f7dd1"
INK = "#102033"
MUTED = "#6d7b8d"
BG = "#eef4fb"
PANEL = "#ffffff"


class QueueWriter:
    def __init__(self, target):
        self.target = target

    def write(self, text):
        if text:
            self.target(text)

    def flush(self):
        pass


class LauncherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1040x700")
        self.minsize(940, 620)
        self.configure(bg=BG)
        self.log_queue = queue.Queue()
        self.bot_process = None
        self.images = {}
        self.env_path = None
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.build_ui()
        self.after(120, self.drain_log)
        self.log("GUI Launcher 已開啟。")

    def build_ui(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        left = tk.Frame(self, bg=INK, width=310)
        left.grid(row=0, column=0, sticky="nsew")
        left.grid_propagate(False)
        left.rowconfigure(4, weight=1)

        logo = self.load_image("github.png", max_width=250, max_height=170)
        if logo:
            tk.Label(left, image=logo, bg=INK).grid(row=0, column=0, padx=28, pady=(28, 16), sticky="ew")
        else:
            tk.Label(left, text="Chino", bg=INK, fg="white", font=("Microsoft JhengHei UI", 28, "bold")).grid(
                row=0, column=0, padx=28, pady=(34, 14), sticky="w"
            )

        tk.Label(
            left,
            text="LINE Image Bot",
            bg=INK,
            fg="white",
            font=("Microsoft JhengHei UI", 20, "bold"),
        ).grid(row=1, column=0, padx=28, sticky="w")
        tk.Label(
            left,
            text="啟動、依賴安裝與 .env 編輯工具",
            bg=INK,
            fg="#b9c7d8",
            font=("Microsoft JhengHei UI", 10),
        ).grid(row=2, column=0, padx=28, pady=(6, 22), sticky="w")

        profile = self.load_image("Profile photo.png", max_width=96, max_height=96)
        cover = self.load_image("cover photo.png", max_width=250, max_height=120)
        preview = tk.Frame(left, bg="#18304b", padx=14, pady=14)
        preview.grid(row=3, column=0, padx=28, pady=(0, 20), sticky="ew")
        if cover:
            tk.Label(preview, image=cover, bg="#18304b").pack(fill="x")
        if profile:
            tk.Label(preview, image=profile, bg="#18304b").pack(pady=(10, 4))
        tk.Label(preview, text="預設頭貼 / 封面可在 .env 開關", bg="#18304b", fg="#d9e7f6").pack()

        actions = tk.Frame(left, bg=INK)
        actions.grid(row=5, column=0, padx=28, pady=28, sticky="ew")
        actions.columnconfigure(0, weight=1)
        self.start_button = ttk.Button(actions, text="啟動 Bot", command=self.start_bot)
        self.start_button.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.stop_button = ttk.Button(actions, text="停止 Bot", command=self.stop_bot, state="disabled")
        self.stop_button.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(actions, text="重新載入 .env", command=self.load_env).grid(row=2, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(actions, text="儲存 .env", command=self.save_env).grid(row=3, column=0, sticky="ew")

        main = tk.Frame(self, bg=BG)
        main.grid(row=0, column=1, sticky="nsew", padx=22, pady=22)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(1, weight=3)
        main.rowconfigure(3, weight=2)

        header = tk.Frame(main, bg=BG)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        header.columnconfigure(0, weight=1)
        tk.Label(header, text="ChinoBot 控制台", bg=BG, fg=INK, font=("Microsoft JhengHei UI", 22, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        self.status = tk.StringVar(value="待命")
        tk.Label(header, textvariable=self.status, bg=PRIMARY, fg="white", padx=16, pady=7).grid(row=0, column=1)

        env_panel = self.panel(main, "環境設定 .env")
        env_panel.grid(row=1, column=0, sticky="nsew")
        env_panel.rowconfigure(2, weight=1)
        env_panel.columnconfigure(0, weight=1)
        tk.Label(
            env_panel,
            text="可直接修改設定。儲存後再次啟動才會套用。",
            bg=PANEL,
            fg=MUTED,
            font=("Microsoft JhengHei UI", 9),
        ).grid(row=1, column=0, sticky="w", padx=14, pady=(4, 8))
        self.env_text = tk.Text(env_panel, wrap="none", undo=True, font=("Consolas", 10), height=12)
        self.env_text.grid(row=2, column=0, sticky="nsew", padx=14, pady=(0, 14))

        log_panel = self.panel(main, "狀態紀錄")
        log_panel.grid(row=3, column=0, sticky="nsew", pady=(16, 0))
        log_panel.rowconfigure(1, weight=1)
        log_panel.columnconfigure(0, weight=1)
        self.log_text = tk.Text(log_panel, wrap="word", state="disabled", font=("Consolas", 10), height=10)
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=14, pady=14)

    def panel(self, parent, title):
        outer = tk.Frame(parent, bg=PANEL, highlightbackground="#dbe6f3", highlightthickness=1)
        tk.Label(outer, text=title, bg=PANEL, fg=INK, font=("Microsoft JhengHei UI", 13, "bold")).grid(
            row=0, column=0, sticky="w", padx=14, pady=(12, 0)
        )
        return outer

    def resource_path(self, name):
        candidates = []
        if getattr(sys, "frozen", False):
            candidates.append(Path(getattr(sys, "_MEIPASS", "")) / "pic" / name)
            exe_dir = Path(sys.executable).resolve().parent
            candidates.append(exe_dir / "pic" / name)
            candidates.append(exe_dir / core.PROJECT_DIR_NAME / "pic" / name)
        candidates.append(Path.cwd() / "pic" / name)
        candidates.append(Path.cwd() / core.PROJECT_DIR_NAME / "pic" / name)
        candidates.append(Path(__file__).resolve().parents[1] / "pic" / name)
        for path in candidates:
            if path.exists():
                return path
        return None

    def load_image(self, name, max_width, max_height):
        path = self.resource_path(name)
        if not path:
            return None
        try:
            image = tk.PhotoImage(file=str(path))
            factor = max(1, int(max(image.width() / max_width, image.height() / max_height)))
            if factor > 1:
                image = image.subsample(factor, factor)
            self.images[name] = image
            return image
        except Exception as exc:
            self.log(f"圖片載入失敗：{name} ({exc})")
            return None

    def start_bot(self):
        if self.bot_process and self.bot_process.poll() is None:
            messagebox.showinfo(APP_NAME, "Bot 已在執行中。")
            return
        self.start_button.configure(state="disabled")
        self.status.set("準備中")
        threading.Thread(target=self.start_bot_worker, daemon=True).start()

    def start_bot_worker(self):
        try:
            with contextlib.redirect_stdout(QueueWriter(self.log)), contextlib.redirect_stderr(QueueWriter(self.log)):
                core.prepare_environment()
                self.env_path = core.ROOT / ".env"
                self.after(0, self.load_env)
                self.log("啟動 Bot 主程式。")
                self.bot_process = subprocess.Popen(
                    [str(core.PYTHON), str(core.ROOT / "main.py")],
                    cwd=core.ROOT,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
            self.after(0, lambda: self.stop_button.configure(state="normal"))
            self.after(0, lambda: self.status.set("執行中"))
            self.read_process_output()
        except Exception as exc:
            self.log(f"啟動失敗：{exc}")
            self.after(0, lambda: self.status.set("啟動失敗"))
            self.after(0, lambda: self.start_button.configure(state="normal"))

    def read_process_output(self):
        if not self.bot_process or not self.bot_process.stdout:
            return
        for line in self.bot_process.stdout:
            self.log(line)
        code = self.bot_process.poll()
        self.log(f"Bot 已結束，exit code: {code}")
        self.after(0, lambda: self.status.set("已停止"))
        self.after(0, lambda: self.start_button.configure(state="normal"))
        self.after(0, lambda: self.stop_button.configure(state="disabled"))

    def stop_bot(self):
        if self.bot_process and self.bot_process.poll() is None:
            self.bot_process.terminate()
            self.log("已送出停止訊號。")

    def load_env(self):
        try:
            if self.env_path is None:
                try:
                    root = core.find_project_root()
                    self.env_path = root / ".env"
                except Exception:
                    self.env_path = None
            if self.env_path and self.env_path.exists():
                text = self.env_path.read_text(encoding="utf-8", errors="replace")
            else:
                text = ""
            self.env_text.delete("1.0", "end")
            self.env_text.insert("1.0", text)
        except Exception as exc:
            self.log(f".env 載入失敗：{exc}")

    def save_env(self):
        try:
            if self.env_path is None:
                root = core.find_project_root()
                self.env_path = root / ".env"
            self.env_path.write_text(self.env_text.get("1.0", "end-1c"), encoding="utf-8")
            self.log(f"已儲存 .env：{self.env_path}")
        except Exception as exc:
            messagebox.showerror(APP_NAME, f".env 儲存失敗：{exc}")

    def log(self, text):
        self.log_queue.put(str(text))

    def drain_log(self):
        try:
            while True:
                text = self.log_queue.get_nowait()
                self.log_text.configure(state="normal")
                self.log_text.insert("end", text)
                if not text.endswith("\n"):
                    self.log_text.insert("end", "\n")
                self.log_text.see("end")
                self.log_text.configure(state="disabled")
        except queue.Empty:
            pass
        self.after(120, self.drain_log)

    def on_close(self):
        if self.bot_process and self.bot_process.poll() is None:
            if not messagebox.askyesno(APP_NAME, "Bot 還在執行，要停止並關閉嗎？"):
                return
            self.stop_bot()
        self.destroy()


if __name__ == "__main__":
    app = LauncherApp()
    app.mainloop()
