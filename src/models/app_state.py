"""
Application State - Manages user data, settings, and game state
"""

import os
import json
import time
from typing import Dict, Optional, List, Any, TypeVar, Type, Union
from pathlib import Path
from datetime import datetime, timedelta
from src.utils.file_utils import atomic_write, atomic_read, backup_file
from .pet import Pet, PetType, PetStage, PetEmotion
from .user import User

T = TypeVar('T', bound='AppState')

class DataValidationError(Exception):
    """Raised when data validation fails."""
    pass

class AppState:
    """Manages the application state including user data and settings."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Prevent re-initialization
        if self._initialized:
            return
        
        self.user: Optional[User] = None
        self.current_pet: Optional[Pet] = None
        self.settings = {}
        self.save_file_path = os.path.join(
            os.path.dirname(__file__), 
            '..', '..', 'user_data', 'save_data.json'
        )
        
        # Runtime study session state (not persisted here)
        self.study_session = {
            'active': False,
            'type': None,              # e.g., 'pomodoro', 'custom', etc.
            'schedule': None,          # dict with 'blocks': [{type, duration}], 'name'
            'current_block': 0,
            'block_type': None,        # 'study' or 'break'
            'block_duration': 0,       # seconds
            'block_start_time': None,  # epoch seconds
            'start_time': None,
            'paused': False,
            'last_activity': None,
            'completed_blocks': [],
            'total_study_time': 0,     # seconds of study only
            'session_paused': False
        }
        
        # Pet state data (migrated from pet_state.json)
        self.pet_state = {
            'stage': 1,                # Pet stage (1-5)
            'emotion': 'HAPPY',        # Current emotion
            'mastery': 0,            # Current mastery points
            'mastery_cap': 200,      # Current mastery cap for evolution (200 for stages 1-4, 1000 for stage 5)
            'last_updated': time.time() # Last update timestamp
        }
        
        # Initialize streak tracking flag
        self._streak_initialized = False
        
        # Load existing data if available
        self.load_data()
        
        # Initialize streak tracking after data is loaded
        if self.user:
            self.initialize_streak_tracking()
        
        # Mark as initialized
        self._initialized = True
    
    def initialize_streak_tracking(self):
        """Initialize streak tracking after user is created."""
        # Only initialize if user exists and hasn't been initialized yet
        if self.user and not self._streak_initialized:
            self._update_streak_on_startup()
            self._streak_initialized = True
    
    def _update_streak_on_startup(self):
        """Update streak based on when the application was last opened."""
        from datetime import datetime, date
        
        today = date.today()
        last_opened = None
        
        # Check if we have a last opened date in the save data
        if hasattr(self, '_last_opened_date'):
            last_opened = self._last_opened_date
        elif 'last_opened' in self.settings:
            from datetime import datetime
            last_opened_str = self.settings['last_opened']
            if last_opened_str:
                last_opened = datetime.strptime(last_opened_str, '%Y-%m-%d').date()
        
        # Initialize streak values if they don't exist
        if not hasattr(self, '_current_streak'):
            self._current_streak = 0
        if not hasattr(self, '_longest_streak'):
            self._longest_streak = 0
        
        # Update streak based on last opened date
        if last_opened is None:
            # First time opening the app
            self._current_streak = 1
            self._longest_streak = 1
        elif last_opened == today:
            # Already opened today, no change
            pass
        elif last_opened == date.fromordinal(today.toordinal() - 1):
            # Yesterday - consecutive day
            self._current_streak += 1
            # Update longest streak if needed
            if self._current_streak > self._longest_streak:
                self._longest_streak = self._current_streak
        else:
            # Not consecutive - reset streak
            self._current_streak = 1
        
        # Save the last opened date
        self._last_opened_date = today
        self.settings['last_opened'] = today.strftime('%Y-%m-%d')
        
        # Save the updated streak values
        self._save_streak_data()
    
    def _save_streak_data(self):
        """Save streak data to the user object and settings."""
        if self.user:
            self.user.streak_days = self._current_streak
            # Add longest_streak as a new attribute if it doesn't exist
            if not hasattr(self.user, 'longest_streak'):
                self.user.longest_streak = self._longest_streak
            else:
                self.user.longest_streak = self._longest_streak
        
        # Also save in settings for backup
        self.settings['current_streak'] = self._current_streak
        self.settings['longest_streak'] = self._longest_streak
        
        # Save the data
        self.save_data()
    
    def get_current_streak(self) -> int:
        """Get the current streak days."""
        return getattr(self, '_current_streak', 0)
    
    def get_longest_streak(self) -> int:
        """Get the longest streak days."""
        return getattr(self, '_longest_streak', 0)
    
    def is_first_time_user(self) -> bool:
        """Check if this is a first-time user (no saved pet)."""
        return self.current_pet is None
    
    def set_selected_pet(self, pet_type: PetType, name: str = ""):
        """Set the user's selected pet."""
        self.current_pet = Pet(pet_type, name)
        
        # Create user if doesn't exist
        if self.user is None:
            self.user = User("Player")
        
        # Initialize streak tracking now that user exists
        self.initialize_streak_tracking()
        
        # Save the data
        self.save_data()
    
    def get_current_pet(self) -> Optional[Pet]:
        """Get the current pet."""
        return self.current_pet
    
    def get_user(self) -> Optional[User]:
        """Get the current user."""
        return self.user
    
    def add_mastery_to_pet(self, amount: int) -> bool:
        """Add mastery to the current pet. Returns True if pet evolved."""
        if self.current_pet:
            evolved = self.current_pet.add_mastery(amount)
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
    
    @classmethod
    def get_save_dir(cls) -> str:
        """Get the directory where save files are stored."""
        return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'user_data')
        
    @classmethod
    def get_save_path(cls) -> str:
        """Get the path to the save file."""
        return os.path.join(cls.get_save_dir(), 'save_data.json')
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate application data."""
        try:
            # Basic structure validation
            if not isinstance(data, dict):
                return False
                
            # Check for required fields
            if 'version' not in data:
                return False
                
            # Version-specific validation
            if data['version'] in ['1.0', '1.5']:
                required_fields = ['user', 'settings', 'pet', 'pet_state']
                return all(field in data for field in required_fields)
                
            # For future versions, we'll need to add more specific validation
            return True
            
        except Exception:
            return False
    
    def save_data(self, force_backup: bool = False) -> bool:
        """
        Save application state to file with atomic write.
        
        Args:
            force_backup: If True, create a backup even if not modified
            
        Returns:
            bool: True if save was successful, False otherwise
        """
        try:
            # Prepare user data (only essential fields)
            user_data = {
                'username': self.user.username if self.user else 'Player',
                'total_study_time': getattr(self.user, 'total_study_time', 0) if self.user else 0,
                'total_questions_answered': getattr(self.user, 'total_questions_answered', 0) if self.user else 0,
                'streak_days': getattr(self.user, 'streak_days', 0) if self.user else 0,
                'longest_streak': getattr(self.user, 'longest_streak', 0) if self.user else 0,
                'last_study_date': getattr(self.user, 'last_study_date', None) if self.user else None
            }
            
            # Prepare pet data (only essential fields)
            pet_data = {}
            if self.current_pet:
                pet_data = {
                    'pet_type': self.current_pet.pet_type.value if hasattr(self.current_pet.pet_type, 'value') else str(self.current_pet.pet_type),
                    'name': getattr(self.current_pet, 'name', '')
                }
                
                # Don't update pet_state from pet object here
                # The pet_state should be managed independently by global_pet_state
                # This prevents overwriting mastery values
                # self.pet_state.update({
                #     'stage': self.current_pet.stage.value if hasattr(self.current_pet.stage, 'value') else int(self.current_pet.stage),
                #     'emotion': self.current_pet.emotion.name if hasattr(self.current_pet.emotion, 'name') else str(self.current_pet.emotion).upper(),
                #     'mastery': int(getattr(self.current_pet, 'mastery', 0)),
                #     'mastery_cap': int(getattr(self.current_pet, 'mastery_cap', 200)),
                #     'last_updated': int(time.time())
                # })
            
            # Prepare data for saving
            data = {
                'version': '1.5',
                'user': user_data,
                'settings': self.settings,
                'pet': pet_data,
                'pet_state': self.pet_state
            }
            
            # Ensure all data is JSON serializable
            def make_serializable(obj):
                if isinstance(obj, (int, float, str, bool, type(None))):
                    return obj
                elif isinstance(obj, dict):
                    return {k: make_serializable(v) for k, v in obj.items()}
                elif isinstance(obj, (list, tuple)):
                    return [make_serializable(x) for x in obj]
                else:
                    return str(obj)
            
            serialized_data = make_serializable(data)
            
            # Create backup if needed
            if force_backup or os.path.exists(self.save_file_path):
                if not backup_file(self.save_file_path):
                    print("Warning: Failed to create backup")
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.save_file_path), exist_ok=True)
            
            # Save with atomic write
            return atomic_write(self.save_file_path, serialized_data)
            
        except Exception as e:
            print(f"Error saving data: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @classmethod
    def load_or_create(cls: Type[T]) -> T:
        """
        Load existing state or create a new instance.
        
        Returns:
            AppState: Loaded or new instance
        """
        instance = cls()
        instance.load_data()
        return instance
    
    def load_data(self) -> bool:
        """
        Load application state from file with validation.
        
        Returns:
            bool: True if data was loaded successfully, False otherwise
        """
        try:
            if not os.path.exists(self.save_file_path):
                print(f"No save file found at {self.save_file_path}")
                return False
                
            try:
                # Load data with atomic read
                data = atomic_read(self.save_file_path)
                if not data:
                    print("Empty save file")
                    return False
            except Exception as e:
                print(f"Error reading save file: {e}")
                return False
            
            try:
                # Validate data
                if not self.validate_data(data):
                    print("Data validation failed")
                    return False
            except Exception as e:
                print(f"Error during data validation: {e}")
                return False
            
            # Load user data
            try:
                if data.get('user'):
                    # Create a new user with basic data
                    from models.user import User  # Lazy import to avoid circular imports
                    user_data = data['user']
                    self.user = User(user_data.get('username', 'Player'))
                    # Set additional user properties if they exist
                    if 'total_study_time' in user_data:
                        self.user.total_study_time = user_data['total_study_time']
                    if 'total_questions_answered' in user_data:
                        self.user.total_questions_answered = user_data['total_questions_answered']
                    if 'streak_days' in user_data:
                        self.user.streak_days = user_data['streak_days']
                        self._current_streak = user_data['streak_days']
                    if 'longest_streak' in user_data:
                        self.user.longest_streak = user_data['longest_streak']
                        self._longest_streak = user_data['longest_streak']
                    if 'last_study_date' in user_data:
                        self.user.last_study_date = user_data['last_study_date']
            except Exception as e:
                print(f"Error loading user data: {e}")
                import traceback
                traceback.print_exc()
                self.user = None
            
            # Load pet data if it exists
            if 'pet' in data and data['pet'] is not None:
                try:
                    from models.pet import Pet, PetType  # Lazy import to avoid circular imports
                    pet_data = data['pet']
                    if 'pet_type' in pet_data:
                        pet_type = PetType(pet_data['pet_type']) if isinstance(pet_data['pet_type'], str) else pet_data['pet_type']
                        self.current_pet = Pet(pet_type, pet_data.get('name', ''))
                        
                        # Update pet state if available
                        if 'pet_state' in data and data['pet_state'] is not None:
                            pet_state = data['pet_state']
                            # Only update if the pet exists in the save data
                            if 'stage' in pet_state:
                                self.current_pet.stage = PetStage(pet_state['stage'])
                            if 'emotion' in pet_state:
                                self.current_pet.emotion = PetEmotion[pet_state['emotion']]
                            if 'mastery' in pet_state:
                                self.current_pet.mastery = int(pet_state['mastery'])
                except (TypeError, ValueError, KeyError) as e:
                    print(f"Error loading pet data: {e}")
                    import traceback
                    traceback.print_exc()
                    self.current_pet = None
            
            # Load pet state if it exists in the save file
            if 'pet_state' in data and data['pet_state'] is not None:
                try:
                    self.pet_state.update({
                        'stage': data['pet_state'].get('stage', self.pet_state['stage']),
                        'emotion': data['pet_state'].get('emotion', self.pet_state['emotion']),
                        'mastery': data['pet_state'].get('mastery', self.pet_state['mastery']),
                        'mastery_cap': data['pet_state'].get('mastery_cap', self.pet_state['mastery_cap']),
                        'last_updated': data['pet_state'].get('last_updated', time.time())
                    })
                except Exception as e:
                    print(f"Error loading pet state: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Load settings
            self.settings = data.get('settings', {})
            
            # Load streak values from settings even if user doesn't exist yet
            if 'current_streak' in self.settings:
                self._current_streak = self.settings['current_streak']
            if 'longest_streak' in self.settings:
                self._longest_streak = self.settings['longest_streak']
            
            # Load streak values from settings if not already loaded (backup)
            if not hasattr(self, '_current_streak') and 'current_streak' in self.settings:
                self._current_streak = self.settings['current_streak']
            if not hasattr(self, '_longest_streak') and 'longest_streak' in self.settings:
                self._longest_streak = self.settings['longest_streak']
            
            # Migrate old session data if it exists
            if 'study_time' in data:
                self.study_session['total_study_time'] = data.get('study_time', 0)
            if 'sessions' in data:
                self.study_session['sessions'] = data.get('sessions', [])
            if 'last_session' in data:
                self.study_session['last_session'] = data.get('last_session')
            
            return True
            
        except Exception as e:
            print(f"Error loading data: {e}")
            import traceback
            traceback.print_exc()
            # Reset to clean state if loading fails
            self.current_pet = None
            self.user = None
            self.settings = {}
            self.study_session = {
                'active': False,
                'type': None,
                'schedule': None,
                'current_block': 0,
                'block_type': None,
                'block_duration': 0,
                'block_start_time': None,
                'start_time': None,
                'paused': False,
                'last_activity': None,
                'completed_blocks': [],
                'total_study_time': 0,
                'session_paused': False
            }
            return False
    
    def _validate_and_repair_pet_data(self, pet_data):
        """Validate and repair corrupted pet data."""
        if not pet_data:
            return None

        try:
            # Check required fields
            required_fields = ['pet_type', 'name', 'stage', 'emotion', 'mastery']
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
                        'happy': 1, 'worried': 2, 'hungry': 3, 'sad': 4, 'angry': 4
                    }
                    if emotion_value.lower() in emotion_map:
                        pet_data['emotion'] = emotion_map[emotion_value.lower()]
                    else:
                        pet_data['emotion'] = 1  # Default to happy
                elif not isinstance(emotion_value, int) or emotion_value < 1 or emotion_value > 4:
                    print(f"Warning: Invalid emotion '{emotion_value}', defaulting to 1")
                    pet_data['emotion'] = 1

                # Ensure mastery is valid
                mastery = pet_data['mastery']
                if not isinstance(mastery, int) or mastery < 0:
                    print(f"Warning: Invalid mastery '{mastery}', defaulting to 0")
                    pet_data['mastery'] = 0

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
        """
        Completely reset all application data to its initial state.
        This includes:
        - User data and settings
        - Current pet and its state
        - Study session data
        - All cached files and directories
        """
        import shutil
        import time
        from pathlib import Path
        
        def safe_delete(path):
            """Safely delete a file or directory with retries"""
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    if os.path.exists(path):
                        if os.path.isfile(path) or os.path.islink(path):
                            os.unlink(path)
                        else:
                            shutil.rmtree(path)
                    return True
                except (OSError, PermissionError) as e:
                    if attempt == max_retries - 1:
                        print(f"Failed to delete {path}: {e}")
                        return False
                    time.sleep(0.1 * (attempt + 1))
            return False
        
        try:
            # 1. Clear in-memory state
            self.user = None
            self.current_pet = None
            self.settings = {}
            
            # 2. Reset study session state
            self.study_session = {
                'active': False,
                'type': None,
                'schedule': None,
                'current_block': 0,
                'block_type': None,
                'block_duration': 0,
                'block_start_time': None,
                'start_time': None,
                'paused': False,
                'last_activity': None,
                'completed_blocks': [],
                'total_study_time': 0,
                'session_paused': False
            }
            
            # 3. Get the user data directory
            user_data_dir = os.path.dirname(self.save_file_path)
            
            # 4. Clear all files in user_data directory
            if os.path.exists(user_data_dir):
                # Delete all files and directories except for the user_data directory itself
                for item in os.listdir(user_data_dir):
                    item_path = os.path.join(user_data_dir, item)
                    safe_delete(item_path)
                
                # Create a fresh empty save file
                os.makedirs(user_data_dir, exist_ok=True)
                with open(self.save_file_path, 'w') as f:
                    json.dump({}, f)
            
            # 5. Clear any cached data in other locations
            cache_dirs = [
                os.path.join(Path.home(), '.cache', 'studypet'),
                os.path.join(os.path.dirname(__file__), '..', '..', '__pycache__'),
                os.path.join(os.path.dirname(__file__), '__pycache__')
            ]
            
            for cache_dir in cache_dirs:
                if os.path.exists(cache_dir):
                    safe_delete(cache_dir)
            
            # 6. Force garbage collection
            import gc
            gc.collect()
            
            return True
            
        except Exception as e:
            print(f"Critical error during reset_data: {e}")
            # Try to at least clear the in-memory state
            self.user = None
            self.current_pet = None
            self.settings = {}
            return False
