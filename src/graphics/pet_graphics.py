import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from typing import Dict, Optional, Tuple

class PetGraphics:
    
    def __init__(self):
        self.image_cache = {}
        self.img_base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'img')
        
        self.pet_folders = {
            'cat': 'Cat',
            'dog': 'Dog',
            'axolotl': 'Axolotl',
            'raccoon': 'Raccoon',
            'penguin': 'Penguin'
        }
        
        self.stage_names = {
            1: 'Egg',
            2: 'Baby',
            3: 'Child', 
            4: 'Grown',
            5: 'Battle_Fit'
        }
        
        self.fallback_emojis = {
            ('cat', 1): '🥚',
            ('cat', 2): '🐱',
            ('cat', 3): '🐱', 
            ('cat', 4): '🐱',
            ('cat', 5): '🐱',
            ('dog', 1): '🥚',
            ('dog', 2): '🐶',
            ('dog', 3): '🐶',
            ('dog', 4): '🐶', 
            ('dog', 5): '🐶',
            ('axolotl', 1): '🥚',
            ('axolotl', 2): '🦎',
            ('axolotl', 3): '🦎', 
            ('axolotl', 4): '🦎',  
            ('axolotl', 5): '🦎',  
            ('raccoon', 1): '🥚',
            ('raccoon', 2): '🦝',
            ('raccoon', 3): '🦝',
            ('raccoon', 4): '🦝',
            ('raccoon', 5): '🦝',
            ('penguin', 1): '🥚',
            ('penguin', 2): '🐧',
            ('penguin', 3): '🐧',
            ('penguin', 4): '🐧',
            ('penguin', 5): '🐧'
        }
    
    def get_pet_image_path(self, pet_type: str, stage: int, emotion: str = None) -> str:
        """Get the file path for a pet image, using Pet_Stage_Emotion format first."""
        folder_name = self.pet_folders.get(pet_type.lower(), 'Cat')
        stage_name = self.stage_names.get(stage, 'Egg')
        
        # Convert pet type to proper case variations
        pet_type_cap = pet_type.capitalize()
        pet_type_lower = pet_type.lower()
        
        # Emotion variations
        emotion_variations = []
        if emotion:
            emotion_variations = [emotion.lower(), emotion.capitalize(), emotion.upper()]
        
        # Priority 1: Pet_Stage_Emotion format (based on your existing files)
        possible_names = []
        if emotion:
            for emotion_var in emotion_variations:
                possible_names.extend([
                    f"{pet_type_cap}_{stage_name}_{emotion_var}.png",
                    f"{pet_type_cap}_{stage_name}_{emotion_var}.jpg",
                    f"{pet_type_cap}_{stage_name}_{emotion_var}.jpeg",
                    f"{folder_name}_{stage_name}_{emotion_var}.png",
                    f"{folder_name}_{stage_name}_{emotion_var}.jpg",
                    f"{folder_name}_{stage_name}_{emotion_var}.jpeg"
                ])
        
        # Priority 2: Pet_Stage format
        possible_names.extend([
            f"{pet_type_cap}_{stage_name}.png",
            f"{pet_type_cap}_{stage_name}.jpg",
            f"{pet_type_cap}_{stage_name}.jpeg", 
            f"{folder_name}_{stage_name}.png",
            f"{folder_name}_{stage_name}.jpg",
            f"{folder_name}_{stage_name}.jpeg"
        ])
        
        # Search in pet type folder first
        for name in possible_names:
            image_path = os.path.join(self.img_base_path, folder_name, name)
            if os.path.exists(image_path):
                return image_path
        
        # Search in root img folder as fallback
        for name in possible_names:
            image_path = os.path.join(self.img_base_path, name)
            if os.path.exists(image_path):
                return image_path
        
        return None
    
    def load_pet_image(self, pet_type: str, stage: int, size: Tuple[int, int] = (200, 200), emotion: str = None) -> Optional[ImageTk.PhotoImage]:
        """Load a pet image and return a PhotoImage object."""
        emotion_suffix = f"_{emotion}" if emotion else ""
        cache_key = f"{pet_type}_{stage}{emotion_suffix}_{size[0]}x{size[1]}"
        
        # Check cache first
        if cache_key in self.image_cache:
            return self.image_cache[cache_key]
        
        image_path = self.get_pet_image_path(pet_type, stage, emotion)
        
        if image_path and os.path.exists(image_path):
            try:
                # Load and resize image
                pil_image = Image.open(image_path)
                
                # Resize while maintaining aspect ratio
                pil_image.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Convert to PhotoImage
                photo_image = ImageTk.PhotoImage(pil_image)
                
                # Cache the image
                self.image_cache[cache_key] = photo_image
                
                return photo_image
                
            except Exception as e:
                print(f"Error loading image {image_path}: {e}")
                return None
        
        return None
    
    def get_fallback_emoji(self, pet_type: str, stage: int) -> str:
        """Get fallback emoji if image loading fails."""
        return self.fallback_emojis.get((pet_type.lower(), stage), '🐱')
    
    def create_pet_display_widget(self, parent, pet_type: str, stage: int, size: Tuple[int, int] = (200, 200), emotion: str = None) -> tk.Widget:
        """Create a widget to display the pet (image or emoji fallback)."""
        # Try to load image first (with emotion if provided)
        pet_image = self.load_pet_image(pet_type, stage, size, emotion)
        
        if pet_image:
            # Create label with image
            image_label = ttk.Label(parent, image=pet_image)
            image_label.image = pet_image  # Keep a reference to prevent garbage collection
            return image_label
        else:
            # Fallback to emoji
            emoji = self.get_fallback_emoji(pet_type, stage)
            emoji_label = ttk.Label(parent, text=emoji, font=("Arial", 96))
            return emoji_label
    
    def update_pet_display_widget(self, widget, pet_type: str, stage: int, size: Tuple[int, int] = (200, 200), emotion: str = None):
        """Update an existing pet display widget."""
        # Try to load new image (with emotion if provided)
        pet_image = self.load_pet_image(pet_type, stage, size, emotion)
        
        if pet_image:
            # Update with image
            widget.configure(image=pet_image, text="")
            widget.image = pet_image  # Keep reference
        else:
            # Update with emoji
            emoji = self.get_fallback_emoji(pet_type, stage)
            widget.configure(text=emoji, image="", font=("Arial", 96))
            widget.image = None
    
    def list_available_images(self) -> Dict[str, list]:
        """List all available pet images."""
        available = {}
        
        for pet_type, folder_name in self.pet_folders.items():
            folder_path = os.path.join(self.img_base_path, folder_name)
            images = []
            
            if os.path.exists(folder_path):
                for file in os.listdir(folder_path):
                    if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                        images.append(file)
            
            available[pet_type] = images
        
        return available
    
    def clear_cache(self):
        """Clear the image cache to free memory."""
        self.image_cache.clear()
    
    def get_cache_info(self) -> Dict[str, int]:
        """Get information about the image cache."""
        return {
            'cached_images': len(self.image_cache),
            'cache_keys': list(self.image_cache.keys())
        }

# Global graphics manager instance
pet_graphics = PetGraphics()
