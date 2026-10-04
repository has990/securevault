"""
Stealth Mode — Disguise SecureVault as another application.

When activated:
- Changes window title and appearance mode
- Stores original state for restoration
- Notifies the app to swap the entire GUI content
"""
import customtkinter as ctk


class StealthMode:
    """App disguise system for covert operation."""

    DISGUISES = {
        "calculator": {
            "title": "Calculator",
            "icon": "🧮",
            "accent_color": "#4a90d9",
            "bg_color": "#f0f0f0",
            "appearance": "light",
        },
        "notepad": {
            "title": "Quick Notes",
            "icon": "📝",
            "accent_color": "#f5c542",
            "bg_color": "#fffdf0",
            "appearance": "light",
        },
        "system_monitor": {
            "title": "System Monitor",
            "icon": "📊",
            "accent_color": "#2ecc71",
            "bg_color": "#1a1a2e",
            "appearance": "dark",
        },
        "file_manager": {
            "title": "File Explorer",
            "icon": "📁",
            "accent_color": "#e8c317",
            "bg_color": "#ffffff",
            "appearance": "light",
        },
    }

    def __init__(self, app):
        self.app = app
        self.original_title = "🔐 SecureVault"
        self.is_stealth = False
        self.current_disguise = None
        self._stealth_view = None

    def activate(self, disguise_name: str = "calculator"):
        """Activate stealth mode with the chosen disguise."""
        if disguise_name not in self.DISGUISES:
            disguise_name = "calculator"

        disguise = self.DISGUISES[disguise_name]
        self.current_disguise = disguise_name
        self.is_stealth = True

        # Change window title and theme
        self.app.title(f"{disguise['icon']}  {disguise['title']}")
        ctk.set_appearance_mode(disguise["appearance"])

        # Hide the real vault view and show a fake GUI
        self._hide_real_view()
        self._show_fake_gui(disguise_name)

    def deactivate(self):
        """Restore the real SecureVault appearance."""
        self.is_stealth = False
        self.current_disguise = None

        # Remove fake GUI
        if self._stealth_view:
            self._stealth_view.destroy()
            self._stealth_view = None

        # Restore window
        self.app.title(self.original_title)
        ctk.set_appearance_mode("dark")

        # Show real view again
        self._restore_real_view()

    def toggle(self, disguise_name: str = "calculator"):
        """Toggle stealth mode on/off."""
        if self.is_stealth:
            self.deactivate()
        else:
            self.activate(disguise_name)

    def _hide_real_view(self):
        """Hide the current vault view."""
        if self.app.current_view:
            self.app.current_view.pack_forget()

    def _restore_real_view(self):
        """Restore the current vault view."""
        if self.app.current_view:
            self.app.current_view.pack(fill="both", expand=True)

    def _show_fake_gui(self, disguise_name: str):
        """Show a convincing fake application GUI."""
        if self._stealth_view:
            self._stealth_view.destroy()

        if disguise_name == "calculator":
            self._stealth_view = self._build_calculator()
        elif disguise_name == "notepad":
            self._stealth_view = self._build_notepad()
        elif disguise_name == "system_monitor":
            self._stealth_view = self._build_system_monitor()
        elif disguise_name == "file_manager":
            self._stealth_view = self._build_file_manager()

        if self._stealth_view:
            self._stealth_view.pack(fill="both", expand=True)

    # ─────────────────────────────────────────────
    #  FAKE APP: CALCULATOR
    # ─────────────────────────────────────────────

    def _build_calculator(self) -> ctk.CTkFrame:
        """Build a convincing fake calculator GUI."""
        frame = ctk.CTkFrame(self.app, fg_color="#f0f0f0")

        # Display
        display = ctk.CTkEntry(
            frame, height=80, font=("Segoe UI", 36),
            corner_radius=10, fg_color="white",
            border_color="#cccccc", text_color="#333333",
            justify="right"
        )
        display.pack(fill="x", padx=20, pady=(30, 15))
        display.insert(0, "0")

        # Button grid
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        buttons = [
            ["C", "±", "%", "÷"],
            ["7", "8", "9", "×"],
            ["4", "5", "6", "−"],
            ["1", "2", "3", "+"],
            ["0", ".", "⌫", "="],
        ]

        # Calculator logic
        calc_state = {"current": "0", "operator": None, "previous": None, "new_number": True}

        def calc_press(btn_text):
            if btn_text in "0123456789":
                if calc_state["new_number"]:
                    calc_state["current"] = btn_text
                    calc_state["new_number"] = False
                else:
                    calc_state["current"] += btn_text
                display.delete(0, "end")
                display.insert(0, calc_state["current"])
            elif btn_text == ".":
                if "." not in calc_state["current"]:
                    calc_state["current"] += "."
                    display.delete(0, "end")
                    display.insert(0, calc_state["current"])
            elif btn_text == "C":
                calc_state["current"] = "0"
                calc_state["operator"] = None
                calc_state["previous"] = None
                calc_state["new_number"] = True
                display.delete(0, "end")
                display.insert(0, "0")
            elif btn_text == "⌫":
                calc_state["current"] = calc_state["current"][:-1] or "0"
                display.delete(0, "end")
                display.insert(0, calc_state["current"])
            elif btn_text in "÷×−+":
                calc_state["previous"] = float(calc_state["current"])
                calc_state["operator"] = btn_text
                calc_state["new_number"] = True
            elif btn_text == "=":
                if calc_state["operator"] and calc_state["previous"] is not None:
                    current = float(calc_state["current"])
                    prev = calc_state["previous"]
                    ops = {"÷": lambda a, b: a / b if b != 0 else 0,
                           "×": lambda a, b: a * b,
                           "−": lambda a, b: a - b,
                           "+": lambda a, b: a + b}
                    result = ops.get(calc_state["operator"], lambda a, b: b)(prev, current)
                    result_str = str(int(result)) if result == int(result) else f"{result:.8g}"
                    calc_state["current"] = result_str
                    calc_state["operator"] = None
                    calc_state["previous"] = None
                    calc_state["new_number"] = True
                    display.delete(0, "end")
                    display.insert(0, result_str)
            elif btn_text == "±":
                if calc_state["current"].startswith("-"):
                    calc_state["current"] = calc_state["current"][1:]
                else:
                    calc_state["current"] = "-" + calc_state["current"]
                display.delete(0, "end")
                display.insert(0, calc_state["current"])
            elif btn_text == "%":
                calc_state["current"] = str(float(calc_state["current"]) / 100)
                display.delete(0, "end")
                display.insert(0, calc_state["current"])

        for row_idx, row in enumerate(buttons):
            btn_frame.grid_rowconfigure(row_idx, weight=1)
            for col_idx, btn_text in enumerate(row):
                btn_frame.grid_columnconfigure(col_idx, weight=1)

                if btn_text == "=":
                    bg = "#4a90d9"
                    hover = "#3a7bc8"
                    text_clr = "white"
                elif btn_text in "÷×−+":
                    bg = "#ff9500"
                    hover = "#e68600"
                    text_clr = "white"
                elif btn_text in ("C", "±", "%"):
                    bg = "#d4d4d4"
                    hover = "#c0c0c0"
                    text_clr = "#333333"
                else:
                    bg = "#e8e8e8"
                    hover = "#d8d8d8"
                    text_clr = "#333333"

                ctk.CTkButton(
                    btn_frame, text=btn_text,
                    font=("Segoe UI", 22, "bold"),
                    fg_color=bg, hover_color=hover,
                    text_color=text_clr,
                    corner_radius=10, border_spacing=4,
                    command=lambda t=btn_text: calc_press(t)
                ).grid(row=row_idx, column=col_idx, padx=4, pady=4, sticky="nsew")

        # Secret: double-click the display to exit stealth
        display.bind("<Double-Button-1>", lambda e: self.deactivate())

        return frame

    # ─────────────────────────────────────────────
    #  FAKE APP: NOTEPAD
    # ─────────────────────────────────────────────

    def _build_notepad(self) -> ctk.CTkFrame:
        """Build a convincing fake notepad GUI."""
        frame = ctk.CTkFrame(self.app, fg_color="#fffdf0")

        # Toolbar
        toolbar = ctk.CTkFrame(frame, fg_color="#f5f0e0", height=45)
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)

        for btn_text in ["📄 New", "📂 Open", "💾 Save", "✂️ Cut", "📋 Paste"]:
            ctk.CTkButton(
                toolbar, text=btn_text, width=70, height=32,
                fg_color="transparent", hover_color="#e8e0c8",
                text_color="#666666", font=("Segoe UI", 11),
                corner_radius=6
            ).pack(side="left", padx=3, pady=6)

        # Text area
        text_area = ctk.CTkTextbox(
            frame, font=("Consolas", 14),
            fg_color="white", text_color="#333333",
            border_color="#ddd8c4", border_width=1,
            corner_radius=0
        )
        text_area.pack(fill="both", expand=True, padx=0, pady=0)
        text_area.insert("1.0", "Shopping List\n─────────────\n• Milk\n• Eggs\n• Bread\n• Coffee\n\nTODO:\n• Call dentist\n• Pay electricity bill\n• Buy birthday gift")

        # Status bar
        status = ctk.CTkFrame(frame, fg_color="#f5f0e0", height=25)
        status.pack(fill="x")
        status.pack_propagate(False)

        ctk.CTkLabel(
            status, text="  Ln 1, Col 1  |  UTF-8  |  LF",
            font=("Segoe UI", 10), text_color="#999999"
        ).pack(side="left", padx=5)

        # Secret exit: triple-click the status bar
        status.bind("<Triple-Button-1>", lambda e: self.deactivate())

        return frame

    # ─────────────────────────────────────────────
    #  FAKE APP: SYSTEM MONITOR
    # ─────────────────────────────────────────────

    def _build_system_monitor(self) -> ctk.CTkFrame:
        """Build a fake system monitor GUI."""
        frame = ctk.CTkFrame(self.app, fg_color="#1a1a2e")

        # Title
        ctk.CTkLabel(
            frame, text="📊 System Monitor",
            font=("Segoe UI", 20, "bold"),
            text_color="#ffffff"
        ).pack(pady=(20, 15), padx=20, anchor="w")

        # Stats cards
        stats_row = ctk.CTkFrame(frame, fg_color="transparent")
        stats_row.pack(fill="x", padx=20, pady=(0, 15))

        stats = [
            ("CPU Usage", "23%", "#2ecc71"),
            ("Memory", "4.2 / 16 GB", "#3498db"),
            ("Disk", "234 GB free", "#e67e22"),
            ("Network", "↓ 2.1 MB/s", "#9b59b6"),
        ]

        for title, value, color in stats:
            card = ctk.CTkFrame(stats_row, fg_color="#16213e", corner_radius=12)
            card.pack(side="left", expand=True, fill="both", padx=5)

            ctk.CTkLabel(
                card, text=title,
                font=("Segoe UI", 11), text_color="#8899aa"
            ).pack(pady=(12, 2), padx=15, anchor="w")

            ctk.CTkLabel(
                card, text=value,
                font=("Segoe UI", 22, "bold"), text_color=color
            ).pack(pady=(0, 12), padx=15, anchor="w")

        # Fake process list
        ctk.CTkLabel(
            frame, text="Running Processes",
            font=("Segoe UI", 14, "bold"),
            text_color="#ffffff"
        ).pack(pady=(10, 5), padx=20, anchor="w")

        process_frame = ctk.CTkScrollableFrame(
            frame, fg_color="#16213e", corner_radius=10
        )
        process_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        processes = [
            ("System Idle Process", "0%", "0.1 MB"),
            ("explorer.exe", "1.2%", "85 MB"),
            ("chrome.exe", "8.4%", "512 MB"),
            ("python.exe", "2.1%", "45 MB"),
            ("svchost.exe", "0.8%", "32 MB"),
            ("RuntimeBroker.exe", "0.3%", "18 MB"),
            ("dwm.exe", "1.5%", "65 MB"),
            ("taskmgr.exe", "0.5%", "22 MB"),
            ("SearchHost.exe", "0.2%", "95 MB"),
            ("spotify.exe", "3.1%", "280 MB"),
            ("discord.exe", "2.8%", "195 MB"),
            ("code.exe", "4.2%", "320 MB"),
        ]

        # Header
        header = ctk.CTkFrame(process_frame, fg_color="transparent")
        header.pack(fill="x", pady=(5, 2))
        ctk.CTkLabel(header, text="Name", font=("Segoe UI", 11, "bold"),
                     text_color="#8899aa", width=200, anchor="w").pack(side="left", padx=10)
        ctk.CTkLabel(header, text="CPU", font=("Segoe UI", 11, "bold"),
                     text_color="#8899aa", width=80, anchor="w").pack(side="left")
        ctk.CTkLabel(header, text="Memory", font=("Segoe UI", 11, "bold"),
                     text_color="#8899aa", width=80, anchor="w").pack(side="left")

        for name, cpu, mem in processes:
            row = ctk.CTkFrame(process_frame, fg_color="transparent", height=30)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)
            ctk.CTkLabel(row, text=name, font=("Consolas", 11),
                         text_color="#cccccc", width=200, anchor="w").pack(side="left", padx=10)
            ctk.CTkLabel(row, text=cpu, font=("Consolas", 11),
                         text_color="#2ecc71", width=80, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=mem, font=("Consolas", 11),
                         text_color="#3498db", width=80, anchor="w").pack(side="left")

        # Secret exit: double-click the title
        frame.winfo_children()[0].bind("<Double-Button-1>", lambda e: self.deactivate())

        return frame

    # ─────────────────────────────────────────────
    #  FAKE APP: FILE MANAGER
    # ─────────────────────────────────────────────

    def _build_file_manager(self) -> ctk.CTkFrame:
        """Build a fake file manager GUI."""
        frame = ctk.CTkFrame(self.app, fg_color="#ffffff")

        # Address bar
        addr_bar = ctk.CTkFrame(frame, fg_color="#f7f7f7", height=45)
        addr_bar.pack(fill="x")
        addr_bar.pack_propagate(False)

        ctk.CTkButton(addr_bar, text="←", width=35, height=30,
                       fg_color="#e0e0e0", hover_color="#d0d0d0",
                       text_color="#666", corner_radius=6).pack(side="left", padx=(10, 2), pady=7)
        ctk.CTkButton(addr_bar, text="→", width=35, height=30,
                       fg_color="#e0e0e0", hover_color="#d0d0d0",
                       text_color="#666", corner_radius=6).pack(side="left", padx=2, pady=7)

        addr_entry = ctk.CTkEntry(
            addr_bar, height=30, corner_radius=6,
            fg_color="white", border_color="#ddd",
            text_color="#333", font=("Segoe UI", 12)
        )
        addr_entry.pack(side="left", fill="x", expand=True, padx=10, pady=7)
        addr_entry.insert(0, "C:\\Users\\user\\Documents")

        # File list
        file_frame = ctk.CTkScrollableFrame(frame, fg_color="white")
        file_frame.pack(fill="both", expand=True, padx=0, pady=0)

        files = [
            ("📁", "Desktop", "Folder", ""),
            ("📁", "Documents", "Folder", ""),
            ("📁", "Downloads", "Folder", ""),
            ("📁", "Music", "Folder", ""),
            ("📁", "Pictures", "Folder", ""),
            ("📁", "Videos", "Folder", ""),
            ("📄", "budget_2026.xlsx", "21 KB", "Mar 1, 2026"),
            ("📄", "meeting_notes.docx", "15 KB", "Feb 28, 2026"),
            ("📄", "vacation_plan.pdf", "340 KB", "Feb 20, 2026"),
            ("🖼️", "family_photo.jpg", "2.4 MB", "Jan 15, 2026"),
            ("📄", "recipe_collection.txt", "8 KB", "Jan 10, 2026"),
            ("📄", "tax_return_2025.pdf", "156 KB", "Dec 5, 2025"),
        ]

        # Header
        header = ctk.CTkFrame(file_frame, fg_color="#f0f0f0", height=30)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="  Name", width=300, anchor="w",
                     font=("Segoe UI", 11, "bold"), text_color="#666").pack(side="left")
        ctk.CTkLabel(header, text="Size", width=100, anchor="w",
                     font=("Segoe UI", 11, "bold"), text_color="#666").pack(side="left")
        ctk.CTkLabel(header, text="Modified", width=150, anchor="w",
                     font=("Segoe UI", 11, "bold"), text_color="#666").pack(side="left")

        for icon, name, size, modified in files:
            row = ctk.CTkFrame(file_frame, fg_color="transparent", height=32)
            row.pack(fill="x")
            row.pack_propagate(False)

            ctk.CTkLabel(row, text=f"  {icon}  {name}", width=300, anchor="w",
                         font=("Segoe UI", 12), text_color="#333").pack(side="left")
            ctk.CTkLabel(row, text=size, width=100, anchor="w",
                         font=("Segoe UI", 11), text_color="#888").pack(side="left")
            ctk.CTkLabel(row, text=modified, width=150, anchor="w",
                         font=("Segoe UI", 11), text_color="#888").pack(side="left")

        # Status bar
        status = ctk.CTkFrame(frame, fg_color="#f7f7f7", height=25)
        status.pack(fill="x")
        status.pack_propagate(False)
        ctk.CTkLabel(status, text="  12 items", font=("Segoe UI", 10),
                     text_color="#999").pack(side="left")

        # Secret exit: double-click address bar
        addr_entry.bind("<Double-Button-1>", lambda e: self.deactivate())

        return frame