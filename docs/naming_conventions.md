# StudyPet Naming Convention Guide

## Overview
This document establishes unified naming conventions for the StudyPet project to ensure consistency, readability, and maintainability across the codebase.

## File Naming Conventions

### Python Files
- **Classes**: `PascalCase` (e.g., `MainGameScreen`, `PetManager`, `StudyTimer`)
- **Functions/Methods**: `snake_case` (e.g., `start_study_session`, `update_pet_info`, `handle_click`)
- **Variables**: `snake_case` (e.g., `current_pet`, `timer_active`, `study_duration`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_DURATION`, `MAX_AFFECTION`, `UI_BLOCK_MARGIN`)

### UI Elements
- **Widget Variables**: `descriptive_name` (e.g., `timer_display_label`, `pause_button`, `status_frame`)
- **Container Variables**: `*_container`, `*_frame`, `*_panel` (e.g., `timer_container`, `status_frame`)
- **Content Variables**: `*_content` (e.g., `status_content`, `timer_content`)

### Method Naming Patterns

#### Display/Update Methods
- `update_*_display()` - For updating visual displays (e.g., `update_pet_display`, `update_timer_display`)
- `update_*_info()` - For updating information displays (e.g., `update_pet_info_display`, `update_status_info`)
- `refresh_*()` - For refreshing UI components (e.g., `refresh_chat_ui`, `refresh_developer_ui`)

#### State Management Methods
- `toggle_*()` - For toggling states (e.g., `toggle_timer_panel`, `toggle_chat_panel`)
- `start_*()` - For starting processes (e.g., `start_study_session`, `start_music_playback`)
- `stop_*()` - For stopping processes (e.g., `stop_study_session`, `stop_music_playback`)
- `pause_*()` / `resume_*()` - For pause/resume functionality

#### Event Handlers
- `handle_*()` - For event handling (e.g., `handle_playground_click`, `handle_window_resize`)
- `on_*()` - Alternative for event handlers (e.g., `on_button_click`, `on_timer_tick`)

#### UI Creation Methods
- `create_*_ui()` - For creating UI components (e.g., `create_timer_ui`, `create_chat_ui`)
- `setup_*()` - For setting up systems (e.g., `setup_ui`, `setup_pet_theme`)
- `_make_*()` - For helper methods that create objects (e.g., `_make_scrollable_panel`)

#### Developer Mode Methods
- `dev_*()` - For developer-specific functionality (e.g., `dev_toggle_mode`, `dev_force_evolve`)
- `_create_dev_*()` / `_show_dev_*()` / `_hide_dev_*()` - For dev UI management

## Variable Naming Conventions

### Boolean Variables
- `*_active` - For active states (e.g., `timer_active`, `study_timer_active`)
- `*_enabled` - For enabled features (e.g., `developer_mode_enabled`, `music_enabled`)
- `*_expanded` - For UI expansion states (e.g., `timer_expanded`, `chat_expanded`)
- `*_visible` - For visibility states (e.g., `controls_visible`, `dev_buttons_visible`)

### State Variables
- `*_state` - For general state (e.g., `timer_state`, `pet_state`)
- `*_status` - For status information (e.g., `connection_status`, `loading_status`)
- `*_progress` - For progress tracking (e.g., `study_progress`, `affection_progress`)

### Thread and Process Variables
- `*_thread` - For background threads (e.g., `study_thread`, `timer_thread`)
- `*_process` - For subprocesses (e.g., `music_process`, `background_process`)
- `*_worker` - For worker objects (e.g., `timer_worker`, `update_worker`)

## Method Parameter Naming
- `parent` - For parent widgets/containers
- `duration` - For time durations
- `callback` - For callback functions
- `event` - For event objects
- `force` - For forcing operations (boolean)

## Color and Theme Naming
- Color variables: `*_color` (e.g., `bg_color`, `text_color`)
- Theme variables: `*_theme` (e.g., `pet_theme`, `ui_theme`)
- Color scheme keys: `bg_*`, `text_*`, `accent_*` (e.g., `bg_main`, `text_dark`, `accent_primary`)

## Database and Data Naming
- Table names: `snake_case` (e.g., `study_sessions`, `pet_data`, `user_preferences`)
- Column names: `snake_case` (e.g., `session_duration`, `pet_name`, `created_at`)
- Model attributes: `snake_case` (e.g., `pet_name`, `stage_level`, `affection_points`)

## Error Handling
- Exception variables: `e`, `err`, `error`
- Error messages: `*_error` (e.g., `connection_error`, `validation_error`)
- Error codes: `ERROR_*` (e.g., `ERROR_CONNECTION_FAILED`, `ERROR_INVALID_INPUT`)

## Testing
- Test files: `test_*.py` (e.g., `test_pet_manager.py`, `test_timer_system.py`)
- Test methods: `test_*()` (e.g., `test_start_session`, `test_pause_functionality`)
- Mock objects: `mock_*` (e.g., `mock_pet`, `mock_timer`)

### Recent UI Improvements (Latest):
1. ✅ **Preset Button Units**: Removed "min" from preset buttons (show "10", "15", "25" instead of "10m", "15m", "25m")
2. ✅ **Immediate Countdown**: Countdown appears instantly when timer starts, no need to reopen panel
3. ✅ **Enhanced Scrolling**: Timer panel always has functional scrolling with auto-scroll to countdown
4. ✅ **Vertical Layout**: Study Timer now uses simple vertical scrolling like Pet Status panel
5. ✅ **2x3 Grid Layout**: Preset buttons arranged in 2 rows with 3 buttons each for better space utilization

### Timer System Standards:
- `countdown_frame` - Bottom section showing active timer display
- `countdown_display` - Large timer display (28pt font)
- `progress_display` - Progress text showing elapsed time
- `timer_controls_frame` - Pause/Stop buttons container
- `update_timer_ui()` - Dynamically switches between selection and active timer states

### New ScrollablePanel Architecture:
- `ScrollablePanel` - Reusable scrollable component in `ui/scrollable_panel.py`
- `scrollable.get_inner_frame()` - Content area for widgets
- `scrollable.refresh_scroll()` - Refresh scroll region and reset position
- `scrollable.scroll_to_bottom()` - Programmatically scroll to bottom
- `scrollable.update_content_size()` - Update scroll region when content changes

### Timer Panel Layout (2x3 Grid):
```
⏱️ Study Timer ▲
┌─────────────────┐
│ ⏱️ Study Timer  │
│ Choose duration │
│                 │
│ Quick Start:    │
│ □ 10   15   25  │ ← Row 1: 3 buttons
│ □ 30   45   60  │ ← Row 2: 3 buttons
│                 │
│ Custom: [___]   │ (dev mode)
│                 │
│ 💡 Study Tips:  │
│ • Set goals     │
│ • Silent phone  │
│ • Keep water    │
│ • Take breaks   │
│                 │
│ 🎯 25:00        │ (when active)
│ ▶️ Pause  ⏹️ Stop│ (when active)
└─────────────────┘
```

### Implementation Guidelines

#### When Using ScrollablePanel:
1. Import: `from ui.scrollable_panel import ScrollablePanel`
2. Create: `scrollable = ScrollablePanel(parent, background_color)`
3. Add Content: `content_frame = scrollable.get_inner_frame()`
4. Control: `scrollable.refresh_scroll()`, `scrollable.scroll_to_bottom()`

## Implementation Guidelines

### When Adding New Code:
1. Follow the established patterns above
2. Use descriptive names that clearly indicate purpose
3. Maintain consistency with existing similar functionality
4. Update this document when new patterns emerge

### When Refactoring:
1. Update method calls throughout the codebase
2. Maintain backward compatibility where possible
3. Update documentation and comments
4. Test thoroughly after changes

## Examples

### Good Examples:
```python
class MainGameScreen:
    def __init__(self):
        self.study_timer_active = False
        self.timer_container = None
        self.current_pet = None

    def start_study_session(self, duration_minutes=25):
        """Start a study session with specified duration."""
        if self.study_timer_active:
            return
        # ... implementation

    def update_pet_info_display(self):
        """Update the pet information display."""
        # ... implementation

    def toggle_timer_panel(self, event=None):
        """Toggle the timer panel expansion."""
        # ... implementation
```

### Bad Examples:
```python
# ❌ Inconsistent naming
class MainGameScreen:
    def __init__(self):
        self.TimerActive = False  # Should be snake_case
        self.timerContainer = None  # Should be snake_case

    def StartSession(self):  # Should be snake_case
        pass

    def updatePetDisplay(self):  # Should be snake_case
        pass
```

This naming convention ensures code readability, maintainability, and consistency across the StudyPet project.
