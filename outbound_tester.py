import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, scrolledtext, messagebox, filedialog
import socket
import threading
import time
import json
import csv
import os
from datetime import datetime


# ─── Color Palette ─────────────────────────────────────────────────────────────
C = {
    "bg":        "#0d1117",
    "surface":   "#161b22",
    "panel":     "#21262d",
    "border":    "#30363d",
    "accent":    "#58a6ff",
    "accent2":   "#3fb950",
    "warn":      "#d29922",
    "danger":    "#f85149",
    "purple":    "#bc8cff",
    "text":      "#e6edf3",
    "muted":     "#8b949e",
    "open":      "#3fb950",
    "closed":    "#f85149",
    "filtered":  "#d29922",
    "error":     "#ff7b72",
    "header_fg": "#58a6ff",
}

FONT_MONO = ("Courier New", 9)   # resolved after Tk init
FONT_UI   = ("Segoe UI", 10)
FONT_SM   = ("Segoe UI", 9)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_HEAD = ("Segoe UI", 15, "bold")
FONT_MED  = ("Segoe UI", 11, "bold")

COMMON_PORTS = {
    "Web":        "80,443,8080,8443",
    "Remote":     "22,23,3389,5900",
    "Mail":       "25,110,143,465,587,993,995",
    "Database":   "1433,1521,3306,5432,6379,27017",
    "DNS/FTP":    "21,53,69",
    "Full Scan":  "21,22,23,25,53,80,110,143,443,465,587,993,995,1433,1521,3306,3389,5432,5900,6379,8080,8443,27017",
}


class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, _=None):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self.tip = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.geometry(f"+{x}+{y}")
        lbl = tk.Label(tw, text=self.text, background="#1c2128", foreground=C["muted"],
                       font=FONT_SM, relief="solid", borderwidth=1, padx=8, pady=4)
        lbl.pack()

    def hide(self, _=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None


class OutboundTester:
    def __init__(self, root):
        self.root = root
        self.root.title("NetProbe — Outbound Connection Tester")
        self.root.geometry("1080x780")
        self.root.minsize(900, 640)
        self.root.configure(bg=C["bg"])

        self.is_running = False
        self.stop_flag  = False
        self.all_results = []
        self.scan_history = []

        self._build_menu()
        self._build_ui()
        self._status("Ready — configure and start a scan.", C["muted"])

    # ── Menu Bar ────────────────────────────────────────────────────────────────
    def _build_menu(self):
        menubar = tk.Menu(self.root, bg=C["surface"], fg=C["text"],
                          activebackground=C["panel"], activeforeground=C["accent"],
                          relief="flat", borderwidth=0)
        self.root.config(menu=menubar)

        # File
        file_menu = tk.Menu(menubar, tearoff=False, bg=C["surface"], fg=C["text"],
                            activebackground=C["panel"], activeforeground=C["accent"])
        file_menu.add_command(label="  Export Results as TXT…",  command=self.export_txt)
        file_menu.add_command(label="  Export Results as CSV…",  command=self.export_csv)
        file_menu.add_command(label="  Export Results as JSON…", command=self.export_json)
        file_menu.add_separator()
        file_menu.add_command(label="  Load Targets from File…", command=self.load_targets)
        file_menu.add_separator()
        file_menu.add_command(label="  Exit",  command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # Scan
        scan_menu = tk.Menu(menubar, tearoff=False, bg=C["surface"], fg=C["text"],
                            activebackground=C["panel"], activeforeground=C["accent"])
        scan_menu.add_command(label="  ▶  Start Scan",  command=self.start_test)
        scan_menu.add_command(label="  ■  Stop Scan",   command=self.stop_test)
        scan_menu.add_separator()
        scan_menu.add_command(label="  Clear Results",  command=self.clear_results)
        menubar.add_cascade(label="Scan", menu=scan_menu)

        # Presets
        preset_menu = tk.Menu(menubar, tearoff=False, bg=C["surface"], fg=C["text"],
                              activebackground=C["panel"], activeforeground=C["accent"])
        for label, ports in COMMON_PORTS.items():
            preset_menu.add_command(
                label=f"  {label}",
                command=lambda p=ports: self._apply_preset(p)
            )
        menubar.add_cascade(label="Port Presets", menu=preset_menu)

        # Tools
        tools_menu = tk.Menu(menubar, tearoff=False, bg=C["surface"], fg=C["text"],
                             activebackground=C["panel"], activeforeground=C["accent"])
        tools_menu.add_command(label="  DNS Lookup",    command=self.dns_lookup)
        tools_menu.add_command(label="  Ping Host",     command=self.ping_host)
        tools_menu.add_command(label="  Scan History",  command=self.show_history)
        menubar.add_cascade(label="Tools", menu=tools_menu)

        # Help
        help_menu = tk.Menu(menubar, tearoff=False, bg=C["surface"], fg=C["text"],
                            activebackground=C["panel"], activeforeground=C["accent"])
        help_menu.add_command(label="  Port Reference Guide", command=self.port_reference)
        help_menu.add_command(label="  About NetProbe",       command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

    # ── Main UI ─────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Top bar
        top = tk.Frame(self.root, bg=C["surface"], height=60)
        top.pack(fill="x")
        top.pack_propagate(False)

        logo_frame = tk.Frame(top, bg=C["surface"])
        logo_frame.pack(side="left", padx=20, pady=10)

        dot = tk.Canvas(logo_frame, width=18, height=18, bg=C["surface"], highlightthickness=0)
        dot.create_oval(2, 2, 16, 16, fill=C["accent"], outline="")
        dot.pack(side="left", padx=(0, 8))

        tk.Label(logo_frame, text="NetProbe", font=FONT_HEAD,
                 bg=C["surface"], fg=C["text"]).pack(side="left")
        tk.Label(logo_frame, text=" v2.0", font=FONT_SM,
                 bg=C["surface"], fg=C["muted"]).pack(side="left", pady=(4, 0))

        self.status_bar_top = tk.Label(top, text="", font=FONT_SM,
                                       bg=C["surface"], fg=C["muted"])
        self.status_bar_top.pack(side="right", padx=20)

        # ── Separator
        tk.Frame(self.root, bg=C["border"], height=1).pack(fill="x")

        # ── Main content (left panel + right results)
        content = tk.Frame(self.root, bg=C["bg"])
        content.pack(fill="both", expand=True)

        # Left panel
        left = tk.Frame(content, bg=C["surface"], width=310)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        tk.Frame(content, bg=C["border"], width=1).pack(side="left", fill="y")

        # Right panel
        right = tk.Frame(content, bg=C["bg"])
        right.pack(side="left", fill="both", expand=True)

        self._build_left(left)
        self._build_right(right)

        # ── Bottom status
        tk.Frame(self.root, bg=C["border"], height=1).pack(fill="x")
        status_frame = tk.Frame(self.root, bg=C["panel"], height=28)
        status_frame.pack(fill="x")
        status_frame.pack_propagate(False)

        self.status_label = tk.Label(status_frame, text="Ready", font=FONT_SM,
                                     bg=C["panel"], fg=C["muted"], anchor="w")
        self.status_label.pack(side="left", padx=12, pady=4)

        self.clock_label = tk.Label(status_frame, text="", font=FONT_SM,
                                    bg=C["panel"], fg=C["muted"])
        self.clock_label.pack(side="right", padx=12)
        self._tick_clock()

    def _build_left(self, parent):
        pad = {"padx": 16}

        # ── Target
        self._section_label(parent, "TARGET")
        tf = tk.Frame(parent, bg=C["surface"])
        tf.pack(fill="x", **pad, pady=(0, 4))
        tk.Label(tf, text="Host / IP", font=FONT_SM, bg=C["surface"], fg=C["muted"]).pack(anchor="w")
        self.host_entry = self._entry(tf, "example.com")
        self.host_entry.pack(fill="x", pady=(2, 0))

        # ── Ports
        self._section_label(parent, "PORTS")
        pf = tk.Frame(parent, bg=C["surface"])
        pf.pack(fill="x", **pad, pady=(0, 4))
        tk.Label(pf, text="Port list (comma-separated)", font=FONT_SM,
                 bg=C["surface"], fg=C["muted"]).pack(anchor="w")
        self.ports_entry = self._entry(pf, "80,443,8080,3389,22,21,25,53")
        self.ports_entry.pack(fill="x", pady=(2, 6))

        # Preset buttons
        preset_row1 = tk.Frame(pf, bg=C["surface"])
        preset_row1.pack(fill="x")
        preset_row2 = tk.Frame(pf, bg=C["surface"])
        preset_row2.pack(fill="x", pady=(4, 0))

        presets = list(COMMON_PORTS.items())
        for i, (label, ports) in enumerate(presets[:3]):
            self._chip(preset_row1, label, lambda p=ports: self._apply_preset(p)).pack(side="left", padx=(0, 4))
        for i, (label, ports) in enumerate(presets[3:6]):
            self._chip(preset_row2, label, lambda p=ports: self._apply_preset(p)).pack(side="left", padx=(0, 4))

        # ── Options
        self._section_label(parent, "OPTIONS")
        of = tk.Frame(parent, bg=C["surface"])
        of.pack(fill="x", **pad, pady=(0, 4))

        row_t = tk.Frame(of, bg=C["surface"])
        row_t.pack(fill="x", pady=2)
        tk.Label(row_t, text="Timeout (s)", font=FONT_SM, bg=C["surface"],
                 fg=C["muted"], width=16, anchor="w").pack(side="left")
        self.timeout_entry = self._entry(row_t, "3", width=8)
        self.timeout_entry.pack(side="left")

        row_th = tk.Frame(of, bg=C["surface"])
        row_th.pack(fill="x", pady=2)
        tk.Label(row_th, text="Threads", font=FONT_SM, bg=C["surface"],
                 fg=C["muted"], width=16, anchor="w").pack(side="left")
        self.threads_entry = self._entry(row_th, "10", width=8)
        self.threads_entry.pack(side="left")
        Tooltip(self.threads_entry, "Parallel connections (1–50)")

        self.show_closed_var = tk.BooleanVar(value=True)
        self.resolve_var     = tk.BooleanVar(value=True)
        self._checkbox(of, "Show closed/filtered ports", self.show_closed_var)
        self._checkbox(of, "Resolve hostname on start",  self.resolve_var)

        # ── Buttons
        tk.Frame(parent, bg=C["border"], height=1).pack(fill="x", padx=16, pady=12)
        bf = tk.Frame(parent, bg=C["surface"])
        bf.pack(fill="x", padx=16, pady=(0, 12))

        self.start_btn = tk.Button(bf, text="▶  Start Scan", command=self.start_test,
                                   bg=C["accent"], fg="#0d1117", font=FONT_BOLD,
                                   relief="flat", cursor="hand2", pady=9)
        self.start_btn.pack(fill="x", pady=(0, 6))

        row_b = tk.Frame(bf, bg=C["surface"])
        row_b.pack(fill="x")
        self.stop_btn = tk.Button(row_b, text="■ Stop", command=self.stop_test,
                                  bg=C["panel"], fg=C["danger"], font=FONT_BOLD,
                                  relief="flat", cursor="hand2", pady=7, state="disabled")
        self.stop_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.clear_btn = tk.Button(row_b, text="⊘ Clear", command=self.clear_results,
                                   bg=C["panel"], fg=C["muted"], font=FONT_BOLD,
                                   relief="flat", cursor="hand2", pady=7)
        self.clear_btn.pack(side="left", fill="x", expand=True)

        # ── Stats summary
        tk.Frame(parent, bg=C["border"], height=1).pack(fill="x", padx=16, pady=(8, 0))
        self._section_label(parent, "LAST SCAN SUMMARY")
        sf = tk.Frame(parent, bg=C["surface"])
        sf.pack(fill="x", padx=16, pady=(0, 12))

        self.stat_vars = {}
        for key, color, label in [
            ("open",     C["open"],     "Open"),
            ("closed",   C["closed"],   "Closed"),
            ("filtered", C["filtered"], "Filtered"),
            ("error",    C["error"],    "Errors"),
            ("total",    C["muted"],    "Total"),
        ]:
            row = tk.Frame(sf, bg=C["surface"])
            row.pack(fill="x", pady=1)
            tk.Label(row, text=label, font=FONT_SM, bg=C["surface"],
                     fg=C["muted"], width=10, anchor="w").pack(side="left")
            var = tk.StringVar(value="—")
            self.stat_vars[key] = var
            tk.Label(row, textvariable=var, font=FONT_BOLD, bg=C["surface"],
                     fg=color, anchor="e").pack(side="right")

    def _build_right(self, parent):
        # ── Toolbar
        tb = tk.Frame(parent, bg=C["panel"], height=40)
        tb.pack(fill="x")
        tb.pack_propagate(False)

        tk.Label(tb, text="Output", font=FONT_MED, bg=C["panel"],
                 fg=C["text"]).pack(side="left", padx=16, pady=8)

        # Filter tabs
        self.filter_var = tk.StringVar(value="All")
        for label in ["All", "Open", "Closed", "Filtered"]:
            btn = tk.Button(tb, text=label, font=FONT_SM,
                            bg=C["panel"], fg=C["muted"],
                            activebackground=C["border"], relief="flat", cursor="hand2",
                            command=lambda l=label: self._apply_filter(l))
            btn.pack(side="left", padx=2, pady=6, ipady=2, ipadx=6)

        tk.Button(tb, text="⬇ Export", font=FONT_SM, bg=C["panel"], fg=C["accent"],
                  relief="flat", cursor="hand2", command=self.export_txt).pack(side="right", padx=12, pady=8)

        tk.Frame(parent, bg=C["border"], height=1).pack(fill="x")

        # ── Progress
        pf = tk.Frame(parent, bg=C["bg"])
        pf.pack(fill="x", padx=16, pady=(10, 4))
        self.progress_label = tk.Label(pf, text="", font=FONT_SM, bg=C["bg"], fg=C["muted"])
        self.progress_label.pack(anchor="w")
        self.progress_bar = ttk.Progressbar(pf, mode="determinate")
        self.progress_bar.pack(fill="x", pady=(4, 0))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Horizontal.TProgressbar",
                        background=C["accent"], troughcolor=C["panel"],
                        bordercolor=C["panel"], lightcolor=C["accent"], darkcolor=C["accent"])

        # ── Results text
        rf = tk.Frame(parent, bg=C["bg"])
        rf.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        self.results_text = scrolledtext.ScrolledText(
            rf, wrap=tk.WORD, font=FONT_MONO,
            bg=C["bg"], fg=C["text"],
            insertbackground=C["accent"],
            selectbackground=C["panel"],
            relief="flat", borderwidth=0,
            padx=12, pady=10
        )
        self.results_text.pack(fill="both", expand=True)

        tags = {
            "header":   (C["header_fg"], True),
            "open":     (C["open"],      False),
            "closed":   (C["closed"],    False),
            "filtered": (C["filtered"],  False),
            "error":    (C["error"],     False),
            "info":     (C["muted"],     False),
            "summary":  (C["purple"],    True),
        }
        for tag, (color, bold) in tags.items():
            font = (FONT_MONO[0], FONT_MONO[1], "bold") if bold else FONT_MONO
            self.results_text.tag_config(tag, foreground=color, font=font)

    # ── Helpers ─────────────────────────────────────────────────────────────────
    def _entry(self, parent, default="", width=None):
        kw = dict(bg=C["panel"], fg=C["text"], insertbackground=C["accent"],
                  relief="flat", font=FONT_UI, bd=0)
        if width:
            kw["width"] = width
        e = tk.Entry(parent, **kw)
        e.insert(0, default)
        e.config(highlightthickness=1, highlightcolor=C["accent"],
                 highlightbackground=C["border"])
        return e

    def _section_label(self, parent, text):
        f = tk.Frame(parent, bg=C["surface"])
        f.pack(fill="x", padx=16, pady=(14, 4))
        tk.Label(f, text=text, font=("Segoe UI", 8, "bold"),
                 bg=C["surface"], fg=C["muted"]).pack(side="left")
        tk.Frame(f, bg=C["border"], height=1).pack(side="left", fill="x", expand=True, padx=(8, 0))

    def _chip(self, parent, text, cmd):
        return tk.Button(parent, text=text, font=("Segoe UI", 8),
                         bg=C["panel"], fg=C["muted"], relief="flat",
                         cursor="hand2", command=cmd, padx=6, pady=2)

    def _checkbox(self, parent, text, var):
        cb = tk.Checkbutton(parent, text=text, variable=var, font=FONT_SM,
                            bg=C["surface"], fg=C["muted"], selectcolor=C["panel"],
                            activebackground=C["surface"], activeforeground=C["text"],
                            relief="flat", cursor="hand2")
        cb.pack(anchor="w", pady=1)

    def _apply_preset(self, ports):
        self.ports_entry.delete(0, tk.END)
        self.ports_entry.insert(0, ports)
        self._status(f"Preset applied: {ports[:40]}{'…' if len(ports)>40 else ''}", C["accent"])

    def _apply_filter(self, mode):
        self.filter_var.set(mode)
        # Re-render stored results
        self.results_text.delete("1.0", tk.END)
        for item in self.all_results:
            status, line, tag = item
            if mode == "All" or status.lower() == mode.lower():
                self.results_text.insert(tk.END, line + "\n", tag)

    def _status(self, msg, color=None):
        color = color or C["muted"]
        self.status_label.config(text=msg, fg=color)

    def _tick_clock(self):
        self.clock_label.config(text=datetime.now().strftime("%H:%M:%S"))
        self.root.after(1000, self._tick_clock)

    def log_result(self, message, tag="info", status=None):
        self.results_text.insert(tk.END, message + "\n", tag)
        self.results_text.see(tk.END)
        self.results_text.update()
        if status:
            self.all_results.append((status, message, tag))

    # ── DNS Lookup (Tools) ───────────────────────────────────────────────────────
    def dns_lookup(self):
        host = self.host_entry.get().strip()
        if not host:
            messagebox.showwarning("DNS Lookup", "Enter a host first.")
            return
        try:
            ip = socket.gethostbyname(host)
            info = socket.gethostbyaddr(ip)
            msg = f"Host: {host}\nResolved IP: {ip}\nReverse DNS: {info[0]}\nAliases: {', '.join(info[1]) or 'none'}"
        except Exception as e:
            msg = f"DNS lookup failed: {e}"
        messagebox.showinfo("DNS Lookup — " + host, msg)

    def ping_host(self):
        host = self.host_entry.get().strip()
        if not host:
            messagebox.showwarning("Ping", "Enter a host first.")
            return
        # Use socket-based connectivity check as a "ping"
        try:
            start = time.time()
            s = socket.create_connection((host, 80), timeout=3)
            s.close()
            ms = (time.time() - start) * 1000
            msg = f"Host: {host}\nPort 80 reachable in {ms:.0f}ms\n(TCP ping via port 80)"
        except Exception as e:
            msg = f"Host: {host}\nUnreachable: {e}"
        messagebox.showinfo("Ping — " + host, msg)

    def show_history(self):
        if not self.scan_history:
            messagebox.showinfo("Scan History", "No scans performed yet.")
            return
        win = tk.Toplevel(self.root)
        win.title("Scan History")
        win.geometry("520x360")
        win.configure(bg=C["bg"])
        tk.Label(win, text="Scan History", font=FONT_HEAD, bg=C["bg"], fg=C["text"]).pack(padx=20, pady=12, anchor="w")
        txt = scrolledtext.ScrolledText(win, font=FONT_MONO, bg=C["surface"], fg=C["text"],
                                        relief="flat", padx=10, pady=8)
        txt.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        for h in self.scan_history:
            txt.insert(tk.END, h + "\n")
        txt.config(state="disabled")

    def port_reference(self):
        win = tk.Toplevel(self.root)
        win.title("Port Reference Guide")
        win.geometry("480x440")
        win.configure(bg=C["bg"])
        tk.Label(win, text="Common Port Reference", font=FONT_HEAD, bg=C["bg"], fg=C["text"]).pack(padx=20, pady=12, anchor="w")
        txt = scrolledtext.ScrolledText(win, font=FONT_MONO, bg=C["surface"], fg=C["text"],
                                        relief="flat", padx=10, pady=8)
        txt.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        ref = [
            ("21",    "FTP — File Transfer Protocol"),
            ("22",    "SSH — Secure Shell"),
            ("23",    "Telnet (unencrypted)"),
            ("25",    "SMTP — Mail Delivery"),
            ("53",    "DNS — Domain Name System"),
            ("80",    "HTTP — Unencrypted Web"),
            ("110",   "POP3 — Email Retrieval"),
            ("143",   "IMAP — Email Retrieval"),
            ("443",   "HTTPS — Encrypted Web"),
            ("465",   "SMTPS — Encrypted Mail"),
            ("587",   "SMTP Submission"),
            ("993",   "IMAPS — Encrypted IMAP"),
            ("995",   "POP3S — Encrypted POP3"),
            ("1433",  "MS SQL Server"),
            ("1521",  "Oracle DB"),
            ("3306",  "MySQL / MariaDB"),
            ("3389",  "RDP — Remote Desktop"),
            ("5432",  "PostgreSQL"),
            ("5900",  "VNC — Remote Desktop"),
            ("6379",  "Redis"),
            ("8080",  "HTTP Alternate / Proxy"),
            ("8443",  "HTTPS Alternate"),
            ("27017", "MongoDB"),
        ]
        for port, desc in ref:
            txt.insert(tk.END, f"  {port:>5}   {desc}\n")
        txt.config(state="disabled")

    def show_about(self):
        messagebox.showinfo(
            "About NetProbe",
            "NetProbe v2.0\nOutbound Connection Tester\n\n"
            "A professional network diagnostic tool for testing outbound "
            "TCP connectivity.\n\n"
            "⚠ Only use on networks you own or have explicit permission to test."
        )

    # ── Export ───────────────────────────────────────────────────────────────────
    def _export_content(self):
        return self.results_text.get("1.0", tk.END)

    def export_txt(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt",
                                            filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if path:
            with open(path, "w") as f:
                f.write(self._export_content())
            self._status(f"Exported TXT → {path}", C["open"])

    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if path:
            with open(path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Status", "Details"])
                for status, line, _ in self.all_results:
                    writer.writerow([status, line.strip()])
            self._status(f"Exported CSV → {path}", C["open"])

    def export_json(self):
        path = filedialog.asksaveasfilename(defaultextension=".json",
                                            filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if path:
            data = [{"status": s, "output": l.strip()} for s, l, _ in self.all_results]
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
            self._status(f"Exported JSON → {path}", C["open"])

    def load_targets(self):
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if path:
            with open(path) as f:
                host = f.readline().strip()
            if host:
                self.host_entry.delete(0, tk.END)
                self.host_entry.insert(0, host)
                self._status(f"Loaded target: {host}", C["accent"])

    # ── Port Test ────────────────────────────────────────────────────────────────
    def test_port(self, host, port, timeout):
        start = time.time()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            elapsed = (time.time() - start) * 1000
            sock.close()
            if result == 0:
                return "open",     elapsed, "Connection successful"
            else:
                return "closed",   elapsed, "Connection refused"
        except socket.timeout:
            return "filtered", (time.time() - start) * 1000, "Timeout"
        except socket.gaierror:
            return "error",    0, "Hostname resolution failed"
        except Exception as e:
            return "error",    0, str(e)

    def run_test(self):
        host       = self.host_entry.get().strip()
        ports_str  = self.ports_entry.get().strip()
        timeout_s  = self.timeout_entry.get().strip()
        threads_s  = self.threads_entry.get().strip()

        if not host:
            messagebox.showerror("Error", "Please enter a target host.")
            self.reset_ui(); return
        try:
            timeout = float(timeout_s)
            assert timeout > 0
        except Exception:
            messagebox.showerror("Error", "Invalid timeout value."); self.reset_ui(); return
        try:
            max_threads = max(1, min(50, int(threads_s)))
        except Exception:
            max_threads = 10
        try:
            ports = [int(p.strip()) for p in ports_str.split(",") if p.strip()]
            assert ports
        except Exception:
            messagebox.showerror("Error", "Invalid port list."); self.reset_ui(); return

        # Resolve hostname
        resolved_ip = host
        if self.resolve_var.get():
            try:
                resolved_ip = socket.gethostbyname(host)
            except Exception:
                resolved_ip = "unresolved"

        self.all_results.clear()

        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_result(f"{'═'*72}", "header")
        self.log_result(f"  NetProbe Scan  ·  {ts}", "header")
        self.log_result(f"  Target  : {host}  ({resolved_ip})", "header")
        self.log_result(f"  Ports   : {len(ports)}  ·  Timeout: {timeout}s  ·  Threads: {max_threads}", "header")
        self.log_result(f"{'═'*72}\n", "header")
        self.log_result(f"  {'PORT':>6}  {'STATUS':<10}  {'TIME':>7}  DETAIL", "info")
        self.log_result(f"  {'─'*6}  {'─'*10}  {'─'*7}  {'─'*30}", "info")

        counters = {"open": 0, "closed": 0, "filtered": 0, "error": 0}
        lock = threading.Lock()
        semaphore = threading.Semaphore(max_threads)
        results_queue = []
        port_index = [0]

        self.progress_bar["maximum"] = len(ports)
        self.progress_bar["value"]   = 0

        def worker(port):
            if self.stop_flag:
                return
            status, elapsed, msg = self.test_port(host, port, timeout)
            with lock:
                results_queue.append((port, status, elapsed, msg))

        threads = []
        for port in ports:
            if self.stop_flag:
                break
            t = threading.Thread(target=worker, args=(port,), daemon=True)
            threads.append(t)
            t.start()

            # Flush results
            while len(results_queue) > 0:
                with lock:
                    if results_queue:
                        p, status, elapsed, msg = results_queue.pop(0)
                    else:
                        break
                self._emit_port_result(p, status, elapsed, msg, counters)
                port_index[0] += 1
                self.progress_bar["value"] = port_index[0]
                self.progress_label.config(
                    text=f"Scanning {port_index[0]}/{len(ports)} ports…")

            # Throttle
            if len([t for t in threads if t.is_alive()]) >= max_threads:
                while len([t for t in threads if t.is_alive()]) >= max_threads:
                    time.sleep(0.02)

        for t in threads:
            t.join(timeout=timeout + 0.5)

        # Flush remaining
        for p, status, elapsed, msg in results_queue:
            self._emit_port_result(p, status, elapsed, msg, counters)

        if self.stop_flag:
            self.log_result("\n  [ SCAN STOPPED BY USER ]\n", "error")
        else:
            total = sum(counters.values())
            self.log_result(f"\n{'═'*72}", "summary")
            self.log_result("  SCAN COMPLETE — SUMMARY", "summary")
            self.log_result(f"{'═'*72}", "summary")
            self.log_result(f"  Total scanned : {total}", "summary")
            self.log_result(f"  Open          : {counters['open']}",     "open")
            self.log_result(f"  Closed        : {counters['closed']}",   "closed")
            self.log_result(f"  Filtered      : {counters['filtered']}", "filtered")
            self.log_result(f"  Errors        : {counters['error']}",    "error")
            self.log_result(f"{'═'*72}\n", "summary")

            # Update stat vars
            self.stat_vars["open"].set(str(counters["open"]))
            self.stat_vars["closed"].set(str(counters["closed"]))
            self.stat_vars["filtered"].set(str(counters["filtered"]))
            self.stat_vars["error"].set(str(counters["error"]))
            self.stat_vars["total"].set(str(total))

            # History
            hist_entry = f"[{ts}] {host} — {total} ports — {counters['open']} open"
            self.scan_history.append(hist_entry)

        self.reset_ui()

    def _emit_port_result(self, port, status, elapsed, msg, counters):
        show_closed = self.show_closed_var.get()
        counters[status] = counters.get(status, 0) + 1
        if status == "open" or show_closed:
            symbol = {"open": "✓", "closed": "✗", "filtered": "◐", "error": "!"}.get(status, "?")
            line = f"  {symbol} {port:>6}  {status.upper():<10}  {elapsed:>6.0f}ms  {msg}"
            tag  = status if status in ("open", "closed", "filtered", "error") else "info"
            self.log_result(line, tag, status=status)
        self._status(f"Port {port} → {status.upper()}", C.get(status, C["muted"]))

    # ── Controls ─────────────────────────────────────────────────────────────────
    def start_test(self):
        if self.is_running:
            return
        self.is_running = True
        self.stop_flag  = False
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.clear_btn.config(state="disabled")
        threading.Thread(target=self.run_test, daemon=True).start()

    def stop_test(self):
        self.stop_flag = True
        self.stop_btn.config(state="disabled")
        self._status("Stopping scan…", C["warn"])

    def reset_ui(self):
        self.is_running = False
        self.stop_flag  = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.clear_btn.config(state="normal")
        self.progress_label.config(text="Scan complete.")
        self._status("Scan finished.", C["open"])

    def clear_results(self):
        self.results_text.delete("1.0", tk.END)
        self.all_results.clear()
        self.progress_bar["value"] = 0
        self.progress_label.config(text="")
        for key in self.stat_vars:
            self.stat_vars[key].set("—")
        self._status("Results cleared.", C["muted"])


def main():
    global FONT_MONO, FONT_MED
    root = tk.Tk()
    root.withdraw()

    families = tkfont.families()
    FONT_MONO = ("JetBrains Mono", 9) if "JetBrains Mono" in families else ("Courier New", 9)
    FONT_MED  = ("Segoe UI Semibold", 11) if "Segoe UI Semibold" in families else ("Segoe UI", 11, "bold")

    app = OutboundTester(root)
    root.deiconify()
    root.mainloop()


if __name__ == "__main__":
    main()
