"""
Global state management for pet attributes including stage, emotion, and mastery.
"""
import os
import json
import time
from enum import Enum, auto
from .state_manager import state_manager, PetStateChange
from .app_state import AppState

class PetStage(Enum):
    EGG = 1
    BABY = 2
    CHILD = 3
    GROWN = 4
    BATTLE_FIT = 5

class PetEmotion(Enum):
    HAPPY = auto()
    SAD = auto()
    WORRIED = auto()
    HUNGRY = auto()
    ANGRY = auto()

class PetState:
    """Singleton class to manage global pet state."""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize pet state, loading from AppState if available."""
        self._app_state = AppState()
        self._is_initializing = True  # Flag to prevent saving during initialization
        
        try:
            # Load state from app_state or use defaults
            if hasattr(self._app_state, 'pet_state') and self._app_state.pet_state:
                ps = self._app_state.pet_state
                
                # Safely get stage with validation
                try:
                    stage_value = int(ps.get('stage', 1))
                    if not 1 <= stage_value <= 5:  # Validate stage range
                        raise ValueError("Invalid stage value")
                    self._stage = PetStage(stage_value)
                except (ValueError, KeyError) as e:
                    print(f"Warning: Invalid stage value, defaulting to EGG: {e}")
                    self._stage = PetStage.EGG
                
                # Safely get emotion with validation
                try:
                    emotion_str = str(ps.get('emotion', 'HAPPY')).upper()
                    self._emotion = PetEmotion[emotion_str]
                except (KeyError, AttributeError) as e:
                    print(f"Warning: Invalid emotion value, defaulting to HAPPY: {e}")
                    self._emotion = PetEmotion.HAPPY
                
                # Safely get mastery with validation
                try:
                    self._mastery = max(0, int(ps.get('mastery', 0)))
                except (ValueError, TypeError) as e:
                    print(f"Warning: Invalid mastery value, defaulting to 0: {e}")
                    self._mastery = 0
                
                # Update pet object if it exists
                if hasattr(self._app_state, 'current_pet') and self._app_state.current_pet:
                    pet = self._app_state.current_pet
                    try:
                        if hasattr(pet, 'mastery'):
                            pet.mastery = self._mastery
                        if hasattr(pet, 'stage'):
                            pet.stage = self._stage
                    except Exception as e:
                        print(f"Warning: Failed to update pet object: {e}")
                        
            else:
                # Default values
                self._stage = PetStage.EGG
                self._emotion = PetEmotion.HAPPY
                self._mastery = 0
                
        except Exception as e:
            print(f"Error initializing pet state, using defaults: {e}")
            import traceback
            traceback.print_exc()
            # Set default values
        if not hasattr(self, '_stage'):
            self._stage = PetStage.EGG
            self._emotion = PetEmotion.HAPPY
            self._mastery = 0
            
        # Mark initialization as complete
        self._is_initializing = False
    
    @property
    def stage(self):
        return self._stage
        
    @stage.setter
    def stage(self, value):
        # Convert to PetStage if it's an int
        if isinstance(value, int):
            value = PetStage(value)
            
        old_stage = getattr(self, '_stage', None)
        
        # Only proceed if the stage is actually changing
        if old_stage == value:
            return
            
        # Update the stage
        self._stage = value
        
        # Reset mastery when evolving to a new stage
        self._mastery = 0
        
        # Notify listeners about the evolution
        if hasattr(self, 'on_evolve'):
            try:
                self.on_evolve(old_stage, value)
            except Exception as e:
                print(f"Error in evolution callback: {e}")
    
    @property
    def emotion(self):
        return self._emotion
    
    @emotion.setter
    def emotion(self, value):
        old_emotion = getattr(self, '_emotion', None)
        self._emotion = value
        
        # Only notify if the emotion actually changed
        if old_emotion != self._emotion:
            state_manager.notify_state_change(PetStateChange.EMOTION)
    
    @property
    def mastery(self):
        return self._mastery
    
    @mastery.setter
    def mastery(self, value):
        old_value = self._mastery
        self._mastery = max(0, min(value, self.mastery_cap))  # Use computed property
        
        # Only update if the value actually changed
        if self._mastery != old_value:
            self._update_emotion()
            # Save state whenever mastery changes
            self.save_state()
            # Check for evolution if mastery reached cap
            if self._mastery >= self.mastery_cap:
                self._check_evolution()
    
    @property
    def mastery_percentage(self):
        return (self._mastery / self.mastery_cap) * 100 if self.mastery_cap > 0 else 0

    @property
    def mastery_cap(self):
        """Dynamically calculate the mastery cap based on current stage."""
        if not hasattr(self, '_stage'):
            return 200  # Default cap if stage not set
        return 1000 if self._stage == PetStage.BATTLE_FIT else 200
    
    @mastery_cap.setter
    def mastery_cap(self, value):
        """Prevent direct setting of mastery cap - it's derived from stage."""
        pass  # Read-only property
    
    def _update_emotion(self):
        percentage = self.mastery_percentage
        old_emotion = getattr(self, '_emotion', None)
        
        if percentage < 20:
            new_emotion = PetEmotion.SAD
        elif percentage < 40:
            new_emotion = PetEmotion.WORRIED
        elif percentage < 60:
            new_emotion = PetEmotion.HUNGRY
        elif percentage < 80:
            new_emotion = PetEmotion.HAPPY
        else:
            new_emotion = PetEmotion.ANGRY
        
        # Only update and notify if the emotion has changed
        if new_emotion != old_emotion:
            self._emotion = new_emotion
            state_manager.notify_state_change(PetStateChange.EMOTION)
    
    def _check_evolution(self):
        # Can't evolve beyond BATTLE_FIT
        if self._stage == PetStage.BATTLE_FIT:
            return False
            
        # Check if we have enough mastery to evolve
        if self._mastery >= self.mastery_cap:
            current_stage = self._stage
            
            # Determine next stage
            if current_stage == PetStage.GROWN:
                new_stage = PetStage.BATTLE_FIT
            else:
                new_stage = PetStage(current_stage.value + 1)
            
            # Update stage (this will reset mastery)
            old_stage = self._stage
            self._stage = new_stage
            self._mastery = 0  # Reset mastery on evolution
            
            # Update the pet object if it exists
            if hasattr(self, '_app_state') and hasattr(self._app_state, 'current_pet'):
                pet = self._app_state.current_pet
                if pet and hasattr(pet, 'stage'):
                    pet.stage = new_stage
                if pet and hasattr(pet, 'mastery'):
                    pet.mastery = 0
            
            # Save the state after evolution
            self.save_state()
            
            # Notify listeners about the evolution
            if hasattr(self, 'on_evolve'):
                try:
                    self.on_evolve(old_stage, new_stage)
                except Exception as e:
                    print(f"Error in evolution callback: {e}")
            
            return True
            
        return False
        
    def _save(self, force_save=False):
        """Save the current state to AppState.
        
        Args:
            force_save: If True, will save even if initialization is not complete.
                      This should only be True when the application is closing.
        """
        if not force_save and (getattr(self, '_is_initializing', False) or not hasattr(self, '_app_state')):
            return False
            
        try:
            # Ensure required attributes exist
            if not all(hasattr(self, attr) for attr in ['_stage', '_emotion', '_mastery']):
                print("Warning: Cannot save pet state - missing required attributes")
                return False
                
            if not hasattr(self, '_app_state') or not hasattr(self._app_state, 'pet_state'):
                print("Warning: Cannot save pet state - invalid app state")
                return False
            
            # Get current time once to ensure consistency
            current_time = int(time.time())
            
            # Update pet_state with current values
            self._app_state.pet_state.update({
                'stage': self._stage.value if hasattr(self._stage, 'value') else int(self._stage),
                'emotion': self._emotion.name if hasattr(self._emotion, 'name') else str(self._emotion).upper(),
                'mastery': int(self._mastery),
                'mastery_cap': self.mastery_cap,
                'last_updated': current_time
            })
            
            # Don't update pet object here to avoid overriding the mastery
            # The pet object should be updated when the app_state loads, not during save
            
            # Force save the app state
            success = self._app_state.save_data(force_backup=True)
            if not success:
                print("Warning: Failed to save app state")
                return False
                
            # Verify the save was successful
            if os.path.exists(self._app_state.save_file_path):
                try:
                    with open(self._app_state.save_file_path, 'r') as f:
                        saved_data = json.load(f)
                        saved_mastery = saved_data.get('pet_state', {}).get('mastery')
                        if saved_mastery != self._mastery:
                            print(f"Warning: Saved mastery ({saved_mastery}) doesn't match current mastery ({self._mastery})")
                            return False
                except Exception as e:
                    print(f"Warning: Failed to verify save file: {e}")
                    return False
                    
            return True
            
        except Exception as e:
            print(f"Error saving pet state to AppState: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    def save_state(self):
        """Explicitly save the current state to AppState.
        This should be called when the application is closing.
        
        Returns:
            bool: True if save was successful, False otherwise
        """
        print("Saving pet state...")
        try:
            result = self._save(force_save=True)
            if result:
                print("✅ Pet state saved successfully")
            else:
                print("⚠️ Failed to save pet state")
            return result
        except Exception as e:
            print(f"⚠️ Error in save_state: {e}")
            import traceback
            traceback.print_exc()
            return False

# Global instance
global_pet_state = PetState()
