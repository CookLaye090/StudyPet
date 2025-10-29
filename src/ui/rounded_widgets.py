import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont

class RoundedButton(tk.Frame):
    def __init__(self, parent, text="", command=None, radius=20, bg="#4A90E2", fg="#FFFFFF", hover_bg=None, active_bg=None, padding=(14, 8), font=("Arial", 10, "bold")):
        super().__init__(parent, bg=parent.cget("bg"))
        self.command = command
        self.radius = radius
        self.bg_normal = bg
        self.bg_hover = hover_bg or bg
        self.bg_active = active_bg or self.bg_hover
        self.fg = fg
        self.padding = padding
        self.text = text
        self.font = tkfont.Font(self, font=font)
        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0, bg=self.cget("bg"))
        self.canvas.pack(fill="both", expand=True)
        self.state = "normal"
        self.enabled = True
        self._saved_command = command
        self.bind_events()
        self.draw()

    def bind_events(self):
        self.canvas.bind("<Enter>", lambda e: self.set_state("hover"))
        self.canvas.bind("<Leave>", lambda e: self.set_state("normal"))
        self.canvas.bind("<ButtonPress-1>", lambda e: self.set_state("active"))
        self.canvas.bind("<ButtonRelease-1>", self._on_click)
        self.bind("<Configure>", lambda e: self.draw())

    def set_state(self, st):
        self.state = st
        self.draw()

    def _on_click(self, e):
        self.set_state("hover")
        if not self.enabled:
            return
        if callable(self.command):
            try:
                self.command()
            except Exception:
                pass

    def draw_round_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1+r, y1,
            x2-r, y1,
            x2, y1,
            x2, y1+r,
            x2, y2-r,
            x2, y2,
            x2-r, y2,
            x1+r, y2,
            x1, y2,
            x1, y2-r,
            x1, y1+r,
            x1, y1,
        ]
        return self.canvas.create_polygon(points, smooth=True, **kwargs)

    def draw(self):
        self.canvas.delete("all")
        txt_w = self.font.measure(self.text)
        txt_h = self.font.metrics("linespace")
        w = txt_w + self.padding[0] * 2
        h = txt_h + self.padding[1] * 2
        self.canvas.config(width=w, height=h)
        if self.state == "active":
            fill = self.bg_active
        elif self.state == "hover":
            fill = self.bg_hover
        else:
            fill = self.bg_normal
        if not self.enabled:
            fill = "#CCCCCC"
        self.draw_round_rect(1, 1, w-1, h-1, self.radius, fill=fill, outline="")
        text_color = self.fg if self.enabled else "#666666"
        self.canvas.create_text(w//2, h//2, text=self.text, font=self.font, fill=text_color)
        self.update_idletasks()

    def set_text(self, text: str):
        self.text = text
        self.draw()

    def set_enabled(self, enabled: bool):
        self.enabled = bool(enabled)
        if self.enabled:
            self.command = self._saved_command
        else:
            # Keep the command but ignore in click handler; also dim colors
            pass
        self.draw()

class RoundedPanel(tk.Frame):
    def __init__(self, parent, radius=20, bg="#FAFAFA", padding=8):
        super().__init__(parent, bg=parent.cget("bg"))
        self.radius = radius
        self.bg_color = bg
        self.padding = padding
        # Optional minimum size hints (content can exceed these)
        self._min_width = None
        self._min_height = None
        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0, bg=self.cget("bg"))
        self.canvas.pack(fill="both", expand=True)
        self.inner = tk.Frame(self.canvas, bg=self.bg_color, highlightthickness=0, bd=0)
        self._win_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self._bg_id = None
        self.bind("<Configure>", self._on_frame_configure)
        self.inner.bind("<Configure>", self._on_inner_configure)
        self._draw_scheduled = False
        self.draw()

    def set_padding(self, padding: int):
        """Update internal padding while keeping content visible."""
        self.padding = padding
        self._schedule_draw()

    def _schedule_draw(self):
        if not self._draw_scheduled:
            self._draw_scheduled = True
            self.after_idle(self.draw)

    def _on_frame_configure(self, event=None):
        self._schedule_draw()

    def _on_inner_configure(self, event=None):
        self._schedule_draw()

    def set_min_size(self, width: int | None = None, height: int | None = None):
        """Set minimum content area size (excluding padding)."""
        if width is not None:
            self._min_width = int(width)
        if height is not None:
            self._min_height = int(height)
        self._schedule_draw()

    def draw_round_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1+r, y1,
            x2-r, y1,
            x2, y1,
            x2, y1+r,
            x2, y2-r,
            x2, y2,
            x2-r, y2,
            x1+r, y2,
            x1, y2,
            x1, y2-r,
            x1, y1+r,
            x1, y1,
        ]
        return self.canvas.create_polygon(points, smooth=True, **kwargs)

    def draw(self):
        self._draw_scheduled = False
        # Measure content including requested size, border, and internal padding
        req_w = self.inner.winfo_reqwidth()
        req_h = self.inner.winfo_reqheight()
        # Available size based on outer widget
        avail_w = max(1, self.winfo_width() - self.padding * 2)
        avail_h = max(1, self.winfo_height() - self.padding * 2)
        # Start from the larger of content vs available
        width = max(req_w, avail_w)
        height = max(req_h, avail_h)
        # Apply minimum size hints (give priority when larger than content)
        if self._min_width is not None:
            width = max(width, self._min_width)
        if self._min_height is not None:
            height = max(height, self._min_height)
        total_w = max(width + self.padding * 2, 20)
        total_h = max(height + self.padding * 2, 20)

        # Update canvas size to accommodate content
        try:
            self.canvas.config(width=total_w, height=total_h)
        except Exception:
            pass

        r = min(self.radius, total_w // 2, total_h // 2)
        if self._bg_id is not None:
            try:
                self.canvas.delete(self._bg_id)
            except Exception:
                pass
        self._bg_id = self.draw_round_rect(1, 1, total_w - 1, total_h - 1, r, fill=self.bg_color, outline="")

        # Position inner frame and ensure it has the measured width/height
        self.canvas.coords(self._win_id, self.padding, self.padding)
        try:
            self.canvas.itemconfigure(self._win_id, width=width, height=height)
            self.canvas.configure(scrollregion=(0, 0, width + self.padding * 2, height + self.padding * 2))
        except Exception:
            pass
