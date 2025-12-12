"""Centralized state management for pet display updates."""
from typing import Callable, List, Optional
from enum import Enum

class PetStateChange(Enum):
    STAGE = "stage"
    EMOTION = "emotion"
    TYPE = "type"
    ALL = "all"

class StateManager:
    _instance = None
    _callbacks = []
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StateManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialized = True
    
    @classmethod
    def subscribe(cls, callback: Callable[[PetStateChange], None]) -> None:
        """Subscribe to state change notifications."""
        if callback not in cls._callbacks:
            cls._callbacks.append(callback)
    
    @classmethod
    def unsubscribe(cls, callback: Callable[[PetStateChange], None]) -> None:
        """Unsubscribe from state change notifications."""
        if callback in cls._callbacks:
            cls._callbacks.remove(callback)
    
    @classmethod
    def notify_state_change(cls, change_type: PetStateChange) -> None:
        """Notify all subscribers of a state change."""
        for callback in cls._callbacks[:]:  # Create a copy to allow modifications during iteration
            try:
                callback(change_type)
            except Exception as e:
                print(f"Error in state change callback: {e}")

# Global instance for easy access
state_manager = StateManager()
