import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import font as tkfont

# Set environment variables to suppress pygame output before importing pygame
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
os.environ['SDL_VIDEO_ALLOW_SCREENSAVER'] = '1'

# Suppress pygame warnings and other warnings
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pygame.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pkg_resources.*")

import pygame

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from screens.greeting_screen import GreetingScreen
from screens.pet_selection_screen import PetSelectionScreen
from screens.main_game_screen import MainGameScreen
from models.app_state import AppState
from utils.music_player import MusicPlayer
from ui.simple_theme import simple_theme

class VirtualPetStudyApp:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("StudyPet")

        # Set icon as early as possible
        self._set_application_icon()

        # Tighten global fonts (labels, menus, text) without touching explicit title fonts
        try:
            for fname, size in ("TkDefaultFont", 10), ("TkTextFont", 10), ("TkMenuFont", 9), ("TkTooltipFont", 9), ("TkCaptionFont", 9):
                try:
                    f = tkfont.nametofont(fname)
                    # Reduce by 1–2pt but keep readable
                    new_size = max(9, min(11, int(size)))
                    f.configure(size=new_size)
                except Exception:
                    pass
        except Exception:
            pass

        self.root.state('zoomed')
        self.root.minsize(800, 600)
        self.root.resizable(True, True)

        self.root.bind('<F11>', self.toggle_fullscreen)

        self.root.configure(bg=simple_theme.get_color("bg_main"))

        self.app_state = AppState()

        self.music_player = MusicPlayer()

        self.current_screen = None

        self.show_greeting()

    def _set_application_icon(self):
        """Set application icon with fallback options."""
        icon_paths = [
            os.path.join(os.path.dirname(__file__), 'img', 'Axos.ico'),
            os.path.join(os.path.dirname(__file__), 'img', 'Axos.png'),
            os.path.join(os.path.dirname(__file__), 'Axos.ico'),
            os.path.join(os.path.dirname(__file__), 'Axos.png')
        ]

        for icon_path in icon_paths:
            if os.path.exists(icon_path):
                try:
                    self.root.iconbitmap(icon_path)
                    return
                except Exception as e:
                    continue

        # If no icon files work, try default system methods
        try:
            self.root.iconbitmap()
        except:
            pass

    def show_greeting(self):
        """Show the greeting screen with proper theme refresh."""
        # Clean up current screen
        if self.current_screen and hasattr(self.current_screen, 'destroy'):
            try:
                self.current_screen.destroy()
            except Exception as e:
                pass
        self.current_screen = None

        # Create new greeting screen
        try:
            self.current_screen = GreetingScreen(
                self.root,
                on_start_callback=self.handle_start_game,
                app_state=self.app_state
            )

            # Force theme refresh immediately
            if hasattr(self.current_screen, 'refresh_theme'):
                self.current_screen.refresh_theme()

            # Force UI update
            self.root.update_idletasks()

        except Exception as e:
            import traceback
            traceback.print_exc()
            return None

        return self.current_screen

    def show_pet_selection(self):
        """Show the pet selection screen."""
        # Clean up current screen
        if self.current_screen and hasattr(self.current_screen, 'destroy'):
            try:
                self.current_screen.destroy()
            except Exception as e:
                pass
        self.current_screen = None

        # Create new pet selection screen
        try:
            self.current_screen = PetSelectionScreen(
                self.root,
                on_pet_selected_callback=self.handle_pet_selected
            )

            # Force UI update
            self.root.update_idletasks()

        except Exception as e:
            import traceback
            traceback.print_exc()
            return None

        return self.current_screen

    def show_main_game(self):
        """Show the main game screen with proper error handling."""
        # Clean up current screen
        if self.current_screen and hasattr(self.current_screen, 'destroy'):
            try:
                self.current_screen.destroy()
            except Exception as e:
                pass
        self.current_screen = None

        # Create new main game screen
        try:
            self.current_screen = MainGameScreen(
                self.root,
                self.app_state,
                self.music_player,
                app_controller=self
            )

            # Verify theme was applied
            if hasattr(self.current_screen, 'colors'):
                current_pet = self.app_state.get_current_pet()
                if current_pet:
                    pass  # Pet display handled by MainGameScreen
                else:
                    pass  # No pet selected

            # Force UI update
            self.root.update_idletasks()

        except Exception as e:
            import traceback
            print(f"❌ Error creating MainGameScreen: {e}")
            print("Full traceback:")
            traceback.print_exc()
            # Fallback: show greeting screen
            self.show_greeting()
            return None

        return self.current_screen

    def handle_start_game(self):
        """Handle the start game action from greeting screen."""
        if self.app_state.is_first_time_user():
            self.show_pet_selection()
        else:
            self.show_main_game()

    def handle_pet_selected(self, pet_type, pet_name):
        """Handle pet selection and go directly to main game screen with pet theme."""
        # Set the pet in app state
        self.app_state.set_selected_pet(pet_type, pet_name)

        # Save data immediately
        try:
            self.app_state.save_data()
        except Exception as e:
            pass

        # Go directly to main game screen
        self.show_main_game()

    def force_theme_refresh_all_screens(self):
        """Force refresh theme on current screen."""
        if self.current_screen and hasattr(self.current_screen, 'refresh_theme'):
            try:
                self.current_screen.refresh_theme()
                self.root.update_idletasks()
            except Exception as e:
                pass
        else:
            pass

    def reset_to_default_greeting(self):
        """Reset and go to default greeting screen (without theme refresh)."""
        # Clear pet data
        if hasattr(self.app_state, 'reset_data'):
            self.app_state.reset_data()

        # Show default greeting screen (no theme refresh)
        greeting_screen = self.show_greeting()
        # Don't refresh theme - let it use default colors

        # Force UI update
        self.root.update_idletasks()

        return greeting_screen

    def toggle_fullscreen(self, event=None):
        current_state = self.root.attributes('-fullscreen')
        new_state = not current_state
        self.root.attributes('-fullscreen', new_state)

        if not new_state:
            self.root.geometry("1200x800")
            self.root.update_idletasks()
            x = (self.root.winfo_screenwidth() // 2) - (1200 // 2)
            y = (self.root.winfo_screenheight() // 2) - (800 // 2)
            self.root.geometry(f"1200x800+{x}+{y}")

    def run(self):
        self.root.mainloop()


def main():
    app = VirtualPetStudyApp()
    app.run()


if __name__ == "__main__":
    main()