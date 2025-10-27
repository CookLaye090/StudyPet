"""
Playground Renderer - Renders the pet playground with animations
"""

import tkinter as tk
from tkinter import Canvas
from PIL import Image, ImageTk
import os
import time
from graphics.pet_playground import PetPlayground, PetAnimation, PetEnvironment, PetMovementPattern

class PlaygroundRenderer:
    """Renders the pet playground environment with animations"""

    def __init__(self, canvas: Canvas, pet_type: str, pet_stage: int, pet_emotion: str = "normal"):
        self.canvas = canvas
        self.pet_type = pet_type
        self.pet_stage = pet_stage
        self.pet_emotion = pet_emotion or "normal"

        # Get canvas dimensions with fallback
        self.canvas.update_idletasks()
        self.width = max(self.canvas.winfo_width(), 800)
        self.height = max(self.canvas.winfo_height(), 600)

        # Ensure canvas has minimum size
        if self.width < 800 or self.height < 600:
            self.width = 800
            self.height = 600
            self.canvas.configure(width=self.width, height=self.height)

        # Initialize playground
        self.playground = PetPlayground(pet_type, self.width, self.height, pet_stage)

        # Canvas items
        self.background_id = None
        self.background_image_tk = None
        self.pet_sprite_id = None
        self.decoration_ids = []
        self.toy_ids = []
        self.pet_image_tk = None
        self.pet_image_size = 320

        # Animation state
        self.animation_frame = 0
        self.animation_timer = None
        self.update_interval = 33  # ms (30 FPS - increased from 20 FPS for smoother movement)

        # Load assets
        self.pet_images = {}
        self.decoration_images = {}
        self.toy_images = {}

        # Pet emoji fallbacks
        self.pet_emojis = {
            'cat': '🐱',
            'dog': '🐶',
            'axolotl': '🦎',
            'raccoon': '🦝',
            'penguin': '🐧'
        }

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

    def _load_pet_image(self):
        """Attempt to load a pet sprite image from <project_root>/img/Pets using
        naming {Pet}_{Stage}_{Emotion} or {Pet}_Egg for stage 1.
        """
        try:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            pet = self.pet_type
            # Candidate directories: img/<Pet>, img/<pet.lower()>, img/<Pet.title()>, img/Pets/<Pet>
            candidate_dirs = [
                os.path.join(project_root, 'img', pet),
                os.path.join(project_root, 'img', str(pet).lower()),
                os.path.join(project_root, 'img', str(pet).title()),
                os.path.join(project_root, 'img', 'Pets', pet),
                os.path.join(project_root, 'img', 'Pets', str(pet).title()),
                os.path.join(project_root, 'img', 'Pets', str(pet).lower()),
            ]
            pet_dir = None
            for d in candidate_dirs:
                if os.path.isdir(d):
                    pet_dir = d
                    break
            if not pet_dir:
                self.pet_image_tk = None
                return
            # Stage naming patterns
            stage_value = int(self.pet_stage)
            emo = (self.pet_emotion or "normal")
            stage_name_map = {
                1: ["Egg"],
                2: ["Baby"],
                3: ["Child", "Teen", "Teenager"],
                4: ["Grown", "Adult"],
                5: ["Battle_Fit", "BattleFit", "Battle-Fit", "Battle"]
            }
            if stage_value == 1:
                stage_names = ["Egg", "egg", "EGG"]
                base_names = []
                for sn in stage_names:
                    base_names += [f"{pet}_{sn}", f"{pet.lower()}_{sn.lower()}", f"{pet.title()}_{sn}"]
            else:
                stage_str_num = str(stage_value)
                base_stage_names = stage_name_map.get(stage_value, [stage_str_num])
                # Expand case and dash/underscore variants
                stage_name_vars = []
                for nm in base_stage_names:
                    variants = {nm, nm.lower(), nm.upper(), nm.title(), nm.replace('-', '_'), nm.replace('_', '-')}
                    stage_name_vars.extend(list(variants))
                emo_vars = [emo, emo.lower(), emo.upper(), emo.title()]
                base_names = []
                for sn in stage_name_vars:
                    for ev in emo_vars:
                        base_names += [
                            f"{pet}_{sn}_{ev}",
                            f"{pet.lower()}_{sn}_{ev}",
                            f"{pet.title()}_{sn}_{ev}",
                            f"{pet}_{stage_str_num}_{ev}",
                            f"{pet.lower()}_{stage_str_num}_{ev}",
                            f"{pet.title()}_{stage_str_num}_{ev}",
                        ]
            candidates = []
            for base in base_names:
                candidates.extend([f"{base}.png", f"{base}.jpg", f"{base}.jpeg"])
            chosen = None
            for name in candidates:
                p = os.path.join(pet_dir, name)
                if os.path.exists(p):
                    chosen = p
                    break
            # Fallback: pick any emotion image for this stage if exact emotion missing
            if not chosen:
                try:
                    files = os.listdir(pet_dir)
                except Exception:
                    files = []
                # Normalize search keys
                stage_str_num = str(stage_value)
                def match_prefixes(fn: str) -> bool:
                    fl = fn.lower()
                    prefixes = []
                    # Stage name variants
                    for sn in (stage_name_vars if stage_value != 1 else ["egg", "Egg", "EGG"]):
                        prefixes.extend([
                            f"{pet.lower()}_{sn.lower()}_",
                            f"{pet.lower()}_{stage_str_num}_"
                        ])
                    return any(fl.startswith(pref) for pref in prefixes)
                for f in files:
                    if f.lower().endswith(('.png', '.jpg', '.jpeg')) and match_prefixes(f):
                        chosen = os.path.join(pet_dir, f)
                        break
            if not chosen:
                self.pet_image_tk = None
                return
            img = Image.open(chosen).convert('RGBA')
            # Scale image to pet_image_size
            size = self.pet_image_size
            img = img.resize((size, size), Image.LANCZOS)
            self.pet_image_tk = ImageTk.PhotoImage(img)
        except Exception:
            self.pet_image_tk = None

    def _render_environment(self):
        """Render the playground environment"""
        # Clear existing items
        self.canvas.delete("all")

        # Background image (if available) or solid color (always set)
        if self.background_image_tk is not None:
            self.background_id = self.canvas.create_image(0, 0, image=self.background_image_tk, anchor='nw', tags='background')
        else:
            # Ensure solid background color is visible
            config = self.playground.get_environment_config()
            bg_color = config.get("bg_color", "#FFFFFF")
            self.canvas.configure(bg=bg_color)

        # Render pet (on top layer)
        self._render_pet()

    def _render_decorations(self):
        """No-op: Non-interactive background only (decorations removed)."""
        return

    def _render_toys(self):
        """No-op: Background components are non-interactive and omitted."""
        return

    def _render_pet(self):
        """Render the pet sprite with boundary checking"""
        x, y, animation = self.playground.update_movement()

        # Egg stage: freeze movement and pin to ground at same level for all pets
        try:
            if int(self.pet_stage) == 1:
                self.playground.is_moving = False
                self.playground.target_x = self.playground.pet_x
                # All eggs positioned at the same ground level (updated for new boundaries)
                egg_ground_y = self.playground.max_y  # Use the new expanded max_y
                y = egg_ground_y
                self.playground.pet_y = y
                self.playground.target_y = y
                # Prevent random movement from starting
                self.playground.next_movement_delay = 10**9
        except Exception:
            pass

        # Simplified UI collision detection - only prevent pets from going into UI panels
        # Use configuration-based boundaries from playground
        ui_right_boundary = self.playground.PET_CONFIG["ui_block_right_margin"] + 30
        ui_bottom_boundary = self.height - (self.playground.PET_CONFIG["ui_block_bottom_margin"] + 30)

        # Only push pets away if they're actually in UI areas (simplified logic)
        if x < ui_right_boundary and y > ui_bottom_boundary:
            # Pet is in UI area - push away horizontally
            x = ui_right_boundary + 40
            # Keep pet at appropriate ground level
            if int(self.pet_stage) == 1:
                y = self.playground.max_y  # Egg ground level
            else:
                y = self.playground.max_y  # Pet ground level

            # Update playground position
            self.playground.pet_x = x
            self.playground.pet_y = y

        # Get pet image for current animation
        pet_data = self.pet_images.get(animation, self.pet_images[PetAnimation.IDLE])

        # Clear previous pet drawings to avoid trails
        self.canvas.delete('pet')

        # Render pet as image if available, else emoji
        if self.pet_image_tk is not None:
            # Centered image
            self.canvas.create_image(x, y, image=self.pet_image_tk, anchor='center', tags='pet')
        else:
            emoji = self.pet_emojis.get(self.pet_type.lower(), "🐾")
            # Larger emoji for visibility with better contrast
            self.canvas.create_text(x, y, text=emoji, font=("Arial", 150, "bold"), fill="#000000", tags="pet")

    def _start_animation_loop(self):
        """Start the animation update loop"""
        self._update_animation()

    def _update_animation(self):
        """Update animation frame"""
        try:
            # Update pet position and animation
            self._render_pet()

            # Increment animation frame
            self.animation_frame += 1

            # Schedule next update
            if self.canvas.winfo_exists():
                self.animation_timer = self.canvas.after(self.update_interval, self._update_animation)
            else:
                pass  # Canvas no longer exists
        except Exception:
            # Try to restart animation after a delay
            if self.canvas.winfo_exists():
                self.animation_timer = self.canvas.after(1000, self._start_animation_loop)

    def stop_animation(self):
        """Stop the animation loop"""
        if self.animation_timer:
            self.canvas.after_cancel(self.animation_timer)
            self.animation_timer = None

    def update_pet_stage(self, new_stage: int):
        """Update pet stage (may affect appearance)"""
        self.pet_stage = new_stage
        # Update playground's pet stage for movement restrictions
        if hasattr(self.playground, 'update_pet_stage'):
            self.playground.update_pet_stage(new_stage)
        # Reload pet image to reflect stage
        self._load_pet_image()
        # If hatched (stage > 1), re-enable movement soon
        try:
            if int(new_stage) > 1:
                # Nudge timers so a new movement can start shortly
                self.playground.last_movement_time = time.time() - 5
                self.playground.next_movement_delay = 2
                # All pets already at correct ground level
        except Exception:
            pass

    def update_pet_emotion(self, new_emotion: str):
        """Update pet emotion and reload sprite."""
        self.pet_emotion = new_emotion or self.pet_emotion
        self._load_pet_image()

    def cleanup(self):
        """Clean up resources"""
        self.stop_animation()
        self.canvas.delete("all")
