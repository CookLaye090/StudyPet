"""
Main Game Screen - Primary interface showing pet, study controls, and navigation
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import time
import datetime
from models.pet import PetStage, PetEmotion
from graphics.pet_graphics import pet_graphics
from graphics.playground_renderer import PlaygroundRenderer
from ui.simple_theme import simple_theme, create_styled_button, create_rounded_button
from ui.rounded_widgets import RoundedPanel
from ui.unified_settings import show_unified_settings
from ui.simple_chat_ui import SimpleChatUI
from ui.scrollable_panel import ScrollablePanel

class MainGameScreen:
    """Main game screen with pet display and study functionality."""
    
    def __init__(self, parent, app_state, music_player, app_controller=None):
        self.parent = parent
        self.app_state = app_state
        self.music_player = music_player
        self.app_controller = app_controller  # Reference to main app for screen transitions
        self.frame = None

        try:
            # Initialize theme based on selected pet
            self.setup_pet_theme()
            self.colors = self.theme.colors
            
            # Study session state
            self.study_timer_active = False
            self.study_timer_paused = False
            self.study_time_remaining = 0
            self.study_session_duration = 25  # Default duration in minutes
            self.study_thread = None
            # Preset durations (minutes) for quick-start timer popup
            self.timer_presets = [10, 15, 20, 25, 30]
            
            # UI variables
            self.timer_var = tk.StringVar(value="")
            self.study_progress_var = tk.StringVar(value="Ready to study!")
            
            # Chat system placeholder (disabled)
            self.chat_interface = None
            self.chat_locked = None  # Track whether chat is currently locked (EGG stage)
            self.chat_panel = None  # Reference to chat panel for dynamic updates
            
            # Playground system
            self.playground_renderer = None
            self.playground_canvas = None
            
            # Developer mode (session only) - Direct integration in main screen
            self.developer_mode_enabled = False
            self.developer_password = "12345"
            
            # Dynamic font sizing system
            self.font_widgets = []  # Store widgets with dynamic fonts
            self.base_font_sizes = {}  # Store base font sizes for scaling
            
            self.setup_ui()
            self.setup_dynamic_fonts()
            self.update_pet_display()
            self.update_pet_info_display()
            self.update_music_button_states()
            
            # Bind window resize event for dynamic behaviors
            self._resize_after_id = None
            self.parent.bind('<Configure>', self.handle_window_resize)

        except Exception as e:
            import traceback
            print(f"❌ Error initializing MainGameScreen: {e}")
            print("Full traceback:")
            traceback.print_exc()
            # Re-raise to let the main app handle it
            raise e


    def setup_pet_theme(self):
        """Set up theme based on selected pet."""
        try:
            # Define color schemes for each pet type (matching greeting screen)
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
            try:
                if self.app_state and hasattr(self.app_state, 'get_current_pet'):
                    current_pet = self.app_state.get_current_pet()
                    if current_pet and hasattr(current_pet, 'pet_type'):
                        # Safely get pet type value
                        try:
                            current_pet_type = current_pet.pet_type.value.lower()
                        except (AttributeError, TypeError) as e:
                            print(f"Warning: Could not get pet_type.value: {e}")
                            # Fallback to string representation
                            current_pet_type = str(current_pet.pet_type).lower()
            except Exception as e:
                print(f"Warning: Error accessing pet data: {e}")

            # Default to penguin (gray theme) if no pet selected or error occurred
            if not current_pet_type:
                current_pet_type = "penguin"

            # Apply pet-specific color scheme
            self.theme = simple_theme
            if current_pet_type in pet_color_schemes:
                self.theme.colors.update(pet_color_schemes[current_pet_type])
            else:
                # Fallback to penguin theme
                self.theme.colors.update(pet_color_schemes["penguin"])

        except Exception as e:
            print(f"❌ Error in setup_pet_theme: {e}")
            import traceback
            traceback.print_exc()
            # Use default theme as fallback
            self.theme = simple_theme


    def setup_ui(self):
        """Create new layered layout: Full-screen playground with compact UI blocks."""
        # Define header background color for UI consistency
        header_bg = self.colors.get("bg_secondary", "#F0F0F0")

        # Main frame fills entire window
        self.frame = tk.Frame(self.parent)
        self.frame.pack(fill="both", expand=True)

        # === LAYER 0: Full-screen playground canvas (background) ===
        self.playground_canvas = tk.Canvas(
            self.frame,
            highlightthickness=0,
            bg=self.colors["bg_main"]
        )
        self.playground_canvas.place(x=0, y=0, relwidth=1.0, relheight=1.0)

        # Ensure canvas is at the bottom layer
        # Removed lower() call that was causing hanging
        # self.playground_canvas.lower()

        # Bind click-to-move functionality
        self.playground_canvas.bind("<Button-1>", self.handle_playground_click)

        # Force canvas to update its size immediately and set a visible background
        self.playground_canvas.update_idletasks()
        canvas_width = self.playground_canvas.winfo_width()
        canvas_height = self.playground_canvas.winfo_height()

        # Set a visible background color immediately
        current_pet = self.app_state.get_current_pet()
        if current_pet:
            try:
                # Safely get pet type string
                if hasattr(current_pet.pet_type, 'value'):
                    pet_type_str = current_pet.pet_type.value
                else:
                    pet_type_str = str(current_pet.pet_type)

                # Set a nice background color based on pet type
                bg_colors = {
                    "axolotl": "#4A90E2",  # Water blue
                    "dog": "#F5E6D3",      # Warm beige
                    "cat": "#FFF8E7",      # Light cream
                    "raccoon": "#E8F4E8",  # Light green
                    "penguin": "#E3F2FD"   # Light blue
                }
                bg_color = bg_colors.get(pet_type_str.lower(), "#FF6B6B")  # Red fallback
                self.playground_canvas.configure(bg=bg_color)
            except Exception as e:
                print(f"Warning: Error setting background color: {e}")
                self.playground_canvas.configure(bg="#E3F2FD")  # Default blue

        # Initialize playground immediately instead of using after()
        if current_pet:
            try:
                # Safely get pet data
                pet_type_str = None
                stage_int = None
                emotion_str = None

                if hasattr(current_pet.pet_type, 'value'):
                    pet_type_str = current_pet.pet_type.value
                else:
                    pet_type_str = str(current_pet.pet_type)

                if hasattr(current_pet.stage, 'value'):
                    stage_int = current_pet.stage.value
                else:
                    stage_int = int(current_pet.stage)

                if hasattr(current_pet.emotion, 'value'):
                    emotion_str = current_pet.emotion.value
                else:
                    emotion_str = str(current_pet.emotion)

                if pet_type_str and stage_int is not None and emotion_str:
                    self._init_playground_immediately(pet_type_str, stage_int, emotion_str)
                else:
                    print("Warning: Missing pet data for playground initialization")
            except Exception as e:
                print(f"Warning: Error initializing playground: {e}")
        
        # === LAYER 2: Top navigation bar ===
        nav_frame = tk.Frame(
            self.frame,
            bg=self.colors["bg_secondary"],  # Use pet-specific secondary background
            relief="flat",
            bd=0
        )
        nav_frame.place(x=0, y=0, relwidth=1.0, height=50)

        # Navigation buttons (NO dev button here - moved to settings)
        nav_buttons = [
            ("📅 Schedule", "schedule"),
            ("📊 Stats", "stats"),
            ("🎵 Music", "music"),
            ("⚙️ Settings", "settings")
        ]

        for text, command in nav_buttons:
            btn = create_rounded_button(
                nav_frame,
                text,
                command=lambda cmd=command: self.switch_tab(cmd),
                style="accent",
                radius=20,
                padding=(12, 6),
                font=("Arial", 10, "bold")
            )
            btn.pack(side="left", padx=8, pady=6)

        # Music controls on right side
        music_controls_frame = tk.Frame(nav_frame, bg=self.colors["bg_secondary"])
        music_controls_frame.pack(side="right", padx=10)

        self.music_label = tk.Label(
            music_controls_frame,
            text="🎵 Music:",
            font=("Arial", 9, "bold"),
            bg=self.colors["bg_secondary"],
            fg=self.colors["text_dark"]  # Use pet-specific dark text
        )

        self.prev_button = create_rounded_button(
            music_controls_frame,
            text="⏮️",
            command=self.previous_track_and_update,
            style="accent",
            radius=20,
            padding=(10, 4),
            font=("Arial", 9, "bold")
        )

        self.play_pause_button = create_rounded_button(
            music_controls_frame,
            text="⏸️",
            command=self.toggle_music_playback,
            style="accent",
            radius=20,
            padding=(10, 4),
            font=("Arial", 9, "bold")
        )

        self.next_button = create_rounded_button(
            music_controls_frame,
            text="⏭️",
            command=self.next_track_and_update,
            style="accent",
            radius=20,
            padding=(10, 4),
            font=("Arial", 9, "bold")
        )

        # === LAYER 1: Collapsible UI blocks ===
        # Pet Status (top-left, collapsible)
        self.status_expanded = False
        self.status_container = tk.Frame(self.frame, bg=self.colors["bg_main"], bd=0)
        self.status_container.place(x=10, y=60, width=250, height=40)
        self.status_header = tk.Frame(self.status_container, bg=self.colors["bg_secondary"], relief="flat", bd=0, cursor="hand2")  # Use pet-specific background
        self.status_header.pack(fill="x")
        self.status_header.bind("<Button-1>", self.toggle_status_panel)
        status_header_label = tk.Label(
            self.status_header,
            text="📊 Pet Status ▼",
            font=("Arial", 10, "bold"),
            bg=self.colors["bg_secondary"],
            fg=self.colors["text_dark"],  # Use pet-specific dark text
            cursor="hand2"
        )
        status_header_label.pack(pady=2)
        status_header_label.bind("<Button-1>", self.toggle_status_panel)

        self.status_panel = tk.Frame(self.status_container, bg=self.colors["bg_secondary"])  # Use pet-specific background

        # Create scrollable status panel using new utility class
        self.status_scrollable = ScrollablePanel(self.status_panel, self.colors["bg_secondary"])
        self.status_canvas = self.status_scrollable.get_canvas()
        self.status_content = self.status_scrollable.get_inner_frame()
        # Initially hidden until expanded

        # Contents of status panel
        self.status_labels = {}
        status_items = ["name", "stage", "emotion", "affection"]
        panel_bg = self.colors["bg_secondary"]  # Use pet-specific background
        for item in status_items:
            label = tk.Label(self.status_content, text=f"{item.title()}: ...", font=("Arial", 10), bg=panel_bg, fg=self.colors["text_dark"])
            label.pack(anchor="w", pady=2)
            self.status_labels[item] = label
        tk.Label(self.status_content, text="Progress:", font=("Arial", 9), bg=panel_bg, fg=self.colors["text_dark"]).pack(anchor="w", pady=(5,0))
        self.affection_progress = ttk.Progressbar(self.status_content, length=220, mode='determinate', style="Horizontal.TProgressbar")
        self.affection_progress.pack(pady=5)
        self.affection_progress['value'] = 0  # Initialize progress bar at 0

        # Study Timer (next to chat, top-right, collapsible)
        self.timer_expanded = False
        self.timer_container = tk.Frame(self.frame, bg=self.colors["bg_main"], bd=0)
        # Place to the left of chat (chat is 250px wide + margins)
        self.timer_container.place(relx=1.0, x=-520, y=60, width=250, height=40)
        self.timer_header = tk.Frame(self.timer_container, bg=self.colors["bg_secondary"], relief="flat", bd=0, cursor="hand2")  # Use pet-specific background
        self.timer_header.pack(fill="x")
        self.timer_header.bind("<Button-1>", self.toggle_timer_panel)
        timer_header_label = tk.Label(
            self.timer_header,
            text="⏱️ Study Timer ▼",
            font=("Arial", 10, "bold"),
            bg=self.colors["bg_secondary"],
            fg=self.colors["text_dark"],  # Use pet-specific dark text
            cursor="hand2"
        )
        timer_header_label.pack(pady=2)
        timer_header_label.bind("<Button-1>", self.toggle_timer_panel)

        self.timer_panel = tk.Frame(self.timer_container, bg=self.colors["bg_secondary"])  # Use pet-specific background

        # Create scrollable timer panel using new utility class
        self.timer_scrollable = ScrollablePanel(self.timer_panel, self.colors["bg_secondary"])
        self.timer_canvas = self.timer_scrollable.get_canvas()
        self.timer_content = self.timer_scrollable.get_inner_frame()
        # Initially hidden until expanded

        # Create unified timer interface once
        self.create_timer_ui(self.timer_content)

        # === LAYER 2: Compact collapsible chatbox (top-right, below nav) ===
        self.chat_expanded = False
        self.chat_container = tk.Frame(self.frame, bg=self.colors["bg_main"])
        self.chat_container.place(relx=1.0, x=-260, y=60, width=250, height=40)

        # Chat header (always visible, clickable) - square
        self.chat_header = tk.Frame(
            self.chat_container,
            bg=self.colors["bg_secondary"],  # Use pet-specific secondary background
            relief="flat",
            bd=0
        )
        self.chat_header.pack(fill="x")
        self.chat_header.bind("<Button-1>", self.toggle_chat_panel)

        chat_header_label = tk.Label(
            self.chat_header,
            text="💬 Pet Chat ▼",
            font=("Arial", 10, "bold"),
            bg=self.colors["bg_secondary"],
            fg=self.colors["text_dark"],  # Use pet-specific dark text
            cursor="hand2"
        )
        chat_header_label.pack(pady=2)
        chat_header_label.bind("<Button-1>", self.toggle_chat_panel)

        # Chat panel (hidden initially, expands on click) - square interior
        self.chat_panel = tk.Frame(self.chat_container, bg=self.colors["bg_secondary"])  # Use pet-specific background

        # Create scrollable chat panel using new utility class
        self.chat_scrollable = ScrollablePanel(self.chat_panel, self.colors["bg_secondary"])
        self.chat_canvas = self.chat_scrollable.get_canvas()
        self.chat_content = self.chat_scrollable.get_inner_frame()
        # Initially hidden
        self.create_chat_ui(self.chat_content)

        # Initialize chat lock state
        self.chat_locked = None  # Will be set based on pet stage
        self.update_chat_lock_state(force=True)

        # Force UI update
        self.parent.update_idletasks()

    # === STUDY TIMER SYSTEM ===
    def start_study_session(self, duration_minutes=25):
        """Start a study session with the specified duration."""
        if self.study_timer_active:
            messagebox.showinfo("Timer Active", "A study session is already running!")
            return

        # Set up the session
        self.study_session_duration = duration_minutes
        self.study_time_remaining = duration_minutes * 60  # Convert to seconds
        self.study_timer_active = True
        self.study_timer_paused = False

        # Update UI
        self.timer_var.set(f"{duration_minutes:02d}:00")
        self.study_progress_var.set(f"Study session started! ({duration_minutes} minutes)")

        # Show control buttons and hide start button
        self.pause_resume_button.pack(side="left", padx=2)
        self.stop_session_button.pack(side="left", padx=2)

        # Start the timer thread
        if self.study_thread is None or not self.study_thread.is_alive():
            self.study_thread = threading.Thread(target=self._run_study_timer, daemon=True)
            self.study_thread.start()

        # Update UI to show active timer state
        self.update_timer_ui()

    def stop_study_session(self):
        """Stop the study session."""
        if self.study_thread and self.study_thread.is_alive():
            self.study_timer_active = False
            self.study_timer_paused = False
            self.study_progress_var.set("Study session stopped")
            self.timer_var.set("")
            self.study_thread.join(timeout=1.0)  # Wait for thread to finish
            self.study_thread = None

            # Hide control buttons
            self.pause_resume_button.pack_forget()
            self.stop_session_button.pack_forget()

            # Hide countdown section
            self.countdown_frame.pack_forget()

            # Update UI to show duration selection
            self.update_timer_ui()

    def pause_resume_study_session(self):
        """Pause or resume the current study session."""
        if self.study_timer_active:
            if self.study_timer_paused:
                self.study_timer_paused = False
                self.study_progress_var.set("Study session resumed!")
                self.pause_resume_button.config(text="⏸️ Pause")
            else:
                self.study_timer_paused = True
                self.study_progress_var.set("Study session paused")
                self.pause_resume_button.config(text="▶️ Resume")

            # Update UI to reflect current state
            self.update_timer_ui()

    def confirm_stop_session(self):
        """Confirm stopping the current study session."""
        if self.study_timer_active:
            result = messagebox.askyesno(
                "Stop Study Session",
                "Are you sure you want to stop the current study session?\n\nThis will end your progress."
            )
            if result:
                self.stop_study_session()

    def _run_study_timer(self):
        """Run the study timer in a separate thread."""
        try:
            while self.study_timer_active and self.study_time_remaining > 0:
                if not self.study_timer_paused:
                    time.sleep(1)
                    self.study_time_remaining -= 1

                    # Update display every second
                    minutes = self.study_time_remaining // 60
                    seconds = self.study_time_remaining % 60
                    self.timer_var.set(f"{minutes:02d}:{seconds:02d}")

                    # Update progress text
                    progress_minutes = (self.study_session_duration * 60 - self.study_time_remaining) // 60
                    progress_seconds = (self.study_session_duration * 60 - self.study_time_remaining) % 60
                    self.study_progress_var.set(f"Progress: {progress_minutes:02d}:{progress_seconds:02d} / {self.study_session_duration:02d}:00")

                time.sleep(0.1)  # Small delay to prevent busy waiting

            # Timer finished
            if self.study_timer_active and self.study_time_remaining <= 0:
                self._timer_finished()

        except Exception as e:
            print(f"Timer thread error: {e}")

    def _timer_finished(self):
        """Handle timer completion."""
        self.study_timer_active = False
        self.study_progress_var.set("🎉 Study session complete!")
        self.timer_var.set("00:00")

        # Save completion to app state if available
        if hasattr(self.app_state, 'complete_study_session'):
            self.app_state.complete_study_session(self.study_session_duration)

        # Show completion message
        self.parent.after(0, lambda: messagebox.showinfo(
            "🎉 Session Complete!",
            f"Congratulations! You completed a {self.study_session_duration}-minute study session!\n\n"
            "Great job staying focused! Take a well-deserved break."
        ))

        # Update UI to show duration selection after a short delay
        self.parent.after(1000, lambda: self.update_timer_ui())

    def start_custom_session(self):
        """Start a custom duration session (dev mode only)."""
        if not self.developer_mode_enabled:
            messagebox.showinfo("Dev Mode Required", "Custom timer durations require developer mode to be enabled.")
            return

        if self.study_timer_active:
            messagebox.showinfo("Timer Active", "A study session is already running!")
            return

        # Ask for custom duration
        custom_duration = simpledialog.askstring("Custom Duration", "Enter duration in minutes:", parent=self.parent)

        if custom_duration:
            try:
                duration = int(custom_duration)
                if duration > 0 and duration <= 180:  # Max 3 hours
                    self.start_study_session(duration)
                else:
                    messagebox.showerror("Invalid Duration", "Duration must be between 1 and 180 minutes.")
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter a valid number.")

        # Clear the custom input after starting
        if hasattr(self, 'custom_var'):
            self.custom_var.set("")

    def toggle_status_panel(self, event=None):
        """Toggle pet status panel expansion/collapse."""
        if not hasattr(self, 'status_expanded') or self.status_panel is None:
            return
        if self.status_expanded:
            # Collapse
            self.status_panel.pack_forget()
            if hasattr(self, 'status_container'):
                self.status_container.place_configure(height=40)
            self.status_expanded = False
            for widget in self.status_header.winfo_children():
                if isinstance(widget, tk.Label):
                    widget.config(text="📊 Pet Status ▼")

            # Hide dev buttons when collapsed
            if hasattr(self, 'dev_button_frame') and self.dev_button_frame:
                self.dev_button_frame.pack_forget()
        else:
            # Expand
            self.status_panel.pack(fill="both", expand=True, pady=(5, 0))
            if hasattr(self, 'status_container'):
                self.status_container.place_configure(height=240)
            self.status_expanded = True
            for widget in self.status_header.winfo_children():
                if isinstance(widget, tk.Label):
                    widget.config(text="📊 Pet Status ▲")
            try:
                self.status_scrollable.refresh_scroll()
            except Exception:
                pass

            # Show dev buttons if dev mode is enabled
            self.refresh_developer_ui()

    def toggle_timer_panel(self, event=None):
        """Toggle study timer panel expansion/collapse."""
        if not hasattr(self, 'timer_expanded') or self.timer_panel is None:
            return
        if self.timer_expanded:
            # Collapse
            self.timer_panel.pack_forget()
            if hasattr(self, 'timer_container'):
                self.timer_container.place_configure(height=40)
            self.timer_expanded = False
            for widget in self.timer_header.winfo_children():
                if isinstance(widget, tk.Label):
                    widget.config(text="⏱️ Study Timer ▼")
        else:
            # Expand
            self.timer_panel.pack(fill="both", expand=True, pady=(5, 0))
            if hasattr(self, 'timer_container'):
                self.timer_container.place_configure(height=350)  # Adjusted for vertical layout
            self.timer_expanded = True
            for widget in self.timer_header.winfo_children():
                if isinstance(widget, tk.Label):
                    widget.config(text="⏱️ Study Timer ▲")
            try:
                self.timer_scrollable.refresh_scroll()
                # Update UI content when expanded
                self.update_timer_ui()
            except Exception:
                pass

    def toggle_chat_panel(self, event=None):
        """Toggle chat panel expansion/collapse."""
        if not hasattr(self, 'chat_expanded') or self.chat_panel is None:
            return
        if self.chat_expanded:
            # Collapse
            self.chat_panel.pack_forget()
            if hasattr(self, 'chat_container'):
                self.chat_container.place_configure(height=40)
            self.chat_expanded = False
            # Update header text
            for widget in self.chat_header.winfo_children():
                if isinstance(widget, tk.Label):
                    widget.config(text="💬 Pet Chat ▼")
        else:
            # Expand
            self.chat_panel.pack(fill="both", expand=True, pady=(5, 0))
            if hasattr(self, 'chat_container'):
                self.chat_container.place_configure(height=400)
            self.chat_expanded = True
            # Update header text
            for widget in self.chat_header.winfo_children():
                if isinstance(widget, tk.Label):
                    widget.config(text="💬 Pet Chat ▲")
            # Ensure scroll updates after geometry settles (only if scroll canvas exists)
            try:
                self.chat_scrollable.refresh_scroll()
            except Exception:
                pass

    def handle_playground_click(self, event):
        """Handle left-click on playground to move pet to click location"""
        try:
            if self.playground_renderer and hasattr(self.playground_renderer, 'playground'):
                # Get click coordinates relative to canvas
                click_x = event.x
                click_y = event.y

                # Check if click is in UI area (avoid moving pet into UI panels)
                # UI boundaries: nav bar (top), status panel (left), timer/chat panels (right)
                canvas_width = self.playground_canvas.winfo_width()
                canvas_height = self.playground_canvas.winfo_height()

                # Use configuration-based boundaries for better click detection
                ui_left_boundary = self.playground_renderer.playground.PET_CONFIG["ui_block_right_margin"] + 20  # Status panel + margin
                ui_right_boundary = canvas_width - (self.playground_renderer.playground.PET_CONFIG["ui_block_right_margin"] + 20)  # Timer/chat + margin
                ui_top_boundary = 60   # Nav bar height + small margin
                ui_bottom_boundary = canvas_height - (self.playground_renderer.playground.PET_CONFIG["ui_block_bottom_margin"] + 50)  # Bottom UI + more margin for click area

                # Only move if click is outside UI areas AND pet is not an egg
                current_pet = self.app_state.get_current_pet()
                is_egg = False
                if current_pet and hasattr(current_pet, 'stage'):
                    try:
                        if hasattr(current_pet.stage, 'value'):
                            is_egg = current_pet.stage.value == 1
                        else:
                            is_egg = int(current_pet.stage) == 1
                    except Exception as e:
                        print(f"Warning: Error checking pet stage: {e}")

                # More permissive click detection - allow clicks closer to UI
                is_in_ui_area = (click_x <= ui_left_boundary or
                                click_x >= ui_right_boundary or
                                click_y <= ui_top_boundary or
                                click_y >= ui_bottom_boundary)

                if not is_in_ui_area and not is_egg:  # Don't allow movement for eggs
                    # Move pet gradually to click location using the movement system
                    # Ground pets only move horizontally, aquatic pets move in all directions
                    current_pet = self.app_state.get_current_pet()
                    if current_pet and hasattr(current_pet, 'pet_type'):
                        try:
                            pet_type_str = None
                            if hasattr(current_pet.pet_type, 'value'):
                                pet_type_str = current_pet.pet_type.value
                            else:
                                pet_type_str = str(current_pet.pet_type)

                            # Check if it's a ground pet (Dog, Cat, Raccoon)
                            is_ground_pet = pet_type_str.lower() in ['dog', 'cat', 'raccoon']

                            if is_ground_pet:
                                # Ground pets only move horizontally to mouse x position, stay on ground
                                self.playground_renderer.playground.set_target(click_x, self.playground_renderer.playground.pet_y)
                            else:
                                # Aquatic pets (Axolotl) can move to both x and y
                                self.playground_renderer.playground.set_target(click_x, click_y)
                        except Exception as e:
                            print(f"Warning: Error moving pet: {e}")
                            # Fallback to old behavior if pet type unknown
                            self.playground_renderer.playground.set_target(click_x, click_y)
                    else:
                        # Fallback to old behavior if pet type unknown
                        self.playground_renderer.playground.set_target(click_x, click_y)

                    # Update the pet display immediately
                    self.update_pet_info_display()
                    self.update_affection_progress_bar()

        except Exception as e:
            print(f"Warning: Error in handle_playground_click: {e}")

    def _init_playground_immediately(self, pet_type_str, stage_int, emotion_str):
        """Initialize playground renderer immediately with proper canvas sizing"""
        # print(f"🎮 Initializing playground: {pet_type_str}, stage {stage_int}, emotion {emotion_str}")

        try:
            # Ensure canvas has proper dimensions
            self.playground_canvas.update_idletasks()
            canvas_width = self.playground_canvas.winfo_width()
            canvas_height = self.playground_canvas.winfo_height()

            # print(f"   Canvas dimensions: {canvas_width}x{canvas_height}")

            # Use fallback dimensions if canvas hasn't sized yet
            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width = 800
                canvas_height = 600
                self.playground_canvas.configure(width=canvas_width, height=canvas_height)
                # print(f"   Using fallback dimensions: {canvas_width}x{canvas_height}")

            # Convert pet type string to proper format
            pet_type_key = pet_type_str.capitalize() if isinstance(pet_type_str, str) else str(pet_type_str)
            # print(f"   Pet type key: {pet_type_key}")

            # Initialize playground renderer
            try:
                from graphics.playground_renderer import PlaygroundRenderer
                self.playground_renderer = PlaygroundRenderer(
                    self.playground_canvas,
                    pet_type_key,
                    stage_int,
                    emotion_str
                )
                # print("✅ PlaygroundRenderer created successfully")

                # Update pet display after successful init
                self.update_pet_info_display()
                # print("✅ Pet info display updated")

            except ImportError as ie:
                # print(f"⚠️ Could not import PlaygroundRenderer: {ie}")
                # print("   Creating fallback renderer...")
                # Create a simple fallback
                self.playground_renderer = None
                self.update_pet_info_display()

            except Exception as e:
                # print(f"⚠️ Error creating PlaygroundRenderer: {e}")
                # Still update display even if renderer fails
                self.update_pet_info_display()

        except Exception as e:
            # print(f"❌ Error in _init_playground_immediately: {e}")
            import traceback
            traceback.print_exc()
            # Still try to update pet info
            try:
                self.update_pet_info_display()
            except Exception:
                pass  # Could not update pet info display


    def create_timer_ui(self, parent_frame):
        """Create simple vertical timer interface like Pet Status panel."""
        panel_bg = self.colors["bg_secondary"]

        # Title section
        title_label = tk.Label(
            parent_frame,
            text="⏱️ Study Timer",
            font=("Arial", 14, "bold"),
            bg=panel_bg,
            fg=self.colors["text_dark"]
        )
        title_label.pack(anchor="w", pady=(15, 5))

        desc_label = tk.Label(
            parent_frame,
            text="Choose a duration and start your focused study session",
            font=("Arial", 9),
            bg=panel_bg,
            fg=self.colors["text_medium"]
        )
        desc_label.pack(anchor="w", pady=(0, 10))

        # Quick start section
        tk.Label(
            parent_frame,
            text="Quick Start (minutes):",
            font=("Arial", 11, "bold"),
            bg=panel_bg,
            fg=self.colors["text_dark"]
        ).pack(anchor="w", pady=(10, 5))

        # Preset durations in 2x3 grid layout
        preset_durations = [10, 15, 25, 30, 45, 60]
        preset_grid = tk.Frame(parent_frame, bg=panel_bg)
        preset_grid.pack(fill="x")

        for i, duration in enumerate(preset_durations):
            btn = create_rounded_button(
                preset_grid,
                text=f"{duration}",
                command=lambda d=duration: self.start_study_session(d),
                style="accent",
                radius=12,
                padding=(15, 8),
                font=("Arial", 9, "bold")
            )
            btn.grid(row=i//3, column=i%3, padx=4, pady=3, sticky="ew")

        # Make columns expand equally
        for i in range(3):
            preset_grid.grid_columnconfigure(i, weight=1)

        # Custom duration section (only if dev mode is active)
        if self.developer_mode_enabled:
            tk.Frame(parent_frame, height=1, bg=self.colors.get("text_light", "#ccc")).pack(fill="x", pady=10)

            tk.Label(
                parent_frame,
                text="🔧 Custom Duration (Dev Mode):",
                font=("Arial", 10, "bold"),
                bg=panel_bg,
                fg=self.colors["text_dark"]
            ).pack(anchor="w", pady=(0, 5))

            custom_input_frame = tk.Frame(parent_frame, bg=panel_bg)
            custom_input_frame.pack(anchor="w", fill="x")

            self.custom_var = tk.StringVar()
            custom_entry = tk.Entry(
                custom_input_frame,
                textvariable=self.custom_var,
                width=8,
                justify="center",
                font=("Arial", 9)
            )
            custom_entry.pack(side="left", padx=(0, 5))

            custom_label = tk.Label(
                custom_input_frame,
                text="minutes",
                font=("Arial", 9),
                bg=panel_bg,
                fg=self.colors["text_medium"]
            )
            custom_label.pack(side="left", padx=(0, 10))

            start_custom_btn = create_rounded_button(
                custom_input_frame,
                text="Start",
                command=self.start_custom_session,
                style="accent",
                radius=12,
                padding=(10, 5),
                font=("Arial", 8, "bold")
            )
            start_custom_btn.pack(side="left")

            # Bind custom entry to enable/disable button
            def check_custom_input(*args):
                custom_value = self.custom_var.get().strip()
                start_custom_btn.config(state="normal" if custom_value else "disabled")

            self.custom_var.trace('w', check_custom_input)
            check_custom_input()  # Initial state

        # Study tips section
        tk.Frame(parent_frame, height=1, bg=self.colors.get("text_light", "#ccc")).pack(fill="x", pady=10)

        tips_title = tk.Label(
            parent_frame,
            text="💡 Study Tips:",
            font=("Arial", 10, "bold"),
            bg=panel_bg,
            fg=self.colors["text_dark"]
        )
        tips_title.pack(anchor="w", pady=(0, 5))

        tips = [
            "🎯 Set clear goals for your session",
            "📱 Put your phone on silent mode",
            "💧 Keep water nearby",
            "🌟 Take short breaks when needed"
        ]

        for tip in tips:
            tip_label = tk.Label(
                parent_frame,
                text=tip,
                font=("Arial", 8),
                bg=panel_bg,
                fg=self.colors["text_medium"],
                anchor="w"
            )
            tip_label.pack(anchor="w", pady=1)

        # Bottom countdown section (only shown when timer active)
        self.countdown_frame = tk.Frame(parent_frame, bg=panel_bg)
        self.countdown_display = tk.Label(
            self.countdown_frame,
            textvariable=self.timer_var,
            font=("Arial", 28, "bold"),
            bg=panel_bg,
            fg=self.colors["text_dark"]
        )
        self.countdown_display.pack(pady=10)

        self.progress_display = tk.Label(
            self.countdown_frame,
            textvariable=self.study_progress_var,
            font=("Arial", 10),
            bg=panel_bg,
            fg=self.colors["text_medium"]
        )
        self.progress_display.pack(pady=(0, 10))

        # Control buttons frame
        self.timer_controls_frame = tk.Frame(self.countdown_frame, bg=panel_bg)
        self.pause_resume_button = create_rounded_button(
            self.timer_controls_frame,
            text="⏸️ Pause",
            command=self.pause_resume_study_session,
            style="accent",
            radius=15,
            padding=(12, 6),
            font=("Arial", 9, "bold")
        )
        self.stop_session_button = create_rounded_button(
            self.timer_controls_frame,
            text="⏹️ Stop",
            command=self.confirm_stop_session,
            style="accent",
            radius=15,
            padding=(12, 6),
            font=("Arial", 9, "bold")
        )

        # Initially hide countdown section
        self.countdown_frame.pack_forget()

    def start_custom_session(self):
        """Start a custom duration session using the input field (dev mode only)."""
        if not self.developer_mode_enabled:
            messagebox.showinfo("Dev Mode Required", "Custom timer durations require developer mode to be enabled.")
            return

        if self.study_timer_active:
            messagebox.showinfo("Timer Active", "A study session is already running!")
            return

        # Get duration from the input field
        custom_duration_str = self.custom_var.get().strip()

        if custom_duration_str:
            try:
                duration = int(custom_duration_str)
                if duration > 0 and duration <= 180:  # Max 3 hours
                    self.start_study_session(duration)
                    # Clear the input after starting
                    self.custom_var.set("")
                else:
                    messagebox.showerror("Invalid Duration", "Duration must be between 1 and 180 minutes.")
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter a valid number.")
        else:
            messagebox.showinfo("No Duration", "Please enter a duration in minutes first.")

    def update_timer_ui(self):
        """Update timer UI to show/hide countdown section."""
        if self.study_timer_active:
            # Show countdown section at bottom
            self.countdown_frame.pack(fill="x", pady=(20, 10))
            self.timer_controls_frame.pack(fill="x")

            # Auto-scroll to show the countdown at bottom
            try:
                self.timer_scrollable.scroll_to_bottom()
            except Exception:
                pass
        else:
            # Hide countdown section but keep the rest of the interface
            self.countdown_frame.pack_forget()

            # Ensure scroll is at top for selection interface
            try:
                self.timer_scrollable.scroll_to_top()
            except Exception:
                pass

    def switch_tab(self, tab_name):
        """Switch to different tab/functionality."""
        if tab_name == "schedule":
            messagebox.showinfo("Schedule", "📅 Study schedule feature coming soon!")
        elif tab_name == "stats":
            messagebox.showinfo("Stats", "📊 Statistics feature coming soon!")
        elif tab_name == "music":
            self.show_music_player()
        elif tab_name == "settings":
            self.show_settings()

    def update_pet_info_display(self):
        """Update the compact pet status block with current pet data."""
        try:
            current_pet = self.app_state.get_current_pet()
            if not current_pet:
                return

            # Update compact status labels (name, stage, emotion, affection)
            if hasattr(self, 'status_labels'):
                try:
                    stage_name = None
                    if hasattr(current_pet.stage, 'name'):
                        stage_name = current_pet.stage.name
                    elif hasattr(current_pet.stage, 'value'):
                        # Map stage values to names
                        stage_mapping = {1: "Egg", 2: "Baby", 3: "Child", 4: "Grown", 5: "Battle-fit"}
                        stage_name = stage_mapping.get(current_pet.stage.value, str(current_pet.stage))
                    else:
                        stage_name = str(current_pet.stage)

                    emotion_name = None
                    if hasattr(current_pet.emotion, 'value'):
                        emotion_name = current_pet.emotion.value
                    else:
                        emotion_name = str(current_pet.emotion)

                    self.status_labels['name'].config(text=f"Name: {current_pet.name}")
                    self.status_labels['stage'].config(text=f"Stage: {stage_name.capitalize()}")
                    self.status_labels['emotion'].config(text=f"Emotion: {emotion_name.capitalize()}")
                    self.status_labels['affection'].config(text=f"Affection: {current_pet.affection}/{current_pet.get_current_stage_limit()}")
                except Exception as e:
                    print(f"Warning: Error updating status labels: {e}")
                    # Set default values
                    for item in ['name', 'stage', 'emotion', 'affection']:
                        if item in self.status_labels:
                            self.status_labels[item].config(text=f"{item.title()}: ...")

            # Update progress bar using the dedicated method
            self.update_affection_progress_bar()

        except Exception as e:
            print(f"Warning: Error in update_pet_info_display: {e}")


    def update_pet_display(self):
        """Update the visual pet display (graphics) and refresh info display."""
        try:
            current_pet = self.app_state.get_current_pet()
            if not current_pet:
                return

            # Update visual pet graphics if playground renderer exists
            if self.playground_renderer:
                # Update stage if it changed
                if hasattr(current_pet.stage, 'value'):
                    stage_int = current_pet.stage.value
                else:
                    stage_int = int(current_pet.stage)

                # Update emotion if it changed
                if hasattr(current_pet.emotion, 'value'):
                    emotion_str = current_pet.emotion.value
                else:
                    emotion_str = str(current_pet.emotion)

                # Update playground renderer
                self.playground_renderer.update_pet_stage(stage_int)
                self.playground_renderer.update_pet_emotion(emotion_str)

            # Also update the info display
            self.update_pet_info_display()

        except Exception as e:
            print(f"Warning: Error in update_pet_display: {e}")


    def update_affection_progress_bar(self):
        """Update the affection progress bar with current pet data"""
        try:
            current_pet = self.app_state.get_current_pet()
            if current_pet and hasattr(self, 'affection_progress'):
                try:
                    current_limit = current_pet.get_current_stage_limit()
                    if current_limit > 0:
                        progress = (current_pet.affection / current_limit) * 100
                        self.affection_progress['value'] = min(progress, 100)
                    else:
                        self.affection_progress['value'] = 100
                except Exception as e:
                    print(f"Warning: Error updating affection progress: {e}")
                    self.affection_progress['value'] = 0
        except Exception as e:
            print(f"Warning: Error in update_affection_progress_bar: {e}")


    def update_chat_lock_state(self, force=False):
        """Refresh chat lock state based on current pet stage."""
        try:
            current_pet = self.app_state.get_current_pet()
            if not current_pet or not hasattr(current_pet, 'stage'):
                return

            stage_value = None
            try:
                if hasattr(current_pet.stage, 'value'):
                    stage_value = current_pet.stage.value
                else:
                    stage_value = current_pet.stage
            except Exception as e:
                print(f"Warning: Error getting stage value: {e}")
                return

            should_lock = (stage_value == 1)
            if force or self.chat_locked is None or should_lock != self.chat_locked:
                self.refresh_chat_ui()
        except Exception as e:
            print(f"Warning: Error in update_chat_lock_state: {e}")


    def create_chat_ui(self, parent_frame):
        """Create chat UI in the given parent frame."""
        try:
            current_pet = self.app_state.get_current_pet()
            pet_name = current_pet.name if current_pet else "Pet"

            # Create SimpleChatUI instance
            self.chat_interface = SimpleChatUI(parent_frame, pet_name)
        except Exception as e:
            # Fallback if chat creation fails
            # Create a simple placeholder
            tk.Label(parent_frame, text="🐾 Chat Coming Soon! 🐾", font=("Arial", 12), fg="gray").pack(pady=20)


    def refresh_chat_ui(self):
        """Recreate chat UI when lock state may have changed."""
        if not self.chat_panel:
            return
        for chat_widget in self.chat_content.winfo_children():
            chat_widget.destroy()
        self.create_chat_ui(self.chat_content)


    def switch_tab(self, tab_name):
        """Switch to different tab/functionality."""
        if tab_name == "schedule":
            messagebox.showinfo("Schedule", "📅 Study schedule feature coming soon!")
        elif tab_name == "stats":
            messagebox.showinfo("Stats", "📊 Statistics feature coming soon!")
        elif tab_name == "music":
            self.show_music_player()
        elif tab_name == "settings":
            self.show_settings()

    def setup_dynamic_fonts(self):
        """Initialize dynamic font sizing system."""
        # Store current font sizes for dynamic scaling
        self.base_font_sizes = {
            "title": 32,
            "subtitle": 18,
            "button": 10,
            "label": 9,
            "small": 8
        }

    def update_music_button_states(self):
        """Update main nav bar music controls based on playback state."""
        try:
            available_tracks = self.music_player.get_available_tracks()
            current_track = self.music_player.get_current_track_info()
            if available_tracks and current_track:
                # Ensure widgets are visible
                try:
                    self.music_label.pack_info()
                except tk.TclError:
                    self.music_label.pack(side="left", padx=(0, 5))
                try:
                    self.prev_button.pack_info()
                except tk.TclError:
                    self.prev_button.pack(side="left", padx=2)
                try:
                    self.play_pause_button.pack_info()
                except tk.TclError:
                    self.play_pause_button.pack(side="left", padx=2)
                try:
                    self.next_button.pack_info()
                except tk.TclError:
                    self.next_button.pack(side="left", padx=2)
                # Update play/pause text
                if self.music_player.is_music_playing():
                    self._btn_set_text(self.play_pause_button, "⏸️")
                else:
                    self._btn_set_text(self.play_pause_button, "▶️")
                # Always enable prev/next
                self._btn_set_enabled(self.prev_button, True)
                self._btn_set_enabled(self.next_button, True)
            else:
                # Hide if nothing to show
                self.music_label.pack_forget()
                self.play_pause_button.pack_forget()
                self.prev_button.pack_forget()
                self.next_button.pack_forget()
        except AttributeError:
            pass

    def _btn_set_text(self, btn, text):
        """Set text on a rounded button."""
        try:
            if hasattr(btn, 'set_text'):
                btn.set_text(text)
            else:
                btn.config(text=text)
        except Exception:
            pass

    def _btn_set_enabled(self, btn, enabled):
        """Enable/disable a button."""
        try:
            if hasattr(btn, 'set_enabled'):
                btn.set_enabled(enabled)
            else:
                btn.config(state="normal" if enabled else "disabled")
        except Exception:
            pass

    def previous_track_and_update(self):
        """Go to previous track and update UIs."""
        if self.music_player.previous_track():
            self.update_music_displays()

    def next_track_and_update(self):
        """Go to next track and update UIs."""
        if self.music_player.next_track():
            self.update_music_displays()

    def toggle_music_playback(self):
        """Toggle music play/pause from main nav bar button."""
        available_tracks = self.music_player.get_available_tracks()
        if not available_tracks:
            messagebox.showinfo(
                "No Music Found",
                "No music files found in the bgm folder!\n\n"
                "To add background music:\n"
                "1. Add MP3, WAV, OGG, or M4A files to the bgm folder\n"
                "2. Open the Music window to refresh"
            )
            return
        current_track = self.music_player.get_current_track_info()
        if not current_track:
            messagebox.showinfo(
                "No Track Selected",
                "Please choose a track first!\n\n"
                "Open the Music Player and click on any track name to select it,\n"
                "then press Play to start listening."
            )
            return
        if self.music_player.is_music_playing():
            self.music_player.pause()
        else:
            self.music_player.resume()
        self.update_music_displays()
        self.update_music_button_states()

    def update_music_displays(self):
        """Update current track label and play/pause button in music window, then nav bar."""
        try:
            current_track = self.music_player.get_current_track_info()
            current_text = current_track["name"] if current_track else "No track selected"
            if hasattr(self, 'current_track_label'):
                self.current_track_label.configure(text=current_text)
            if hasattr(self, 'music_play_pause_btn'):
                if self.music_player.is_music_playing():
                    self.music_play_pause_btn.configure(text="⏸️ Pause")
                else:
                    self.music_play_pause_btn.configure(text="▶️ Play")
            self.update_music_button_states()
        except AttributeError:
            pass

    def show_music_player(self):
        """Show music player controls in a popup."""
        music_window = tk.Toplevel(self.parent)
        music_window.title("🎵 Music Player")
        music_window.geometry("500x500")
        music_window.resizable(True, True)

        # Main container with scrollable frame
        main_canvas = tk.Canvas(music_window)
        scrollbar = ttk.Scrollbar(music_window, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )

        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)

        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Music controls frame
        controls_frame = ttk.Frame(scrollable_frame, padding=20)
        controls_frame.pack(fill="both", expand=True)

        # Title
        ttk.Label(controls_frame, text="🎵 Music Player", font=("Arial", 18, "bold")).pack(pady=(0, 20))

        # Current track info
        now_playing_frame = ttk.LabelFrame(controls_frame, text="Now Playing", padding=15)
        now_playing_frame.pack(fill="x", pady=(0, 15))

        current_track = self.music_player.get_current_track_info()
        current_text = current_track["name"] if current_track else "No track selected"

        self.current_track_label = ttk.Label(now_playing_frame, text=current_text, font=("Arial", 12, "bold"), foreground="blue")
        self.current_track_label.pack()

        # Playback controls
        playback_frame = ttk.LabelFrame(controls_frame, text="Playback Controls", padding=15)
        playback_frame.pack(fill="x", pady=(0, 15))

        button_frame = ttk.Frame(playback_frame)
        button_frame.pack()

        # Control buttons
        ttk.Button(
            button_frame,
            text="⏮️ Previous",
            command=lambda: self.previous_track_and_update(),
            width=12
        ).grid(row=0, column=0, padx=5, pady=5)

        play_pause_btn = ttk.Button(
            button_frame,
            text="⏸️ Pause" if self.music_player.is_music_playing() else "▶️ Play",
            command=lambda: self.toggle_music_and_update(),
            width=12
        )
        play_pause_btn.grid(row=0, column=1, padx=5, pady=5)
        # Store reference for dynamic updates
        self.music_play_pause_btn = play_pause_btn

        ttk.Button(
            button_frame,
            text="⏭️ Next",
            command=lambda: self.next_track_and_update(),
            width=12
        ).grid(row=0, column=2, padx=5, pady=5)

        # Stop button
        ttk.Button(
            button_frame,
            text="⏹️ Stop",
            command=lambda: self.stop_music_and_update(),
            width=12
        ).grid(row=1, column=1, padx=5, pady=5)

        # Volume control
        volume_frame = ttk.LabelFrame(controls_frame, text="Volume Control", padding=15)
        volume_frame.pack(fill="x", pady=(0, 15))

        volume_control_frame = ttk.Frame(volume_frame)
        volume_control_frame.pack(fill="x")

        ttk.Label(volume_control_frame, text="🔈", font=("Arial", 12)).pack(side="left", padx=(0, 10))

        volume_scale = ttk.Scale(
            volume_control_frame,
            from_=0, to=100,
            orient="horizontal",
            command=lambda v: self.music_player.set_volume(float(v)/100)
        )
        volume_scale.set(self.music_player.get_volume() * 100)
        volume_scale.pack(side="left", fill="x", expand=True)

        ttk.Label(volume_control_frame, text="🔊", font=("Arial", 12)).pack(side="left", padx=(10, 0))

        # Available tracks
        tracks_frame = ttk.LabelFrame(controls_frame, text="Track Library", padding=15)
        tracks_frame.pack(fill="both", expand=True, pady=(0, 15))

        available_tracks = self.music_player.get_available_tracks()
        if available_tracks:
            for i, track in enumerate(available_tracks):
                track_frame = ttk.Frame(tracks_frame)
                track_frame.pack(fill="x", pady=2)

                current_track = self.music_player.get_current_track_info()
                is_current = current_track and current_track.get('name') == track['name']

                btn_text = f"🎵 {track['name']}" + ("  ✓" if is_current else "")
                track_button = ttk.Button(
                    track_frame,
                    text=btn_text,
                    command=lambda idx=i: self.select_track_and_update(idx)
                )
                track_button.pack(fill="x")
        else:
            ttk.Label(
                tracks_frame,
                text="🎵 No Music Found\n\nAdd MP3, WAV, OGG, or M4A files to the 'bgm' folder",
                font=("Arial", 12),
                foreground="gray",
                justify="center"
            ).pack(pady=20)

        # Close button
        ttk.Button(
            controls_frame,
            text="❌ Close Player",
            command=music_window.destroy,
            width=15
        ).pack(pady=(10, 0))

    def select_track_and_update(self, track_index):
        """Select a track without playing and update UIs."""
        if self.music_player.select_track(track_index):
            self.update_music_displays()
            self.update_music_button_states()

    def toggle_music_and_update(self):
        """Toggle music in player window and refresh buttons."""
        current_track = self.music_player.get_current_track_info()
        if not current_track:
            messagebox.showinfo(
                "No Track Selected",
                "Please choose a track first!\n\n"
                "Click on any track name in the Track Library to select it,"
                "then press Play to start listening."
            )
            return
        self.music_player.toggle_playback()
        self.update_music_displays()
        self.update_music_button_states()

    def stop_music_and_update(self):
        """Stop playback and hide main nav play button."""
        self.music_player.stop_playback()
        self.update_music_displays()
        try:
            self.play_pause_button.pack_forget()
        except AttributeError:
            pass

    def show_settings(self):
        """Show unified settings window."""
        try:
            show_unified_settings(self.parent, self.app_state, self.music_player)
        except Exception as e:
            print(f"Warning: Could not open settings: {e}")
            messagebox.showinfo("Settings", "⚙️ Settings feature coming soon!")

    def handle_window_resize(self, event):
        """Handle window resize events."""
        try:
            if self._resize_after_id is not None:
                self.parent.after_cancel(self._resize_after_id)
        except Exception:
            pass
        self._resize_after_id = self.parent.after(150, self.update_pet_info_display)

    # === DEVELOPER MODE SYSTEM ===
    def dev_toggle_mode(self):
        """Toggle developer mode on/off."""
        if self.developer_mode_enabled:
            # Disable dev mode
            self.developer_mode_enabled = False
            self._hide_dev_mode_ui()
            messagebox.showinfo("Dev Mode", "Developer mode disabled!")
        else:
            # Enable dev mode (password verification handled in settings)
            self.developer_mode_enabled = True
            self._show_dev_mode_ui()
            messagebox.showinfo("Dev Mode", "Developer mode enabled!\n\nAdvanced features are now available.")

        # Refresh timer UI to show/hide custom duration
        if hasattr(self, 'timer_expanded') and self.timer_expanded:
            self.update_timer_ui()

    def _create_dev_mode_ui(self):
        """Create developer mode UI elements."""
        panel_bg = self.colors["bg_secondary"]

        # Developer mode buttons container
        self.dev_button_frame = tk.Frame(self.status_content, bg=panel_bg)

        # Create main button container that fills the width
        button_container = tk.Frame(self.dev_button_frame, bg=panel_bg)
        button_container.pack(fill="x")

        # Left side - 3 buttons vertically (uniform width)
        left_frame = tk.Frame(button_container, bg=panel_bg, width=100)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        left_frame.pack_propagate(False)  # Maintain fixed width

        self.dev_force_evolve_button = create_rounded_button(
            left_frame,
            text="Force Evolve",
            command=self.dev_force_evolve,
            style="accent",
            radius=15,
            padding=(8, 4),
            font=("Arial", 8, "bold")
        )
        self.dev_force_evolve_button.pack(fill="x", pady=1)

        self.dev_set_stage_button = create_rounded_button(
            left_frame,
            text="Set Stage",
            command=self.dev_set_stage,
            style="accent",
            radius=15,
            padding=(8, 4),
            font=("Arial", 8, "bold")
        )
        self.dev_set_stage_button.pack(fill="x", pady=1)

        self.dev_set_emotion_button = create_rounded_button(
            left_frame,
            text="Set Emotion",
            command=self.dev_set_emotion,
            style="accent",
            radius=15,
            padding=(8, 4),
            font=("Arial", 8, "bold")
        )
        self.dev_set_emotion_button.pack(fill="x", pady=1)

        # Right side - 2 buttons vertically (uniform width)
        right_frame = tk.Frame(button_container, bg=panel_bg, width=100)
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        right_frame.pack_propagate(False)  # Maintain fixed width

        self.dev_plus_50_affection_button = create_rounded_button(
            right_frame,
            text="+50 Affection",
            command=self.dev_plus_50_affection,
            style="accent",
            radius=15,
            padding=(8, 4),
            font=("Arial", 8, "bold")
        )
        self.dev_plus_50_affection_button.pack(fill="x", pady=1)

        self.dev_reset_affection_button = create_rounded_button(
            right_frame,
            text="Reset Affection",
            command=self.dev_reset_affection,
            style="accent",
            radius=15,
            padding=(8, 4),
            font=("Arial", 8, "bold")
        )
        self.dev_reset_affection_button.pack(fill="x", pady=1)

    def _show_dev_mode_ui(self):
        """Show developer mode UI elements."""
        if not hasattr(self, 'dev_button_frame'):
            self._create_dev_mode_ui()

        if hasattr(self, 'dev_button_frame'):
            self.dev_button_frame.pack(fill="x", pady=(10, 0))

    def _hide_dev_mode_ui(self):
        """Hide developer mode UI elements."""
        if hasattr(self, 'dev_button_frame'):
            self.dev_button_frame.pack_forget()

    def dev_force_evolve(self):
        """Force evolve pet to next stage (developer function)."""
        if not self.developer_mode_enabled:
            return

        current_pet = self.app_state.get_current_pet()
        if current_pet:
            # Get current stage
            current_stage = current_pet.stage.value if hasattr(current_pet.stage, 'value') else current_pet.stage

            # Don't evolve if already at max stage (assuming 5 is max)
            if current_stage >= 5:
                messagebox.showinfo("Cannot Evolve", "Pet is already at maximum stage!")
                return

            # Evolve to next stage
            new_stage = current_pet.stage.__class__(current_stage + 1)
            current_pet.stage = new_stage

            # Reset affection for new stage
            current_pet.affection = 0

            # Save and update display
            self.app_state.save_data()
            self.update_pet_display()
            messagebox.showinfo("Force Evolve", f"Pet evolved to stage {new_stage}!")

    def dev_set_stage(self):
        """Set pet to specific stage (developer function)."""
        if not self.developer_mode_enabled:
            return

        current_pet = self.app_state.get_current_pet()
        if current_pet:
            # Get available stages (1-5)
            stages = ["1 (Egg)", "2 (Baby)", "3 (Child)", "4 (Teen)", "5 (Adult)"]
            stage_str = simpledialog.askstring("Set Stage", "Enter stage (1-5):", initialvalue="1")

            if stage_str:
                try:
                    stage_num = int(stage_str)
                    if 1 <= stage_num <= 5:
                        current_pet.stage = current_pet.stage.__class__(stage_num)
                        current_pet.affection = 0  # Reset affection for new stage

                        # Save and update display
                        self.app_state.save_data()
                        self.update_pet_display()
                        messagebox.showinfo("Stage Set", f"Pet stage set to {stage_num}!")
                    else:
                        messagebox.showerror("Invalid Stage", "Stage must be between 1 and 5!")
                except ValueError:
                    messagebox.showerror("Invalid Input", "Please enter a number between 1 and 5!")

    def dev_set_emotion(self):
        """Set pet to specific emotion (developer function)."""
        if not self.developer_mode_enabled:
            return

        current_pet = self.app_state.get_current_pet()
        if current_pet:
            # Get available emotions
            emotions = ["1 (Happy)", "2 (Curious)", "3 (Hungry)", "4 (Sad)"]
            emotion_str = simpledialog.askstring("Set Emotion", "Enter emotion (1-4):\n1=Happy, 2=Curious, 3=Hungry, 4=Sad", initialvalue="1")

            if emotion_str:
                try:
                    emotion_num = int(emotion_str)
                    if 1 <= emotion_num <= 4:
                        current_pet.emotion = current_pet.emotion.__class__(emotion_num)

                        # Save and update display
                        self.app_state.save_data()
                        self.update_pet_display()
                        emotion_names = ["Happy", "Curious", "Hungry", "Sad"]
                        messagebox.showinfo("Emotion Set", f"Pet emotion set to {emotion_names[emotion_num-1]}!")
                    else:
                        messagebox.showerror("Invalid Emotion", "Emotion must be between 1 and 4!")
                except ValueError:
                    messagebox.showerror("Invalid Input", "Please enter a number between 1 and 4!")

    def dev_plus_50_affection(self):
        """Add 50 affection points (developer function)."""
        if not self.developer_mode_enabled:
            return

        current_pet = self.app_state.get_current_pet()
        if current_pet:
            max_affection = current_pet.get_current_stage_limit()
            new_affection = min(current_pet.affection + 50, max_affection)

            current_pet.affection = new_affection

            # Save and update display
            self.app_state.save_data()
            self.update_pet_display()
            messagebox.showinfo("+50 Affection", f"Added 50 affection points! ({new_affection}/{max_affection})")

    def dev_reset_affection(self):
        """Reset affection to 0 (developer function)."""
        if not self.developer_mode_enabled:
            return

        current_pet = self.app_state.get_current_pet()
        if current_pet:
            current_pet.affection = 0

            # Save and update display
            self.app_state.save_data()
            self.update_pet_display()
            messagebox.showinfo("Affection Reset", "Pet affection has been reset to 0!")

    def refresh_developer_ui(self):
        """Refresh developer UI when dev mode is toggled."""
        if self.developer_mode_enabled:
            self._show_dev_mode_ui()
        else:
            self._hide_dev_mode_ui()