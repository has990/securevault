"""
Cyberpunk Toast Notification — Slides in from top-right with neon glow.
"""
import customtkinter as ctk


class ToastNotification:
    """Non-blocking popup notification with auto-dismiss."""

    # Color schemes for different toast types
    STYLES = {
        "success": {
            "bg": "#0a1f15",
            "border": "#00ff9f",
            "text": "#00ff9f",
            "icon": "✓",
        },
        "error": {
            "bg": "#1f0a0a",
            "border": "#ff0040",
            "text": "#ff0040",
            "icon": "✗",
        },
        "warning": {
            "bg": "#1f1a0a",
            "border": "#ffff00",
            "text": "#ffff00",
            "icon": "⚠",
        },
        "info": {
            "bg": "#0a0f1f",
            "border": "#00f0ff",
            "text": "#00f0ff",
            "icon": "◈",
        },
    }

    @staticmethod
    def show(parent, message, toast_type="success", duration_ms=3000):
        """
        Show a toast notification.
        
        Args:
            parent: Parent widget
            message: Text to display
            toast_type: "success", "error", "warning", or "info"
            duration_ms: How long to show (milliseconds)
        """
        style = ToastNotification.STYLES.get(toast_type, ToastNotification.STYLES["info"])

        # Create the toast frame
        toast = ctk.CTkFrame(
            parent,
            fg_color=style["bg"],
            corner_radius=6,
            border_width=1,
            border_color=style["border"],
            height=45,
            width=400,
        )

        # Position at top-right
        toast.place(relx=0.98, rely=0.02, anchor="ne")
        toast.lift()

        # Inner content
        inner = ctk.CTkFrame(toast, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=12, pady=8)

        # Icon
        ctk.CTkLabel(
            inner,
            text=style["icon"],
            font=("Consolas", 14, "bold"),
            text_color=style["text"],
            width=20,
        ).pack(side="left", padx=(0, 8))

        # Message
        ctk.CTkLabel(
            inner,
            text=message,
            font=("Consolas", 11),
            text_color=style["text"],
        ).pack(side="left", fill="x", expand=True)

        # Close button
        ctk.CTkButton(
            inner,
            text="✕",
            width=24, height=24,
            fg_color="transparent",
            hover_color=style["border"],
            text_color=style["text"],
            font=("Consolas", 12),
            corner_radius=4,
            command=lambda: toast.destroy()
        ).pack(side="right", padx=(8, 0))

        # Auto-dismiss after duration
        def _dismiss():
            try:
                toast.destroy()
            except Exception:
                pass

        parent.after(duration_ms, _dismiss)

        return toast