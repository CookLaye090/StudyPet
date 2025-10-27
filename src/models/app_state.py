"""
Application State - Manages user data, settings, and game state
"""

import json
import os
from typing import Dict, Optional, List
from .pet import Pet, PetType
from .user import User

class AppState:
    """Manages the application state including user data and settings."""
    
    def __init__(self):
        self.user: Optional[User] = None
        self.current_pet: Optional[Pet] = None
        self.settings = {}
        self.save_file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', '..', 'user_data', 'save_data.json'
        )
        
        # Load existing data if available
        self.load_data()
    
    def is_first_time_user(self) -> bool:
        """Check if this is a first-time user (no saved pet)."""
        return self.current_pet is None
    
    def set_selected_pet(self, pet_type: PetType, name: str = ""):
        """Set the user's selected pet."""
        self.current_pet = Pet(pet_type, name)
        
        # Create user if doesn't exist
        if self.user is None:
            self.user = User("Player")
        
        # Save the data
        self.save_data()
    
    def get_current_pet(self) -> Optional[Pet]:
        """Get the current pet."""
        return self.current_pet
    
    def get_user(self) -> Optional[User]:
        """Get the current user."""
        return self.user
    
    def add_affection_to_pet(self, amount: int) -> bool:
        """Add affection to the current pet. Returns True if pet evolved."""
        if self.current_pet:
            evolved = self.current_pet.add_affection(amount)
            if evolved:
                self.save_data()
            return evolved
        return False
    
    def update_user_stats(self, study_time: int, questions_answered: int):
        """Update user statistics."""
        if self.user:
            self.user.add_study_time(study_time)
            self.user.add_questions_answered(questions_answered)
            self.save_data()
    
    def get_setting(self, key: str, default=None):
        """Get a setting value."""
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value):
        """Set a setting value."""
        self.settings[key] = value
        self.save_data()
    
    def save_data(self):
        """Save application state to file."""
        try:
            data = {
                "user": self.user.to_dict() if self.user else None,
                "current_pet": self.current_pet.to_dict() if self.current_pet else None,
                "settings": self.settings
            }
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.save_file_path), exist_ok=True)
            
            with open(self.save_file_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving data: {e}")
    
    def load_data(self):
        """Load application state from file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.save_file_path), exist_ok=True)
            
            if os.path.exists(self.save_file_path):
                with open(self.save_file_path, 'r') as f:
                    data = json.load(f)
                
                # Load user
                user_data = data.get("user")
                if user_data:
                    self.user = User.from_dict(user_data)
                
                # Load pet with validation
                pet_data = data.get("current_pet")
                if pet_data:
                    # Validate and repair pet data
                    validated_pet_data = self._validate_and_repair_pet_data(pet_data)
                    if validated_pet_data:
                        try:
                            self.current_pet = Pet.from_dict(validated_pet_data)
                        except Exception as e:
                            print(f"Warning: Could not create pet from validated data: {e}")
                            self.current_pet = None
                    else:
                        print("Warning: Pet data validation failed, starting fresh")
                        self.current_pet = None
                
                # Load settings
                self.settings = data.get("settings", {})
        except Exception as e:
            print(f"Error loading data: {e}")
            # Reset to clean state if loading fails
            self.current_pet = None
            self.user = None
            self.settings = {}
    
    def _validate_and_repair_pet_data(self, pet_data):
        """Validate and repair corrupted pet data."""
        if not pet_data:
            return None

        try:
            # Check required fields
            required_fields = ['pet_type', 'name', 'stage', 'emotion', 'affection']
            for field in required_fields:
                if field not in pet_data:
                    print(f"Warning: Missing field '{field}' in pet data")
                    return None

            # Validate and fix enum values
            try:
                # Ensure pet_type is valid
                pet_type_str = pet_data['pet_type']
                if pet_type_str not in ['cat', 'dog', 'axolotl', 'raccoon', 'penguin']:
                    print(f"Warning: Invalid pet_type '{pet_type_str}', defaulting to penguin")
                    pet_data['pet_type'] = 'penguin'

                # Ensure stage is valid (1-5)
                stage_value = pet_data['stage']
                if not isinstance(stage_value, int) or stage_value < 1 or stage_value > 5:
                    print(f"Warning: Invalid stage '{stage_value}', defaulting to 1")
                    pet_data['stage'] = 1

                # Ensure emotion is valid (1-4 or string)
                emotion_value = pet_data['emotion']
                if isinstance(emotion_value, str):
                    # Convert string emotions to enum values
                    emotion_map = {
                        'happy': 1, 'curious': 2, 'hungry': 3, 'sad': 4, 'angry': 4
                    }
                    if emotion_value.lower() in emotion_map:
                        pet_data['emotion'] = emotion_map[emotion_value.lower()]
                    else:
                        pet_data['emotion'] = 1  # Default to happy
                elif not isinstance(emotion_value, int) or emotion_value < 1 or emotion_value > 4:
                    print(f"Warning: Invalid emotion '{emotion_value}', defaulting to 1")
                    pet_data['emotion'] = 1

                # Ensure affection is valid
                affection = pet_data['affection']
                if not isinstance(affection, int) or affection < 0:
                    print(f"Warning: Invalid affection '{affection}', defaulting to 0")
                    pet_data['affection'] = 0

                # Fix experience and level if missing
                if 'experience' not in pet_data:
                    pet_data['experience'] = 0
                if 'level' not in pet_data:
                    pet_data['level'] = 1
                if 'hatch_time' not in pet_data:
                    pet_data['hatch_time'] = None

                return pet_data

            except Exception as e:
                print(f"Warning: Error validating pet data: {e}")
                return None

        except Exception as e:
            print(f"Warning: Error repairing pet data: {e}")
            return None
    
    def get_theme(self) -> str:
        """Get current theme setting."""
        return self.get_setting('theme', 'soft_pink')
    
    def set_theme(self, theme: str):
        """Set theme setting."""
        self.set_setting('theme', theme)
    
    def reset_data(self):
        """Reset all application data (for testing/demo purposes)."""
        self.user = None
        self.current_pet = None
        self.settings = {}

        # Delete entire user_data directory for complete reset
        user_data_dir = os.path.dirname(self.save_file_path)
        if os.path.exists(user_data_dir):
            try:
                import shutil
                shutil.rmtree(user_data_dir)
            except Exception as e:
                # Fallback: try to delete just the save file
                if os.path.exists(self.save_file_path):
                    os.remove(self.save_file_path)