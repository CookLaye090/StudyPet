"""
Main Game Screen - Primary interface showing pet, study controls, and navigation
"""

import os
import sys
import time
from datetime import datetime
import json
import random
import threading
import tkinter as tk

from tkinter import ttk, messagebox, simpledialog, filedialog
from pathlib import Path
from PIL import Image, ImageTk, ImageDraw, ImageFont
import pygame
import numpy as np
import cv2
from tensorflow.keras.models import load_model

from typing import Optional, Dict, List, Tuple, Callable, Any, Union

# Local imports
from utils.drowsiness_detector import DrowsinessDetector
from graphics.pet_graphics import pet_graphics
from graphics.playground_renderer import PlaygroundRenderer
from ui.simple_theme import simple_theme, create_styled_button, create_rounded_button
from ui.rounded_widgets import RoundedPanel
from ui.unified_settings import show_unified_settings
from ui.simple_chat_ui import SimpleChatUI
# from screens.scheduler_screen import SchedulerScreen  # Scheduler temporarily disabled
from utils.notifications import StudyPetNotification

class MainGameScreen:
    """Main game screen with pet display and study functionality."""
    
    def stop_study_timer(self):
        """Safely stop the unified countdown timer if it's running."""
        try:
            # Cancel any pending timer callbacks
            if hasattr(self, 'timer_id') and self.timer_id:
                if hasattr(self, 'root') and self.root:
                    try:
                        self.root.after_cancel(self.timer_id)
                    except (tk.TclError, AttributeError) as e:
                        if "can't invoke" not in str(e):
                            print(f"Error stopping timer: {e}")
                self.timer_id = None

            # Reset timer and study-session flags
            self.timer_running = False
            if hasattr(self, 'study_timer_active'):
                self.study_timer_active = False
            if hasattr(self, 'study_timer_paused'):
                self.study_timer_paused = False
        except Exception as e:
            print(f"Error in stop_study_timer: {e}")
    
    def _safe_destroy_widget(self, widget):
        """Safely destroy a widget if it exists."""
        try:
            if widget and hasattr(widget, 'winfo_exists') and widget.winfo_exists():
                # First, destroy all children
                for child in widget.winfo_children():
                    self._safe_destroy_widget(child)
                # Then destroy the widget itself
                widget.destroy()
        except (tk.TclError, AttributeError) as e:
            if "can't invoke" not in str(e) and "invalid command name" not in str(e):
                print(f"Warning: Error destroying widget: {e}")
    
    def _safe_unbind_events(self, widget):
        """
        Safely unbind all events from a widget.
        
        Args:
            widget: The Tkinter widget to unbind events from
        """
        try:
            # Check if widget exists and is a valid Tkinter widget
            if not widget or not hasattr(widget, 'winfo_exists') or not widget.winfo_exists():
                return
                
            # Check if widget has the bind method
            if not hasattr(widget, 'bind') or not callable(widget.bind):
                return
                
            # Get all bound events
            try:
                bindings = widget.bind()
                if not bindings:
                    return
                    
                # Unbind each event
                for sequence in list(bindings):  # Create a copy of the list to avoid modification during iteration
                    try:
                        # Skip empty or invalid sequences
                        if not sequence or not isinstance(sequence, str):
                            continue
                            
                        # Special handling for mouse wheel events on Windows/Linux
                        if sequence.startswith('<MouseWheel') or sequence.startswith('<Button-4>') or sequence.startswith('<Button-5>'):
                            try:
                                widget.unbind_all(sequence)
                            except tk.TclError:
                                pass
                        else:
                            widget.unbind(sequence)
                            
                    except tk.TclError as e:
                        # Ignore errors about non-existent bindings
                        if 'no binding' not in str(e).lower():
                            print(f"Warning: Error unbinding sequence '{sequence}': {e}")
                    except Exception as e:
                        print(f"Warning: Unexpected error unbinding sequence '{sequence}': {e}")
                        
            except tk.TclError as e:
                # Handle case where widget is being destroyed
                if 'bad window path name' not in str(e):
                    print(f"Warning: Error getting bindings: {e}")
                    
        except Exception as e:
            # Catch any other unexpected errors
            if 'bad window path name' not in str(e):  # Skip the specific error we're trying to prevent
                print(f"Warning: Error in _safe_unbind_events: {e}")
                import traceback
                traceback.print_exc()
    
    def _prompt_for_camera(self):
        """Show a dialog to ask if user wants to enable the camera."""
        if hasattr(self, 'camera_manager') and self.camera_manager:
            return True  # Camera already initialized
            
        response = messagebox.askyesno(
            "Enable Camera", 
            "Would you like to enable the camera for study monitoring?\n\n"
            "This will help track your study focus and provide better insights.",
            parent=self.parent
        )
        
        if not response:
            return False
            
        # Show camera selection dialog
        available_cameras = self._get_available_cameras()
        if not available_cameras:
            messagebox.showwarning(
                "No Cameras Found",
                "No cameras were detected on your system. Study monitoring will be disabled.",
                parent=self.parent
            )
            return False
            
        # If only one camera, use it automatically
        if len(available_cameras) == 1:
            return self._initialize_camera(0)
            
        # Show camera selection dialog
        camera_choice = self._show_camera_selection(available_cameras)
        if camera_choice is None:  # User cancelled
            return False
            
        return self._initialize_camera(camera_choice)

    def _get_available_cameras(self, max_cameras=5):
        """Detect available cameras on the system."""
        available = []
        for i in range(max_cameras):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available.append(f"Camera {i}")
                cap.release()
        return available

    def _show_camera_selection(self, cameras):
        """Show a dialog to select which camera to use."""
        selection = tk.Toplevel(self.parent)
        selection.title("Select Camera")
        selection.transient(self.parent)
        selection.grab_set()
        
        # Center the window
        window_width = 300
        window_height = 150
        screen_width = selection.winfo_screenwidth()
        screen_height = selection.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        selection.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Add label
        ttk.Label(
            selection, 
            text="Select a camera to use:",
            padding=10
        ).pack()
        
        # Add camera selection
        selected_cam = tk.IntVar(value=0)
        for i, cam in enumerate(cameras):
            rb = ttk.Radiobutton(
                selection,
                text=cam,
                variable=selected_cam,
                value=i
            )
            rb.pack(anchor='w', padx=20)
        
        # Add buttons
        btn_frame = ttk.Frame(selection)
        btn_frame.pack(pady=10)
        
        result = {"choice": None}
        
        def on_ok():
            result["choice"] = selected_cam.get()
            selection.destroy()
        
        def on_cancel():
            selection.destroy()
        
        ttk.Button(btn_frame, text="OK", command=on_ok).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side='left', padx=5)
        
        selection.wait_window()
        return result["choice"]

    def _initialize_camera(self, camera_index):
        """Initialize the selected camera."""
        try:
            from utils.camera import CameraHandler
            self.camera_manager = CameraHandler(camera_index=camera_index)
            if not self.camera_manager.start():
                raise RuntimeError("Could not start camera")
            return True
        except Exception as e:
            print(f"Error initializing camera: {e}")
            messagebox.showerror(
                "Camera Error",
                f"Could not initialize camera: {str(e)}",
                parent=self.parent
            )
            return False

    def cleanup(self):
        """
        Clean up all resources, timers, and references.
        This should be called before destroying the screen.
        """
        try:
            # 1. First stop any active timers and animations
            if hasattr(self, 'stop_study_timer'):
                try:
                    self.stop_study_timer()
                except Exception as e:
                    print(f"Error in stop_study_timer: {e}")
            
            # 2. Stop any background threads
            if hasattr(self, 'stop_drowsiness_detection'):
                try:
                    self.stop_drowsiness_detection()
                except Exception as e:
                    print(f"Error in stop_drowsiness_detection: {e}")
            
            # 3. Clear any scheduled callbacks
            if hasattr(self, 'timer_id') and self.timer_id:
                try:
                    if hasattr(self, 'root') and self.root and hasattr(self.root, 'after'):
                        self.root.after_cancel(self.timer_id)
                except (tk.TclError, AttributeError) as e:
                    if "can't invoke" not in str(e):
                        print(f"Error cancelling timer: {e}")
                self.timer_id = None
            
            # 4. Clean up camera and other hardware resources
            if hasattr(self, 'camera_manager') and self.camera_manager:
                try:
                    self.camera_manager.cleanup()
                except Exception as e:
                    print(f"Error cleaning up camera manager: {e}")
                self.camera_manager = None
            
            if hasattr(self, 'drowsiness_detector') and self.drowsiness_detector:
                try:
                    self.drowsiness_detector.cleanup()
                except Exception as e:
                    print(f"Error cleaning up drowsiness detector: {e}")
                self.drowsiness_detector = None
            
            # 5. Clean up playground renderer
            if hasattr(self, 'playground_renderer') and self.playground_renderer:
                try:
                    # Store reference to canvas before cleanup
                    canvas = getattr(self.playground_renderer, 'canvas', None)
                    
                    # Call cleanup on the renderer
                    if hasattr(self.playground_renderer, 'cleanup'):
                        self.playground_renderer.cleanup()
                    
                    # Additional canvas cleanup if it still exists
                    if canvas and hasattr(canvas, 'winfo_exists') and canvas.winfo_exists():
                        try:
                            canvas.delete('all')
                        except tk.TclError as e:
                            if "can't invoke" not in str(e):
                                print(f"Error cleaning up canvas: {e}")
                except Exception as e:
                    print(f"Error cleaning up playground renderer: {e}")
                finally:
                    self.playground_renderer = None
            
            # 6. Clean up chat interface
            if hasattr(self, 'chat_interface') and self.chat_interface:
                try:
                    if hasattr(self.chat_interface, 'cleanup'):
                        self.chat_interface.cleanup()
                except Exception as e:
                    print(f"Error cleaning up chat interface: {e}")
                self.chat_interface = None
            
            # 7. Clean up frame and its widgets (do this after cleaning up children)
            if hasattr(self, 'frame') and self.frame:
                try:
                    # First, unbind all events
                    self._safe_unbind_events(self.frame)
                    
                    # Then destroy all child widgets
                    self._safe_destroy_widget(self.frame)
                    
                    # Finally, destroy the frame itself if it still exists
                    if hasattr(self.frame, 'winfo_exists') and self.frame.winfo_exists():
                        try:
                            self.frame.destroy()
                        except tk.TclError as e:
                            if "can't invoke" not in str(e):
                                print(f"Error destroying frame: {e}")
                    
                    # Clear the reference
                    self.frame = None
                    
                except Exception as e:
                    print(f"Error during frame cleanup: {e}")
                    
                    print(f"Error during widget cleanup: {e}")
            
            # Clean up any remaining widgets that might be direct children of parent
            if hasattr(self, 'parent') and self.parent:
                try:
                    for widget in self.parent.winfo_children():
                        if widget != self.frame:  # Skip frame if it's still there
                            self._safe_destroy_widget(widget)
                except Exception as e:
                    print(f"Error cleaning up parent widgets: {e}")
            
            # Clear all widget lists and references
            for attr in ['font_widgets', 'timer_widgets', 'control_widgets']:
                if hasattr(self, attr):
                    getattr(self, attr).clear()
            
            # Clear other references
            for attr in ['app_state', 'music_player', 'app_controller', 'root', 'parent']:
                if hasattr(self, attr):
                    setattr(self, attr, None)
            
            # Clean up any remaining references
            if hasattr(self, '_study_stop_event') and self._study_stop_event:
                try:
                    self._study_stop_event.set()
                except:
                    pass
            
            # Force garbage collection
            import gc
            gc.collect()
            
        except Exception as e:
            print(f"Error during cleanup: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Ensure we don't keep any circular references
            if hasattr(self, 'parent') and self.parent:
                try:
                    self.parent.unbind('<Configure>', None)
                except:
                    pass
    
    def __init__(self, parent, app_state, music_player, app_controller=None):
        """Initialize the main game screen.
        
        Args:
            parent: Parent widget
            app_state: Application state object
            music_player: Music player instance
            app_controller: Main application controller
        """
        self.parent = parent
        self.app_state = app_state
        self.music_player = music_player
        self.app_controller = app_controller
        self.frame = None
        self.playground_canvas = None
        self.playground_renderer = None
        self.pet_sprite = None
        self.pet_image = None
        self.pet_photo = None
        self.pet_image_id = None
        self.pet_x = 100
        self.pet_y = 100
        self.pet_speed = 5
        self.pet_direction = 1
        self.pet_state = "idle"
        self.pet_frame = 0
        self.pet_frame_time = 0
        self.pet_frame_delay = 0.1
        self.pet_animation = None
        self.pet_animation_frame = 0
        self.pet_animation_frames = []
        self.pet_animation_loop = False
        self.pet_animation_speed = 0.1
        self.pet_animation_time = 0
        self.pet_animation_callback = None
        self.pet_animation_callback_args = ()
        self.pet_animation_callback_kwargs = {}
        self.pet_animation_callback_called = False
        self.pet_animation_callback_delay = 0
        self.pet_animation_callback_time = 0
        self.pet_animation_callback_called_time = 0
        self.pet_animation_callback_called_delay = 0
        self.pet_animation_callback_called_time_delay = 0
        self.pet_animation_callback_called_delay_time = 0
        self.pet_animation_callback_called_delay_time_delay = 0
        
        # Drowsiness detection attributes
        self.drowsiness_detector = None
        self.detection_active = False
        self.developer_mode = False  # Set this based on your app's settings
        self.study_thread = None
        self._stop_detection = threading.Event()
        self._last_alert_time = 0
        self._drowsiness_alert_active = False
        
        # Focus tracking and logging
        self.predictions = []  # Store the last 10 predictions (6s each = 1 minute)
        self.last_prediction_time = 0
        self.prediction_interval = 6  # seconds between predictions
        self.log_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs", "camera_log.txt")
        
        # Create logs directory if it doesn't exist
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        # Initialize log file with header if it doesn't exist
        if not os.path.exists(self.log_file):
            # Create an empty file so logs are plain timestamp-status lines
            open(self.log_file, 'a').close()

        # Emotion tracking (parallel to focus tracking)
        self.emotion_predictions = []       # Store last 10 emotion indices
        self.last_emotion_time = 0.0
        self.emotion_prediction_interval = 6  # seconds between emotion samples

        # Emotion model (optional)
        self.emotion_model = None
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            emotion_model_path = os.path.join(project_root, "models", "emotion_detection_model.keras")
            if os.path.exists(emotion_model_path):
                print(f"Loading emotion model from: {emotion_model_path}")
                self.emotion_model = load_model(emotion_model_path)
            else:
                print(f"Emotion model not found at {emotion_model_path}")
        except Exception as e:
            print(f"Warning: Could not load emotion model: {e}")
            self.emotion_model = None
        
        # Drowsiness prediction storage (unified variables)
        self.latest_drowsy_status = False
        self.latest_drowsy_confidence = 0.0
        self.latest_awake_confidence = 0.0
        self.drowsiness_status_var = None  # Will be initialized in setup_ui
        
        # Runtime study tracking (seconds during this app instance)
        self.runtime_study_seconds = 0
        
        # Initialize pygame for audio
        pygame.mixer.init()
        
        # Initialize theme and colors before setting up UI
        self.theme = simple_theme
        self.colors = self.theme.colors
        
        # Set up evolution callback
        from models.pet_state import global_pet_state
        try:
            global_pet_state.on_evolve = self._handle_pet_evolution
        except AttributeError:
            print("Warning: _handle_pet_evolution not available on MainGameScreen; evolution callbacks disabled.")
        
        try:
            # Developer mode state
            self.developer_mode = False
            
            # Initialize theme based on selected pet
            self.setup_pet_theme()
            self.colors = self.theme.colors
            
            # Study session state (flags only; timing uses unified countdown timer)
            self.study_timer_active = False
            self.study_timer_paused = False
            self.study_session_duration = 25  # Default duration in minutes
            
            self.timer_running = False  # Unified timer state
            self.timer_id = None  # For tracking scheduled updates
            self.total_duration_seconds = 25 * 60  # Total duration in seconds (default 25 minutes)
            self.time_remaining = self.total_duration_seconds  # Initialize with full duration
            
            # Preset durations (minutes) for quick-start timer popup
            self.timer_presets = [10, 15, 20, 25, 30]
            
            # UI variables
            self.timer_var = tk.StringVar(value="25:00")
            self.study_progress_var = tk.StringVar(value="Ready to study!")
            self.status_var = tk.StringVar(value="Timer ready")
            self.drowsiness_status_var = tk.StringVar(value="AWAKE")  # Drowsiness status display
            
            # Camera and drowsiness detection
            self.camera_manager = None  # Will hold the camera manager instance
            self.drowsiness_detection_active = False
            self.drowsiness_thread = None
            self._drowsiness_stop_event = threading.Event()
            self.drowsy_start_time = 0
            self.consecutive_drowsy_sessions = 0
            self.speech_bubble_visible = False
            self.speech_bubble_image = None
            self.speech_bubble_label = None
            self.encouraging_messages = [
                "Stay focused! You're doing great!",
                "Keep it up! Just a bit longer!",
                "You've got this! Stay with me!",
                "Don't give up! You're almost there!",
                "Take a deep breath and refocus!"
            ]
            self.rest_messages = [
                "Time for a break! You've earned it.",
                "Let's take a short break and come back refreshed!",
                "Your brain needs a rest. Take a short walk!",
                "A quick break now will help you focus better later!"
            ]
            
            # Chat system placeholder (disabled)
            self.chat_interface = None
            self.chat_locked = None  # Track whether chat is currently locked (EGG stage)
            self.chat_panel = None  # Reference to chat panel for dynamic updates
            
            # Playground system
            self.playground_renderer = None
            self.playground_canvas = None
            
            # Dynamic font sizing system
            self.font_widgets = []  # Store widgets with dynamic fonts
            self.base_font_sizes = {}  # Store base font sizes for scaling

            # Scheduler temporarily disabled
            # self.schedule_plan = None  # e.g., {"mode": "quick", "focus": 25}
            # self.scheduled_session_ready = False
            
            # Set up the screen after all initialization is complete
            self.setup_ui()
            self.setup_dynamic_fonts()
            self.update_pet_info_display()
            self.update_music_button_states()
            
            # Bind window resize event for dynamic behaviors
            self._resize_after_id = None
            self.parent.bind('<Configure>', self.handle_window_resize)

            if hasattr(self.app_controller, 'session_manager'):
                self.app_controller.session_manager.set_ui_callback(self.update_session_ui)

        except Exception as e:
            import traceback
            print(f"❌ Error initializing MainGameScreen: {e}")
            print("Full traceback:")
            traceback.print_exc()
            # Re-raise to let the main app handle it
            raise e
            
    def previous_track_and_update(self):
        """Go to previous track and update UI."""
        if hasattr(self, 'music_player'):
            self.music_player.previous_track()
            self.update_music_display()
    
    def next_track_and_update(self):
        """Go to next track and update UI."""
        if hasattr(self, 'music_player'):
            self.music_player.next_track()
            self.update_music_display()
    
    def update_music_display(self):
        """Update the music display with current track info."""
        if hasattr(self, 'music_player'):
            current_track = self.music_player.get_current_track_info()
            if hasattr(self, 'music_display') and current_track:
                self.music_display.config(text=current_track.get('name', 'No track'))
    
    def toggle_music_playback(self):
        """Toggle music playback and update the play/pause button icon."""
        if not hasattr(self, 'music_player'):
            return
            
        if self.music_player.is_playing():
            self.music_player.pause()
            # Update button to show play icon
            if hasattr(self, 'play_pause_btn'):
                self.play_pause_btn.config(text="▶️")
        else:
            self.music_player.play()
            # Update button to show pause icon
            if hasattr(self, 'play_pause_btn'):
                self.play_pause_btn.config(text="⏸️")
                
    def update_music_button_states(self):
        """Update the state of music control buttons based on current state."""
        if not hasattr(self, 'music_player'):
            return
            
        # Update play/pause button
        if hasattr(self, 'play_pause_btn'):
            if self.music_player.is_playing():
                self.play_pause_btn.config(text="⏸️")
            else:
                self.play_pause_btn.config(text="▶️")
                
        # Update track info display
        self.update_music_display()
        
    def add_mastery(self, amount=50):
        """
        Add mastery points to the current pet using the global state.
        
        Args:
            amount (int): Amount of mastery to add (default: 50)
        """
        from models.pet_state import global_pet_state
        
        try:
            # Store old stage to check for evolution
            old_stage = global_pet_state.stage
            
            # Add mastery (this will handle the cap automatically)
            global_pet_state.mastery += amount
            
            # Update the UI
            self.update_pet_info_display()
            
            # Show a small notification
            if hasattr(self, 'show_notification'):
                self.show_notification(f"+{amount} Mastery!")
            
            # Check for evolution
            if global_pet_state.stage != old_stage:
                messagebox.showinfo(
                    "Pet Evolved!",
                    f"Your pet has evolved to {global_pet_state.stage.name.replace('_', ' ').title()}!"
                )
                
            print(f"Added {amount} mastery points. New total: {global_pet_state.mastery}")
            
        except Exception as e:
            print(f"Error updating mastery: {e}")
            import traceback
            traceback.print_exc()
            
    def reset_mastery(self):
        """Reset the pet's mastery to zero using the global state."""
        from models.pet_state import global_pet_state
        
        try:
            # Reset Mastery to 0
            global_pet_state.mastery = 0
            
            # Update the UI
            self.update_pet_info_display()
            
            # Show a small notification
            if hasattr(self, 'show_notification'):
                self.show_notification("Mastery reset to 0!")
                
            print("Reset pet's mastery to 0")
            
        except Exception as e:
            print(f"Error resetting Mastery: {e}")
            import traceback
            traceback.print_exc()
            
    def set_pet_stage(self):
        """Open a dialog to set the pet's stage directly."""
        if not hasattr(self, 'app_state') or not self.app_state:
            print("Error: App state not available")
            return
            
        current_pet = self.app_state.get_current_pet()
        if not current_pet:
            print("Error: No active pet found")
            return
            
        try:
            # Get available stages
            if hasattr(current_pet, 'get_available_stages'):
                available_stages = current_pet.get_available_stages()
            else:
                available_stages = ["EGG", "BABY", "ADULT"]
                
            current_stage = getattr(current_pet, 'stage', available_stages[0] if available_stages else "EGG")
            
            # Create dialog
            dialog = tk.Toplevel(self.parent)
            dialog.title("Set Pet Stage")
            dialog.transient(self.parent)
            dialog.grab_set()
            
            # Center the dialog
            dialog.geometry(f"300x150+{self.parent.winfo_x() + 100}+{self.parent.winfo_y() + 100}")
            
            # Stage selection
            tk.Label(dialog, text="Select Stage:").pack(pady=5)
            
            stage_var = tk.StringVar(value=current_stage)
            stage_menu = ttk.Combobox(dialog, textvariable=stage_var, values=available_stages, state="readonly")
            stage_menu.pack(pady=5, padx=20, fill='x')
            
            # Buttons
            btn_frame = tk.Frame(dialog)
            btn_frame.pack(pady=10)
            
            def apply_changes():
                new_stage = stage_var.get()
                if new_stage and new_stage != current_stage:
                    setattr(current_pet, 'stage', new_stage)
                    self.update_pet_info_display()
                    
                    if hasattr(self, 'playground_canvas'):
                        # Just call with pet_type, stage and emotion will be taken from global_pet_state
                        self._init_playground_immediately(current_pet.pet_type)
                    
                    if hasattr(self, 'show_notification'):
                        self.show_notification(f"Stage set to {new_stage}")
                        
                    print(f"Pet stage set to {new_stage}")
                
                dialog.destroy()
            
            ttk.Button(btn_frame, text="Apply", command=apply_changes).pack(side='left', padx=5)
            ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side='right', padx=5)
            
            dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
            
        except Exception as e:
            print(f"Error setting pet stage: {e}")
            if hasattr(self, 'show_notification'):
                self.show_notification(f"Error: {str(e)}")
                
    def set_pet_emotion(self):
        """Open a dialog to set the pet's emotion."""
        if not hasattr(self, 'app_state') or not self.app_state:
            print("Error: App state not available")
            return
            
        current_pet = self.app_state.get_current_pet()
        if not current_pet:
            print("Error: No active pet found")
            return
            
        try:
            # Define available emotions
            available_emotions = ["HAPPY", "SAD", "WORRIED", "HUNGRY", "ANGRY"]
            current_emotion = getattr(current_pet, 'emotion', 'HAPPY')
            
            # Create dialog
            dialog = tk.Toplevel(self.parent)
            dialog.title("Set Pet Emotion")
            dialog.transient(self.parent)
            dialog.grab_set()
            
            # Center the dialog
            dialog.geometry(f"300x150+{self.parent.winfo_x() + 100}+{self.parent.winfo_y() + 100}")
            
            # Emotion selection
            tk.Label(dialog, text="Select Emotion:").pack(pady=5)
            
            emotion_var = tk.StringVar(value=current_emotion)
            emotion_menu = ttk.Combobox(dialog, textvariable=emotion_var, values=available_emotions, state="readonly")
            emotion_menu.pack(pady=5, padx=20, fill='x')
            
            # Buttons
            btn_frame = tk.Frame(dialog)
            btn_frame.pack(pady=10)
            
            def apply_changes():
                new_emotion = emotion_var.get()
                if new_emotion and new_emotion != current_emotion:
                    setattr(current_pet, 'emotion', new_emotion)
                    self.update_pet_info_display()
                    
                    if hasattr(self, 'playground_canvas'):
                        # Just call with pet_type, stage and emotion will be taken from global_pet_state
                        self._init_playground_immediately(current_pet.pet_type)
                    
                    if hasattr(self, 'show_notification'):
                        self.show_notification(f"Emotion set to {new_emotion}")
                        
                    print(f"Pet emotion set to {new_emotion}")
                
                dialog.destroy()
            
            ttk.Button(btn_frame, text="Apply", command=apply_changes).pack(side='left', padx=5)
            ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side='right', padx=5)
            
            dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
            
        except Exception as e:
            print(f"Error setting pet emotion: {e}")
            if hasattr(self, 'show_notification'):
                self.show_notification(f"Error: {str(e)}")
                
    def update_pet_info_display(self):
        """Update the pet information display in the status panel."""
        from models.pet_state import global_pet_state
        
        if not hasattr(self, 'app_state') or not self.app_state:
            return
            
        current_pet = self.app_state.get_current_pet()
        if not current_pet or not hasattr(self, 'status_labels'):
            return
            
        try:
            # Get pet attributes
            name = getattr(current_pet, 'name', 'Unnamed Pet')
            level = getattr(current_pet, 'level', 1)
            
            # Get values from global state
            stage = global_pet_state.stage.name.replace('_', ' ').title()
            emotion = global_pet_state.emotion.name.title()
            mastery = global_pet_state.mastery
            max_mastery = global_pet_state.mastery_cap
            
            # Update status labels if they exist
            if hasattr(self, 'status_labels'):
                labels = self.status_labels
                if 'name' in labels and labels['name'].winfo_exists():
                    labels['name'].config(text=f"Name: {name}")
                if 'level' in labels and labels['level'].winfo_exists():
                    labels['level'].config(text=f"Level: {level}")
                if 'stage' in labels and labels['stage'].winfo_exists():
                    labels['stage'].config(text=f"Stage: {stage}")
                if 'emotion' in labels and labels['emotion'].winfo_exists():
                    labels['emotion'].config(text=f"Mood: {emotion}")
                if 'mastery' in labels and labels['mastery'].winfo_exists():
                    labels['mastery'].config(
                        text=f"Mastery: {mastery}/{max_mastery} "
                             f"({global_pet_state.mastery_percentage:.1f}%)"
                    )
            
            # Update window title
            if hasattr(self, 'parent') and hasattr(self.parent, 'title'):
                self.parent.title(f"StudyPet - {name}")
                
            # Update taskbar name label if it exists
            if hasattr(self, 'taskbar_name_label') and self.taskbar_name_label.winfo_exists():
                self.taskbar_name_label.config(text=name)
                
            # Update mastery progress bar if it exists
            if hasattr(self, 'mastery_progress') and self.mastery_progress.winfo_exists():
                # Ensure we don't exceed 100% in the progress bar
                percentage = min(100, global_pet_state.mastery_percentage)
                self.mastery_progress['value'] = percentage
                
            # Update taskbar evolution progress bar if it exists
            if hasattr(self, 'taskbar_evolution_progress') and self.taskbar_evolution_progress.winfo_exists():
                # Ensure we don't exceed 100% in the progress bar
                percentage = min(100, global_pet_state.mastery_percentage)
                self.taskbar_evolution_progress['value'] = percentage
                
        except Exception as e:
            print(f"Error updating pet info: {e}")
            import traceback
            traceback.print_exc()

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


    # Study timer related methods have been removed
    
    # Timer related methods have been removed
    
    # Study timer panel refresh method has been removed
    
    def update_session_ui(self, status_text="", show_continue=False):
        """Update the session UI elements."""
        try:
            if hasattr(self, 'session_status_label'):
                if status_text:
                    self.session_status_label.config(text=status_text)
            
            s = getattr(self.app_state, 'study_session', {})
            if s.get('active') and hasattr(self, 'session_progress'):
                total_blocks = len((s.get('schedule') or {}).get('blocks', [])) or 1
                completed = len(s.get('completed_blocks', []))
                progress = (completed / total_blocks) * 100
                self.session_progress['value'] = progress
            
            # Update button states
            if hasattr(self, 'btn_start_session') and hasattr(self, 'btn_continue'):
                has_schedule = bool(s.get('schedule'))
                is_active = s.get('active', False)
                
                self.btn_start_session.config(
                    state=tk.NORMAL if has_schedule and not is_active else tk.DISABLED
                )
                self.btn_continue.config(
                    state=tk.NORMAL if show_continue and is_active else tk.DISABLED
                )
                
                # Manage countdown frame visibility
                if hasattr(self, 'countdown_frame'):
                    if show_continue:
                        # Show the countdown frame with the current status text
                        self.countdown_label.config(text=status_text)
                        if not self.countdown_frame.winfo_ismapped():
                            self.countdown_frame.pack(fill='x', pady=5, after=self.session_status_label)
                    else:
                        # Hide the countdown frame
                        if self.countdown_frame.winfo_ismapped():
                            self.countdown_frame.pack_forget()
                        
        except Exception as e:
            print(f"Error updating timer UI: {e}")
            import traceback
            traceback.print_exc()
    
    def start_session(self):
        """Start a new study session."""
        s = getattr(self.app_state, 'study_session', {})
        schedule = s.get('schedule', {})
        blocks = schedule.get('blocks', [])
        
        if not blocks:
            messagebox.showerror("Error", "No schedule selected")
            return
            
        # Show session summary
        summary = "Study Session Schedule:\\n\\n"
        for i, b in enumerate(blocks, 1):
            block_type = 'Study' if b.get('type') == 'study' else 'Break'
            summary += f"{i}. {block_type}: {b.get('duration', 0)} minutes\\n"
            
        total_minutes = sum(b.get('duration', 0) for b in blocks)
        summary += f"\\nTotal duration: {total_minutes} minutes\\n\\n"
        summary += "You'll have 5 minutes to confirm each block. Start session?"
        
        if messagebox.askyesno("Start Session", summary):
            if hasattr(self, 'app_controller') and hasattr(self.app_controller, 'session_manager'):
                if self.app_controller.session_manager.start_session():
                    self.update_session_ui("Starting first block...")
                    return
            messagebox.showerror("Error", "Failed to start session")
    
    def confirm_next_block(self):
        """Confirm continuing to the next block."""
        if hasattr(self, 'app_controller') and hasattr(self.app_controller, 'session_manager'):
            if self.app_controller.session_manager.confirm_next_block():
                self.update_session_ui("Starting next block...")
    
    # Scheduler temporarily disabled
    # def open_scheduler_window(self):
    #     """Open the scheduler window."""
    #     win = tk.Toplevel(self.parent)
    #     win.title("Scheduler")
    #     win.geometry("700x600")
        
    #     # Create the scheduler screen
    #     # from screens.scheduler_screen import SchedulerScreen  # Scheduler temporarily disabled
    #     SchedulerScreen(win, self.app_state)
        
    #     def on_close():
    #         win.destroy()
    #         if hasattr(self, '_refresh_study_timer_panel'):
    #             self._refresh_study_timer_panel()
                
    #     win.protocol("WM_DELETE_WINDOW", on_close)

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

                if pet_type_str:
                    # Just call with pet_type, stage and emotion will be taken from global_pet_state
                    self._init_playground_immediately(pet_type_str)
                else:
                    print("Warning: Missing pet type for playground initialization")
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
            ("📊 Stats", lambda: self.switch_tab("stats")),
            ("🎵 Music", lambda: self.switch_tab("music")),
            ("⚙️ Settings", lambda: self.switch_tab("settings"))
        ]

        for text, command in nav_buttons:
            btn = create_rounded_button(
                nav_frame,
                text,
                command=command,
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

        # Music controls frame remains for other controls

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

        # Status content (no scrolling)
        self.status_content = tk.Frame(self.status_panel, bg=self.colors["bg_secondary"])  # Use pet-specific background
        # Initially hidden until expanded

        # Initialize status labels dictionary if it doesn't exist
        if not hasattr(self, 'status_labels'):
            self.status_labels = {}
            
        # Contents of status panel
        status_items = ["name", "stage", "emotion", "mastery"]
        panel_bg = self.colors["bg_secondary"]  # Use pet-specific background
        
        # Clear existing labels if they exist
        for widget in self.status_content.winfo_children():
            widget.destroy()
            
        # Create new labels with just the values (no field names)
        for item in status_items:
            # Create label for the value only
            value_label = tk.Label(
                self.status_content,
                text="...",
                font=("Arial", 10),
                bg=panel_bg,
                fg=self.colors["text_dark"],
                anchor="w"
            )
            value_label.pack(fill="x", pady=2, padx=5)
            self.status_labels[item] = value_label
        
        # Make sure the status content is packed and visible
        self.status_content.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Force an immediate update of the pet info display using parent's after method
        if hasattr(self, 'parent') and hasattr(self.parent, 'after'):
            self.parent.after(100, self.update_pet_info_display)
            
        # Add developer tools section
        self.dev_tools_frame = tk.Frame(self.status_content, bg=panel_bg, bd=1, relief="groove")
        
        # Developer tools header
        self.dev_header = tk.Label(
            self.dev_tools_frame,
            text="🔧 Developer Tools",
            font=("Arial", 9, "bold"),
            bg=panel_bg,
            fg=self.colors["text_dark"]
        )
        self.dev_header.pack(anchor="w", pady=(5, 2), padx=5)
        
        # Developer buttons frame - using grid for better layout control
        self.dev_buttons_frame = tk.Frame(self.dev_tools_frame, bg=panel_bg)
        self.dev_buttons_frame.pack(fill="x", padx=5, pady=(0, 5))
        
        # Top row: Mastery controls
        self.mastery_frame = tk.Frame(self.dev_buttons_frame, bg=panel_bg)
        self.mastery_frame.pack(fill="x", pady=(0, 5))
        
        # +50 Mastery button
        self.add_mastery_btn = create_rounded_button(
            self.mastery_frame,
            text="+50 Mastery",
            command=self.add_mastery,
            style="accent",
            radius=15,
            padding=(8, 4),
            font=("Arial", 9, "bold")
        )
        self.add_mastery_btn.pack(side="left", expand=True, fill="x", padx=(0, 3))
        
        # Reset Mastery button
        self.reset_mastery_btn = create_rounded_button(
            self.mastery_frame,
            text="Reset Mastery",
            command=self.reset_mastery,
            style="accent",
            radius=15,
            padding=(8, 4),
            font=("Arial", 9, "bold")
        )
        self.reset_mastery_btn.pack(side="right", expand=True, fill="x", padx=(3, 0))
        
        # Middle row: Evolution controls
        self.evolution_frame = tk.Frame(self.dev_buttons_frame, bg=panel_bg)
        self.evolution_frame.pack(fill="x", pady=(0, 5))
        
        # Force Evolve button
        self.force_evolve_btn = create_rounded_button(
            self.evolution_frame,
            text="Force Evolve",
            command=lambda: hasattr(self, 'force_evolve') and self.force_evolve(),
            style="accent",
            radius=15,
            padding=(8, 4),
            font=("Arial", 9, "bold")
        )
        self.force_evolve_btn.pack(side="left", expand=True, fill="x", padx=(0, 3))
        
        # Set Stage button
        self.set_stage_btn = create_rounded_button(
            self.evolution_frame,
            text="Set Stage",
            command=self.set_pet_stage,
            style="accent",
            radius=15,
            padding=(8, 4),
            font=("Arial", 9, "bold")
        )
        self.set_stage_btn.pack(side="right", expand=True, fill="x", padx=(3, 0))
        
        # Bottom row: Emotion control
        self.emotion_frame = tk.Frame(self.dev_buttons_frame, bg=panel_bg)
        self.emotion_frame.pack(fill="x", pady=(0, 5))
        
        # Set Emotion button (centered in its own row)
        self.set_emotion_btn = create_rounded_button(
            self.emotion_frame,
            text="Set Emotion",
            command=self.set_pet_emotion,
            style="accent",
            radius=15,
            padding=(8, 4),
            font=("Arial", 9, "bold")
        )
        self.set_emotion_btn.pack(expand=True, fill="x")
        
        # Add some space at the bottom
        tk.Frame(self.status_content, height=10, bg=self.colors["bg_secondary"]).pack(fill='x')
        
        # Initially hide developer tools
        self.dev_tools_frame.pack_forget()
        
        # Pack status content inside status panel
        self.status_content.pack(fill="both", expand=True)

        # Study Timer (next to chat, top-right, collapsible)
        self.timer_expanded = False
        self.timer_container = tk.Frame(self.frame, bg=self.colors["bg_main"], bd=0)
        # Place to the left of chat (chat is 250px wide + margins)
        # Increased width from 250 to 350, adjusted x position to account for wider panel
        self.timer_container.place(relx=1.0, x=-620, y=60, width=350, height=40)
        self.timer_header = tk.Frame(self.timer_container, bg=self.colors["bg_secondary"], relief="flat", bd=0, cursor="hand2")
        self.timer_header.pack(fill="x")
        self.timer_header.bind("<Button-1>", self.toggle_timer_panel)
        self.timer_header_label = tk.Label(
            self.timer_header,
            text="⏱️ Study Timer ▼",
            font=("Arial", 10, "bold"),
            bg=self.colors["bg_secondary"],
            fg=self.colors["text_dark"],
            cursor="hand2"
        )
        self.timer_header_label.pack(pady=2)
        self.timer_header_label.bind("<Button-1>", self.toggle_timer_panel)

        self.timer_panel = tk.Frame(self.timer_container, bg=self.colors["bg_secondary"])
        self.timer_content = tk.Frame(self.timer_panel, bg=self.colors["bg_secondary"])
        self.timer_content.pack(fill='both', expand=True)
        
        # Create unified timer interface
        self.create_timer_ui(self.timer_content)
        
        # Show timer content by default since we're removing scrolling

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

        # Chat content frame (no scrolling)
        self.chat_content = tk.Frame(self.chat_panel, bg=self.colors["bg_secondary"])
        # Initially hidden, contents created in create_chat_ui
        if hasattr(self, "create_chat_ui"):
            self.create_chat_ui(self.chat_content)

        # Initialize chat lock state
        self.chat_locked = None  # Will be set based on pet stage
        self.update_chat_lock_state(force=True)

        # === LAYER 3: Bottom overlay taskbar (with pet name + evolution progress) ===
        try:
            self.taskbar = tk.Frame(self.frame, bg=self.colors["bg_secondary"], bd=0, highlightthickness=0)
            # Near bottom, with margins; overlay style
            self.taskbar.place(relx=0.5, rely=1.0, anchor='s', relwidth=0.9, height=56, y=-10)

            # Left: Pet info frame
            left = tk.Frame(self.taskbar, bg=self.colors["bg_secondary"]) 
            left.pack(side="left", padx=10)
            
            # Pet name
            name_frame = tk.Frame(left, bg=self.colors["bg_secondary"])
            name_frame.pack(side="top", fill="x")
            tk.Label(name_frame, text="Name:", font=("Arial", 9, "bold"), 
                    bg=self.colors["bg_secondary"], 
                    fg=self.colors["text_medium"]).pack(side="left", padx=(0,4))
            self.taskbar_name_label = tk.Label(name_frame, text="...", 
                                             font=("Arial", 11, "bold"), 
                                             bg=self.colors["bg_secondary"], 
                                             fg=self.colors["text_dark"]) 
            self.taskbar_name_label.pack(side="left")
            
            # Empty frame for consistent spacing
            tk.Frame(left, height=10, bg=self.colors["bg_secondary"]).pack()

            # Center-left: Mastery progress bar
            center_left = tk.Frame(self.taskbar, bg=self.colors["bg_secondary"]) 
            center_left.pack(side="left", fill="x", expand=True, padx=10)
            
            # Evolution Progress label
            tk.Frame(center_left, height=2, bg=self.colors["bg_secondary"]).pack()  # Spacer
            tk.Label(center_left, text="Evolution Progress", font=("Arial", 9, "bold"), 
                    bg=self.colors["bg_secondary"], 
                    fg=self.colors["text_medium"],
                    anchor="w").pack(fill="x")
            
            ttk.Style().configure("Taskbar.Horizontal.TProgressbar", thickness=8)
            self.taskbar_evolution_progress = ttk.Progressbar(
                center_left, 
                mode='determinate', 
                style="Taskbar.Horizontal.TProgressbar",
                maximum=100  # Set maximum to 100 for percentage
            )
            self.taskbar_evolution_progress.pack(fill="x", pady=(2, 0))

            # Center-right: XP progress bar
            center_right = tk.Frame(self.taskbar, bg=self.colors["bg_secondary"]) 
            center_right.pack(side="left", fill="x", expand=True, padx=10)
            
            # Timer Progress label
            tk.Frame(center_right, height=2, bg=self.colors["bg_secondary"]).pack()  # Spacer
            tk.Label(center_right, text="Timer Progress", font=("Arial", 9, "bold"), 
                   bg=self.colors["bg_secondary"], 
                   fg=self.colors["text_medium"],
                   anchor="w").pack(fill="x")
            
            ttk.Style().configure("TaskbarTimer.Horizontal.TProgressbar", thickness=8)
            self.taskbar_timer_progress = ttk.Progressbar(
                center_right, 
                mode='determinate', 
                style="TaskbarTimer.Horizontal.TProgressbar"
            )
            self.taskbar_timer_progress.pack(fill="x", pady=(2, 0))

            # Right spacer
            tk.Frame(self.taskbar, bg=self.colors["bg_secondary"], width=10).pack(side="right")
        except Exception:
            pass

        # Force UI update
        self.parent.update_idletasks()

    # === STUDY TIMER SYSTEM (UNIFIED) ===

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
        else:
            # Expand
            self.status_panel.pack(fill="both", expand=True, pady=(5, 0))
            if hasattr(self, 'status_container'):
                # Use larger height if developer mode is enabled
                height = 350 if hasattr(self, 'developer_mode') and self.developer_mode else 240
                self.status_container.place_configure(height=height)
            self.status_expanded = True
            for widget in self.status_header.winfo_children():
                if isinstance(widget, tk.Label):
                    widget.config(text="📊 Pet Status ▲")

    def toggle_timer_panel(self, event=None, force_expand=None):
        """Toggle or force the timer panel expansion."""
        if force_expand is not None:
            self.timer_expanded = force_expand
        else:
            self.timer_expanded = not getattr(self, 'timer_expanded', False)

        if self.timer_expanded:
            # Expanded state - adjust height based on content
            base_height = 550  # Increased to 550 to better fit Long Study preset times
            if getattr(self, 'scheduled_session_ready', False):
                base_height += 50  # Add space for the plan CTA if visible
            
            # Show the panel with proper expansion and increased padding
            self.timer_panel.pack(fill="both", expand=True, pady=(10, 0), padx=5)
            
            # Update container height
            if hasattr(self, 'timer_container'):
                self.timer_container.place_configure(height=base_height)
                
            # Update header text to show collapse indicator
            self.timer_header_label.config(text="⏱️ Study Timer ▲")
            
            # No need to force update UI here - it will be handled by the timer loop
        else:
            # Collapsed state
            self.timer_panel.pack_forget()
            if hasattr(self, 'timer_container'):
                self.timer_container.place_configure(height=40)
            for widget in self.timer_header.winfo_children():
                if isinstance(widget, tk.Label):
                    widget.config(text="⏱️ Study Timer ▼")

    def toggle_chat_panel(self, event=None):
        """Toggle chat panel expansion/collapse."""
        if not hasattr(self, 'chat_expanded') or self.chat_panel is None:
            return
        if self.chat_expanded:
            # Collapse
            self.chat_panel.pack_forget()
            try:
                self.chat_content.pack_forget()
            except Exception:
                pass
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
            # Ensure chat content is visible
            try:
                self.chat_content.pack(fill='both', expand=True)
            except Exception:
                pass
            if hasattr(self, 'chat_container'):
                self.chat_container.place_configure(height=400)
            self.chat_expanded = True
            # Update header text
            for widget in self.chat_header.winfo_children():
                if isinstance(widget, tk.Label):
                    widget.config(text="💬 Pet Chat ▲")


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

                    # Update the pet display
                    self.update_pet_info_display()

        except Exception as e:
            print(f"Warning: Error in handle_playground_click: {e}")

    def _init_playground_immediately(self, pet_type_str, stage_int=None, emotion_str=None):
        """Initialize playground renderer immediately with proper canvas sizing"""
        from models.pet_state import global_pet_state, PetStage, PetEmotion
        
        # Define default values at the start
        canvas_width, canvas_height = 800, 600
        pet_type_key = 'penguin'
        stage = 1
        emotion = 'HAPPY'
        
        def _safe_get_pet_info():
            """Safely get pet information with error handling"""
            nonlocal canvas_width, canvas_height, pet_type_key, stage, emotion
            
            try:
                # Ensure canvas has proper dimensions
                self.playground_canvas.update_idletasks()
                
                # Safely get canvas dimensions with fallbacks
                try:
                    canvas_width = max(self.playground_canvas.winfo_width(), 100)
                    canvas_height = max(self.playground_canvas.winfo_height(), 100)
                    
                    # Configure canvas with safe dimensions
                    self.playground_canvas.configure(width=canvas_width, height=canvas_height)
                except tk.TclError as e:
                    print(f"Warning: Could not configure canvas: {e}")

                # Safely get current pet type with fallback
                try:
                    current_pet = self.app_state.get_current_pet()
                    if current_pet and hasattr(current_pet, 'pet_type'):
                        pet_type_key = current_pet.pet_type.value if hasattr(current_pet.pet_type, 'value') else str(current_pet.pet_type)
                except Exception as e:
                    print(f"Warning: Could not get current pet: {e}")
                    
                # Ensure pet_type_key is a string and has a value
                pet_type_key = str(pet_type_key) if pet_type_key else 'penguin'
                
                # Safely get stage and emotion from global pet state with fallbacks
                try:
                    stage = stage_int if stage_int is not None else global_pet_state.stage.value
                    emotion = emotion_str.upper() if emotion_str else (
                        global_pet_state.emotion.name.upper() 
                        if hasattr(global_pet_state.emotion, 'name') 
                        else str(global_pet_state.emotion).upper()
                    )
                except Exception as e:
                    print(f"Warning: Error getting pet state, using defaults: {e}")
                    stage = 1  # Default to EGG stage
                    emotion = 'HAPPY'  # Default emotion
                    
            except Exception as e:
                print(f"Error in _safe_get_pet_info: {e}")
                import traceback
                traceback.print_exc()
        
        # Call the function to get pet info
        _safe_get_pet_info()
        
        # If we already have a renderer, just update its state
        if hasattr(self, 'playground_renderer') and self.playground_renderer is not None:
            try:
                # Update the existing renderer's state
                self.playground_renderer.update_pet_state(
                    pet_type=pet_type_key,
                    pet_stage=stage,
                    pet_emotion=emotion.lower()
                )
                print(f"✅ Updated pet state: {pet_type_key} (Stage: {stage}, Emotion: {emotion})")
                self.update_pet_info_display()
                return  # Exit after updating state
            except Exception as e:
                print(f"Error updating existing renderer: {e}")
                # If update fails, continue with reinitialization
        
        # Initialize the simple playground renderer with robust error handling
        try:
            from graphics.simple_playground import SimplePlayground
            
            # Ensure we have valid values before initialization
            stage = max(1, min(5, int(stage) if str(stage).isdigit() else 1))  # Clamp to 1-5
            emotion = str(emotion).upper()
            
            try:
                self.playground_renderer = SimplePlayground(
                    self.playground_canvas,
                    pet_type=pet_type_key,
                    pet_stage=stage,
                    pet_emotion=emotion.lower()
                )
                print(f"✅ SimplePlayground initialized with {pet_type_key} (Stage: {stage}, Emotion: {emotion})")
                self.update_pet_info_display()
                
            except tk.TclError as te:
                print(f"⚠️ Tkinter error initializing playground: {te}")
                self._show_playground_error(canvas_width, canvas_height, pet_type_key, stage, emotion)
            except Exception as e:
                print(f"⚠️ Error initializing playground: {e}")
                import traceback
                traceback.print_exc()
                self._show_playground_error(canvas_width, canvas_height, pet_type_key, stage, emotion)
                
        except ImportError as ie:
            print(f"⚠️ Could not import SimplePlayground: {ie}")
            self._show_playground_error(canvas_width, canvas_height, pet_type_key, stage, emotion)
                
    def _show_playground_error(self, width, height, pet_type, stage, emotion):
        """Display a fallback UI when the playground fails to initialize"""
        try:
            self.playground_renderer = None
            self.playground_canvas.delete("all")
            self.playground_canvas.create_text(
                width // 2, 
                height // 2,
                text=f"Pet: {pet_type}\nStage: {stage}\nEmotion: {emotion}",
                fill="black",
                font=('Arial', 12),
                tags=("fallback_text",)
            )
            self.update_pet_info_display()
        except Exception as e:
            print(f"⚠️ Error showing fallback UI: {e}")
            # Still try to update display even if renderer fails
            try:
                self.update_pet_info_display()
            except Exception as update_error:
                print(f"⚠️ Error updating pet info: {update_error}")


    def create_timer_ui(self, parent_frame):
        """
        Create a clean and organized timer interface with controls and presets.
        
        Args:
            parent_frame: The parent frame to place the timer UI in
        """
        # Clear any existing widgets
        for widget in parent_frame.winfo_children():
            widget.destroy()
        
        # Get background color from parent
        bg_color = parent_frame['bg']
        text_color = self.colors.get("text_dark", "#333333")
        accent_color = self.colors.get("accent", "#4CAF50")
        
        # Configure parent frame to expand
        parent_frame.pack_propagate(False)
        
        # Main container with padding
        container = tk.Frame(parent_frame, bg=bg_color)
        container.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Timer display frame
        self.timer_display_frame = tk.Frame(container, bg=bg_color)
        self.timer_display_frame.pack(fill='x', pady=(0, 20))
        
        # Timer display
        self.timer_var = tk.StringVar(value="25:00")
        self.timer_label = tk.Label(
            self.timer_display_frame,
            textvariable=self.timer_var,
            font=("Arial", 48, "bold"),
            bg=bg_color,
            fg=text_color
        )
        self.timer_label.pack()
        
        # Status message
        self.status_var = tk.StringVar(value="Ready to study!")
        status_label = tk.Label(
            self.timer_display_frame,
            textvariable=self.status_var,
            font=("Arial", 10),
            bg=bg_color,
            fg=text_color
        )
        status_label.pack(pady=(0, 20))
        
        # Control buttons frame
        btn_frame = tk.Frame(container, bg=bg_color)
        btn_frame.pack(fill='x', pady=(0, 15))
        
        # Start/Pause button
        self.start_pause_btn = tk.Button(
            btn_frame,
            text="Start",
            command=self.toggle_timer,
            bg=self.colors.get("bg_accent", accent_color),
            fg=self.colors.get("text_dark", "#333"),
            font=("Arial", 10, "bold"),
            relief="flat",
            padx=20,
            pady=8,
            bd=0
        )
        self.start_pause_btn.pack(side='left', expand=True, padx=5)
        
        # Stop button
        self.stop_btn = tk.Button(
            btn_frame,
            text="Stop",
            command=self.stop_timer,
            bg=self.colors.get("bg_secondary", "#eee"),
            fg=self.colors.get("text_dark", "#333"),
            font=("Arial", 10, "bold"),
            relief="flat",
            padx=20,
            pady=8,
            bd=0,
            state="disabled"
        )
        self.stop_btn.pack(side='left', expand=True, padx=5)
        
        # Create a separator line
        separator = ttk.Separator(container, orient='horizontal')
        separator.pack(fill='x', pady=10)
        
        # Create a frame for preset buttons
        presets_frame = tk.Frame(container, bg=bg_color)
        presets_frame.pack(fill='x', pady=(0, 10))
        
        # Function to create preset buttons
        def create_preset_row(title, presets, break_info, row):
            # Title label with break info in parentheses
            title_label = tk.Label(
                presets_frame,
                text=f"{title} ({break_info})",
                font=("Arial", 9, "bold"),
                bg=bg_color,
                fg=text_color,
                anchor='w'
            )
            title_label.grid(row=row*2, column=0, columnspan=4, sticky='w', pady=(10, 5))
            
            # Preset buttons
            for i, (minutes, text) in enumerate(presets):
                btn = tk.Button(
                    presets_frame,
                    text=text,
                    command=lambda m=minutes: self.set_timer_duration(m),
                    bg=self.colors.get("bg_secondary", "#f0f0f0"),
                    fg=text_color,
                    font=("Arial", 9),
                    relief="flat",
                    padx=10,
                    pady=5,
                    bd=1,
                    activebackground=self.colors.get("bg_accent", "#e0e0e0")
                )
                btn.grid(row=row*2+1, column=i, padx=2, pady=(0, 10), sticky='ew')
            
            # Configure column weights for even spacing
            for i in range(4):
                presets_frame.columnconfigure(i, weight=1)
        
        # Define preset configurations
        short_presets = [
            (10, "10 min"),
            (15, "15 min"),
            (20, "20 min"),
            (25, "25 min")
        ]
        
        medium_presets = [
            (30, "30 min"),
            (60, "1 hr"),
            (90, "1h 30m"),
            (120, "2 hrs")
        ]
        
        long_presets = [
            (150, "2h 30m"),
            (180, "3 hrs"),
            (240, "4 hrs"),
            (300, "5 hrs")
        ]
        
        # Create preset rows with proper spacing
        create_preset_row("Short Focus", short_presets, "2 min/10 min break", 0)
        
        # Add separator between preset sections
        separator2 = ttk.Separator(container, orient='horizontal')
        separator2.pack(fill='x', pady=5)
        
        create_preset_row("Medium Sessions", medium_presets, "5 min/30 min break", 2)
        
        # Add separator between preset sections
        separator3 = ttk.Separator(container, orient='horizontal')
        separator3.pack(fill='x', pady=5)
        
        create_preset_row("Long Study", long_presets, "20 min/30 min break", 4)
        
        # Initialize timer with default duration (25 minutes)
        default_minutes = 25
        self.total_duration_seconds = default_minutes * 60
        self.time_remaining = self.total_duration_seconds
        self.timer_var.set(self.format_time(self.time_remaining))
        self.status_var.set(f"Set for {default_minutes} minutes")
        
        # Reset taskbar timer progress
        try:
            if hasattr(self, 'taskbar_timer_progress'):
                self.taskbar_timer_progress['value'] = 0
        except Exception:
            pass
                
    def _handle_camera_choice(self, *args, **kwargs):
        """Legacy method kept for compatibility."""
        self.start_timer()
    
    def _start_timer_after_camera_check(self, from_resume=False):
        """Internal method to start the timer after camera permission is handled.
        
        Args:
            from_resume (bool): Whether this is being called from resume operation
        """
        if not self.timer_running and self.time_remaining > 0:
            try:
                # Auto-expand timer panel if collapsed
                if not getattr(self, 'timer_expanded', False):
                    self.toggle_timer_panel(force_expand=True)
            except Exception:
                pass
                
            self.timer_running = True
            self.start_pause_btn.config(text="Pause")
            self.stop_btn.config(state="normal")
            self.update_timer()
    
        # Timer state is now initialized in __init__

        
        # Study tips are now shown as notifications when the timer starts
        
    def format_time(self, seconds):
        """Format seconds into MM:SS format."""
        mins, secs = divmod(int(seconds), 60)
        return f"{mins:02d}:{secs:02d}"
        
    def set_timer_duration(self, minutes):
        """Set the timer duration in minutes and refresh progress baseline."""
        self.total_duration_seconds = max(1, minutes * 60)
        self.time_remaining = self.total_duration_seconds
        self.study_session_duration = minutes
        self.timer_var.set(self.format_time(self.time_remaining))
        self.status_var.set(f"Set for {minutes} minutes")
        
        # Reset taskbar timer progress
        try:
            if hasattr(self, 'taskbar_timer_progress'):
                self.taskbar_timer_progress['value'] = 0
                self.taskbar_timer_progress['maximum'] = self.total_duration_seconds
        except Exception as e:
            print(f"Error updating taskbar progress: {e}")
            
    def update_timer_ui(self):
        """Update all timer-related UI elements."""
        if not hasattr(self, 'timer_var') or not hasattr(self, 'time_remaining'):
            return
            
        # Update timer display
        self.timer_var.set(self.format_time(self.time_remaining))
        
        # Update progress bar if it exists
        if hasattr(self, 'taskbar_timer_progress') and hasattr(self, 'total_duration_seconds'):
            try:
                progress = max(0, self.total_duration_seconds - self.time_remaining)
                self.taskbar_timer_progress['value'] = progress
            except Exception as e:
                print(f"Error updating progress bar: {e}")
        
    def toggle_timer(self):
        """Toggle the timer between start and pause states."""
        print("\n=== toggle_timer called ===")
        
        if self.timer_running:
            print("Pausing timer")
            self.pause_timer()
        else:
            print("Starting timer")
            self.start_timer()
                
        print("=== toggle_timer finished ===\n")
        
    def stop_timer(self):
        """Stop the countdown timer and reset UI state."""
        try:
            # Stop drowsiness detection and release camera
            if getattr(self, 'drowsiness_detection_active', False):
                self._stop_drowsiness_detection()
            
            # Stop the underlying study timer logic
            if hasattr(self, 'stop_study_timer'):
                self.stop_study_timer()

            # Reset remaining time to full duration
            if hasattr(self, 'total_duration_seconds'):
                self.time_remaining = self.total_duration_seconds

            # Update timer display and status message
            if hasattr(self, 'timer_var') and hasattr(self, 'time_remaining'):
                self.timer_var.set(self.format_time(self.time_remaining))
            if hasattr(self, 'status_var'):
                self.status_var.set("Timer stopped")

            # Update control buttons
            if hasattr(self, 'start_pause_btn'):
                self.start_pause_btn.config(text="Start")
            if hasattr(self, 'stop_btn'):
                self.stop_btn.config(state="disabled")

            # Ensure timer_running flag is cleared
            self.timer_running = False

            # Reset taskbar timer progress
            try:
                if hasattr(self, 'taskbar_timer_progress'):
                    self.taskbar_timer_progress['value'] = 0
            except Exception:
                pass

        except Exception as e:
            print(f"Error in stop_timer: {e}")

    def start_timer(self, from_resume=False):
        """Start or resume the countdown timer."""
        if not self.time_remaining:
            self.time_remaining = self.total_duration_seconds
            
        if not self.timer_running:
            # If not resuming, prompt for camera permission
            if not from_resume and not getattr(self, 'drowsiness_detection_active', False):
                self._prompt_camera_permission()
                return
                
            self.timer_running = True
            
            # Update UI
            if hasattr(self, 'start_pause_btn'):
                self.start_pause_btn.config(text="Pause")
            if hasattr(self, 'stop_btn'):
                self.stop_btn.config(state="normal")
                
            # Auto-expand timer panel if collapsed
            if hasattr(self, 'timer_expanded') and not self.timer_expanded:
                self.toggle_timer_panel(force_expand=True)
                
            # Start the timer
            self.update_timer()
    
    def _prompt_camera_permission(self):
        """Show dialog to ask for camera permission for drowsiness detection."""
        response = messagebox.askyesno(
            "Enable Drowsiness Detection",
            "Would you like to enable the camera for drowsiness detection?\n\n"
            "This feature can help you stay focused by detecting when you're getting tired. "
            "Your camera feed is processed locally and never stored.\n\n"
            "Note: Camera is required to start the timer.",
            parent=self.parent
        )
        
        if response:
            self._init_drowsiness_detection()
        else:
            messagebox.showinfo(
                "Camera Required",
                "The timer will not start because camera access is required for study monitoring.\n\n"
                "Please enable the camera if you wish to use the timer.",
                parent=self.parent
            )
    
    def _init_drowsiness_detection(self):
        """Initialize the drowsiness detection system."""
        try:
            # Show a temporary loading message while initializing
            loading_window = tk.Toplevel(self.parent)
            loading_window.title("Initializing Camera")
            loading_window.geometry("300x100")
            loading_window.transient(self.parent)
            loading_window.grab_set()
            
            # Center the loading window
            window_width = 300
            window_height = 100
            screen_width = loading_window.winfo_screenwidth()
            screen_height = loading_window.winfo_screenheight()
            x = (screen_width // 2) - (window_width // 2)
            y = (screen_height // 2) - (window_height // 2)
            loading_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
            
            ttk.Label(loading_window, text="Initializing camera...").pack(pady=20)
            loading_window.update()
            
            # Initialize the drowsiness detector
            if not self._init_drowsiness_detector():
                raise Exception("Failed to initialize drowsiness detector")
                
            # Start the detection in a separate thread
            if not self._start_drowsiness_detection():
                raise Exception("Failed to start drowsiness detection")
            
            # Update state
            self.drowsiness_detection_active = True
            
            # Close loading window
            loading_window.destroy()

            # Start the timer
            self._start_timer_after_camera_check()
            
        except Exception as e:
            print(f"Error initializing drowsiness detection: {e}")
            if 'loading_window' in locals() and loading_window.winfo_exists():
                loading_window.destroy()
            messagebox.showerror(
                "Error",
                "Could not initialize the camera. Starting timer without drowsiness detection.",
                parent=self.parent
            )
            self._start_timer_after_camera_check()
    
    def _start_timer_after_camera_check(self, from_resume=False):
        """Internal method to start the timer after camera initialization is complete."""
        # Update UI
        self.timer_running = True
        if hasattr(self, 'start_pause_btn'):
            self.start_pause_btn.config(text="Pause")
        if hasattr(self, 'stop_btn'):
            self.stop_btn.config(state="normal")
        
        # Clear any existing timer ID and start the timer
        self.timer_id = None
        self.update_timer()
        
    def update_timer(self):
        """Update the timer display and handle countdown logic."""
        if not self.timer_running:
            return
            
        # Update the time remaining
        if hasattr(self, 'time_remaining') and self.time_remaining > 0:
            # Update the timer display
            if hasattr(self, 'timer_var'):
                self.timer_var.set(self.format_time(self.time_remaining))
                
            # Update progress bar if it exists
            if hasattr(self, 'taskbar_timer_progress'):
                try:
                    progress = ((self.total_duration_seconds - self.time_remaining) / 
                              self.total_duration_seconds) * 100
                    self.taskbar_timer_progress['value'] = progress
                except (TypeError, KeyError, ZeroDivisionError):
                    pass
            
            # Decrement the time remaining
            self.time_remaining -= 1
            
            # Schedule the next update
            self.timer_id = self.parent.after(1000, self.update_timer)
        else:
            # Timer has finished
            self.timer_finished()
            
    def timer_finished(self):
        """Handle timer completion."""
        self.timer_running = False
        self.time_remaining = 0
        
        # Update UI
        if hasattr(self, 'timer_var'):
            self.timer_var.set("00:00")
            
        if hasattr(self, 'start_pause_btn'):
            self.start_pause_btn.config(text="Start")
            
        if hasattr(self, 'stop_btn'):
            self.stop_btn.config(state="disabled")
            
        # Update progress bar
        if hasattr(self, 'taskbar_timer_progress'):
            try:
                self.taskbar_timer_progress['value'] = 100
            except (TypeError, KeyError):
                pass
                
        # Show notification
        if hasattr(self, 'show_notification'):
            self.show_notification("Timer completed!")
        else:
            print("Timer completed!")
    #                     # Fallback to main panel if timer_panel doesn't exist
    #                     self.plan_frame_container = tk.Frame(self.status_content, bg=self.colors["bg_secondary"])
    #                     self.plan_frame_container.pack(fill='x', pady=(10, 0), padx=5)
                
    #             # Clear any existing plan frame
    #             if hasattr(self, 'plan_frame'):
    #                 self.plan_frame.destroy()
                
    #             # Create new plan frame in the container
    #             self.plan_frame = tk.Frame(self.plan_frame_container, bg=self.colors["bg_secondary"])
    #             self.plan_frame.pack(fill='x', expand=True)
                
    #             # Recreate the CTA button in the new frame
    #             self.plan_cta = tk.Button(
    #                 self.plan_frame,
    #                 text=f"Start {plan['focus']} Minute Focus Session",
    #                 command=self.begin_study_plan,
    #                 bg=self.colors.get("bg_accent", "#4CAF50"),
    #                 fg=self.colors.get("text_dark", "#333"),
    #                 font=("Arial", 10, "bold"),
    #                 relief="flat",
    #                 padx=10,
    #                 pady=5,
    #                 bd=0,
    #                 activebackground=self.colors.get("bg_accent", "#e0e0e0")
    #             )
    #             self.plan_cta.pack(anchor='w', padx=5, pady=5)
                
    #             # Ensure the container is visible
    #             self.plan_frame_container.pack(fill='x', pady=(10, 0), padx=5, before=None)
                
    #             # Force update to ensure UI is refreshed
    #             self.plan_frame.update_idletasks()
                
    #         except Exception as e:
    #             print(f"Error showing plan frame: {e}")
    #     finally:
    #         try:
    #             window.destroy()
    #         except Exception:
    #             pass

    def begin_study_plan(self):
        """Begin the prepared schedule plan."""
        if not self.scheduled_session_ready or not self.schedule_plan:
            return
        focus = int(self.schedule_plan.get('focus', 25))
        self.set_timer_duration(focus)
        self.start_timer()
        # Hide CTA after starting
        try:
            self.plan_frame.pack_forget()
        except Exception:
            pass
        self.scheduled_session_ready = False


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


    def show_statistics(self):
        """Display user and pet statistics in a clean format."""
        if not hasattr(self, 'app_state') or not hasattr(self.app_state, 'user') or not self.app_state.user:
            messagebox.showinfo("Statistics", "No user data available.")
            return
            
        user = self.app_state.user

        # Username (fallback to a friendly default)
        username = getattr(user, 'username', None) or "Player"

        # Saved total minutes from user model
        saved_total_minutes = getattr(user, 'total_study_time', 0)

        # Runtime minutes for this app instance (not yet flushed)
        runtime_minutes = 0
        if hasattr(self, 'runtime_study_seconds'):
            try:
                runtime_minutes = int(self.runtime_study_seconds // 60)
            except Exception:
                runtime_minutes = 0

        combined_total_minutes = max(0, int(saved_total_minutes) + runtime_minutes)

        # Daily and weekly stats come from the user model
        today_stats = user.get_today_stats()
        week_stats = user.get_week_stats()

        today_minutes = max(0, int(today_stats.get('study_time', 0)))
        week_minutes = max(0, int(week_stats.get('study_time', 0)))

        # Build base statistics message
        stats_lines = []
        stats_lines.append(f"📊 Study Statistics for {username}")
        stats_lines.append("")
        stats_lines.append(f"📅 Level: {user.level} (XP: {user.experience}/{(user.level) * 100})")
        stats_lines.append(f"🔥 Current Streak: {user.streak_days} days")
        stats_lines.append(
            f"⏱️  Total Study Time: {combined_total_minutes // 60}h {combined_total_minutes % 60}m"
        )
        stats_lines.append("")
        stats_lines.append("📈 Today's Progress")
        stats_lines.append(
            f"⏱️  {today_minutes // 60}h {today_minutes % 60}m studied"
        )
        stats_lines.append("")
        stats_lines.append("📆 This Week")
        stats_lines.append(
            f"⏱️  {week_minutes // 60}h {week_minutes % 60}m studied"
        )

        # Add pet statistics using the same global state as the Pet Status panel
        try:
            from models.pet_state import global_pet_state
        except Exception:
            global_pet_state = None

        if hasattr(self.app_state, 'current_pet') and self.app_state.current_pet:
            pet = self.app_state.current_pet
            pet_name = getattr(pet, 'name', None) or "Unnamed"

            stats_lines.append("")
            stats_lines.append(f"🐾 Pet: {pet_name}")

            # Mastery from global_pet_state if available, otherwise from pet
            mastery = None
            if global_pet_state is not None and hasattr(global_pet_state, 'mastery'):
                mastery = global_pet_state.mastery
            elif hasattr(pet, 'mastery'):
                mastery = pet.mastery

            if mastery is not None:
                stats_lines.append(f"🎓 Mastery: {mastery}")

            # Stage from global_pet_state if available
            stage_label = None
            if global_pet_state is not None and hasattr(global_pet_state, 'stage'):
                try:
                    raw_stage = global_pet_state.stage.name if hasattr(global_pet_state.stage, 'name') else str(global_pet_state.stage)
                    stage_label = raw_stage.replace('_', ' ').title()
                except Exception:
                    stage_label = None

            if not stage_label and hasattr(pet, 'stage'):
                try:
                    raw_stage = pet.stage.name if hasattr(pet.stage, 'name') else str(pet.stage)
                    stage_label = raw_stage.replace('_', ' ').title()
                except Exception:
                    stage_label = None

            if stage_label:
                stats_lines.append(f"📈 Stage: {stage_label}")

        stats_message = "\n".join(stats_lines)
        messagebox.showinfo("Your Study Statistics", stats_message)
    
    def switch_tab(self, tab_name):
        """Switch to different tab/functionality."""
        if tab_name == "schedule":
            messagebox.showinfo("Schedule", "📅 Study schedule feature coming soon!")
        elif tab_name == "stats":
            # Save current data before showing statistics
            try:
                if hasattr(self, 'app_state') and hasattr(self.app_state, 'save_data'):
                    self.app_state.save_data()
            except Exception as e:
                print(f"Error saving data before showing stats: {e}")
            self.show_statistics()
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

    def toggle_developer_mode(self):
        """Toggle developer mode on/off."""
        self.developer_mode = not self.developer_mode
        self.refresh_developer_ui()
        
        # Save the state
        self.app_state.settings['developer_mode'] = self.developer_mode
        self.app_state.save_settings()

    def _init_drowsiness_detector(self) -> bool:
        """Initialize the drowsiness detector.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        try:
            print("Initializing drowsiness detector...")
            
            # Try multiple possible model paths
            possible_paths = [
                # Relative to project root
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                           "models", "drowsiness_model.keras"),
                # Relative to src directory
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "..", "models", "drowsiness_model.keras"),
                # Absolute path from project root
                os.path.join(os.getcwd(), "models", "drowsiness_model.keras")
            ]
            
            model_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    model_path = path
                    break
            
            if not model_path or not os.path.exists(model_path):
                error_msg = f"Drowsiness model not found. Tried paths:\n" + "\n".join(possible_paths)
                print(error_msg)
                messagebox.showerror("Model Not Found", 
                                   "Could not find the drowsiness detection model.\n"
                                   "Please make sure the model file exists in the models directory.")
                return False
            
            print(f"Found model at: {model_path}")
                
            # Initialize the detector
            try:
                self.drowsiness_detector = DrowsinessDetector(
                    model_path=model_path,
                    root_window=self.parent
                )
                print("Drowsiness detector initialized successfully")
                
                # Initialize the camera
                if not hasattr(self.drowsiness_detector, 'camera'):
                    print("Error: Drowsiness detector does not have a camera instance")
                    return False
                
                # Start the camera
                print("Starting camera...")
                if not self.drowsiness_detector.camera.start():
                    print("Failed to start camera for drowsiness detection")
                    return False
                
                # Test the model with a small delay to ensure it's loaded
                print("Testing model with sample prediction...")
                test_frame = np.zeros((100, 100, 3), dtype=np.uint8)
                is_drowsy, drowsy_conf, awake_conf = self.drowsiness_detector.predict_drowsiness(test_frame)
                print(f"Test prediction - Drowsy: {is_drowsy}, Drowsy Conf: {drowsy_conf:.2f}, Awake Conf: {awake_conf:.2f}")
                
                return True
                
            except Exception as e:
                error_msg = f"Error initializing drowsiness detector: {str(e)}"
                print(error_msg)
                import traceback
                traceback.print_exc()
                messagebox.showerror("Initialization Error", 
                                   f"Failed to initialize drowsiness detector:\n{str(e)}")
                return False
            
        except Exception as e:
            error_msg = f"Unexpected error in _init_drowsiness_detector: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return False

    def _start_drowsiness_detection(self):
        """Start the drowsiness detection in a separate thread with improved error handling and logging."""
        try:
            print("Starting drowsiness detection...")
            
            if self.drowsiness_detection_active:
                print("Drowsiness detection is already active")
                return False
                
            if not self.drowsiness_detector:
                print("Error: Drowsiness detector not initialized")
                return False
                
            print("Initializing camera...")
            try:
                # Start the camera
                if not self.drowsiness_detector.camera.start():
                    print("Failed to start camera")
                    return False
                    
                print("Camera started successfully")
                
            except Exception as e:
                print(f"Camera initialization error: {str(e)}")
                return False
                
            self.drowsiness_detection_active = True
            self.drowsy_start_time = 0
            self._drowsiness_stop_event.clear()

            def detection_loop():
                try:
                    last_drowsy_check = time.time()
                    last_fps_update = time.time()
                    frame_count = 0
                    fps = 0
                    consecutive_drowsy_seconds = 0
                    
                    print("Drowsiness detection loop started")
                    
                    # Only create window if in developer mode
                    if self.developer_mode:
                        cv2.namedWindow('Drowsiness Detection', cv2.WINDOW_NORMAL)
                        cv2.resizeWindow('Drowsiness Detection', 800, 600)
                    
                    while not self._drowsiness_stop_event.is_set() and self.drowsiness_detection_active:
                        try:
                            frame_start_time = time.time()
                            time_since_last_check = frame_start_time - last_drowsy_check
                            last_drowsy_check = frame_start_time
                            
                            # Read a frame from the camera
                            ret, frame = self.drowsiness_detector.camera.cap.read()
                            
                            if not ret:
                                print("Failed to capture frame from camera")
                                time.sleep(0.1)  # Small delay before retrying
                                continue
                            
                            # Create a copy for display (only if in dev mode)
                            display_frame = frame.copy() if self.developer_mode else None
                            
                            # Detect faces in the frame (always, like the demo)
                            faces = self.drowsiness_detector.detect_face(frame)

                            # Process each detected face
                            for (x, y, w, h) in faces:
                                # Extract face ROI
                                face_roi = frame[y:y+h, x:x+w]

                                # Get drowsiness status
                                is_drowsy, drowsy_confidence, awake_confidence = self.drowsiness_detector.predict_drowsiness(face_roi)

                                # Store in unified instance variables for consistent access
                                self.latest_drowsy_status = is_drowsy
                                self.latest_drowsy_confidence = drowsy_confidence
                                self.latest_awake_confidence = awake_confidence

                                # Emotion prediction (if model is available)
                                emotion_label = "Unknown"
                                if getattr(self, "emotion_model", None) is not None:
                                    try:
                                        gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
                                        gray = cv2.resize(gray, (48, 48))
                                        gray = gray.astype("float32") / 255.0
                                        gray = np.expand_dims(gray, axis=-1)
                                        gray = np.expand_dims(gray, axis=0)
                                        preds = self.emotion_model.predict(gray, verbose=0)[0]
                                        emotion_idx = int(np.argmax(preds))

                                        from emotion_demo import EMOTION_LABELS
                                        if 0 <= emotion_idx < len(EMOTION_LABELS):
                                            emotion_label = EMOTION_LABELS[emotion_idx]
                                        else:
                                            emotion_label = str(emotion_idx)

                                        # Update emotion tracker
                                        self._update_emotion_tracking(emotion_idx)
                                    except Exception as e:
                                        print(f"Emotion prediction error: {e}")

                                # Update focus tracking and log status periodically
                                self._update_focus_tracking(is_drowsy, drowsy_confidence, awake_confidence)

                                confidence = drowsy_confidence if is_drowsy else awake_confidence
                                from datetime import datetime
                                timestamp = datetime.now().strftime("%H:%M:%S")
                                status = "DROWSY" if is_drowsy else "AWAKE"

                                # Update UI variable for display
                                if hasattr(self, 'drowsiness_status_var'):
                                    self.drowsiness_status_var.set(status)

                                # Console output (unconditional when faces are detected)
                                print(
                                    f"[{timestamp}] Status: {status} | "
                                    f"Drowsy: {drowsy_confidence*100:.1f}% | Awake: {awake_confidence*100:.1f}% | "
                                    f"Emotion: {emotion_label}"
                                )

                                # Update display if in dev mode
                                if self.developer_mode and display_frame is not None:
                                    # Use the detector's draw_detection method for consistent visualization
                                    display_frame = self.drowsiness_detector.draw_detection(
                                        display_frame,
                                        (x, y, w, h),
                                        is_drowsy,
                                        drowsy_confidence,
                                        awake_confidence
                                    )

                                # Track drowsiness for alerts only when the study timer is actually running
                                if self.study_timer_active and not self.study_timer_paused:
                                    if is_drowsy and drowsy_confidence > 0.8:  # High confidence of drowsiness
                                        # Track consecutive drowsy seconds
                                        consecutive_drowsy_seconds += time_since_last_check

                                        # If drowsy for more than 30 seconds
                                        if consecutive_drowsy_seconds >= 30:
                                            self.parent.after(0, self._handle_prolonged_drowsiness)
                                            consecutive_drowsy_seconds = 0  # Reset counter after handling
                                    else:
                                        # Reset counter if not drowsy
                                        consecutive_drowsy_seconds = 0
                            
                            # Update FPS counter
                            frame_count += 1
                            current_time = time.time()
                            if current_time - last_fps_update >= 1.0:  # Update FPS every second
                                fps = frame_count / (current_time - last_fps_update)
                                frame_count = 0
                                last_fps_update = current_time
                            
                            # Add FPS to display if in dev mode
                            if self.developer_mode and display_frame is not None:
                                # Add FPS counter to the frame
                                cv2.putText(display_frame, f'FPS: {fps:.1f}', 
                                          (display_frame.shape[1] - 120, 30), 
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                                
                                # Display the frame
                                cv2.imshow('Drowsiness Detection', display_frame)
                                
                                # Check for 'q' key to quit
                                if cv2.waitKey(1) & 0xFF == ord('q'):
                                    break
                            else:
                                # Small delay to prevent high CPU usage when not displaying
                                # but still maintain good responsiveness
                                time_elapsed = time.time() - frame_start_time
                                time_to_wait = max(0.01, (1.0/15.0) - time_elapsed)  # Target ~15 FPS when not displaying
                                time.sleep(time_to_wait)
                            
                        except Exception as e:
                            print(f"Error in drowsiness detection loop: {str(e)}")
                            import traceback
                            traceback.print_exc()
                            self.parent.after(0, lambda: messagebox.showerror(
                                "Detection Error", 
                                f"Error in drowsiness detection: {str(e)}",
                                parent=self.parent
                            ))
                            self._stop_drowsiness_detection()
                            break
                    
                    # Clean up
                    if self.developer_mode:
                        cv2.destroyAllWindows()
                                                    
                except Exception as e:
                    print(f"Fatal error in detection thread: {str(e)}")
                    self.parent.after(0, lambda: messagebox.showerror(
                        "Fatal Error", 
                        "Drowsiness detection has stopped due to an error.",
                        parent=self.parent
                    ))
                    self._stop_drowsiness_detection()
            
            # Start the detection thread
            try:
                self.drowsiness_thread = threading.Thread(target=detection_loop, daemon=True)
                self.drowsiness_thread.start()
                print("Drowsiness detection thread started successfully")
                return True
            except Exception as e:
                print(f"Failed to start detection thread: {str(e)}")
                self._stop_drowsiness_detection()
                return False
                
        except Exception as e:
            print(f"Error in _start_drowsiness_detection: {str(e)}")
            self._stop_drowsiness_detection()
            return False
    
    def _handle_prolonged_drowsiness(self):
        """Handle when user is drowsy for a prolonged period."""
        self.consecutive_drowsy_sessions += 1
        
        # Show speech bubble with encouraging message
        message = random.choice(self.encouraging_messages)
        self._show_speech_bubble(message)
        
        # Show notification
        self._show_notification("Stay Focused!", message)
        
        # If this is the 3rd time, force stop the session
        if self.consecutive_drowsy_sessions >= 3:
            self._handle_excessive_drowsiness()
    
    def _handle_excessive_drowsiness(self):
        """Handle when user is consistently not focusing."""
        # Stop the current session
        was_running = self.study_timer_active and not self.study_timer_paused
        if was_running:
            self.stop_study_session()
        
        # Show speech bubble with rest message
        rest_message = random.choice(self.rest_messages)
        self._show_speech_bubble(rest_message)
        
        # Show notification
        self._show_notification("Time for a Break!", rest_message)
        
        # Reset counter
        self.consecutive_drowsy_sessions = 0
    
    def _update_emotion_tracking(self, emotion_idx):
        """
        Update emotion tracking with the latest prediction and log status periodically.

        Args:
            emotion_idx (int): Index of the predicted emotion class.
        """
        # Only track when drowsiness detection is active
        if not getattr(self, "drowsiness_detection_active", False):
            return

        current_time = time.time()

        # Only process a prediction every emotion_prediction_interval seconds
        if current_time - self.last_emotion_time < getattr(self, "emotion_prediction_interval", 6):
            return

        self.last_emotion_time = current_time

        # Store the emotion index
        try:
            self.emotion_predictions.append(int(emotion_idx))
        except Exception:
            return

        # Keep only the last 10 (1 minute of data)
        if len(self.emotion_predictions) > 10:
            self.emotion_predictions = self.emotion_predictions[-10:]

        if len(self.emotion_predictions) == 10:
            # Majority vote over last 10 predictions
            from collections import Counter
            counts = Counter(self.emotion_predictions)
            majority_idx, _ = counts.most_common(1)[0]

            # Map to label using the demo's labels
            from emotion_demo import EMOTION_LABELS
            if 0 <= majority_idx < len(EMOTION_LABELS):
                emotion_label = EMOTION_LABELS[majority_idx]
            else:
                emotion_label = str(majority_idx)

            # Log combined focus + emotion status
            self._log_focus_status_with_emotion(emotion_label)

            # Clear for next minute
            self.emotion_predictions = []

    def _update_focus_tracking(self, is_drowsy, drowsy_confidence, awake_confidence):
        """
        Update focus tracking with the latest prediction and log periodically.

        Args:
            is_drowsy (bool): Whether the user is drowsy or not.
            drowsy_confidence (float): Confidence of drowsiness.
            awake_confidence (float): Confidence of being awake.
        """
        # Only track when drowsiness detection is active
        if not getattr(self, "drowsiness_detection_active", False):
            return

        current_time = time.time()

        # Only process a prediction every focus_prediction_interval seconds
        if current_time - self.last_prediction_time < getattr(self, "focus_prediction_interval", 6):
            return

        self.last_prediction_time = current_time

        # Store the prediction
        try:
            self.predictions.append(int(is_drowsy))
        except Exception:
            return

        # Keep only the last 10 (1 minute of data)
        if len(self.predictions) > 10:
            self.predictions = self.predictions[-10:]

        if len(self.predictions) == 10:
            # Count how many times the user was drowsy in the last minute
            drowsy_count = sum(self.predictions)
            
            # If at least 4 out of 10 predictions were drowsy, log as DROWSY, otherwise AWAKE
            status = "DROWSY" if drowsy_count >= 4 else "AWAKE"
            # self._log_focus_status(status)  # Commented out - emotion tracking handles logging
            
            # Clear predictions for the next minute
            self.predictions = []

    def _log_focus_status(self, status):
        """
        Log the focus status to the log file.
        
        Args:
            status (str): The status to log ("AWAKE" or "DROWSY")
        """
        try:
            # Get current timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Format the log entry
            log_entry = f"{timestamp} - {status}\n"
            
            # Append to log file
            with open(self.log_file, 'a') as f:
                f.write(log_entry)
                
            print(f"Logged focus status: {status} at {timestamp}")
            
        except Exception as e:
            print(f"Error logging focus status: {e}")

    def _log_focus_status_with_emotion(self, emotion_label):
        """Log combined focus state and aggregated emotion to the log file."""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status = "DROWSY" if getattr(self, "latest_drowsy_status", False) else "AWAKE"
            log_entry = f"{timestamp} - {status} - {emotion_label}\n"
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
            print(f"Logged focus/emotion: {status}, {emotion_label} at {timestamp}")
        except Exception as e:
            print(f"Error logging focus/emotion status: {e}")

    def _stop_drowsiness_detection(self):
        """
        Stop the drowsiness detection and clean up all resources.
        This method ensures all camera resources are properly released and threads are terminated.
        """
        print("Stopping drowsiness detection and cleaning up resources...")
        
        # Reset focus tracking state so the next session starts fresh
        self.predictions = []
        self.last_prediction_time = 0
        
        # Log AWAKE status when stopping detection
        if hasattr(self, 'log_file'):
            self._log_focus_status("AWAKE")
        
        # Set flags to stop the detection loop
        self.drowsiness_detection_active = False
        if hasattr(self, '_drowsiness_stop_event'):
            self._drowsiness_stop_event.set()
        
        # Wait for the detection thread to finish
        if hasattr(self, 'drowsiness_thread') and self.drowsiness_thread and self.drowsiness_thread.is_alive():
            print("Waiting for drowsiness detection thread to finish...")
            self.drowsiness_thread.join(timeout=2.0)
            if self.drowsiness_thread.is_alive():
                print("Warning: Drowsiness detection thread did not stop gracefully")
        
        # Clean up the drowsiness detector and camera
        if hasattr(self, 'drowsiness_detector') and self.drowsiness_detector:
            try:
                # Stop the camera if it exists
                if hasattr(self.drowsiness_detector, 'camera') and self.drowsiness_detector.camera:
                    print("Stopping drowsiness detector camera...")
                    try:
                        self.drowsiness_detector.camera.stop()
                        # Explicitly release the camera capture if it exists
                        if hasattr(self.drowsiness_detector.camera, 'cap'):
                            try:
                                self.drowsiness_detector.camera.cap.release()
                            except Exception as e:
                                print(f"Error releasing camera capture: {e}")
                    except Exception as e:
                        print(f"Error stopping drowsiness detector camera: {e}")
                
                # Call stop_detection if it exists
                if hasattr(self.drowsiness_detector, 'stop_detection'):
                    try:
                        self.drowsiness_detector.stop_detection()
                    except Exception as e:
                        print(f"Error in drowsiness detector stop_detection: {e}")
                
                # Additional cleanup for the detector if needed
                if hasattr(self.drowsiness_detector, 'cleanup'):
                    try:
                        self.drowsiness_detector.cleanup()
                    except Exception as e:
                        print(f"Error in drowsiness detector cleanup: {e}")
                
            except Exception as e:
                print(f"Error during drowsiness detection cleanup: {e}")
        
        # Ensure all OpenCV windows are closed
        try:
            cv2.destroyAllWindows()
        except Exception as e:
            print(f"Error closing OpenCV windows: {e}")
        
        # Reset the stop event for future use
        if hasattr(self, '_drowsiness_stop_event'):
            self._drowsiness_stop_event.clear()
            
        print("Drowsiness detection stopped and resources cleaned up")
    
    def _handle_drowsiness_detected(self):
        """Handle when drowsiness is detected."""
        if not self.study_timer_active or self.study_timer_paused:
            return
            
        # Pause the timer
        was_running = self.study_timer_active and not self.study_timer_paused
        if was_running:
            self.pause_resume_study_session()
        
        # Show warning
        messagebox.showwarning(
            "Drowsiness Detected",
            "You seem to be getting drowsy! The timer has been paused. "
            "Take a short break, stretch, or get some fresh air before continuing.",
            parent=self.parent
        )
        
        # If the timer was running before, give option to resume
        if was_running and messagebox.askyesno(
            "Resume Study Session",
            "Would you like to resume your study session?",
            parent=self.parent
        ):
            self.pause_resume_study_session()
    
    def show_settings(self):
        """Show unified settings window."""
        try:
            # Get has_dev_key from app_controller if available
            has_dev_key = getattr(self.app_controller, 'has_dev_key', False)
            
            # Pass correct arguments including has_dev_key and game_screen reference
            show_unified_settings(
                parent=self.parent, 
                app_state=self.app_state,
                title="StudyPet Settings - Game Screen",
                has_dev_key=has_dev_key,
                game_screen=self  # Pass self as game_screen for proper cleanup
            )
        except Exception as e:
            error_msg = f"Could not open settings: {str(e)}"
            print(f"Error in show_settings: {error_msg}")
            messagebox.showerror(
                "Error",
                error_msg,
                parent=self.parent
            )

    def handle_window_resize(self, event):
        """Handle window resize events."""
        try:
            # Check if parent exists and has the after method
            if not hasattr(self, 'parent') or not hasattr(self.parent, 'after'):
                return
                
            # Cancel any pending resize
            if hasattr(self, '_resize_after_id') and self._resize_after_id is not None:
                try:
                    self.parent.after_cancel(self._resize_after_id)
                except (tk.TclError, AttributeError):
                    pass
            
            # Schedule the update
            try:
                self._resize_after_id = self.parent.after(150, self.update_pet_info_display)
            except (tk.TclError, AttributeError):
                self._resize_after_id = None
        except Exception as e:
            print(f"Error in handle_window_resize: {e}")
            import traceback
            traceback.print_exc()

    def add_mastery(self, amount=50):
        """
        Add mastery points to the current pet using the global state.
        
        Args:
            amount (int): Amount of mastery to add (default: 50)
        """
        from models.pet_state import global_pet_state
        
        try:
            # Store old stage to check for evolution
            old_stage = global_pet_state.stage
            
            # Add mastery (this will handle the cap automatically)
            global_pet_state.mastery += amount
            
            # Update the UI
            self.update_pet_info_display()
            
            # Show a small notification
            if hasattr(self, 'show_notification'):
                self.show_notification(f"+{amount} Mastery!")
            
            # Check for evolution
            if global_pet_state.stage != old_stage:
                messagebox.showinfo(
                    "Pet Evolved!",
                    f"Your pet has evolved to {global_pet_state.stage.name.replace('_', ' ').title()}!"
                )
                
            print(f"Added {amount} mastery points. New total: {global_pet_state.mastery}")
            
        except Exception as e:
            print(f"Error updating mastery: {e}")
            import traceback
            traceback.print_exc()

    def subtract_mastery(self, amount=20):
        """
        Subtract mastery points from the current pet using the global state.
        
        Args:
            amount (int): Amount of mastery to subtract (default: 20)
        """
        from models.pet_state import global_pet_state
        
        try:
            # Store old mastery for notification
            old_mastery = global_pet_state.mastery
            
            # Subtract mastery (ensuring it doesn't go below 0)
            new_mastery = max(0, old_mastery - amount)
            global_pet_state.mastery = new_mastery
            
            # Update the UI
            self.update_pet_info_display()
            
            # Show a small notification
            if hasattr(self, 'show_notification'):
                self.show_notification(f"-{amount} Mastery!")
                
            print(f"Subtracted {amount} mastery points. New total: {new_mastery}")
            
        except Exception as e:
            print(f"Error subtracting mastery: {e}")
            import traceback
            traceback.print_exc()

    def set_pet_stage(self):
        """Open a dialog to set the pet's stage directly."""
        from models.pet_state import global_pet_state, PetStage
        from tkinter import simpledialog
        
        try:
            current_stage = global_pet_state.stage
            
            stage = simpledialog.askinteger(
                "Set Pet Stage",
                f"Enter stage (1-5):\n1. Egg\n2. Baby\n3. Child\n4. Grown\n5. Battle Fit\n\nCurrent: {current_stage.name.replace('_', ' ').title()} ({current_stage.value})",
                parent=self.parent,
                minvalue=1,
                maxvalue=5
            )
            
            if stage is not None:
                # Convert to PetStage enum
                new_stage = PetStage(stage)
                global_pet_state.stage = new_stage
                
                # Update UI
                self.update_pet_info_display()
                
                # Show success message
                messagebox.showinfo(
                    "Stage Updated",
                    f"Pet stage set to {new_stage.name.replace('_', ' ').title()}"
                )
                
                print(f"Pet stage set to {new_stage.name}")
                
        except Exception as e:
            print(f"Error setting pet stage: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Failed to set stage: {e}")

    def set_pet_emotion(self):
        """Set the pet's emotion through a dialog."""
        from models.pet_state import global_pet_state, PetEmotion
        from tkinter import simpledialog, messagebox
        
        try:
            current_emotion = global_pet_state.emotion
            
            # Show dialog to select new emotion
            emotion_names = [e.name for e in PetEmotion]
            emotion = simpledialog.askstring(
                "Set Pet Emotion",
                f"Current emotion: {current_emotion.name}\n\n"
                f"Available emotions: {', '.join(emotion_names)}\n"
                "Enter new emotion:",
                parent=self.parent
            )
            
            if emotion and emotion.upper() in emotion_names:
                # Set the new emotion
                global_pet_state.emotion = PetEmotion[emotion.upper()]
                
                # Update the UI
                self.update_pet_info_display()
                
                # Show a small notification
                if hasattr(self, 'show_notification'):
                    self.show_notification(f"Pet emotion changed to {emotion.upper()}")
                
                print(f"Pet emotion changed to {emotion.upper()}")
            
        except Exception as e:
            print(f"Error resetting Mastery: {e}")
            import traceback
            traceback.print_exc()

    def force_evolve(self):
        """Force the pet to evolve to the next stage using the global state."""
        from models.pet_state import global_pet_state, PetStage
        
        try:
            # Store current stage before evolving
            old_stage = global_pet_state.stage
            
            # Check if already at max stage
            if old_stage == PetStage.BATTLE_FIT:
                if hasattr(self, 'show_notification'):
                    self.show_notification("Max stage reached!")
                messagebox.showinfo(
                    "Max Stage",
                    "Your pet is already at the maximum evolution stage!"
                )
                return
                
            # Move to next stage
            global_pet_state.stage = PetStage(old_stage.value + 1)
            
            # Update UI
            self.update_pet_info_display()
            
            # Show evolution message
            messagebox.showinfo(
                "Pet Evolved!",
                f"Your pet has evolved from {old_stage.name.replace('_', ' ').title()} to {global_pet_state.stage.name.replace('_', ' ').title()}!"
            )
            
            print(f"Pet force evolved to {global_pet_state.stage.name}")
            
        except Exception as e:
            print(f"Error forcing evolution: {e}")
            import traceback
            traceback.print_exc()

    def _handle_pet_evolution(self, old_stage, new_stage):
        """Handle pet evolution event by updating the display."""
        try:
            print(f"Pet evolved from {old_stage.name} to {new_stage.name}")
            
            # Update the pet info display
            self.update_pet_info_display()
            
            # Reinitialize the playground with the new stage
            current_pet = self.app_state.get_current_pet()
            if current_pet and hasattr(self, 'playground_canvas'):
                # Ensure pet_type is a string
                pet_type = str(current_pet.pet_type)
                if hasattr(current_pet.pet_type, 'value'):  # If it's an enum with value
                    pet_type = str(current_pet.pet_type.value)
                elif hasattr(current_pet.pet_type, 'name'):  # If it's an enum with name
                    pet_type = str(current_pet.pet_type.name)
                
                # Also ensure emotion is a string
                emotion = getattr(current_pet, 'emotion', 'HAPPY')
                if hasattr(emotion, 'name'):  # If it's an enum
                    emotion = emotion.name
                
                # Reinitialize the playground with pet type
                # Stage and emotion will be taken from global_pet_state
                self._init_playground_immediately(pet_type
                )
                
                # Show evolution notification
                if hasattr(self, 'show_notification'):
                    self.show_notification(f"Evolved to {new_stage.name.replace('_', ' ').title()}!")
                    
        except Exception as e:
            print(f"Error handling pet evolution: {e}")
            import traceback
            traceback.print_exc()
    
    def refresh_developer_ui(self):
        """Update developer UI elements based on current state."""
        if hasattr(self, 'dev_tools_frame'):
            if self.developer_mode:
                self.dev_tools_frame.pack(fill="x", pady=(10, 5), padx=5)
                # Update status panel height if expanded
                if hasattr(self, 'status_expanded') and self.status_expanded and hasattr(self, 'status_container'):
                    self.status_container.place_configure(height=350)
            else:
                self.dev_tools_frame.pack_forget()
                # Reset status panel height if expanded
                if hasattr(self, 'status_expanded') and self.status_expanded and hasattr(self, 'status_container'):
                    self.status_container.place_configure(height=240)
