"""
Playground Renderer - Renders the pet playground with animations
"""

import tkinter as tk
from tkinter import Canvas
from PIL import Image, ImageTk, ImageOps
import os
import time
import logging
from graphics.pet_playground import PetPlayground, PetAnimation, PetEnvironment, PetMovementPattern

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlaygroundRenderer:
    """Renders the pet playground environment with animations"""

    def __init__(self, canvas: Canvas, pet_type: str, pet_stage: int, pet_emotion: str = "normal"):
        self.canvas = canvas
        self.pet_type = pet_type.lower()
        self.pet_stage = pet_stage
        self.pet_emotion = pet_emotion.lower()
        
        # Set up canvas
        self.canvas.update_idletasks()
        self.width = max(self.canvas.winfo_width(), 800)
        self.height = max(self.canvas.winfo_height(), 600)
        self.canvas.configure(width=self.width, height=height)
        
        # Initialize playground
        self.playground = PetPlayground(pet_type, self.width, self.height, pet_stage)
        
        # Pet display state
        self.pet_image = None
        self.pet_photo = None
        self.pet_id = None
        self.pet_x = self.width // 2
        self.pet_y = self.height // 2
        
        # Animation
        self.animation_timer = None
        self.update_interval = 50  # 20 FPS
        self.is_moving = False
        self.target_x = self.pet_x
        self.target_y = self.pet_y
        self.speed = 5
        
        # Load pet image
        self._load_pet_image()
        
        # Set up event bindings
        self._setup_bindings()
        
        # Start animation loop
        self._start_animation()

        self._setup_canvas()
        self._load_placeholder_assets()
        self._load_background_image()
        self._load_pet_image()
        self._render_environment()
        self._start_animation_loop()

    def _setup_canvas(self):
        """Configure canvas"""
        # Get background color from environment config immediately
        config = self.playground.get_environment_config()
        bg_color = config.get("bg_color", "#FFFFFF")
        self.canvas.configure(bg=bg_color, width=self.width, height=self.height)

    def _load_placeholder_assets(self):
        """Load or create placeholder assets for pets, decorations, and toys"""
        # For now, we'll use colored rectangles as placeholders
        # Later these can be replaced with actual sprite images

        # Pet placeholder (will be replaced with actual pet image)
        self.pet_images = {
            PetAnimation.IDLE: self._create_placeholder_pet("blue"),
            PetAnimation.WALK_LEFT: self._create_placeholder_pet("green"),
            PetAnimation.WALK_RIGHT: self._create_placeholder_pet("green"),
            PetAnimation.SWIM_LEFT: self._create_placeholder_pet("cyan"),
            PetAnimation.SWIM_RIGHT: self._create_placeholder_pet("cyan"),
            PetAnimation.SWIM_UP: self._create_placeholder_pet("lightblue"),
            PetAnimation.SWIM_DOWN: self._create_placeholder_pet("lightblue"),
        }

    def _create_placeholder_pet(self, color: str):
        """Create a placeholder colored rectangle for pet"""
        # This will be replaced with actual sprite loading
        return {"color": color, "size": 120}

    def _load_background_image(self):
        """Attempt to load a background image for current pet type.
        Looks under <project_root>/img/Background/ with pet-specific filenames.
        """
        try:
            # Compute project root from src/graphics/..
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            bg_dir = os.path.join(project_root, 'img', 'Background')
            if not os.path.isdir(bg_dir):
                # Set background color directly on canvas instead of relying on image
                config = self.playground.get_environment_config()
                bg_color = config.get("bg_color", "#FFFFFF")
                self.canvas.configure(bg=bg_color)
                self.background_image_tk = None
                return

            # Candidate filenames (case and extension variations)
            pet = self.pet_type
            candidates = [
                f"{pet}.png", f"{pet}.jpg", f"{pet}.jpeg",
                f"{pet.lower()}.png", f"{pet.lower()}.jpg", f"{pet.lower()}.jpeg",
                f"{pet.title()}.png", f"{pet.title()}.jpg", f"{pet.title()}.jpeg",
            ]
            chosen = None
            for name in candidates:
                path = os.path.join(bg_dir, name)
                if os.path.exists(path):
                    chosen = path
                    break

            if not chosen:
                # No background image found, use solid color
                config = self.playground.get_environment_config()
                bg_color = config.get("bg_color", "#FFFFFF")
                self.canvas.configure(bg=bg_color)
                self.background_image_tk = None
                return

            # Load and scale to canvas size
            img = Image.open(chosen).convert('RGB')
            # Ensure dimensions are current
            self.canvas.update_idletasks()
            self.width = max(self.canvas.winfo_width(), 800)
            self.height = max(self.canvas.winfo_height(), 600)
            img = img.resize((self.width, self.height))
            self.background_image_tk = ImageTk.PhotoImage(img)
        except Exception:
            # Any error in loading, use solid background color
            config = self.playground.get_environment_config()
            bg_color = config.get("bg_color", "#FFFFFF")
            self.canvas.configure(bg=bg_color)
            self.background_image_tk = None

    def _get_cache_key(self):
        """Generate a cache key for the current pet state."""
        return f"{self.pet_type}_{self.pet_stage}_{self.pet_emotion}"
        
    def _load_pet_image(self):
        """Load the pet image with fallback to a colored rectangle"""
        try:
            # Try to load the pet image
            img_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'assets', 'pets', self.pet_type, f"{self.pet_type}_{self.pet_emotion}.png"
            )
            
            if os.path.exists(img_path):
                self.pet_image = Image.open(img_path).convert('RGBA')
                # Resize if needed
                self.pet_image = self.pet_image.resize((100, 100), Image.Resampling.LANCZOS)
            else:
                # Create a fallback image
                logger.warning(f"Pet image not found at {img_path}, using fallback")
                self._create_fallback_image()
                
            # Convert to PhotoImage for Tkinter
            self.pet_photo = ImageTk.PhotoImage(self.pet_image)
            
            # Create or update the pet on canvas
            if self.pet_id is None:
                self.pet_id = self.canvas.create_image(
                    self.pet_x, self.pet_y,
                    image=self.pet_photo,
                    anchor=tk.CENTER
                )
            else:
                self.canvas.itemconfig(self.pet_id, image=self.pet_photo)
                
            return True
            
        except Exception as e:
            logger.error(f"Error loading pet image: {e}")
            self._create_fallback_image()
            return False
    
    def _create_fallback_image(self):
        """Create a simple colored rectangle as a fallback"""
        from PIL import ImageDraw
        
        # Choose color based on pet type
        colors = {
            'cat': 'gray', 'dog': 'brown', 'axolotl': 'pink',
            'raccoon': 'darkgray', 'penguin': 'black'
        }
        color = colors.get(self.pet_type, 'blue')
        
        # Create a simple image
        self.pet_image = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
        draw = ImageDraw.Draw(self.pet_image)
        draw.ellipse((10, 10, 90, 90), fill=color)
        
        # Add text
        draw.text((50, 50), self.pet_type[0].upper(), fill='white', anchor='mm')
        
        # Convert to PhotoImage
        self.pet_photo = ImageTk.PhotoImage(self.pet_image)

    def stop_animation(self):
        """Stop the animation loop"""
        if self.animation_timer:
            self.canvas.after_cancel(self.animation_timer)
            self.animation_timer = None
    

    def update_pet_emotion(self, new_emotion: str):
        """Update pet emotion and reload sprite."""
        if new_emotion != self.pet_emotion:
            self.pet_emotion = new_emotion or self.pet_emotion
            self._load_pet_image(force_reload=True)
            # Reset rendering state to force update
            self.last_rendered_image = None

    def update_pet_stage(self, new_stage: int):
        """Update pet stage (may affect appearance)"""
        if new_stage != self.pet_stage:
            self.pet_stage = new_stage
            self.playground.update_pet_stage(new_stage)
            self._load_pet_image(force_reload=True)
            # Reset rendering state to force update
            self.last_rendered_image = None
            # If hatched (stage > 1), re-enable movement soon
            try:
                if int(new_stage) > 1:
                    # Nudge timers so a new movement can start shortly
                    self.playground.last_movement_time = time.time() - 5
                    self.playground.next_movement_delay = 2
                    # All pets already at correct ground level
            except Exception:
                pass

    def cleanup(self):
        """Clean up resources"""
        self.stop_animation()
        self.canvas.delete("all")
        # Clear image cache to free memory
        self.image_cache.clear()
