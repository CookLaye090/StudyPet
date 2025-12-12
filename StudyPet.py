import os
import sys

# Suppress TensorFlow oneDNN warnings
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# Suppress TensorFlow logging
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # 1 = filter INFO, 2 = filter INFO & WARNING, 3 = filter INFO, WARNING, & ERROR

# Set environment variables to suppress pygame output before importing pygame
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
os.environ['SDL_VIDEO_ALLOW_SCREENSAVER'] = '1'

import os
import sys
import warnings

# Suppress warnings before other imports
warnings.filterwarnings("ignore", category=UserWarning, module="pygame.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pkg_resources.*")
warnings.filterwarnings("ignore", category=UserWarning, message=".*Skipping variable loading for optimizer.*")
warnings.filterwarnings("ignore", category=UserWarning, module="keras.*")

# Set environment variables before imports
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Suppress TensorFlow oneDNN warnings
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
os.environ['SDL_VIDEO_ALLOW_SCREENSAVER'] = '1'

import tkinter as tk
from tkinter import messagebox
from tkinter import font as tkfont
import pygame

# Add project root and src to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Local imports
from src.screens.greeting_screen import GreetingScreen
from src.screens.pet_selection_screen import PetSelectionScreen
from src.screens.main_game_screen import MainGameScreen
from src.models.app_state import AppState
from src.models.pet import PetType, Pet  # Import Pet class for pet creation
from src.utils.music_player import MusicPlayer
from src.ui.simple_theme import simple_theme
from src.utils.session_manager import SessionManager

class VirtualPetStudyApp:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("StudyPet")
        
        # Set up cleanup on window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Check for dev_mode.key once at startup
        self.has_dev_key = self._check_dev_key()
        
        # Set icon as early as possible
        self._set_application_icon()

        # Tighten global fonts (labels, menus, text) without touching explicit title fonts
        font_specs = [
            ("TkDefaultFont", 10),
            ("TkTextFont", 10),
            ("TkMenuFont", 9),
            ("TkTooltipFont", 9),
            ("TkCaptionFont", 9)
        ]
        
        for fname, size in font_specs:
            try:
                font = tkfont.nametofont(fname)
                # Reduce by 1–2pt but keep readable
                new_size = max(9, min(11, size))
                font.configure(size=new_size)
            except (tk.TclError, ValueError) as e:
                print(f"Warning: Could not configure font {fname}: {e}")

        self.root.state('zoomed')
        self.root.minsize(800, 600)
        self.root.resizable(True, True)

        self.root.configure(bg=simple_theme.get_color("bg_main"))

        # Reset application log files at startup
        try:
            self._reset_logs_on_start()
        except Exception as e:
            print(f"Warning: Could not reset logs on start: {e}")

        # Initialize app state with proper error handling
        try:
            self.app_state = AppState.load_or_create()
            self.app_state.root = self.root
        except Exception as e:
            print(f"Error initializing app state: {e}")
            # Create a minimal working state if initialization fails
            self.app_state = AppState()
            self.app_state.root = self.root

        self.music_player = MusicPlayer()

        self.current_screen = None

        user_data_dir = os.path.join(os.path.dirname(__file__), 'user_data')
        os.makedirs(user_data_dir, exist_ok=True)
        self.session_manager = SessionManager(
            self.app_state,
            os.path.join(user_data_dir, 'save_data.json')
        )

        self.show_greeting()

    def _check_dev_key(self):
        """Check if dev_mode.key exists in the root directory.
        
        Returns:
            bool: True if dev_mode.key exists, False otherwise
        """
        dev_key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dev_mode.key')
        return os.path.exists(dev_key_path)
        
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
                except (tk.TclError, AttributeError) as e:
                    print(f"Warning: Could not load icon {icon_path}: {e}")
                    continue

        # If no icon files work, try default system methods
        try:
            self.root.iconbitmap()
        except tk.TclError as e:
            print(f"Warning: Could not set default icon: {e}")

    def _reset_logs_on_start(self):
        """Reset/clear application log files when the app starts.

        This keeps logs focused on the current session. It safely truncates
        known log files if they exist and ensures the logs directory exists.
        """
        try:
            project_root = os.path.dirname(os.path.abspath(__file__))

            # Camera log used by MainGameScreen
            logs_dir = os.path.join(project_root, 'logs')
            os.makedirs(logs_dir, exist_ok=True)
            camera_log_path = os.path.join(logs_dir, 'camera_log.txt')
            if os.path.exists(camera_log_path):
                open(camera_log_path, 'w', encoding='utf-8').close()

            # Placeholder for any other future logs (extend as needed)
        except Exception as e:
            print(f"Warning: Error while resetting logs: {e}")

    def show_greeting(self):
        """Show the greeting screen with proper theme refresh and reset window title."""
        # Reset window title to default
        if hasattr(self, 'root') and self.root:
            self.root.title("StudyPet")
            
        # Clean up current screen
        if self.current_screen and hasattr(self.current_screen, 'destroy'):
            try:
                # Call cleanup method if it exists
                if hasattr(self.current_screen, 'cleanup'):
                    self.current_screen.cleanup()
                self.current_screen.destroy()
            except (tk.TclError, AttributeError) as e:
                print(f"Warning: Error destroying screen: {e}")
        self.current_screen = None

        # Create new greeting screen
        try:
            self.current_screen = GreetingScreen(
                parent=self.root,
                on_start_callback=self.handle_start_game,
                app_state=self.app_state,
                app_controller=self  # Pass the app_controller reference
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
            except (tk.TclError, AttributeError) as e:
                print(f"Warning: Error destroying screen: {e}")
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
            except (tk.TclError, AttributeError) as e:
                print(f"Warning: Error destroying screen: {e}")
        self.current_screen = None

        # Update window title with pet's name if available
        current_pet = self.app_state.get_current_pet()
        if current_pet and hasattr(current_pet, 'name'):
            self.root.title(f"StudyPet - {current_pet.name}")
        else:
            self.root.title("StudyPet")

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

    def handle_pet_selected(self, pet_type, pet_name, username):
        """
        Handle pet selection and go directly to main game screen with pet theme.
        
        Args:
            pet_type: The type of pet to create
            pet_name: The name to give to the pet
            username: The username for the player
            
        Handles any errors during pet creation and selection.
        """
        if not pet_type:
            messagebox.showerror("Error", "No pet type specified")
            return
            
        try:
            # Create a new pet instance
            new_pet = Pet(pet_type, pet_name or "")
            
            # Set the pet in app state
            self.app_state.current_pet = new_pet
            
            # Ensure user exists and set username from selection screen
            from models.user import User  # Lazy import to avoid circular imports
            if self.app_state.user is None:
                self.app_state.user = User(username or "Player")
            else:
                # Update existing user's username to the new value
                self.app_state.user.username = username or self.app_state.user.username
            
            # Update window title with new pet's name
            if hasattr(self, 'root') and self.root:
                title = f"StudyPet - {pet_name}" if pet_name else "StudyPet"
                self.root.title(title)
            
            # Save data immediately
            try:
                self.app_state.save_data()
            except (IOError, OSError) as e:
                print(f"Warning: Could not save pet data: {e}")
                # Continue even if save fails
            
            # Update window title with pet's name
            title = f"StudyPet - {pet_name}" if pet_name else "StudyPet"
            self.root.title(title)
            
            # Force a small delay to ensure the UI updates
            self.root.update_idletasks()
            
            # Go directly to main game screen
            self.show_main_game()
            
        except Exception as e:
            import traceback
            error_msg = f"Failed to select pet: {str(e)}"
            print(f"Error in handle_pet_selected: {error_msg}")
            traceback.print_exc()
            
            try:
                messagebox.showerror("Error", error_msg)
            except Exception as msg_err:
                print(f"Could not show error message: {msg_err}")
                
            # Try to recover by showing the pet selection screen again
            try:
                self.show_pet_selection()
            except Exception as recover_err:
                print(f"Failed to recover to pet selection: {recover_err}")
                # If we can't recover, try to show the greeting screen
                try:
                    self.show_greeting()
                except Exception as fatal_err:
                    print(f"Fatal error: Could not recover to any screen: {fatal_err}")
                    self.root.quit()

    def force_theme_refresh_all_screens(self):
        """
        Force refresh theme on current screen.
        
        Handles any errors that might occur during theme refresh.
        """
        if not hasattr(self, 'current_screen') or not self.current_screen:
            return
            
        if hasattr(self.current_screen, 'refresh_theme'):
            try:
                self.current_screen.refresh_theme()
                self.root.update_idletasks()
            except (AttributeError, tk.TclError) as e:
                print(f"Warning: Error refreshing theme: {e}")

    def _reinitialize_app_state(self) -> bool:
        """
        Reinitialize the application state after a reset.
        
        Returns:
            bool: True if reinitialization was successful, False otherwise
        """
        try:
            # Clear existing state
            if hasattr(self, 'app_state'):
                try:
                    if hasattr(self.app_state, 'reset_data'):
                        self.app_state.reset_data()
                except Exception as e:
                    print(f"Error resetting app state: {e}")
            
            # Reinitialize the app state
            from models.app_state import AppState
            self.app_state = AppState()
            self.app_state.root = self.root
            
            # Reinitialize session manager with proper error handling
            try:
                user_data_dir = os.path.join(os.path.dirname(__file__), 'user_data')
                os.makedirs(user_data_dir, exist_ok=True)
                self.session_manager = SessionManager(
                    self.app_state,
                    os.path.join(user_data_dir, 'save_data.json')
                )
            except Exception as e:
                print(f"Error reinitializing session manager: {e}")
                # Continue with a basic session manager if initialization fails
                self.session_manager = None
            
            # Reset the music player
            try:
                if hasattr(self, 'music_player'):
                    self.music_player.stop()
                self.music_player = MusicPlayer()
            except Exception as e:
                print(f"Error reinitializing music player: {e}")
                self.music_player = None
            
            # Force garbage collection
            import gc
            gc.collect()
            
            return True
            
        except Exception as e:
            print(f"Critical error reinitializing app state: {e}")
            return False
    
    def reset_to_default_greeting(self):
        """
        Reset the application to its initial state and show the greeting screen.
        This performs a complete cleanup of all resources and resets all states.
        """
        from tkinter import messagebox
        from models.pet_state import global_pet_state, PetStage, PetEmotion
        
        # Show confirmation dialog
        if not messagebox.askyesno(
            "Reset Application",
            "Are you sure you want to reset the application?\n"
            "All your data will be permanently deleted and the pet will be reset to its initial state."
        ):
            return False
        
        try:
            # 1. Reset window title to default immediately
            if hasattr(self, 'root') and self.root:
                self.root.title("StudyPet")
                self.root.update_idletasks()
            
            # 2. Clean up current screen if it exists
            if hasattr(self, 'current_screen') and self.current_screen:
                try:
                    # Call cleanup method if it exists
                    if hasattr(self.current_screen, 'cleanup'):
                        self.current_screen.cleanup()
                    
                    # Destroy the screen's frame if it exists
                    if hasattr(self.current_screen, 'frame') and self.current_screen.frame:
                        try:
                            frame = self.current_screen.frame
                            # Check if frame still exists
                            try:
                                if not frame.winfo_exists():
                                    return
                                
                                # Unbind all events to prevent memory leaks
                                for sequence in frame.bind():
                                    try:
                                        frame.unbind_all(sequence)
                                    except tk.TclError:
                                        pass
                                
                                # Destroy all children widgets safely
                                for widget in frame.winfo_children():
                                    try:
                                        if widget.winfo_exists():
                                            widget.destroy()
                                    except (tk.TclError, AttributeError) as e:
                                        if "can't invoke" not in str(e):
                                            print(f"Warning: Error destroying widget: {e}")
                                
                                # Destroy the frame itself if it still exists
                                if frame.winfo_exists():
                                    frame.destroy()
                                    
                            except tk.TclError as e:
                                if "can't invoke" not in str(e):
                                    print(f"Warning: Error accessing frame: {e}")
                                    
                        except Exception as e:
                            print(f"Error during frame cleanup: {e}")
                    
                    # Clear the reference
                    self.current_screen = None
                    
                    # Force garbage collection
                    import gc
                    gc.collect()
                    
                except Exception as e:
                    print(f"Error during screen cleanup: {e}")
            
            # 3. Reset application state
            if hasattr(self, 'app_state') and hasattr(self.app_state, 'reset_data'):
                if not self.app_state.reset_data():
                    messagebox.showwarning(
                        "Reset Warning",
                        "Some data may not have been fully reset.\n"
                        "The application will continue with a fresh state."
                    )
            
            # 4. Reinitialize app state to get fresh data
            try:
                self.app_state = AppState.load_or_create()
                self.app_state.root = self.root
            except Exception as e:
                print(f"Error reinitializing app state: {e}")
                self.app_state = AppState()
                self.app_state.root = self.root
            
            # 5. Reset pet state to default values
            try:
                # Reset pet stage to EGG
                global_pet_state.stage = PetStage.EGG
                # Reset emotion to HAPPY
                global_pet_state.emotion = PetEmotion.HAPPY
                # Reset mastery to 0
                global_pet_state.mastery = 0
                
                # Save the reset state
                global_pet_state._save()
                print("Pet state reset to default values")
            except Exception as e:
                print(f"Error resetting pet state: {e}")
            
            # 6. Reset the session manager with new app state
            user_data_dir = os.path.join(os.path.dirname(__file__), 'user_data')
            os.makedirs(user_data_dir, exist_ok=True)
            self.session_manager = SessionManager(
                self.app_state,
                os.path.join(user_data_dir, 'save_data.json')
            )
            
            # 7. Clear any remaining references
            if hasattr(self, 'frame') and self.frame:
                try:
                    self.frame.destroy()
                    self.frame = None
                except Exception as e:
                    print(f"Error cleaning up main frame: {e}")
            
            # 8. Force update the UI to reflect changes
            if hasattr(self, 'root') and self.root:
                self.root.update_idletasks()
            
            # 9. Show the greeting screen with fresh state
            self.show_greeting()
            
            # Show success message
            messagebox.showinfo(
                "Reset Complete",
                "Successfully reset! Ready for a new adventure!"
            )
            
            return True
            
        except Exception as e:
            print(f"Error during reset: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror(
                "Reset Error",
                "An error occurred while resetting the application.\n"
                f"Error: {str(e)}\n"
                "Please restart the application."
            )
            return False

    def _on_close(self):
        """Handle application close event.
        
        Only saves the pet state if the application is being closed while
        on the main game screen. This prevents unnecessary saves when
        closing from other screens.
        """
        # Only save if we're on the main game screen
        if hasattr(self, 'current_screen') and self.current_screen is not None:
            try:
                from src.screens.main_game_screen import MainGameScreen
                if isinstance(self.current_screen, MainGameScreen):
                    from models.pet_state import global_pet_state
                    # Save pet state
                    global_pet_state.save_state()
                    print("✅ Pet state saved successfully")

                    # Flush any in-memory runtime study time into user stats
                    try:
                        if hasattr(self.current_screen, 'flush_runtime_study_time'):
                            self.current_screen.flush_runtime_study_time()
                    except Exception as flush_err:
                        print(f"⚠️ Error flushing runtime study time on close: {flush_err}")

                    # Note: global_pet_state.save_state() already saves the full app state
                    # No need to call app_state.save_data() again
                else:
                    print("ℹ️  Not saving - not on main game screen")
            except Exception as e:
                print(f"⚠️ Error saving pet state on close: {e}")
        else:
            print("ℹ️  No active screen - skipping save")
        
        # Clean up any resources
        if hasattr(self, 'music_player'):
            try:
                self.music_player.stop_playback()
            except Exception as e:
                print(f"⚠️ Error stopping music player: {e}")
        
        # Close the application
        try:
            self.root.destroy()
        except Exception as e:
            print(f"⚠️ Error destroying root window: {e}")
            # Force exit if destroy fails
            import os
            import sys
            os._exit(0)

    def run(self):
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self._on_close()
        except Exception as e:
            print(f"Unexpected error: {e}")
            self._on_close()


def main():
    app = VirtualPetStudyApp()
    app.run()


if __name__ == "__main__":
    main()
