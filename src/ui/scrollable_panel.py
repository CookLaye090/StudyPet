"""
Scrollable Panel Utility
Reusable scrollable panel component for StudyPet UI elements.

This utility provides a reusable scrollable panel component that can be used
throughout the StudyPet application for consistent scrolling behavior.

Usage:
    from ui.scrollable_panel import ScrollablePanel

    # Create a scrollable panel
    scrollable = ScrollablePanel(parent_frame, background_color="#F0F0F0")

    # Get the inner frame to add content
    content_frame = scrollable.get_inner_frame()

    # Add your widgets to the content frame
    tk.Label(content_frame, text="Content here").pack()

    # Control scrolling programmatically
    scrollable.scroll_to_top()
    scrollable.scroll_to_bottom()
    scrollable.refresh_scroll()
    scrollable.update_content_size()

Features:
- Cross-platform mouse wheel support (Windows, Linux, macOS)
- Automatic scroll region management
- Consistent scrollbar styling
- Robust error handling
- Easy-to-use API for all UI components

Available Methods:
- get_canvas() - Get the underlying canvas widget
- get_inner_frame() - Get the frame for adding content
- get_scrollbar() - Get the scrollbar widget
- refresh_scroll() - Refresh scroll region and reset to top
- scroll_to_top() - Scroll to top of content
- scroll_to_bottom() - Scroll to bottom of content
- update_content_size() - Update scroll region when content changes
- destroy() - Clean up resources
"""

import tkinter as tk
import tkinter.ttk as ttk


class ScrollablePanel:
    """A reusable scrollable panel component for StudyPet UI elements."""

    def __init__(self, parent, background_color=None, scrollbar_width=16):
        """
        Create a scrollable panel.

        Args:
            parent: Parent widget (tk.Frame, tk.LabelFrame, etc.)
            background_color: Background color for the panel (optional)
            scrollbar_width: Width of the scrollbar in pixels (default: 16)
        """
        self.parent = parent
        self.canvas = None
        self.scrollbar = None
        self.inner_frame = None
        self.background_color = background_color or parent.cget("bg")

        # Create the scrollable panel
        self._create_scrollable_panel(scrollbar_width)

    def _create_scrollable_panel(self, scrollbar_width):
        """Create the canvas, scrollbar, and inner frame."""
        # Create canvas
        self.canvas = tk.Canvas(
            self.parent,
            highlightthickness=0,
            bg=self.background_color
        )

        # Create scrollbar with proper styling
        self.scrollbar = ttk.Scrollbar(
            self.parent,
            orient="vertical",
            command=self.canvas.yview
        )

        # Connect scrollbar to canvas
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Pack widgets
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Create inner frame
        self.inner_frame = tk.Frame(self.canvas, bg=self.background_color)
        inner_id = self.canvas.create_window(
            (0, 0),
            window=self.inner_frame,
            anchor="nw"
        )

        # Configure scroll region updates
        def _on_configure(event):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            # Resize inner width to match canvas width
            self.canvas.itemconfigure(inner_id, width=self.canvas.winfo_width())

        self.inner_frame.bind("<Configure>", _on_configure)

        # Enhanced mouse wheel support for cross-platform compatibility
        def _on_mousewheel(event):
            try:
                # Handle different delta formats (Windows, Linux, macOS)
                if hasattr(event, 'delta'):
                    if event.delta > 0:
                        delta = -1  # Scroll up
                    else:
                        delta = 1   # Scroll down
                elif hasattr(event, 'num'):
                    if event.num == 4:
                        delta = -1  # Scroll up (Linux)
                    else:
                        delta = 1   # Scroll down (Linux)
                else:
                    return "break"

                self.canvas.yview_scroll(delta, "units")
            except Exception:
                pass
            return "break"

        self.canvas.bind("<MouseWheel>", _on_mousewheel)
        self.inner_frame.bind("<MouseWheel>", _on_mousewheel)

        # Ensure scrollbar functionality with multiple updates
        def _update_scroll_region():
            try:
                self.canvas.configure(scrollregion=self.canvas.bbox("all"))
                self.canvas.update_idletasks()
                # Ensure scrollbar is properly connected
                self.scrollbar.configure(command=self.canvas.yview)
                self.canvas.configure(yscrollcommand=self.scrollbar.set)
            except Exception:
                pass

        # Multiple attempts to ensure scroll region is set
        self.inner_frame.after(100, _update_scroll_region)
        self.inner_frame.after(500, _update_scroll_region)
        self.inner_frame.after(1000, _update_scroll_region)

    def refresh_scroll(self):
        """Force refresh the scroll region and ensure scrollbar is functional."""
        try:
            if self.canvas and self.scrollbar:
                self.canvas.update_idletasks()
                self.canvas.configure(scrollregion=self.canvas.bbox("all"))
                self.canvas.yview_moveto(0)
        except Exception:
            pass

    def scroll_to_bottom(self):
        """Scroll to the bottom of the panel."""
        try:
            if self.canvas:
                self.canvas.update_idletasks()
                self.canvas.configure(scrollregion=self.canvas.bbox("all"))
                self.canvas.yview_moveto(1.0)  # Scroll to bottom
        except Exception:
            pass

    def scroll_to_top(self):
        """Scroll to the top of the panel."""
        try:
            if self.canvas:
                self.canvas.update_idletasks()
                self.canvas.configure(scrollregion=self.canvas.bbox("all"))
                self.canvas.yview_moveto(0.0)  # Scroll to top
        except Exception:
            pass

    def update_content_size(self):
        """Update the scroll region when content changes."""
        try:
            if self.canvas:
                self.canvas.configure(scrollregion=self.canvas.bbox("all"))
                self.canvas.update_idletasks()
        except Exception:
            pass

    def get_canvas(self):
        """Get the canvas widget."""
        return self.canvas

    def get_inner_frame(self):
        """Get the inner frame for adding content."""
        return self.inner_frame

    def get_scrollbar(self):
        """Get the scrollbar widget."""
        return self.scrollbar

    def destroy(self):
        """Clean up the scrollable panel."""
        try:
            if self.canvas:
                self.canvas.destroy()
            if self.scrollbar:
                self.scrollbar.destroy()
            if self.inner_frame:
                self.inner_frame.destroy()
        except Exception:
            pass
