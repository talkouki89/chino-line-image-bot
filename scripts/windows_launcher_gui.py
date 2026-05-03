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
PRIMARY = "#10b981"
ACCENT = "#22d3ee"
INK = "#0d1726"
INK_2 = "#14243a"
MUTED = "#607086"
BG = "#edf4fb"
PANEL = "#ffffff"
LINE_GREEN = "#06c755"


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
        self.geometry("1280x820")
        self.minsize(1180, 760)
        self.configure(bg=BG)
        self.log_queue = queue.Queue()
        self.bot_process = None
        self.images = {}
        self.env_path = None
        self.project_root = None
        self.left_status = tk.StringVar(value="待命")
        self.set_window_icon()
        self.configure_style()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.build_ui()
        self.after(120, self.drain_log)
        self.log("GUI Launcher 已開啟。")

    def set_window_icon(self):
        icon = self.resource_path("icon.ico")
        if not icon:
            return
        try:
            self.iconbitmap(str(icon))
        except Exception as exc:
            self.log(f"視窗 icon 載入失敗：{exc}")

    def configure_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Primary.TButton", font=("Microsoft JhengHei UI", 11, "bold"), padding=(14, 10))
        style.map("Primary.TButton", background=[("active", "#0ea5a4")], foreground=[("active", "white")])
        style.configure("Primary.TButton", background=PRIMARY, foreground="white", borderwidth=0)
        style.configure("Soft.TButton", font=("Microsoft JhengHei UI", 10), padding=(12, 8), borderwidth=0)
        style.configure("Danger.TButton", font=("Microsoft JhengHei UI", 10, "bold"), padding=(12, 8), borderwidth=0)
        style.configure("TButton", font=("Microsoft JhengHei UI", 10), padding=(10, 7))

    def build_ui(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        left = tk.Frame(self, bg=PANEL, width=250, highlightbackground="#d9e4f0", highlightthickness=1)
        left.grid(row=0, column=0, sticky="nsew")
        left.grid_propagate(False)
        left.rowconfigure(7, weight=1)

        brand = tk.Frame(left, bg=PANEL)
        brand.grid(row=0, column=0, sticky="ew", padx=28, pady=(26, 22))
        tk.Label(brand, text="Chino", bg=PANEL, fg=INK, font=("Microsoft JhengHei UI", 22, "bold")).pack(anchor="w")
        tk.Label(
            brand,
            text="LINE Image Bot",
            bg=PANEL,
            fg=PRIMARY,
            font=("Microsoft JhengHei UI", 10, "bold"),
        ).pack(anchor="w", pady=(2, 0))

        tk.Label(left, text="Menu", bg=PANEL, fg=MUTED, font=("Microsoft JhengHei UI", 9, "bold")).grid(
            row=1, column=0, padx=28, sticky="w"
        )

        nav = tk.Frame(left, bg=PANEL)
        nav.grid(row=2, column=0, sticky="ew", padx=18, pady=(12, 18))
        nav.columnconfigure(0, weight=1)
        self.sidebar_button(nav, "首頁", 0, lambda: self.log("目前在首頁。"), active=True)
        self.sidebar_button(nav, "檢查環境", 1, self.check_environment)
        self.sidebar_button(nav, "開啟資料夾", 2, self.open_project_folder)
        self.sidebar_button(nav, "開啟 .env", 3, self.open_env_file)
        self.sidebar_button(nav, "開啟 README", 4, self.open_readme)

        status_card = tk.Frame(left, bg="#f03ea5", padx=16, pady=16)
        status_card.grid(row=8, column=0, padx=28, pady=(18, 28), sticky="ew")
        tk.Label(status_card, text="Launcher Status", bg="#f03ea5", fg="white", font=("Microsoft JhengHei UI", 9)).pack(
            anchor="w"
        )
        tk.Label(
            status_card,
            textvariable=self.left_status,
            bg="#f03ea5",
            fg="white",
            font=("Microsoft JhengHei UI", 17, "bold"),
        ).pack(anchor="w", pady=(3, 0))

        main = tk.Frame(self, bg=BG)
        main.grid(row=0, column=1, sticky="nsew", padx=30, pady=28)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(3, weight=3)
        main.rowconfigure(5, weight=2)

        hero = tk.Frame(main, bg="#fff8fd", padx=26, pady=20, highlightbackground="#f3d6ea", highlightthickness=1)
        hero.grid(row=0, column=0, sticky="ew", pady=(0, 18))
        hero.columnconfigure(0, weight=1)
        tk.Label(
            hero,
            text="Welcome to ChinoBot.",
            bg="#fff8fd",
            fg="#d946b3",
            font=("Microsoft JhengHei UI", 22, "bold"),
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            hero,
            text="管理啟動流程、依賴安裝、環境變數與執行紀錄。",
            bg="#fff8fd",
            fg=MUTED,
            font=("Microsoft JhengHei UI", 10),
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))
        self.status = tk.StringVar(value="待命")
        tk.Label(hero, textvariable=self.status, bg=LINE_GREEN, fg="white", padx=16, pady=7).grid(
            row=0, column=1, rowspan=2, sticky="e"
        )

        shortcuts = tk.Frame(main, bg=BG)
        shortcuts.grid(row=1, column=0, sticky="ew", pady=(0, 18))
        for index in range(5):
            shortcuts.columnconfigure(index, weight=1)
        self.start_button = ttk.Button(shortcuts, text="啟動 Bot", command=self.start_bot, style="Primary.TButton")
        self.start_button.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self.stop_button = ttk.Button(shortcuts, text="停止 Bot", command=self.stop_bot, state="disabled", style="Danger.TButton")
        self.stop_button.grid(row=0, column=1, padx=8, sticky="ew")
        ttk.Button(shortcuts, text="檢查環境", command=self.check_environment).grid(row=0, column=2, padx=8, sticky="ew")
        ttk.Button(shortcuts, text="儲存 .env", command=self.save_env).grid(row=0, column=3, padx=8, sticky="ew")
        ttk.Button(shortcuts, text="開啟資料夾", command=self.open_project_folder).grid(row=0, column=4, padx=(8, 0), sticky="ew")

        metrics = tk.Frame(main, bg=BG)
        metrics.grid(row=2, column=0, sticky="ew", pady=(0, 18))
        for index in range(4):
            metrics.columnconfigure(index, weight=1)
        self.metric_card(metrics, "Environment", "Python / Git", "自動檢查與安裝", 0)
        self.metric_card(metrics, "Configuration", ".env", "可直接編輯儲存", 1)
        self.metric_card(metrics, "Window", "CMD Login", "驗證碼在獨立視窗", 2)
        self.metric_card(metrics, "Runtime", "Status", "GUI 監看執行狀態", 3)

        env_panel = self.panel(main, "環境設定 .env")
        env_panel.grid(row=3, column=0, sticky="nsew")
        env_panel.rowconfigure(2, weight=1)
        env_panel.columnconfigure(0, weight=1)
        tk.Label(
            env_panel,
            text="可直接修改設定。儲存後再次啟動才會套用。常用操作可用右上方快捷按鈕。",
            bg=PANEL,
            fg=MUTED,
            font=("Microsoft JhengHei UI", 9),
        ).grid(row=1, column=0, sticky="w", padx=14, pady=(4, 8))
        self.env_text = tk.Text(env_panel, wrap="none", undo=True, font=("Consolas", 10), height=12)
        self.env_text.grid(row=2, column=0, sticky="nsew", padx=14, pady=(0, 14))

        tools = tk.Frame(main, bg=BG)
        tools.grid(row=4, column=0, sticky="ew", pady=(14, 0))
        for index in range(4):
            tools.columnconfigure(index, weight=1)
        ttk.Button(tools, text="重新載入 .env", command=self.load_env).grid(row=0, column=0, padx=(0, 8), sticky="ew")
        ttk.Button(tools, text="開啟 .env", command=self.open_env_file).grid(row=0, column=1, padx=8, sticky="ew")
        ttk.Button(tools, text="開啟 README", command=self.open_readme).grid(row=0, column=2, padx=8, sticky="ew")
        ttk.Button(tools, text="清空紀錄", command=self.clear_log).grid(row=0, column=3, padx=(8, 0), sticky="ew")

        log_panel = self.panel(main, "狀態紀錄")
        log_panel.grid(row=5, column=0, sticky="nsew", pady=(16, 0))
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

    def sidebar_button(self, parent, text, row, command, active=False):
        bg = "#f7e8fb" if active else "#f8fbff"
        fg = "#d946b3" if active else INK_2
        button = tk.Button(
            parent,
            text=text,
            bg=bg,
            fg=fg,
            anchor="w",
            padx=16,
            pady=11,
            relief="flat",
            bd=0,
            activebackground="#edf7ff",
            activeforeground="#d946b3",
            cursor="hand2",
            command=command,
            font=("Microsoft JhengHei UI", 10, "bold" if active else "normal"),
        )
        button.grid(row=row, column=0, sticky="ew", pady=3)
        return button

    def metric_card(self, parent, title, value, subtitle, column):
        card = tk.Frame(parent, bg=PANEL, padx=18, pady=14, highlightbackground="#dbe6f3", highlightthickness=1)
        card.grid(row=0, column=column, padx=(0 if column == 0 else 10, 0), sticky="ew")
        tk.Label(card, text=title, bg=PANEL, fg=MUTED, font=("Microsoft JhengHei UI", 9)).pack(anchor="w")
        tk.Label(card, text=value, bg=PANEL, fg=INK, font=("Microsoft JhengHei UI", 15, "bold")).pack(anchor="w", pady=(4, 0))
        tk.Label(card, text=subtitle, bg=PANEL, fg="#8aa0b7", font=("Microsoft JhengHei UI", 9)).pack(anchor="w", pady=(2, 0))
        return card

    def set_status(self, value):
        self.status.set(value)
        self.left_status.set(value)

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
        self.set_status("準備中")
        threading.Thread(target=self.start_bot_worker, daemon=True).start()

    def start_bot_worker(self):
        try:
            with contextlib.redirect_stdout(QueueWriter(self.log)), contextlib.redirect_stderr(QueueWriter(self.log)):
                core.prepare_environment()
                self.env_path = core.ROOT / ".env"
                self.after(0, self.load_env)
                self.log("啟動 Bot 主程式（獨立 CMD 視窗）。")
                self.log("登入驗證碼 / QR Code 會顯示在新開的 CMD 視窗，不會顯示在 GUI 紀錄區。")
                self.bot_process = subprocess.Popen(
                    [str(core.PYTHON), str(core.ROOT / "main.py")],
                    cwd=core.ROOT,
                    env=core.process_env(),
                    creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0),
                )
            self.after(0, lambda: self.stop_button.configure(state="normal"))
            self.after(0, lambda: self.set_status("執行中"))
            self.watch_bot_process()
        except Exception as exc:
            self.log(f"啟動失敗：{exc}")
            self.after(0, lambda: self.set_status("啟動失敗"))
            self.after(0, lambda: self.start_button.configure(state="normal"))

    def watch_bot_process(self):
        if not self.bot_process:
            return
        code = self.bot_process.wait()
        self.log(f"Bot 已結束，exit code: {code}")
        self.after(0, lambda: self.set_status("已停止"))
        self.after(0, lambda: self.start_button.configure(state="normal"))
        self.after(0, lambda: self.stop_button.configure(state="disabled"))

    def stop_bot(self):
        if self.bot_process and self.bot_process.poll() is None:
            self.bot_process.terminate()
            self.log("已送出停止訊號。")

    def check_environment(self):
        self.start_button.configure(state="disabled")
        self.set_status("檢查中")
        threading.Thread(target=self.check_environment_worker, daemon=True).start()

    def check_environment_worker(self):
        try:
            with contextlib.redirect_stdout(QueueWriter(self.log)), contextlib.redirect_stderr(QueueWriter(self.log)):
                core.prepare_environment()
                self.project_root = core.ROOT
                self.env_path = core.ROOT / ".env"
                self.log("環境檢查完成。第一次登入請按「啟動 Bot」，再到新開的 CMD 視窗查看驗證碼 / QR Code。")
            self.after(0, self.load_env)
            self.after(0, lambda: self.set_status("待命"))
        except Exception as exc:
            self.log(f"環境檢查失敗：{exc}")
            self.after(0, lambda: self.set_status("檢查失敗"))
        finally:
            self.after(0, lambda: self.start_button.configure(state="normal"))

    def load_env(self):
        try:
            if self.env_path is None:
                try:
                    root = core.find_project_root()
                    self.project_root = root
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

    def open_path(self, path):
        try:
            if path and Path(path).exists():
                os.startfile(str(path))
            else:
                messagebox.showinfo(APP_NAME, "找不到檔案或資料夾。")
        except Exception as exc:
            messagebox.showerror(APP_NAME, f"開啟失敗：{exc}")

    def resolve_project_root(self):
        if self.project_root and Path(self.project_root).exists():
            return Path(self.project_root)
        try:
            self.project_root = core.find_project_root()
            return self.project_root
        except Exception as exc:
            self.log(f"取得專案路徑失敗：{exc}")
            return None

    def open_project_folder(self):
        self.open_path(self.resolve_project_root())

    def open_env_file(self):
        if self.env_path is None:
            root = self.resolve_project_root()
            self.env_path = root / ".env" if root else None
        self.open_path(self.env_path)

    def open_readme(self):
        root = self.resolve_project_root()
        self.open_path(root / "README.md" if root else None)

    def clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

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
