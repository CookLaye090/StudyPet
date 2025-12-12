"""Notification system for StudyPet application with smooth scrolling effects."""
import tkinter as tk
from tkinter import ttk
import time
import threading
from math import sin, pi

class StudyPetNotification:
    @staticmethod
    def show_camera_permission(parent, choice_callback=None):
        """
        Show a notification for camera permission (stub for compatibility).
        
        Args:
            parent: Parent window
            choice_callback: Callback function that receives (success, None)
        """
        # For compatibility, immediately call back with camera not available
        if choice_callback:
            parent.after(100, lambda: choice_callback(False, None))

        # Create a top-level window
        win = tk.Toplevel(parent)
        win.title("Notification")
        win.resizable(False, False)
        win.overrideredirect(True)  # Remove window decorations for smoother animation
        win.withdraw()  # Hide until we're ready to show with animation
        
        # Set window size and calculate position for animation
        window_width = 400
        window_height = 200
        
        # Set a fixed size for the window
        win.geometry(f"{window_width}x{window_height}")
        
        # Calculate position for centering on screen
        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()
        start_x = screen_width  # Start off-screen to the right
        target_x = (screen_width - window_width) // 2
        target_y = (screen_height - window_height) // 2
        
        # Create main container
        container = tk.Frame(win, bg='#f0f0f0', padx=20, pady=20)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Add title
        title = tk.Label(container, text="Notification", 
                        font=('Arial', 14, 'bold'), bg='#f0f0f0')
        title.pack(pady=(0, 15))
        
        # Add message
        message = "This is a notification."
        msg_label = tk.Label(container, text=message, justify=tk.LEFT, 
                           wraplength=window_width-40, bg='#f0f0f0')
        msg_label.pack(pady=(0, 20))
        
        # Button frame
        btn_frame = tk.Frame(container, bg='#f0f0f0')
        btn_frame.pack()
        
        # Accept button
        accept_btn = tk.Button(btn_frame, text="OK", 
                             command=lambda: win.destroy(), width=12)
        accept_btn.pack(side=tk.LEFT, padx=10)
        
        # Configure button styles
        for btn in [accept_btn]:
            btn.configure(
                bg='#e0e0e0',
                activebackground='#d0d0d0',
                relief=tk.FLAT,
                padx=10,
                pady=5
            )
            
            # Add hover effects
            def on_enter(e):
                e.widget['bg'] = '#d0d0d0'
                e.widget['relief'] = 'sunken'
                
            def on_leave(e):
                e.widget['bg'] = '#e0e0e0'
                e.widget['relief'] = 'flat'
                
            btn.bind('<Enter>', on_enter)
            btn.bind('<Leave>', on_leave)
        
        # Show the window with animation
        def slide_in():
            nonlocal start_x
            if start_x > target_x:
                distance = start_x - target_x
                move = max(20, int(distance * 0.3))
                start_x -= move
                win.geometry(f"{window_width}x{window_height}+{start_x}+{target_y}")
                win.after(16, slide_in)
            else:
                win.geometry(f"{window_width}x{window_height}+{target_x}+{target_y}")
        
        # Position window off-screen to the right and start animation
        win.geometry(f"{window_width}x{window_height}+{start_x}+{target_y}")
        win.after(100, slide_in)
        win.geometry(f"{window_width}x{window_height}+{start_x}+{target_y}")
        win.deiconify()  # Show the window (still off-screen)
        win.update()  # Force update to ensure window is rendered
        
        # Make window modal after it's shown
        win.transient(parent)
        win.grab_set()
        win.focus_force()
        
        # Animate window sliding in from the right
        def slide_in():
            nonlocal start_x
            if start_x > target_x:
                # Ease-out animation (starts fast, slows down)
                distance = start_x - target_x
                move = max(20, int(distance * 0.2))  # Never move less than 20px per frame
                start_x -= move
                win.geometry(f"{window_width}x{window_height}+{start_x}+{target_y}")
                win.after(16, slide_in)  # ~60fps
            else:
                win.geometry(f"{window_width}x{window_height}+{target_x}+{target_y}")
        
        # Start the slide-in animation
        slide_in()
        
        # Create main container with padding and border
        main_container = ttk.Frame(win)
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Create a frame that will contain both content and buttons
        content_container = ttk.Frame(main_container)
        content_container.pack(fill=tk.BOTH, expand=True)
        
        # Main content frame that will contain the scrollable area
        content_frame = ttk.Frame(content_container)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))  # Add bottom margin for buttons
        
        # Create canvas with scrollbar and subtle border
        canvas = tk.Canvas(content_frame, highlightthickness=0, bd=0, bg='white')
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, padding=(20, 15))
        
        # Configure the canvas scrolling
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        # Create window in canvas to hold the scrollable frame
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack the canvas and scrollbar in a frame with some padding at the bottom
        canvas_frame = ttk.Frame(content_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        # Add mouse wheel scrolling with safety checks
        def _on_mousewheel(event):
            try:
                if canvas.winfo_exists():  # Check if canvas still exists
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except tk.TclError:
                # If we get here, the canvas was destroyed - unbind the event
                canvas.unbind_all("<MouseWheel>")
        
        # Store the binding ID so we can unbind it later
        canvas._mousewheel_binding = canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Main content container inside scrollable frame
        container = ttk.Frame(scrollable_frame, padding=20)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title = ttk.Label(
            container,
            text="📷 Camera Access for Study Session",
            font=("Arial", 12, "bold")
        )
        title.pack(pady=(0, 15), anchor='w')
        
        # Message with more detailed information that might require scrolling
        message_text = ("Would you like to enable camera access during study sessions?\n\n"
                      "🔍 This feature helps track your focus and attention by monitoring when you're at your desk.\n\n"
                      "✅ Highly recommended for computer-based learning as it helps you stay accountable.\n\n"
                      "🔒 Your privacy is respected - no recordings or images are saved. The camera is only used to detect presence.\n\n"
                      "⚙️ You can change this setting at any time in the application settings.\n\n"
                      "📊 The data helps improve your study analytics and pet's responsiveness to your study habits.")
        
        message = ttk.Label(
            container,
            text=message_text,
            wraplength=350,
            justify=tk.LEFT
        )
        message.pack(pady=(0, 20), anchor='w')
        
        # Make sure the scrollbar appears when content is too long
        def check_scroll_needed():
            canvas.update_idletasks()
            if container.winfo_height() > 300:  # If content is taller than 300px
                canvas.configure(height=300)  # Set a fixed height with scrollbar
            else:
                canvas.configure(height=container.winfo_height())
        
        win.after(100, check_scroll_needed)  # Check after UI is rendered
        
        # Button frame right below the content
        button_frame = ttk.Frame(content_container)
        button_frame.pack(fill=tk.X, pady=(10, 5))  # Add top margin to separate from content
        
        # Configure button styles
        style = ttk.Style()
        
        # Style for the primary action button
        style.configure('Accept.TButton', 
                      font=('Arial', 10, 'bold'),
                      padding=10,
                      foreground='white')
        
        # Style for the secondary action button
        style.configure('Decline.TButton',
                      font=('Arial', 10),
                      padding=10)
        
        # Accept button (primary action)
        accept_btn = tk.Button(
            button_frame,
            text="✓  Enable Camera",
            command=on_accept,
            bg='#4CAF50',  # Green color
            fg='white',
            activebackground='#45a049',
            activeforeground='white',
            bd=0,
            relief='flat',
            padx=30,
            pady=10,
            font=('Arial', 11, 'bold'),
            cursor='hand2',
            highlightthickness=0
        )
        accept_btn.pack(side=tk.RIGHT, padx=(15, 0), ipady=4)
        
        # Decline button (secondary action)
        decline_btn = tk.Button(
            button_frame,
            text="Not Now",
            command=on_decline,
            bg='#f0f0f0',
            fg='#333',
            activebackground='#e0e0e0',
            activeforeground='#000',
            bd=0,
            relief='flat',
            padx=30,
            pady=10,
            font=('Arial', 11),
            cursor='hand2',
            highlightthickness=0
        )
        decline_btn.pack(side=tk.RIGHT, ipady=4)
        
        # Add hover effects
        def on_enter_accept(e):
            accept_btn['bg'] = '#45a049'
            accept_btn['relief'] = 'sunken'
            
        def on_leave_accept(e):
            accept_btn['bg'] = '#4CAF50'
            accept_btn['relief'] = 'flat'
            
        def on_enter_decline(e):
            decline_btn['bg'] = '#e0e0e0'
            decline_btn['relief'] = 'sunken'
            
        def on_leave_decline(e):
            decline_btn['bg'] = '#f0f0f0'
            decline_btn['relief'] = 'flat'
        
        # Bind hover events
        accept_btn.bind('<Enter>', on_enter_accept)
        accept_btn.bind('<Leave>', on_leave_accept)
        decline_btn.bind('<Enter>', on_enter_decline)
        decline_btn.bind('<Leave>', on_leave_decline)
        
        def on_choice(choice, cam_manager):
            """Handle user's choice and close the window with animation."""
            if choice_callback:
                choice_callback(choice, cam_manager)
        
        # Make sure the window stays on top during animation
        win.lift()
        win.attributes('-topmost', True)
        win.after(100, lambda: win.attributes('-topmost', False))

if __name__ == "__main__":
    # Test the notification
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    def handle_choice(choice):
        print(f"User chose to {'enable' if choice else 'disable'} camera")
        root.quit()
    
    StudyPetNotification.ask_camera_permission(root, handle_choice)
    root.mainloop()
