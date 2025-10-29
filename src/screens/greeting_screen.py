"""
Greeting Screen - The startup screen of the Virtual Pet Study App
"""

import tkinter as tk
from tkinter import ttk, messagebox
from ui.simple_theme import simple_theme, create_styled_button, create_rounded_button
from ui.rounded_widgets import RoundedPanel

from ui.unified_settings import show_unified_settings

class GreetingScreen:
    """Greeting screen with app title and start button."""
    
    def __init__(self, parent, on_start_callback, app_state=None):
        self.parent = parent
        self.on_start_callback = on_start_callback
        self.app_state = app_state
        self.frame = None

        # Initialize theme based on selected pet
        self.setup_pet_theme()
        self.create_widgets()
    
    def setup_pet_theme(self):
        """Set up theme based on selected pet."""
        # Define color schemes for each pet type
        pet_color_schemes = {
            "axolotl": {
                # Pastel pink theme for axolotl
                "bg_main": "#FDF2F8",        # Very light pink
                "bg_secondary": "#FCE7F3",   # Light pink
                "bg_accent": "#FBCFE8",      # Medium pink
                "text_dark": "#831843",      # Dark pink
                "text_medium": "#BE185D",    # Medium pink
                "text_light": "#DB2777",     # Light pink
                "text_pink": "#EC4899",      # Pink accent
                "coral_pink": "#F472B6",     # Coral pink
                "soft_pink": "#F9A8D4"       # Soft pink
            },
            "cat": {
                # Pastel Purple and Blue theme for cat
                "bg_main": "#F8F9FA",        # Light gray-blue
                "bg_secondary": "#E5E7EB",   # Light gray
                "bg_accent": "#D1D5DB",      # Medium gray
                "text_dark": "#374151",      # Dark gray
                "text_medium": "#6B7280",    # Medium gray
                "text_light": "#9CA3AF",     # Light gray
                "text_pink": "#8B5CF6",      # Purple accent
                "coral_pink": "#6366F1",     # Blue accent
                "soft_pink": "#A78BFA"       # Light purple
            },
            "dog": {
                # Pastel Yellow theme for dog
                "bg_main": "#FFFBF0",        # Very light yellow
                "bg_secondary": "#FEF3C7",   # Light yellow
                "bg_accent": "#FDE68A",      # Medium yellow
                "text_dark": "#92400E",      # Dark brown
                "text_medium": "#B45309",    # Medium brown
                "text_light": "#D97706",     # Light brown
                "text_pink": "#F59E0B",      # Yellow accent
                "coral_pink": "#FCD34D",     # Light yellow
                "soft_pink": "#FDE047"       # Soft yellow
            },
            "raccoon": {
                # Pastel brown theme for raccoon
                "bg_main": "#FEF7ED",        # Very light brown
                "bg_secondary": "#FED7AA",   # Light brown
                "bg_accent": "#FDBA74",      # Medium brown
                "text_dark": "#9A3412",      # Dark brown
                "text_medium": "#C2410C",    # Medium brown
                "text_light": "#EA580C",     # Light brown
                "text_pink": "#DC2626",      # Red-brown accent
                "coral_pink": "#F97316",     # Orange-brown
                "soft_pink": "#FB923C"       # Soft brown
            },
            "penguin": {
                # Gray theme for penguin (current default)
                "bg_main": "#FFFFFF",        # White
                "bg_secondary": "#F5F5F5",   # Light gray
                "bg_accent": "#E5E5E5",      # Medium gray
                "text_dark": "#000000",      # Black
                "text_medium": "#666666",    # Medium gray
                "text_light": "#999999",     # Light gray
                "text_pink": "#000000",      # Black
                "coral_pink": "#666666",     # Medium gray
                "soft_pink": "#F5F5F5"       # Light gray
            }
        }

        # Get current pet type from app state
        current_pet_type = None
        if self.app_state and hasattr(self.app_state, 'get_current_pet'):
            current_pet = self.app_state.get_current_pet()
            if current_pet and hasattr(current_pet, 'pet_type'):
                current_pet_type = current_pet.pet_type.value.lower()

        # Default to penguin (gray theme) if no pet selected
        if not current_pet_type:
            current_pet_type = "penguin"

        # Apply pet-specific color scheme
        self.theme = simple_theme
        if current_pet_type in pet_color_schemes:
            self.theme.colors.update(pet_color_schemes[current_pet_type])
        else:
            # Fallback to penguin theme
            self.theme.colors.update(pet_color_schemes["penguin"])

        self.colors = self.theme.colors

    def refresh_theme(self):
        """Refresh the theme based on current pet selection."""
        self.setup_pet_theme()

        # Update existing widgets with new colors
        if self.frame:
            self.parent.configure(bg=self.colors["bg_main"])
            self.frame.configure(bg=self.colors["bg_main"])

            # Update title colors if they exist
            for widget in self.frame.winfo_children():
                if hasattr(widget, 'inner'):  # RoundedPanel
                    widget.configure(bg=self.colors["bg_main"])
                    widget.inner.configure(bg=self.colors["bg_secondary"])
                    for child in widget.inner.winfo_children():
                        if isinstance(child, tk.Frame):
                            child.configure(bg=self.colors["bg_secondary"])
                            # Update title labels
                            for label in child.winfo_children():
                                if isinstance(label, tk.Label):
                                    if "StudyPet" in label.cget("text"):
                                        label.configure(fg=self.colors["text_pink"])
                                    elif "Virtual Study Companion" in label.cget("text"):
                                        label.configure(fg=self.colors["text_medium"])
                                elif hasattr(label, 'bg_normal'):  # Start button
                                    current_pet_type = None
                                    if self.app_state and hasattr(self.app_state, 'get_current_pet'):
                                        current_pet = self.app_state.get_current_pet()
                                        if current_pet and hasattr(current_pet, 'pet_type'):
                                            current_pet_type = current_pet.pet_type.value.lower()

                                    if not current_pet_type:
                                        current_pet_type = "penguin"

                                    pet_button_colors = {
                                        "axolotl": {"primary": {"bg": "#EC4899", "fg": "#FFFFFF", "hover": "#DB2777", "active": "#BE185D"}},
                                        "cat": {"primary": {"bg": "#8B5CF6", "fg": "#FFFFFF", "hover": "#7C3AED", "active": "#6D28D9"}},
                                        "dog": {"primary": {"bg": "#F59E0B", "fg": "#FFFFFF", "hover": "#D97706", "active": "#B45309"}},
                                        "raccoon": {"primary": {"bg": "#DC2626", "fg": "#FFFFFF", "hover": "#B91C1C", "active": "#991B1B"}},
                                        "penguin": {"primary": {"bg": "#000000", "fg": "#FFFFFF", "hover": "#333333", "active": "#666666"}}
                                    }

                                    colors = pet_button_colors.get(current_pet_type, pet_button_colors["penguin"])["primary"]
                                    label.bg_normal = colors["bg"]
                                    label.bg_hover = colors["hover"]
                                    label.bg_active = colors["active"]
                                    label.fg = colors["fg"]
                                    label.draw()

            # Update button colors if buttons exist
            for widget in self.frame.winfo_children():
                if isinstance(widget, tk.Frame):  # Bottom frame containing buttons
                    for child in widget.winfo_children():
                        if hasattr(child, 'bg_normal'):  # RoundedButton
                            # Find which button this is and update accordingly
                            if hasattr(child, 'text'):
                                current_pet_type = None
                                if self.app_state and hasattr(self.app_state, 'get_current_pet'):
                                    current_pet = self.app_state.get_current_pet()
                                    if current_pet and hasattr(current_pet, 'pet_type'):
                                        current_pet_type = current_pet.pet_type.value.lower()

                                if not current_pet_type:
                                    current_pet_type = "penguin"

                                pet_button_colors = {
                                    "axolotl": {
                                        "primary": {"bg": "#EC4899", "fg": "#FFFFFF", "hover": "#DB2777", "active": "#BE185D"},
                                        "secondary": {"bg": "#F472B6", "fg": "#831843", "hover": "#F9A8D4", "active": "#FBCFE8"}
                                    },
                                    "cat": {
                                        "primary": {"bg": "#8B5CF6", "fg": "#FFFFFF", "hover": "#7C3AED", "active": "#6D28D9"},
                                        "secondary": {"bg": "#A78BFA", "fg": "#374151", "hover": "#C4B5FD", "active": "#DDD6FE"}
                                    },
                                    "dog": {
                                        "primary": {"bg": "#F59E0B", "fg": "#FFFFFF", "hover": "#D97706", "active": "#B45309"},
                                        "secondary": {"bg": "#FDE047", "fg": "#92400E", "hover": "#FACC15", "active": "#EAB308"}
                                    },
                                    "raccoon": {
                                        "primary": {"bg": "#DC2626", "fg": "#FFFFFF", "hover": "#B91C1C", "active": "#991B1B"},
                                        "secondary": {"bg": "#FB923C", "fg": "#9A3412", "hover": "#FD8A37", "active": "#EA580C"}
                                    },
                                    "penguin": {
                                        "primary": {"bg": "#000000", "fg": "#FFFFFF", "hover": "#333333", "active": "#666666"},
                                        "secondary": {"bg": "#999999", "fg": "#000000", "hover": "#777777", "active": "#555555"}
                                    }
                                }

                                colors = pet_button_colors.get(current_pet_type, pet_button_colors["penguin"])

                                if "START" in child.text:
                                    # Primary button
                                    child.bg_normal = colors["primary"]["bg"]
                                    child.bg_hover = colors["primary"]["hover"]
                                    child.bg_active = colors["primary"]["active"]
                                    child.fg = colors["primary"]["fg"]
                                else:
                                    # Secondary buttons (Settings, About)
                                    child.bg_normal = colors["secondary"]["bg"]
                                    child.bg_hover = colors["secondary"]["hover"]
                                    child.bg_active = colors["secondary"]["active"]
                                    child.fg = colors["secondary"]["fg"]

                                child.draw()

    def create_widgets(self):
        """Create and layout the greeting screen widgets with simple theme."""
        # Configure parent background
        self.parent.configure(bg=self.colors["bg_main"])
        
        # Main frame with theme
        self.frame = tk.Frame(self.parent, bg=self.colors["bg_main"])
        self.frame.pack(fill="both", expand=True, padx=30, pady=30)
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=0)
        self.frame.grid_columnconfigure(0, weight=1)
        
        # Title section with beautiful rounded background
        title_panel = RoundedPanel(self.frame, radius=60, bg=self.colors["bg_secondary"], padding=16)
        title_panel.grid(row=0, column=0, sticky="nsew", padx=20, pady=(20, 10))
        
        title_frame = tk.Frame(title_panel.inner, bg=self.colors["bg_secondary"])
        title_frame.pack(expand=True, pady=20)
        
        # App title
        title_label = tk.Label(
            title_frame,
            text="StudyPet",
            font=("Comic Sans MS", 32, "bold"),
            fg=self.colors["text_pink"],  # Use pet-specific pink accent
            bg=self.colors["bg_secondary"]
        )
        title_label.pack(pady=(40, 20))
        
        # Subtitle with enhanced styling
        subtitle_label = tk.Label(
            title_frame,
            text="Virtual Study Companion!",
            font=("Arial", 18, "bold"),
            fg=self.colors["text_medium"],  # Use pet-specific medium text color
            bg=self.colors["bg_secondary"]
        )
        subtitle_label.pack(pady=(0, 20))
        
        # Start button with enhanced styling
        start_button = create_rounded_button(
            title_frame,
            text="START!",
            command=self.on_start_clicked,
            style="primary",
            radius=20,
            padding=(30, 15),
            font=("Arial", 16, "bold")
        )
        start_button.pack(pady=20)
        start_button.update_idletasks()

        # Bottom buttons frame with theme
        bottom_frame = tk.Frame(self.frame, bg=self.colors["bg_main"])
        bottom_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        bottom_frame.grid_columnconfigure(0, weight=1)
        bottom_frame.grid_columnconfigure(1, weight=1)

        # Settings button with styling
        settings_button = create_rounded_button(
            bottom_frame,
            text="Settings",
            command=self.show_settings,
            style="secondary",
            radius=20
        )
        settings_button.grid(row=0, column=0, sticky="w", padx=20, pady=(10, 20))

        # About button with styling
        about_button = create_rounded_button(
            bottom_frame,
            text="About",
            command=self.show_about,
            style="secondary",
            radius=20
        )
        about_button.grid(row=0, column=1, sticky="e", padx=20, pady=(10, 20))

        # Update button colors to match pet theme
        self.update_button_colors(start_button, settings_button, about_button)

    def update_button_colors(self, start_button, settings_button, about_button):
        """Update button colors to match the current pet theme."""
        # Define pet-specific button color schemes
        pet_button_colors = {
            "axolotl": {
                "primary": {"bg": "#EC4899", "fg": "#FFFFFF", "hover": "#DB2777", "active": "#BE185D"},
                "secondary": {"bg": "#F472B6", "fg": "#831843", "hover": "#F9A8D4", "active": "#FBCFE8"}
            },
            "cat": {
                "primary": {"bg": "#8B5CF6", "fg": "#FFFFFF", "hover": "#7C3AED", "active": "#6D28D9"},
                "secondary": {"bg": "#A78BFA", "fg": "#374151", "hover": "#C4B5FD", "active": "#DDD6FE"}
            },
            "dog": {
                "primary": {"bg": "#F59E0B", "fg": "#FFFFFF", "hover": "#D97706", "active": "#B45309"},
                "secondary": {"bg": "#FDE047", "fg": "#92400E", "hover": "#FACC15", "active": "#EAB308"}
            },
            "raccoon": {
                "primary": {"bg": "#DC2626", "fg": "#FFFFFF", "hover": "#B91C1C", "active": "#991B1B"},
                "secondary": {"bg": "#FB923C", "fg": "#9A3412", "hover": "#FD8A37", "active": "#EA580C"}
            },
            "penguin": {
                "primary": {"bg": "#000000", "fg": "#FFFFFF", "hover": "#333333", "active": "#666666"},
                "secondary": {"bg": "#999999", "fg": "#000000", "hover": "#777777", "active": "#555555"}
            }
        }

        # Get current pet type
        current_pet_type = None
        if self.app_state and hasattr(self.app_state, 'get_current_pet'):
            current_pet = self.app_state.get_current_pet()
            if current_pet and hasattr(current_pet, 'pet_type'):
                current_pet_type = current_pet.pet_type.value.lower()

        if not current_pet_type:
            current_pet_type = "penguin"

        colors = pet_button_colors.get(current_pet_type, pet_button_colors["penguin"])

        # Update start button (primary style)
        if hasattr(start_button, 'bg_normal'):
            start_button.bg_normal = colors["primary"]["bg"]
            start_button.bg_hover = colors["primary"]["hover"]
            start_button.bg_active = colors["primary"]["active"]
            start_button.fg = colors["primary"]["fg"]
            start_button.draw()

        # Update settings and about buttons (secondary style)
        for button in [settings_button, about_button]:
            if hasattr(button, 'bg_normal'):
                button.bg_normal = colors["secondary"]["bg"]
                button.bg_hover = colors["secondary"]["hover"]
                button.bg_active = colors["secondary"]["active"]
                button.fg = colors["secondary"]["fg"]
                button.draw()
    
    def on_start_clicked(self):
        """Handle start button click."""
        if self.on_start_callback:
            self.on_start_callback()

    def show_settings(self):
        """Show unified settings dialog."""
        show_unified_settings(self.parent, self.app_state, "StudyPet Settings - Welcome Screen")

    def show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About StudyPet",
            "StudyPet v1.2\n\n" +
            "A gamified learning companion featuring virtual pets " +
            "that evolve based on your study progress.\n\n" +
            "Features:\n" +
            "• Clean and modern interface\n" +
            "• 5-emotion system (Happy, Tired, Hungry, Sad, Angry)\n" +
            "• Dynamic theming based on selected pet\n" +
            "• Scrollable interfaces for small screens\n" +
            "• 5 different pet types with evolution stages\n" +
            "• Smart emotion system with context awareness\n" +
            "• Study timer with pet encouragement\n" +
            "• Interactive chat with your pet companion\n" +
            "• Built-in music player with focus tracks\n\n"
        )
    
    def destroy(self):
        """Clean up the screen."""
        if self.frame:
            self.frame.destroy()
            self.frame = None