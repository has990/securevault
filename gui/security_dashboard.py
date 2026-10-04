"""
Security Dashboard — Visual overview of vault password health.
Shows: overall score, weak/reused/breached counts, per-entry breakdown.
"""
import threading
import customtkinter as ctk
from core.password_health import PasswordHealth
from core.breach_checker import BreachChecker
from gui.animations import FadeAnimations, PulseAnimations
from gui.components.toast_notification import ToastNotification


class SecurityDashboard(ctk.CTkFrame):
    """Password health and security scoring dashboard."""

    def __init__(self, parent, colors, encryption_engine, vault_id, db):
        super().__init__(parent, fg_color=colors["bg_dark"])
        self.colors = colors
        self.parent_app = parent
        self.engine = encryption_engine
        self.vault_id = vault_id
        self.db = db

        # ── Header ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=40, pady=(30, 20))

        ctk.CTkButton(
            header, text="← Back", width=80, height=35,
            fg_color=colors["border"], hover_color=colors["bg_card"],
            corner_radius=10, font=("Segoe UI", 12),
            command=lambda: parent.show_vault()
        ).pack(side="left")

        ctk.CTkLabel(
            header, text="📊  Security Dashboard",
            font=("Segoe UI", 24, "bold"),
            text_color=colors["text_primary"]
        ).pack(side="left", padx=20)

        # ── Content ──
        self.content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.content.pack(fill="both", expand=True, padx=40, pady=(0, 30))

        # Decrypt all passwords for analysis
        self._passwords = self._decrypt_all_passwords()
        report = PasswordHealth.analyze_vault(self._passwords)

        # ── Score Card ──
        score_card = ctk.CTkFrame(self.content, fg_color=colors["bg_card"],
                                   corner_radius=20, height=180)
        score_card.pack(fill="x", pady=(0, 20))
        score_card.pack_propagate(False)

        score_inner = ctk.CTkFrame(score_card, fg_color="transparent")
        score_inner.pack(expand=True)

        score = report["overall_score"]
        score_color = (colors["success"] if score >= 75
                       else colors["warning"] if score >= 50
                       else colors["danger"])

        self.score_label = ctk.CTkLabel(
            score_inner, text=f"{score}",
            font=("Segoe UI", 72, "bold"),
            text_color=score_color
        )
        self.score_label.pack()

        ctk.CTkLabel(
            score_inner, text="Overall Security Score",
            font=("Segoe UI", 14),
            text_color=colors["text_secondary"]
        ).pack()

        # Pulse the score if it's low
        if score < 50:
            PulseAnimations.pulse_glow(
                score_card,
                base_color=colors["bg_card"],
                glow_color=colors["danger"],
                duration_ms=2000, loops=3
            )

        # ── Stat Cards Row ──
        stats_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, 20))

        stats = [
            ("🔢 Total",   str(report["total"]),   colors["accent"]),
            ("💪 Strong",  str(report["strong"]),  colors["success"]),
            ("⚠️ Weak",    str(report["weak"]),    colors["warning"]),
            ("♻️ Reused",  str(report["reused"]),  colors["danger"]),
        ]

        for label_text, value, color in stats:
            stat_card = ctk.CTkFrame(stats_frame, fg_color=colors["bg_card"],
                                      corner_radius=15, width=150, height=100)
            stat_card.pack(side="left", expand=True, fill="x", padx=5)
            stat_card.pack_propagate(False)

            ctk.CTkLabel(
                stat_card, text=value,
                font=("Segoe UI", 32, "bold"),
                text_color=color
            ).pack(expand=True)

            ctk.CTkLabel(
                stat_card, text=label_text,
                font=("Segoe UI", 12),
                text_color=colors["text_secondary"]
            ).pack(pady=(0, 12))

        # ── Breach Check Button ──
        self.breach_btn = ctk.CTkButton(
            self.content, text="🛡️  Check All Passwords Against Breaches",
            height=45, corner_radius=12,
            fg_color=colors["accent"], hover_color=colors["accent_hover"],
            font=("Segoe UI", 14, "bold"),
            command=self._run_breach_check
        )
        self.breach_btn.pack(fill="x", pady=(0, 15))

        # Breach results area (initially hidden)
        self.breach_results_frame = ctk.CTkFrame(
            self.content, fg_color="transparent"
        )
        self.breach_results_frame.pack(fill="x", pady=(0, 10))

        # ── Per-Entry Breakdown ──
        ctk.CTkLabel(
            self.content, text="Per-Entry Breakdown",
            font=("Segoe UI", 16, "bold"),
            text_color=colors["text_primary"]
        ).pack(anchor="w", pady=(10, 8))

        for entry_report in report["entries"]:
            self._create_entry_row(entry_report)

    def _decrypt_all_passwords(self) -> list[dict]:
        """
        Prepare vault entries for password-health analysis.
        Passwords protected by the per-password lock are intentionally
        not decrypted. They are marked explicitly so downstream security
        checks can avoid treating the placeholder as a real password.
        """
        raw_entries = self.db.get_entries_by_vault(self.vault_id)
        results = []
        for raw in raw_entries:
            try:
                service = self.engine.decrypt(raw["service"])
                password_protected = (
                    raw.get("per_pass_salt") is not None
                )
                if password_protected:
                    password = "[Secret-Protected]"
                else:
                    password = self.engine.decrypt(
                        raw["password"]
                    )
                results.append({
                    "service": service,
                    "password": password,
                    "password_protected": password_protected,
                })
            except Exception:
                continue
        return results

    def _create_entry_row(self, entry_report: dict):
        """Create a row for each entry in the breakdown table."""
        row = ctk.CTkFrame(self.content, fg_color=self.colors["bg_card"],
                            corner_radius=12, height=50)
        row.pack(fill="x", pady=3)
        row.pack_propagate(False)

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=15, pady=8)

        # Service name
        ctk.CTkLabel(
            inner, text=entry_report.get("service", "Unknown"),
            font=("Segoe UI", 13, "bold"),
            text_color=self.colors["text_primary"]
        ).pack(side="left")

        # Reused badge
        if entry_report.get("reused"):
            ctk.CTkLabel(
                inner, text="♻️ REUSED",
                font=("Segoe UI", 10, "bold"),
                text_color=self.colors["danger"],
                fg_color=self.colors["bg_dark"],
                corner_radius=6, width=70, height=22
            ).pack(side="right", padx=(5, 0))

        # Strength badge
        strength = entry_report.get("strength", {})
        label = strength.get("label", "Unknown")
        badge_colors = {
            "Weak":        self.colors["danger"],
            "Fair":        self.colors["warning"],
            "Strong":      self.colors["accent"],
            "Very Strong": self.colors["success"],
        }
        badge_color = badge_colors.get(label, self.colors["text_secondary"])

        ctk.CTkLabel(
            inner, text=label,
            font=("Segoe UI", 11, "bold"),
            text_color=badge_color
        ).pack(side="right")

    def _run_breach_check(self):
        """Run breach check in background thread."""
        self.breach_btn.configure(
            text="🔄  Checking breaches...",
            state="disabled",
            fg_color=self.colors["border"]
        )

        def _check():
            results = PasswordHealth.check_breaches(self._passwords)
            self.after(0, lambda: self._display_breach_results(results))

        thread = threading.Thread(target=_check, daemon=True)
        thread.start()

    def _display_breach_results(self, results: list):
        """Display breach check results."""
        self.breach_btn.configure(
            text="✅  Breach check complete",
            state="normal",
            fg_color=self.colors["success"]
        )

        # Clear previous results
        for widget in self.breach_results_frame.winfo_children():
            widget.destroy()

        breached_count = sum(1 for r in results if r["breached"])

        if breached_count == 0:
            ctk.CTkLabel(
                self.breach_results_frame,
                text="✅ No passwords found in known breaches!",
                font=("Segoe UI", 14, "bold"),
                text_color=self.colors["success"]
            ).pack(anchor="w", pady=5)
        else:
            ctk.CTkLabel(
                self.breach_results_frame,
                text=f"🚨 {breached_count} password(s) found in data breaches!",
                font=("Segoe UI", 14, "bold"),
                text_color=self.colors["danger"]
            ).pack(anchor="w", pady=5)

            for result in results:
                if result["breached"]:
                    row = ctk.CTkFrame(
                        self.breach_results_frame,
                        fg_color=self.colors["bg_card"],
                        corner_radius=10, height=40
                    )
                    row.pack(fill="x", pady=2)
                    row.pack_propagate(False)

                    row_inner = ctk.CTkFrame(row, fg_color="transparent")
                    row_inner.pack(fill="both", expand=True, padx=15, pady=6)

                    ctk.CTkLabel(
                        row_inner, text=f"🚨 {result['service']}",
                        font=("Segoe UI", 12, "bold"),
                        text_color=self.colors["danger"]
                    ).pack(side="left")

                    ctk.CTkLabel(
                        row_inner,
                        text=f"Seen {result['breach_count']:,} times in breaches",
                        font=("Segoe UI", 11),
                        text_color=self.colors["text_secondary"]
                    ).pack(side="right")

            # Animated warning
            FadeAnimations.fade_in_widget(
                self.breach_results_frame, duration_ms=500,
                start_color=self.colors["bg_dark"],
                end_color=self.colors["bg_dark"]
            )

        ToastNotification.show(
            self,
            f"Breach check done: {breached_count} exposed" if breached_count
            else "All passwords are safe!",
            "error" if breached_count else "success"
        )
