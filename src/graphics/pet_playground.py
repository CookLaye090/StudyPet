"""
Pet Playground System - Manages pet environments, movement, and animations
"""

import random
import time
from enum import Enum
from typing import Tuple, Optional

class PetMovementPattern(Enum):
    """Movement patterns for different pet types"""
    GROUND = "ground"  # Left/Right only (Dog, Cat, Raccoon)
    AQUATIC = "aquatic"  # All directions (Axolotl)
    FLYING = "flying"  # All directions with preference for upper area (future birds)

class PetEnvironment(Enum):
    """Environment themes for different pet types"""
    ROOM = "room"  # Dog, Cat, Raccoon - cozy room with toys
    AQUARIUM = "aquarium"  # Axolotl - underwater scene
    ICY_TERRAIN = "icy_terrain"  # Penguin - snowy/icy landscape
    GARDEN = "garden"  # Future pets - outdoor garden

class PetAnimation(Enum):
    """Animation states"""
    IDLE = "idle"
    WALK_LEFT = "walk_left"
    WALK_RIGHT = "walk_right"
    SWIM_LEFT = "swim_left"
    SWIM_RIGHT = "swim_right"
    SWIM_UP = "swim_up"
    SWIM_DOWN = "swim_down"

class PetPlayground:
    """Manages pet playground environment and movement"""

    # Pet positioning and UI configuration - easily adjustable
    # To adjust pet positioning:
    # - Decrease "ground_level_offset" to move pets DOWN (lower number = lower position)
    # - Increase "ground_level_offset" to move pets UP (higher number = higher position)
    # - Decrease "vertical_range_bottom_offset" to give pets more vertical movement UP
    # - Adjust "ui_block_*" values to change UI collision boundaries
    # - Modify movement timing in "idle_delay_*" and "movement_duration_*" values
    PET_CONFIG = {
        # Pet positioning (pixels from edges)
        "min_x_margin": 50,                    # Left/right margins for pet movement
        "ground_level_offset": 300,            # Distance from bottom of screen (higher = more upward)
        "vertical_range_top": 80,              # Top boundary for aquatic pets
        "vertical_range_bottom_offset": 450,   # Bottom boundary offset from screen bottom

        # UI collision boundaries
        "ui_block_right_margin": 240,          # Right panel width (status/timer/chat) - reduced for more click area
        "ui_block_bottom_margin": 200,         # Bottom UI area height - reduced for more click area

        # Movement settings
        "movement_speed": 4.0,                 # Pixels per frame - increased significantly for fast movement
        "idle_delay_min": 30,                  # Minimum idle time (reduced from 180)
        "idle_delay_max": 60,                  # Maximum idle time (reduced from 300)
        "movement_duration_min": 3,            # Minimum movement duration (reduced from 8)
        "movement_duration_max": 5,            # Maximum movement duration (reduced from 12)
    }
    
    # Environment configurations
    ENVIRONMENTS = {
        "Axolotl": {
            "type": PetEnvironment.AQUARIUM,
            "movement": PetMovementPattern.AQUATIC,
            "bg_color": "#4A90E2",  # Water blue
            "decorations": ["seaweed", "rocks", "bubbles", "coral"],
            "toys": ["treasure_chest", "castle", "shell"]
        },
        "Dog": {
            "type": PetEnvironment.ROOM,
            "movement": PetMovementPattern.GROUND,
            "bg_color": "#F5E6D3",  # Warm beige
            "decorations": ["rug", "cushion", "plant"],
            "toys": ["ball", "bone", "toy_rope"]
        },
        "Cat": {
            "type": PetEnvironment.ROOM,
            "movement": PetMovementPattern.GROUND,
            "bg_color": "#FFF8E7",  # Light cream
            "decorations": ["cat_tree", "scratching_post", "cushion"],
            "toys": ["yarn_ball", "mouse_toy", "feather_wand"]
        },
        "Raccoon": {
            "type": PetEnvironment.ROOM,
            "movement": PetMovementPattern.GROUND,
            "bg_color": "#E8F4E8",  # Light green
            "decorations": ["log", "leaves", "rocks"],
            "toys": ["shiny_object", "trash_can", "food_bowl"]
        }
    }
    
    def __init__(self, pet_type: str, playground_width: int = 600, playground_height: int = 400, pet_stage: int = 1):
        self.pet_type = pet_type
        self.pet_stage = pet_stage  # Store pet stage to know if it's an egg
        self.hatch_time = None  # Store hatch time for delay
        self.width = playground_width
        self.height = playground_height

        # Get environment config
        self.config = self.ENVIRONMENTS.get(pet_type, self.ENVIRONMENTS["Dog"])
        self.movement_pattern = self.config["movement"]

        # Calculate boundaries first (before using them)
        # Expanded boundaries for much more movement room
        self.min_x = self.PET_CONFIG["min_x_margin"]  # Much smaller left margin
        self.max_x = playground_width - self.PET_CONFIG["min_x_margin"]  # Much smaller right margin

        # Expanded vertical movement range
        if self.movement_pattern == PetMovementPattern.AQUATIC:
            # Axolotl can move throughout most of the aquarium (but not too low for eggs)
            self.min_y = self.PET_CONFIG["vertical_range_top"]   # Much higher up
            self.max_y = playground_height - self.PET_CONFIG["ground_level_offset"]  # Higher up for eggs, lower for adults (moved up by 50px)
        else:
            # Ground pets positioned with much more vertical range
            self.min_y = playground_height - self.PET_CONFIG["vertical_range_bottom_offset"]  # Higher up from bottom (moved up by 50px)
            self.max_y = playground_height - self.PET_CONFIG["ground_level_offset"]  # Lower down for variety (moved up by 50px)

        # Pet position - consistent ground starting position for all pets
        # Use the max_y as the ground level for all pets (works for both aquatic and ground)
        self.pet_x = playground_width // 2
        self.pet_y = self.max_y  # All pets start at ground level

        # Movement state
        self.current_animation = PetAnimation.IDLE
        self.is_moving = False
        self.target_x = self.pet_x
        self.target_y = self.pet_y
        self.movement_speed = self.PET_CONFIG["movement_speed"]  # pixels per frame (now much faster)
        self.movement_start_time = 0.0

        # Timing for random movement - now much more responsive
        self.last_movement_time = time.time()
        # Idle 30-60 seconds before deciding to move again (was 3-5 minutes)
        self.next_movement_delay = random.randint(self.PET_CONFIG["idle_delay_min"], self.PET_CONFIG["idle_delay_max"])
        # Move for about 3-5 seconds (was 8-12 seconds)
        self.movement_duration = 0
        
    def get_environment_config(self) -> dict:
        """Get the environment configuration for this pet"""
        return self.config
    
    def update_movement(self) -> Tuple[int, int, PetAnimation]:
        """
        Update pet position based on movement AI
        Returns: (x, y, animation_state)
        """
        current_time = time.time()

        # Check if it's time to start a new movement (but not for eggs)
        if not self.is_moving:
            if current_time - self.last_movement_time >= self.next_movement_delay:
                # Only eggs (stage 1) are restricted from random movement
                if not hasattr(self, 'pet_stage') or self.pet_stage != 1:
                    self._start_new_movement()
                    self.last_movement_time = current_time
        
        # Update position if moving
        if self.is_moving:
            self._move_towards_target()
            # Stop movement after duration window regardless of reaching target
            if (current_time - self.movement_start_time) >= self.movement_duration:
                self._stop_movement()

            # Check if reached target (more responsive stopping condition)
            elif abs(self.pet_x - self.target_x) < 2.0 and \
                 abs(self.pet_y - self.target_y) < 2.0:
                self._stop_movement()
        
        return self.pet_x, self.pet_y, self.current_animation
    
    def _start_new_movement(self):
        """Start a new random movement"""
        self.is_moving = True
        self.movement_start_time = time.time()
        
        # Choose random target based on movement pattern
        if self.movement_pattern == PetMovementPattern.AQUATIC:
            # Axolotl can move anywhere in the aquarium
            self.target_x = random.randint(self.min_x, self.max_x)
            self.target_y = random.randint(self.min_y, self.max_y)
            
            # Determine animation based on direction
            dx = self.target_x - self.pet_x
            dy = self.target_y - self.pet_y
            
            if abs(dx) > abs(dy):
                self.current_animation = PetAnimation.SWIM_LEFT if dx < 0 else PetAnimation.SWIM_RIGHT
            else:
                self.current_animation = PetAnimation.SWIM_UP if dy < 0 else PetAnimation.SWIM_DOWN
                
        elif self.movement_pattern == PetMovementPattern.GROUND:
            # Ground pets only move left/right
            self.target_x = random.randint(self.min_x, self.max_x)
            self.target_y = self.pet_y  # Keep same Y position (ground level)
            
            # Determine animation
            if self.target_x < self.pet_x:
                self.current_animation = PetAnimation.WALK_LEFT
            else:
                self.current_animation = PetAnimation.WALK_RIGHT
        
        # Movement duration about 3-5 seconds (was 8-12 seconds)
        self.movement_duration = random.randint(self.PET_CONFIG["movement_duration_min"], self.PET_CONFIG["movement_duration_max"])

        # Next idle period 30-60 seconds (was 3-5 minutes)
        self.next_movement_delay = random.randint(self.PET_CONFIG["idle_delay_min"], self.PET_CONFIG["idle_delay_max"])
    
    def _move_towards_target(self):
        """Move pet towards target position with smooth, consistent movement"""
        # Calculate direction
        dx = self.target_x - self.pet_x
        dy = self.target_y - self.pet_y

        # Calculate distance
        distance = (dx**2 + dy**2) ** 0.5

        if distance > 0:
            # Normalize direction vector and apply speed
            move_x = (dx / distance) * self.movement_speed
            move_y = (dy / distance) * self.movement_speed

            # Update position with improved boundary handling
            new_x = self.pet_x + move_x
            new_y = self.pet_y + move_y

            # Smooth boundary clamping - prevent jerky movement at edges
            self.pet_x = max(self.min_x, min(self.max_x, new_x))
            self.pet_y = max(self.min_y, min(self.max_y, new_y))
    
    def _stop_movement(self):
        """Stop current movement and return to idle"""
        self.is_moving = False
        self.current_animation = PetAnimation.IDLE
        self.target_x = self.pet_x
        self.target_y = self.pet_y
    
    def update_pet_stage(self, new_stage: int):
        """Update the pet stage (for movement restrictions)"""
        self.pet_stage = new_stage
        # If hatching from egg, set hatch time
        if new_stage == 2 and self.hatch_time is None:  # Just hatched
            self.hatch_time = time.time()
    
    def get_decoration_positions(self) -> list:
        """
        Get positions for environment decorations
        Returns list of (decoration_name, x, y) tuples
        """
        decorations = []
        decoration_list = self.config.get("decorations", [])

        # Use configuration-based positions (proportional to screen size)
        if self.movement_pattern == PetMovementPattern.AQUATIC:
            # Aquarium decorations
            positions = [
                (0.15, 0.75),  # Bottom left
                (0.85, 0.65),  # Bottom right
                (0.5, 0.8),    # Bottom center
                (0.1, 0.25),   # Mid left
            ]
        else:
            # Ground environment decorations
            positions = [
                (0.15, 0.65),  # Bottom left
                (0.85, 0.65),  # Bottom right
                (0.5, 0.6),    # Bottom center
            ]

        for i, decoration in enumerate(decoration_list[:len(positions)]):
            x = int(positions[i][0] * self.width)
            y = int(positions[i][1] * self.height)
            decorations.append((decoration, x, y))

        return decorations

    def get_toy_positions(self) -> list:
        """
        Get positions for interactive toys
        Returns list of (toy_name, x, y) tuples
        """
        toys = []
        toy_list = self.config.get("toys", [])

        # Use configuration-based positions (proportional to screen size)
        if self.movement_pattern == PetMovementPattern.AQUATIC:
            positions = [
                (0.25, 0.3),   # Top area
                (0.75, 0.4),   # Mid-right
                (0.5, 0.2),    # Top center
            ]
        else:
            positions = [
                (0.25, 0.55),  # Left side
                (0.75, 0.55),  # Right side
                (0.5, 0.5),    # Center
            ]

        for i, toy in enumerate(toy_list[:len(positions)]):
            x = int(positions[i][0] * self.width)
            y = int(positions[i][1] * self.height)
            toys.append((toy, x, y))

        return toys
    
    def interact_with_toy(self, toy_name: str) -> bool:
        """
        Check if pet is near a toy and can interact
        Returns True if interaction occurred
        """
        toys = self.get_toy_positions()
        
        for toy, tx, ty in toys:
            if toy == toy_name:
                # Check distance to toy
                distance = ((self.pet_x - tx)**2 + (self.pet_y - ty)**2) ** 0.5
                if distance < 50:  # Within interaction range
                    return True
        
        return False
    
    def set_target(self, x: int, y: int):
        """Set target position for user-initiated movement (gradual, not teleport)"""
        # Don't allow movement for eggs
        if self.pet_stage == 1:
            return

        # Clamp target to boundaries
        self.target_x = max(self.min_x, min(self.max_x, x))

        # For ground pets, always keep them on ground level (ignore Y coordinate)
        if self.movement_pattern == PetMovementPattern.GROUND:
            self.target_y = self.pet_y  # Stay on current ground level
        else:
            # Aquatic pets can move vertically
            self.target_y = max(self.min_y, min(self.max_y, y))

        # Start movement if not already moving
        if not self.is_moving:
            self.is_moving = True
            self.movement_start_time = time.time()

            # Determine animation based on direction and movement pattern
            if self.movement_pattern == PetMovementPattern.AQUATIC:
                dx = self.target_x - self.pet_x
                dy = self.target_y - self.pet_y

                if abs(dx) > abs(dy):
                    self.current_animation = PetAnimation.SWIM_LEFT if dx < 0 else PetAnimation.SWIM_RIGHT
                else:
                    self.current_animation = PetAnimation.SWIM_UP if dy < 0 else PetAnimation.SWIM_DOWN
            else:  # Ground movement
                if self.target_x < self.pet_x:
                    self.current_animation = PetAnimation.WALK_LEFT
                else:
                    self.current_animation = PetAnimation.WALK_RIGHT
