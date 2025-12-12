#!/usr/bin/env python3
"""
Voice Box Component for StudyPet
A speech bubble that appears above the pet when it wants to communicate
"""
import tkinter as tk
from tkinter import ttk
import threading
import time

class VoiceBox:
    """A speech bubble that appears above the pet to show messages."""

    def __init__(self, parent_canvas, pet_x, pet_y, message="Hello!", duration=3000):
        """
        Initialize the voice box.

        Args:
            parent_canvas: The canvas where the pet is displayed
            pet_x: Pet's X coordinate
            pet_y: Pet's Y coordinate (top of pet)
            message: Message to display
            duration: How long to show the message (ms)
        """
        self.canvas = parent_canvas
        self.pet_x = pet_x
        self.pet_y = pet_y
        self.message = message
        self.duration = duration

        # Voice box dimensions
        self.bubble_width = 200
        self.bubble_height = 80
        self.arrow_height = 20
        self.padding = 15

        # Calculate bubble position (above pet, centered)
        self.bubble_x = pet_x - self.bubble_width // 2
        self.bubble_y = pet_y - self.bubble_height - self.arrow_height - 10

        # Create the voice box
        self.create_voice_box()

        # Auto-hide after duration
        if duration > 0:
            self.canvas.after(duration, self.hide)

    def create_voice_box(self):
        """Create the visual speech bubble."""
        # Main bubble (rounded rectangle)
        self.bubble = self.canvas.create_oval(
            self.bubble_x, self.bubble_y,
            self.bubble_x + self.bubble_width,
            self.bubble_y + self.bubble_height,
            fill="white", outline="#cccccc", width=2
        )

        # Speech bubble arrow (triangle pointing down)
        arrow_points = [
            self.pet_x - 10, self.bubble_y + self.bubble_height,  # Left point
            self.pet_x + 10, self.bubble_y + self.bubble_height,  # Right point
            self.pet_x, self.bubble_y + self.bubble_height + self.arrow_height  # Bottom point
        ]
        self.arrow = self.canvas.create_polygon(
            arrow_points,
            fill="white", outline="#cccccc", width=2
        )

        # Message text
        self.text = self.canvas.create_text(
            self.bubble_x + self.bubble_width // 2,
            self.bubble_y + self.bubble_height // 2,
            text=self.message,
            font=("Arial", 10, "bold"),
            fill="#333333",
            justify="center",
            width=self.bubble_width - 2 * self.padding
        )

        # Bring to front
        self.canvas.tag_raise(self.bubble)
        self.canvas.tag_raise(self.arrow)
        self.canvas.tag_raise(self.text)

    def update_message(self, new_message):
        """Update the message text."""
        self.message = new_message
        self.canvas.itemconfig(self.text, text=new_message)

    def move_to_pet(self, pet_x, pet_y):
        """Move the voice box to follow the pet."""
        self.pet_x = pet_x
        self.pet_y = pet_y

        # Recalculate position
        bubble_x = pet_x - self.bubble_width // 2
        bubble_y = pet_y - self.bubble_height - self.arrow_height - 10

        # Update bubble position
        self.canvas.coords(
            self.bubble,
            bubble_x, bubble_y,
            bubble_x + self.bubble_width,
            bubble_y + self.bubble_height
        )

        # Update arrow position
        arrow_points = [
            pet_x - 10, bubble_y + self.bubble_height,
            pet_x + 10, bubble_y + self.bubble_height,
            pet_x, bubble_y + self.bubble_height + self.arrow_height
        ]
        self.canvas.coords(self.arrow, *arrow_points)

        # Update text position
        self.canvas.coords(
            self.text,
            bubble_x + self.bubble_width // 2,
            bubble_y + self.bubble_height // 2
        )

    def hide(self):
        """Hide the voice box."""
        try:
            self.canvas.delete(self.bubble)
            self.canvas.delete(self.arrow)
            self.canvas.delete(self.text)
        except:
            pass  # Already deleted

    def destroy(self):
        """Destroy the voice box."""
        self.hide()


class PetVoiceSystem:
    """Manages voice box functionality for the pet."""

    def __init__(self, main_game_screen):
        """
        Initialize the pet voice system.

        Args:
            main_game_screen: Reference to the MainGameScreen instance
        """
        self.game_screen = main_game_screen
        self.canvas = main_game_screen.playground_canvas
        self.current_pet = None
        self.voice_box = None
        self.is_speaking = False

        # Voice check settings
        self.check_interval = 60  # Check every 60 seconds during study
        self.check_timer = None

        # Focus detection (placeholder - would need actual implementation)
        self.last_activity_time = time.time()
        self.focus_threshold = 300  # 5 minutes of inactivity = unfocused

    def start_study_session(self):
        """Start monitoring during study sessions."""
        if self.check_timer:
            self.canvas.after_cancel(self.check_timer)

        # Start periodic focus checks
        self._schedule_next_check()

    def stop_study_session(self):
        """Stop monitoring when study session ends."""
        if self.check_timer:
            self.canvas.after_cancel(self.check_timer)
            self.check_timer = None

        # Hide any active voice box
        if self.voice_box:
            self.voice_box.hide()
            self.voice_box = None

    def _schedule_next_check(self):
        """Schedule the next focus check."""
        if self.check_timer:
            self.canvas.after_cancel(self.check_timer)

        self.check_timer = self.canvas.after(
            self.check_interval * 1000,
            self._perform_focus_check
        )

    def _perform_focus_check(self):
        """Check if user is focused and respond accordingly."""
        current_time = time.time()
        time_since_activity = current_time - self.last_activity_time

        # Get current pet for personalized messages
        current_pet = self.game_screen.app_state.get_current_pet()
        if not current_pet:
            self._schedule_next_check()
            return

        pet_name = current_pet.name

        if time_since_activity > self.focus_threshold:
            # User seems unfocused - encourage them
            self.speak(self._get_encouragement_message(pet_name))
        else:
            # User is focused - give positive feedback
            self.speak(self._get_positive_message(pet_name))

        # Schedule next check
        self._schedule_next_check()

    def _get_encouragement_message(self, pet_name):
        """Get a random encouragement message."""
        messages = [
            f"Hey {pet_name}! I notice you've been away. Ready to get back to studying? 📚",
            f"{pet_name} here! Don't forget about our study goals! 🌟",
            f"Hi {pet_name}! Let's focus together and crush those study sessions! 💪",
            f"{pet_name} checking in! How's the studying going? I believe in you! ✨",
            f"Hey there! {pet_name} wants to remind you: every minute counts! ⏰"
        ]
        import random
        return random.choice(messages)

    def _get_positive_message(self, pet_name):
        """Get a random positive reinforcement message."""
        messages = [
            f"Great focus, {pet_name}! Keep it up! 🎉",
            f"You're doing amazing! {pet_name} is proud of you! 🏆",
            f"Excellent work! {pet_name} loves seeing you study! ⭐",
            f"You're on fire today! Keep going! 🔥",
            f"Fantastic progress! {pet_name} is cheering you on! 📈"
        ]
        import random
        return random.choice(messages)

    def speak(self, message, duration=4000):
        """
        Make the pet speak a message.

        Args:
            message: The message to display
            duration: How long to show the message (ms)
        """
        # Hide any existing voice box
        if self.voice_box:
            self.voice_box.hide()

        # Get current pet position
        current_pet = self.game_screen.app_state.get_current_pet()
        if not current_pet or not self.game_screen.playground_renderer:
            return

        # Get pet position from renderer
        pet_x, pet_y = self.game_screen.playground_renderer.playground.get_pet_position()

        # Create new voice box
        self.voice_box = VoiceBox(
            self.canvas,
            pet_x,
            pet_y,
            message,
            duration
        )

        self.is_speaking = True

    def update_pet_position(self):
        """Update voice box position when pet moves."""
        if self.voice_box and self.game_screen.playground_renderer:
            pet_x, pet_y = self.game_screen.playground_renderer.playground.get_pet_position()
            self.voice_box.move_to_pet(pet_x, pet_y)

    def on_user_activity(self):
        """Call this when user shows activity (mouse, keyboard, etc.)."""
        self.last_activity_time = time.time()

    def destroy(self):
        """Clean up the voice system."""
        self.stop_study_session()
        if self.voice_box:
            self.voice_box.destroy()
            self.voice_box = None
