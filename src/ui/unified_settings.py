"""
Unified Settings Window for StudyPet
Shared settings interface for both greeting screen and main game screen
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sys
import os
from ui.simple_theme import simple_theme, create_styled_button, create_rounded_button
from ui.rounded_widgets import RoundedPanel


class UnifiedSettings:
    """Unified settings window with simple theme and proper reset functionality."""
    
    def __init__(self, parent, app_state=None, title="⚙️ StudyPet Settings", game_screen=None):
        self.parent = parent
        self.app_state = app_state
        self.title = title
        self.game_screen = game_screen
        self.theme = simple_theme
        self.colors = self.theme.colors
        
        # Create and show the settings window
        self.create_settings_window()
    
    def create_settings_window(self):
        """Create the unified settings window."""
        self.settings_window = tk.Toplevel(self.parent)
        self.settings_window.title(self.title)
        self.settings_window.geometry("600x820")
        self.settings_window.minsize(560, 720)
        self.settings_window.resizable(True, True)
        self.settings_window.configure(bg=self.colors["bg_main"])

        # Make window modal (but don't grab focus immediately to avoid issues)
        self.settings_window.transient(self.parent)
        self.settings_window.protocol("WM_DELETE_WINDOW", self._safe_destroy_settings)

        # Center the window
        self.settings_window.update_idletasks()
        x = (self.settings_window.winfo_screenwidth() - self.settings_window.winfo_width()) // 2
        y = (self.settings_window.winfo_screenheight() - self.settings_window.winfo_height()) // 2
        self.settings_window.geometry(f"+{x}+{y}")

        # Set grab after window is fully created and positioned
        try:
            self.settings_window.after(100, lambda: self._set_modal_grab())
        except:
            pass
        
        # Create scrollable content
        self.create_scrollable_content()
        
        # Bind mouse wheel for scrolling
        self.settings_window.bind("<MouseWheel>", self.on_mouse_wheel)
    
    def create_scrollable_content(self):
        """Create the scrollable content area."""
        # Main container with scrollable frame
        self.main_canvas = tk.Canvas(
            self.settings_window, 
            bg=self.colors["bg_main"], 
            highlightthickness=0
        )
        self.scrollbar = tk.Scrollbar(
            self.settings_window,
            command=self.main_canvas.yview,
            bg=self.colors["bg_secondary"],
            troughcolor=self.colors["bg_panel"],
            activebackground=self.colors["bg_accent"]
        )
        self.scrollable_frame = tk.Frame(self.main_canvas, bg=self.colors["bg_main"])
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        )
        
        inner_id = self.main_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.main_canvas.configure(yscrollcommand=self.scrollbar.set)
        # Keep inner frame width equal to canvas width
        def _resize_inner(event=None):
            try:
                self.main_canvas.itemconfigure(inner_id, width=self.main_canvas.winfo_width())
                self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
            except Exception:
                pass
        self.main_canvas.bind("<Configure>", _resize_inner)
        
        # Pack canvas and scrollbar
        self.main_canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Create the settings content
        self.create_settings_content()

    def _scroll_widget_into_view(self, widget, pad=20):
        """Ensure the given widget (usually near bottom) is completely visible inside the canvas."""
        try:
            self.settings_window.update_idletasks()
            canvas_y = self.main_canvas.winfo_rooty()
            canvas_h = self.main_canvas.winfo_height()

            # Widget top and bottom relative to scrollable frame
            y_top = widget.winfo_rooty() - self.scrollable_frame.winfo_rooty()
            y_bottom = y_top + widget.winfo_height()

            total_h = max(1, self.scrollable_frame.winfo_height())

            # Determine needed scroll fraction
            if y_top - pad < self.main_canvas.canvasy(0):
                # Need to scroll up so top is visible
                target = max(0, (y_top - pad) / total_h)
            elif y_bottom + pad > self.main_canvas.canvasy(canvas_h):
                # Need to scroll down so bottom is visible
                target = max(0, (y_bottom + pad - canvas_h) / total_h)
            else:
                return  # Already fully visible
            self.main_canvas.yview_moveto(min(1.0, target))
        except Exception:
            pass
    
    def create_settings_content(self):
        """Create the main settings content."""
        # Main content frame
        settings_frame = tk.Frame(self.scrollable_frame, bg=self.colors["bg_main"], padx=20, pady=20)
        settings_frame.pack(fill="both", expand=True)
        
        # Title with decorative styling in rounded block
        title_panel = RoundedPanel(settings_frame, radius=16, bg=self.colors["bg_secondary"], padding=8)
        title_panel.set_padding(10)
        title_panel.pack(fill="x", pady=(0, 16))
        title_frame = tk.Frame(title_panel.inner, bg=self.colors["bg_secondary"], relief="flat", bd=0)
        title_frame.pack(fill="x")

        title_label = tk.Label(
            title_frame,
            text="🌸 StudyPet Settings 🌸",
            font=("Comic Sans MS", 20, "bold"),
            fg=self.colors["text_pink"],
            bg=self.colors["bg_secondary"]
        )
        title_label.pack(pady=15)
        
        # App Info Section
        self.create_app_info_section(settings_frame)
        
        # Developer Mode Section (always available with password protection)
        self.create_developer_mode_section(settings_frame)
        
        # Available Settings Section
        self.create_available_settings_section(settings_frame)
        
        # Data Management Section
        reset_btn = self.create_data_management_section(settings_frame)
        
        # Close Button
        self.create_close_button(settings_frame)
        # Ensure the reset button is fully visible by default
        if reset_btn is not None:
            self.settings_window.after(100, lambda: self._scroll_widget_into_view(reset_btn))
    
    def create_app_info_section(self, parent):
        """Create the app information section."""
        info_panel = RoundedPanel(parent, radius=16, bg="#F2F2F2", padding=8)
        info_panel.set_padding(10)
        info_panel.pack(fill="x", pady=(0, 12))
        container = info_panel.inner
        
        info_title = tk.Label(
            container,
            text="📱 Application Information",
            font=("Arial", 14, "bold"),
            fg=self.colors["text_dark"],
            bg="#F2F2F2"
        )
        info_title.pack(pady=(10, 6))
        
        info_text = (
            "StudyPet v1.2\n"
        )
        
        info_label = tk.Label(
            container,
            text=info_text,
            font=("Arial", 11),
            fg=self.colors["text_medium"],
            bg="#F2F2F2",
            justify="center"
        )
        info_label.pack(pady=(0, 10))
    
    def create_available_settings_section(self, parent):
        """Create the available settings section."""
        settings_panel = RoundedPanel(parent, radius=16, bg="#F2F2F2", padding=8)
        settings_panel.set_padding(10)
        settings_panel.pack(fill="x", pady=(0, 12))
        container = settings_panel.inner
        
        settings_title = tk.Label(
            container,
            text="⚙️ Available Settings",
            font=("Arial", 14, "bold"),
            fg=self.colors["text_dark"],
            bg="#F2F2F2"
        )
        settings_title.pack(pady=(10, 6))
        
        features_text = (
            "Current features available:\n\n"
            "• Music volume control and playlist management\n"
            "• Study timer with custom durations\n"
            "• Pet evolution and emotion system\n"
            "• Study progress and statistics tracking\n"
            "• Clean and modern interface\n"
            "• Interactive pet chat system\n"
            "• Responsive design for all screen sizes"
        )
        
        features_label = tk.Label(
            container,
            text=features_text,
            font=("Arial", 11),
            fg=self.colors["text_dark"],
            bg="#F2F2F2",
            justify="left"
        )
        features_label.pack(padx=12, pady=(0, 10))
    
    def create_developer_mode_section(self, parent):
        """Create the developer mode section."""
        dev_panel = RoundedPanel(parent, radius=16, bg="#F2F2F2", padding=10)
        dev_panel.set_padding(16)
        dev_panel.set_min_size(height=240)
        dev_panel.pack(fill="x", pady=(0, 16))
        container = dev_panel.inner

        dev_title = tk.Label(
            container,
            text="🔧 Developer Mode",
            font=("Arial", 14, "bold"),
            fg=self.colors["text_dark"],
            bg="#F2F2F2"
        )
        dev_title.pack(pady=(12, 8))

        # Check dev mode status directly from game screen
        dev_enabled = False
        if self.game_screen and hasattr(self.game_screen, 'developer_mode_enabled'):
            dev_enabled = self.game_screen.developer_mode_enabled

        # Status label
        status_text = "Enabled ✓" if dev_enabled else "Disabled"
        status_color = self.colors.get("success_green", "#28a745") if dev_enabled else self.colors["text_medium"]

        self.dev_status_label = tk.Label(
            container,
            text=f"Status: {status_text}",
            font=("Arial", 12, "bold"),
            fg=status_color,
            bg="#F2F2F2"
        )
        self.dev_status_label.pack(pady=6)

        info_label = tk.Label(
            container,
            text="Advanced testing and development controls (requires dev key)",
            font=("Arial", 10),
            fg=self.colors["text_medium"],
            bg="#F2F2F2",
            justify="center"
        )
        info_label.pack(pady=6)

        # Toggle button
        toggle_btn = create_rounded_button(
            container,
            text=("🔓 Disable Dev Mode" if dev_enabled else "🔧 Enable Dev Mode"),
            command=self.toggle_dev_mode,
            style="accent",
            radius=20,
            padding=(14, 8),
            font=("Arial", 10, "bold")
        )
        toggle_btn.pack(pady=(8, 14))
        # Extra spacer to increase block height
        tk.Frame(container, height=8, bg="#F2F2F2").pack(fill="x")
        self.dev_toggle_btn = toggle_btn
    
    def toggle_dev_mode(self):
        """Toggle developer mode on/off using direct integration."""
        if not self.game_screen or not hasattr(self.game_screen, 'developer_mode_enabled'):
            messagebox.showerror("Dev Mode Error", "Developer mode not available.", parent=self.settings_window)
            return

        # Get current status
        dev_enabled = self.game_screen.developer_mode_enabled

        if not dev_enabled:
            # Ask for password to enable
            password = simpledialog.askstring(
                "Developer Mode",
                "Enter developer password:",
                show='*',
                parent=self.settings_window
            )
            if password == "12345":  # Direct dev mode password
                # Enable dev mode directly (no double password prompt)
                self.game_screen.developer_mode_enabled = True
                # Show dev buttons in status panel
                if hasattr(self.game_screen, 'dev_button_frame'):
                    self.game_screen.dev_button_frame.pack(fill="x", pady=(10, 0))

                # Call refresh to ensure UI is updated everywhere
                if hasattr(self.game_screen, 'refresh_developer_ui'):
                    self.game_screen.refresh_developer_ui()

                # Update UI status
                self.dev_status_label.config(
                    text="Status: Enabled ✓",
                    fg=self.colors.get("success_green", "#28a745")
                )
                self.dev_toggle_btn.set_text("🔓 Disable Dev Mode")

                messagebox.showinfo(
                    "Developer Mode",
                    "Developer mode enabled!\n\nAdvanced features are now available throughout the application.",
                    parent=self.settings_window
                )
            else:
                messagebox.showerror(
                    "Access Denied",
                    "Incorrect password!",
                    parent=self.settings_window
                )
        else:
            # Disable dev mode directly
            self.game_screen.developer_mode_enabled = False
            # Hide dev buttons in status panel
            if hasattr(self.game_screen, 'dev_button_frame'):
                self.game_screen.dev_button_frame.pack_forget()

            # Call refresh to ensure UI is updated everywhere
            if hasattr(self.game_screen, 'refresh_developer_ui'):
                self.game_screen.refresh_developer_ui()

            # Update UI status
            self.dev_status_label.config(
                text="Status: Disabled",
                fg=self.colors["text_medium"]
            )
            self.dev_toggle_btn.set_text("🔧 Enable Dev Mode")

            messagebox.showinfo(
                "Developer Mode",
                "Developer mode disabled!",
                parent=self.settings_window
            )
    
    def create_data_management_section(self, parent):
        """Create the data management section with proper restart functionality."""
        data_panel = RoundedPanel(parent, radius=16, bg="#F2F2F2", padding=10)
        data_panel.set_padding(16)
        data_panel.set_min_size(height=280)
        data_panel.pack(fill="x", pady=(0, 16))
        container = data_panel.inner
        
        data_title = tk.Label(
            container,
            text="🗂️ Data Management",
            font=("Arial", 14, "bold"),
            fg=self.colors["text_dark"],
            bg="#F2F2F2"
        )
        data_title.pack(pady=(12, 8))
        
        warning_text = (
            "⚠️ Reset all progress and start fresh:\n\n"
            "This will permanently delete:\n"
            "• Your current pet and all progress\n"
            "• Study statistics and achievements\n" 
            "• User preferences and settings\n\n"
            "StudyPet will automatically restart after reset."
        )
        
        warning_label = tk.Label(
            container,
            text=warning_text,
            font=("Arial", 11),
            fg=self.colors["text_dark"],
            bg="#F2F2F2",
            justify="left"
        )
        warning_label.pack(padx=14, pady=(0, 14))
        
        # Reset button with enhanced styling
        reset_button = create_rounded_button(
            container,
            text="🔄 Reset All Data & Restart",
            command=self.reset_all_data_and_restart,
            style="primary",
            radius=20,
            padding=(16, 10),
            font=("Arial", 11, "bold")
        )
        reset_button.pack(pady=(2, 16))
        # Extra spacer to increase block height
        tk.Frame(container, height=10, bg="#F2F2F2").pack(fill="x")
        return reset_button
    
    def create_close_button(self, parent):
        """Create the close button."""
        close_frame = tk.Frame(parent, bg=self.colors["bg_main"])
        close_frame.pack(fill="x", pady=(12, 0))
        
        close_button = create_rounded_button(
            close_frame,
            text="✨ Close Settings ✨",
            command=self._safe_destroy_settings,
            style="accent",
            radius=20,
            padding=(20, 10),
            font=("Arial", 13, "bold")
        )
        close_button.pack()
    
    def reset_all_data_and_restart(self):
        """Reset all application data and return to startup screen (like dev mode)."""
        result = messagebox.askyesno(
            "🔄 Reset All Data",
            "Are you sure you want to reset ALL StudyPet data?\n\n" +
            "This will permanently delete:\n" +
            "• Your current pet and progress\n" +
            "• All study statistics\n" +
            "• Settings and preferences\n\n" +
            "⚠️ This action cannot be undone!\n\n" +
            "StudyPet will return to the welcome screen.",
            icon="warning"
        )

        if result:
            try:
                # Reset all data using app_state
                if hasattr(self.app_state, 'reset_data'):
                    self.app_state.reset_data()

                # Navigate back to default (non-themed) greeting screen
                if hasattr(self, 'game_screen') and self.game_screen and hasattr(self.game_screen, 'app_controller') and self.game_screen.app_controller:
                    # Reset to default greeting screen (without theme refresh)
                    if hasattr(self.game_screen.app_controller, 'reset_to_default_greeting'):
                        self.game_screen.app_controller.reset_to_default_greeting()

                        # Show success message after reset
                        messagebox.showinfo(
                            "🎉 Reset Complete",
                            "All data has been reset successfully! StudyPet is ready for a fresh start.",
                            parent=self.settings_window
                        )
                    else:
                        # Fallback to old method
                        if hasattr(self.game_screen, 'destroy'):
                            self.game_screen.destroy()
                        self.game_screen.app_controller.show_greeting()
                else:
                    # When called from greeting screen, just show success
                    messagebox.showinfo(
                        "🎉 Reset Complete",
                        "All data has been reset! StudyPet is ready for a fresh start."
                    )

                # Close settings window safely
                self._safe_destroy_settings()

            except Exception as e:
                error_msg = str(e)
                if "bad window path" in error_msg.lower() or "toplevel" in error_msg.lower():
                    # Handle tkinter window path errors gracefully
                    messagebox.showinfo(
                        "🎉 Reset Complete",
                        "All data has been reset successfully! StudyPet is ready for a fresh start.",
                        parent=self.settings_window if hasattr(self, 'settings_window') and self.settings_window else None
                    )
                    try:
                        self._safe_destroy_settings()
                    except:
                        pass
                else:
                    # Show other errors normally
                    messagebox.showerror(
                        "❌ Reset Failed",
                        f"Could not reset data: {e}\n\n" +
                        "You may need to manually delete the user_data folder and restart the application."
                    )

    def _set_modal_grab(self):
        """Set modal grab for the settings window after it's properly created."""
        try:
            if hasattr(self, 'settings_window') and self.settings_window and self.settings_window.winfo_exists():
                self.settings_window.grab_set()
                self.settings_window.focus_set()
        except Exception:
            pass

    def _safe_destroy_settings(self):
        """Safely destroy the settings window without tkinter errors."""
        try:
            if hasattr(self, 'settings_window') and self.settings_window and self.settings_window.winfo_exists():
                # First release grab if it exists
                try:
                    self.settings_window.grab_release()
                except:
                    pass

                # Then destroy the window
                self.settings_window.destroy()
                self.settings_window = None
        except Exception:
            # If anything fails, just set to None
            self.settings_window = None

    def on_mouse_wheel(self, event):
        """Handle mouse wheel scrolling."""
        try:
            if hasattr(self, 'main_canvas') and self.main_canvas.winfo_exists():
                self.main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        except (tk.TclError, AttributeError):
            # Canvas destroyed or doesn't exist
            pass


def show_unified_settings(parent, app_state=None, title="⚙️ StudyPet Settings", game_screen=None):
    """Show the unified settings window."""
    return UnifiedSettings(parent, app_state, title, game_screen)