"""
Simple Chat UI - A clean chat interface for StudyPet
Displays chat UI without functional chatbot (Coming Soon)
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime


class SimpleChatUI:
    """Simple chat interface with modern UI design."""
    
    def __init__(self, parent_frame, pet_name="Pet"):
        """
        Initialize the chat UI.
        
        Args:
            parent_frame: Parent tkinter frame to contain the chat
            pet_name: Name of the pet for display
        """
        self.parent_frame = parent_frame
        self.pet_name = pet_name
        self.messages = []
        
        self.create_interface()
        self.add_welcome_message()
    
    def create_interface(self):
        """Create the chat interface components."""
        # Main container
        self.chat_container = ttk.Frame(self.parent_frame)
        self.chat_container.pack(fill="both", expand=True)
        
        # Chat display area with scrollbar
        display_frame = ttk.Frame(self.chat_container)
        display_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Scrolled text widget for messages
        self.chat_display = scrolledtext.ScrolledText(
            display_frame,
            wrap=tk.WORD,
            width=40,
            height=15,
            font=("Arial", 10),
            bg="#F5F5F5",
            fg="#000000",
            state=tk.DISABLED,
            relief="flat",
            padx=10,
            pady=10
        )
        self.chat_display.pack(fill="both", expand=True)
        
        # Configure text tags for styling
        self.chat_display.tag_config("pet", foreground="#0066CC", font=("Arial", 10, "bold"))
        self.chat_display.tag_config("user", foreground="#006600", font=("Arial", 10, "bold"))
        self.chat_display.tag_config("system", foreground="#666666", font=("Arial", 9, "italic"))
        self.chat_display.tag_config("timestamp", foreground="#999999", font=("Arial", 8))
        
        # Input area
        input_frame = ttk.Frame(self.chat_container)
        input_frame.pack(fill="x", padx=5, pady=(0, 5))
        
        # Text input
        self.message_entry = tk.Text(
            input_frame,
            height=3,
            width=30,
            font=("Arial", 10),
            wrap=tk.WORD,
            relief="solid",
            borderwidth=1
        )
        self.message_entry.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Bind Enter key (Shift+Enter for new line)
        self.message_entry.bind("<Return>", self.on_enter_key)
        self.message_entry.bind("<Shift-Return>", lambda e: None)  # Allow Shift+Enter for newline
        
        # Send button
        self.send_button = ttk.Button(
            input_frame,
            text="📤 Send",
            command=self.send_message,
            width=10
        )
        self.send_button.pack(side="right")
        
        # Add placeholder text
        self.add_placeholder()
    
    def add_placeholder(self):
        """Add placeholder text to input field."""
        self.placeholder_active = True
        self.message_entry.delete("1.0", tk.END)
        self.message_entry.insert("1.0", "Type your message here...")
        self.message_entry.config(fg="#999999")
        self.message_entry.bind("<FocusIn>", self.remove_placeholder)
        self.message_entry.bind("<FocusOut>", self.add_placeholder_if_empty)
        self.message_entry.bind("<Key>", self.on_key_press)
    
    def on_key_press(self, event=None):
        """Handle any key press to remove placeholder."""
        if self.placeholder_active:
            self.remove_placeholder()
    
    def remove_placeholder(self, event=None):
        """Remove placeholder text when focused."""
        if self.placeholder_active:
            self.placeholder_active = False
            self.message_entry.delete("1.0", tk.END)
            self.message_entry.config(fg="#000000")
            self.message_entry.unbind("<Key>")
    
    def add_placeholder_if_empty(self, event=None):
        """Add placeholder back if field is empty."""
        if not self.message_entry.get("1.0", "end-1c").strip():
            self.message_entry.delete("1.0", tk.END)
            self.add_placeholder()
    
    def on_enter_key(self, event):
        """Handle Enter key press."""
        # If Shift is held, allow newline
        if event.state & 0x1:  # Shift key
            return None
        
        # Otherwise, send message
        self.send_message()
        return "break"  # Prevent default newline
    
    def send_message(self):
        """Handle sending a message."""
        # Get message text
        message_text = self.message_entry.get("1.0", "end-1c").strip()
        
        # Ignore if placeholder or empty
        if not message_text or message_text == "Type your message here...":
            return
        
        # Add user message to display
        self.add_message(message_text, sender="user")
        
        # Clear input
        self.message_entry.delete("1.0", tk.END)
        self.add_placeholder()
        
        # Show "coming soon" response
        self.parent_frame.after(500, self.show_coming_soon_response)
    
    def show_coming_soon_response(self):
        """Show a 'coming soon' message from the pet."""
        responses = [
            "I'm still learning how to chat! 🐾",
            "Chat feature coming soon! Stay tuned! ✨",
            "I can't wait to talk with you properly! 💕",
            "The developers are working on my voice! 🎤",
            "Soon I'll be able to respond! 🌟"
        ]
        import random
        response = random.choice(responses)
        self.add_message(response, sender="pet")
    
    def add_message(self, message, sender="pet"):
        """
        Add a message to the chat display.
        
        Args:
            message: The message text
            sender: 'pet', 'user', or 'system'
        """
        self.chat_display.config(state=tk.NORMAL)
        was_empty = (len(self.messages) == 0)
        
        # Get timestamp
        timestamp = datetime.now().strftime("%H:%M")
        
        # Format message based on sender
        if sender == "pet":
            sender_name = f"{self.pet_name}"
            tag = "pet"
        elif sender == "user":
            sender_name = "You"
            tag = "user"
        else:
            sender_name = "System"
            tag = "system"
        
        # Add message with formatting
        self.chat_display.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.chat_display.insert(tk.END, f"{sender_name}: ", tag)
        self.chat_display.insert(tk.END, f"{message}\n\n")
        
        # Scroll behavior: top for initial message (visibility), bottom for subsequent
        if was_empty:
            self.chat_display.see("1.0")
        else:
            self.chat_display.see(tk.END)
        
        self.chat_display.config(state=tk.DISABLED)
        
        # Store message
        self.messages.append({
            "sender": sender,
            "message": message,
            "timestamp": timestamp
        })
    
    def add_welcome_message(self):
        """Add initial welcome message."""
        self.add_message(
            f"Hi there! I'm {self.pet_name}! 🐾\n"
            "Chat functionality is coming soon, but feel free to type messages!\n"
            "I'll respond once the developers finish my training! 💕",
            sender="pet"
        )
    
    def clear_chat(self):
        """Clear all messages from the chat."""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete("1.0", tk.END)
        self.chat_display.config(state=tk.DISABLED)
        self.messages = []
        self.add_welcome_message()
    
    def destroy(self):
        """Clean up the chat interface."""
        if self.chat_container:
            self.chat_container.destroy()
