#!/usr/bin/env python3
"""
Simple Voice Box - Just the speech bubble without AI
"""
import tkinter as tk
from tkinter import ttk

class SimpleVoiceBox:
    """A simple speech bubble that appears above the pet."""

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


def show_voice_box(canvas, pet_x, pet_y, message, duration=4000):
    """Simple function to show a voice box."""
    return SimpleVoiceBox(canvas, pet_x, pet_y, message, duration)
