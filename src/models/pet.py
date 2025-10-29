"""
Pet Model - Represents virtual pets with different stages and emotions
"""

from enum import Enum
from typing import Dict, List
import json
import os

class PetType(Enum):
    """Available pet types."""
    CAT = "cat"
    DOG = "dog"
    AXOLOTL = "axolotl"
    RACCOON = "raccoon"
    PENGUIN = "penguin"

class PetStage(Enum):
    """Pet evolution stages."""
    EGG = 1
    BABY = 2
    CHILD = 3
    GROWN = 4
    BATTLE_FIT = 5

class PetEmotion(Enum):
    """Pet emotions."""
    HAPPY = "happy"
    TIRED = "tired"
    HUNGRY = "hungry"
    SAD = "sad"
    ANGRY = "angry"

class Pet:
    """Virtual pet class with stages, emotions, and affection system."""
    
    def _get_pet_theme_colors(self):
        """Get theme colors based on pet type."""
        from ui.simple_theme import simple_theme

        pet_themes = {
            'axolotl': {'bg_main': '#FDF2F8', 'text_pink': '#EC4899'},
            'cat': {'bg_main': '#F8F9FA', 'text_pink': '#8B5CF6'},
            'dog': {'bg_main': '#FFFBF0', 'text_pink': '#F59E0B'},
            'raccoon': {'bg_main': '#FEF7ED', 'text_pink': '#DC2626'},
            'penguin': {'bg_main': '#FFFFFF', 'text_pink': '#000000'}
        }

        pet_type_str = self.pet_type.value.lower() if hasattr(self.pet_type, 'value') else str(self.pet_type).lower()
        return pet_themes.get(pet_type_str, pet_themes['penguin'])

    def __init__(self, pet_type: PetType, name: str = ""):
        self.pet_type = pet_type
        self.name = name or pet_type.value
        self.stage = PetStage.EGG
        self.emotion = PetEmotion.HAPPY
        self.affection = 0

        # Theme-related attributes
        self.theme_colors = self._get_pet_theme_colors()
        self.bg_color = self.theme_colors.get('bg_main', '#FFFFFF')
        self.accent_color = self.theme_colors.get('text_pink', '#000000')
        self.experience = 0
        self.level = 1

        # Load pet configuration data
        self.pet_data = self._load_pet_data()

        # Initialize stage targets
        self.stage_targets = self._build_stage_targets()

        # Track hatch time for movement delay
        self.hatch_time = None  # When the pet hatched (for movement delay)
        
    def _load_pet_data(self) -> Dict:
        """Load pet data from JSON configuration."""
        try:
            data_path = os.path.join(
                os.path.dirname(__file__), 
                '..', '..', 'game_data', 'pets.json'
            )
            with open(data_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Return default data if file doesn't exist
            return self._get_default_pet_data()
    
    def _get_default_pet_data(self) -> Dict:
        """Return default pet configuration."""
        return {
            pet_type.value: {
                "stages": {
                    str(stage.value): {
                        "name": f"{pet_type.value.capitalize()} {stage.name.capitalize()}",
                        "affection_required": 200 if stage.value <= 4 else 1000,
                        "image": f"{pet_type.value}_{stage.value}.png"
                    } for stage in PetStage
                },
                "emotions": {
                    emotion.value: {
                        "image": f"{pet_type.value}_{emotion.value}.png",
                        "description": emotion.value.capitalize()
                    } for emotion in PetEmotion
                }
            } for pet_type in PetType
        }
    
    def get_current_stage_info(self) -> Dict:
        """Get information about the current stage."""
        pet_config = self.pet_data.get(self.pet_type.value, {})
        stages = pet_config.get("stages", {})
        return stages.get(str(self.stage.value), {})
    
    def get_current_emotion_info(self) -> Dict:
        """Get information about the current emotion."""
        pet_config = self.pet_data.get(self.pet_type.value, {})
        emotions = pet_config.get("emotions", {})
        return emotions.get(self.emotion.value, {})
    
    def _build_stage_targets(self) -> Dict[int, int]:
        """Build affection targets for each stage from config or defaults."""
        targets = {}
        pet_config = self.pet_data.get(self.pet_type.value, {}) if hasattr(self, 'pet_data') else {}
        stages = pet_config.get("stages", {})

        # Custom affection limits: 200 for stages 1-4, 1000 for stage 5 (Battle-fit)
        for stage in PetStage:
            info = stages.get(str(stage.value), {})
            required = info.get("affection_required")

            if required is None:
                if stage.value <= 4:  # Stages 1-4: Egg, Baby, Child, Grown
                    required = 200  # Auto-evolve at 200, reset to 0
                else:  # Stage 5: Battle-fit
                    required = 1000  # Final stage cap at 1000

            targets[stage.value] = max(0, int(required))

        return targets

    def add_affection(self, amount: int) -> bool:
        """Add affection points and check for stage evolution. Returns True if evolved."""
        if amount == 0:
            self._update_emotion_from_affection(amount)
            return False

        self.affection = max(0, self.affection + amount)
        if amount > 0:
            self.experience += amount

        evolved = self._check_evolution()

        # Update emotion based on affection gain
        self._update_emotion_from_affection(amount)

        # Ensure affection is not negative after adjustments
        if self.affection < 0:
            self.affection = 0
        if evolved and self.affection < 0:
            self.affection = 0

        # Return evolution status for UI updates
        return evolved
    
    def _check_evolution(self) -> bool:
        """Check if pet should evolve to the next stage. Returns True if evolved."""
        max_stage = max(stage.value for stage in PetStage)
        current_stage_value = self.stage.value
        required_affection = self.stage_targets.get(current_stage_value, 0)

        # Fallback if stage_targets not properly initialized
        if required_affection <= 0:
            if current_stage_value <= 4:
                required_affection = 200  # Stages 1-4
            else:
                required_affection = 1000  # Stage 5

        evolved = False
        while current_stage_value < max_stage and self.affection >= required_affection:
            self.affection = 0  # Reset affection to 0 when evolving
            current_stage_value += 1
            self.stage = PetStage(current_stage_value)
            self.level += 1
            self.emotion = PetEmotion.HAPPY

            # Set hatch time when evolving from egg (stage 1 to stage 2)
            if current_stage_value == 2:  # Just hatched
                import time
                self.hatch_time = time.time()

            evolved = True
            # Get requirement for next stage
            required_affection = self.stage_targets.get(current_stage_value, 200 if current_stage_value <= 4 else 1000)

        if current_stage_value >= max_stage:
            # Final stage (Battle-fit) cap at 1000 instead of 500
            cap = self.stage_targets.get(current_stage_value, 1000)
            self.affection = min(self.affection, cap)

        return evolved
    
    def _update_emotion_from_affection(self, affection_gained: int):
        """Update pet emotion based on affection gained."""
        import random
        
        if affection_gained >= 30:
            # Large affection gain - happy
            self.emotion = PetEmotion.HAPPY
        elif affection_gained >= 10:
            # Medium affection gain - happy
            self.emotion = PetEmotion.HAPPY
        elif affection_gained >= 1:
            # Small affection gain - tired
            self.emotion = PetEmotion.TIRED
        elif affection_gained == 0:
            # No affection change - stay current or become happy
            if random.random() < 0.7:  # 70% chance to stay current
                pass  # Keep current emotion
            else:
                self.emotion = PetEmotion.HAPPY
        else:
            # Negative affection (shouldn't happen normally) - sad or hungry
            self.emotion = random.choice([PetEmotion.SAD, PetEmotion.HUNGRY])
    
    def set_emotion(self, emotion: PetEmotion):
        """Manually set pet emotion."""
        self.emotion = emotion
    
    def update_emotion_over_time(self):
        """Update pet emotion based on time passage and current state."""
        import random
        import datetime
        
        # Get current hour to determine time-based emotions
        current_hour = datetime.datetime.now().hour
        
        # Random chance for emotion changes (10% chance every call)
        if random.random() < 0.1:
            # Time-based emotion tendencies
            if 22 <= current_hour or current_hour <= 6:  # Night/early morning
                # More likely to be happy or tired (night owls)
                if self.emotion not in [PetEmotion.SAD, PetEmotion.ANGRY]:
                    self.emotion = random.choice([PetEmotion.HAPPY, PetEmotion.TIRED])
            elif 12 <= current_hour <= 14:  # Lunch time
                # More likely to be hungry or happy
                if random.random() < 0.3:
                    self.emotion = PetEmotion.HUNGRY
            elif 6 <= current_hour <= 12:  # Morning
                # More likely to be happy or tired (just woke up)
                if self.emotion != PetEmotion.ANGRY:
                    self.emotion = random.choice([PetEmotion.HAPPY, PetEmotion.TIRED])
    
    def trigger_contextual_emotion(self, context: str):
        """Trigger emotions based on specific contexts."""
        import random
        
        context_emotions = {
            "study_success": [PetEmotion.HAPPY],
            "long_study": [PetEmotion.TIRED, PetEmotion.HAPPY],
            "quiz_correct": [PetEmotion.HAPPY],
            "quiz_wrong": [PetEmotion.SAD, PetEmotion.HAPPY],
            "no_interaction": [PetEmotion.SAD, PetEmotion.HUNGRY],
            "feeding": [PetEmotion.HAPPY],
            "neglect": [PetEmotion.SAD, PetEmotion.ANGRY],
            "play": [PetEmotion.HAPPY, PetEmotion.TIRED]
        }
        
        if context in context_emotions:
            self.emotion = random.choice(context_emotions[context])
    
    def get_image_path(self) -> str:
        """Get the image path for current stage and emotion."""
        stage_info = self.get_current_stage_info()
        emotion_info = self.get_current_emotion_info()
        
        # Try emotion-specific image first
        emotion_image = emotion_info.get("image", "")
        if emotion_image:
            return os.path.join("assets", "images", emotion_image)
        
        # Fall back to stage image
        stage_image = stage_info.get("image", "")
        if stage_image:
            return os.path.join("assets", "images", stage_image)
        
        # Default placeholder
        return os.path.join("assets", "images", "placeholder.png")
    
    def get_current_stage_limit(self) -> int:
        """Get the affection limit for the current stage."""
        if self.stage.value <= 4:  # Stages 1-4
            return 200
        else:  # Stage 5 (Battle-fit)
            return 1000
    
    def get_status_text(self) -> str:
        """Get descriptive text about the pet's current status."""
        stage_info = self.get_current_stage_info()
        stage_name = stage_info.get("name", self.stage.name.capitalize())
        
        return (f"{self.name} - {stage_name}\\n"
                f"Level: {self.level}\\n"
                f"Affection: {self.affection}\\n"
                f"Feeling: {self.emotion.value.capitalize()}")
    
    def to_dict(self) -> Dict:
        """Convert pet to dictionary for saving."""
        return {
            "pet_type": self.pet_type.value,
            "name": self.name,
            "stage": self.stage.value,
            "emotion": self.emotion.value,
            "affection": self.affection,
            "experience": self.experience,
            "level": self.level,
            "hatch_time": self.hatch_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Create pet from dictionary."""
        pet = cls(PetType(data["pet_type"]), data["name"])

        # Handle stage - can be int or enum
        stage_value = data["stage"]
        if isinstance(stage_value, int):
            pet.stage = PetStage(stage_value)
        else:
            pet.stage = PetStage[stage_value] if hasattr(PetStage, stage_value) else PetStage.EGG

        # Handle emotion - can be int, string, or enum
        emotion_value = data["emotion"]
        if isinstance(emotion_value, int):
            # Map integers to enum values
            emotion_map = {1: "HAPPY", 2: "TIRED", 3: "HUNGRY", 4: "SAD"}
            emotion_name = emotion_map.get(emotion_value, "HAPPY")
            pet.emotion = PetEmotion[emotion_name]
        elif isinstance(emotion_value, str):
            # Handle string values
            if emotion_value.isdigit():
                # Convert numeric string to enum
                emotion_map = {1: "HAPPY", 2: "TIRED", 3: "HUNGRY", 4: "SAD"}
                emotion_name = emotion_map.get(int(emotion_value), "HAPPY")
                pet.emotion = PetEmotion[emotion_name]
            else:
                # Handle string enum names
                try:
                    pet.emotion = PetEmotion(emotion_value.lower())
                except ValueError:
                    pet.emotion = PetEmotion.HAPPY
        else:
            # Fallback
            pet.emotion = PetEmotion.HAPPY

        pet.affection = data["affection"]
        pet.experience = data["experience"]
        pet.level = data["level"]

        # Load hatch time if available
        pet.hatch_time = data.get("hatch_time")

        # Ensure stage_targets are properly initialized after loading
        pet.stage_targets = pet._build_stage_targets()

        return pet