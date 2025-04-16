# UI and Game Engine Integration Guidelines

## Introduction

This document outlines best practices and design patterns for integrating UI components with game logic in text-based adventure games. These guidelines aim to prevent issues like the dialogue UI bug that occurred after implementing character creation features.

## Core Issues to Avoid

- **Inconsistent References**: Using different attribute names (`self.ui` vs `self.app`) to reference the same component
- **Implicit Dependencies**: Components depending on each other without clear interfaces
- **Late Binding**: Setting up relationships between components after initialization
- **Testing Gaps**: Missing test coverage for key UI interactions

## Recommended Design Patterns

### 1. Dependency Injection with Interface Contracts

```python
# Define clear interfaces
class DialogueUI(Protocol):
    def start_dialogue(self, npc_name: str, responses: List[DialogueResponse]) -> None: ...
    def end_dialogue(self) -> None: ...
    # Other required methods

# Use constructor injection
class GameEngine:
    def __init__(self, config: GameConfig, ui_provider: DialogueUI):
        self.config = config
        self.ui = ui_provider  # Consistent naming
        
    # Methods can now use self.ui with confidence
```

### 2. Event-Based Communication

```python
# Define events
class DialogueStartedEvent:
    def __init__(self, npc_name: str, responses: List[DialogueResponse]):
        self.npc_name = npc_name
        self.responses = responses

# Publish events instead of direct calls
def _handle_talk_to_npc(self, npc_name: str) -> str:
    # ...processing...
    event = DialogueStartedEvent(npc_display_name, responses)
    self.event_bus.publish(event)
    return ""

# Subscribe to events
def on_mount(self):
    self.event_bus.subscribe(DialogueStartedEvent, self.handle_dialogue_started)
    
def handle_dialogue_started(self, event: DialogueStartedEvent):
    self.dialogue_mode.start_dialogue(event.npc_name, event.responses)
```

### 3. Single Source of Truth for UI State

```python
class GameState:
    def __init__(self):
        self.dialogue_state = DialogueState()
        self.character_state = CharacterState()
        # Other state containers
        
    # Methods to update state that notify observers

class DialogueState:
    def __init__(self):
        self.is_active = False
        self.npc_name = ""
        self.options = []
        self.selected_index = 0
        self.history = []
        self.observers = []
        
    def set_active(self, active: bool):
        self.is_active = active
        self._notify_observers()
        
    def _notify_observers(self):
        for observer in self.observers:
            observer.on_dialogue_state_changed(self)
```

### 4. Automated Tests for UI Interactions

```python
def test_dialogue_ui_after_character_creation():
    # Arrange
    config = MockGameConfig()
    engine = GameEngine(config)
    ui = MockGameUI()
    engine.ui = ui
    
    # Act
    engine.start_character_creation()  # Should set up character
    # Simulate completion of character creation
    engine.process_input("talk to barkeeper")
    
    # Assert
    assert ui.dialogue_mode.is_active
    assert len(ui.dialogue_mode.options) > 0
    assert ui.game_input.has_focus
```

### 5. Consistent Component Initialization

```python
def main():
    # Initialize components
    config = load_config("game_config.yaml")
    
    # Create UI first
    app = GameUI()
    
    # Create engine with UI reference
    game_engine = GameEngine(config, ui_provider=app)
    
    # Set up bidirectional reference if needed
    app.game_engine = game_engine
    
    return app
```

## Common Pitfalls

1. **Attribute Name Mismatches**: Using inconsistent attribute names like `self.ui` in one place and `self.app` in another

2. **Circular Dependencies**: Components that reference each other creating initialization order problems

3. **Missing Interface Definitions**: Components assuming methods/attributes exist without verification

4. **Late UI Updates**: Making changes to UI state outside the UI thread or after components are mounted

5. **Tight Coupling**: Game logic directly manipulating UI elements instead of going through proper channels

## Implementation Checklist

- [ ] Define clear interfaces for all component interactions
- [ ] Use consistent naming conventions for component references
- [ ] Initialize dependencies at construction time where possible
- [ ] Implement an event system for loose coupling between components
- [ ] Create unit tests that verify UI behavior in different game states
- [ ] Document the responsibility boundaries between UI and game logic
- [ ] Add runtime checks to verify component references before use

## Example Refactoring

Before:
```python
# In game_engine.py
def _handle_talk_to_npc(self, npc_name: str) -> str:
    # ...processing...
    if hasattr(self, 'ui') and self.ui:
        self.ui.dialogue_mode.start_dialogue(npc_display_name, responses)
    # ...
```

After:
```python
# In game_engine.py
def __init__(self, config: GameConfig, ui=None):
    self.config = config
    self.ui = ui  # Single consistent name
    # Runtime check
    if self.ui is not None and not hasattr(self.ui, 'dialogue_mode'):
        raise AttributeError("UI component missing required dialogue_mode attribute")

def _handle_talk_to_npc(self, npc_name: str) -> str:
    # ...processing...
    if self.ui is not None:
        self.ui.dialogue_mode.start_dialogue(npc_display_name, responses)
    # ...
``` 