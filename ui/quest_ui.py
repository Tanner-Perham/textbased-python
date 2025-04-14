"""
Quest UI component for displaying quests and notifications.
"""
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Static, Label, Button, Tab
from textual.reactive import reactive
from quest.quest_manager import QuestManager, NotificationType
from game.game_state import GameState, QuestStatus
from config.config_loader import Quest, QuestStage
from typing import List, Optional, Set, Dict, Any

class QuestNotification(Static):
    """Widget for displaying a quest notification."""
    
    def __init__(self, notification):
        super().__init__()
        self.notification = notification
        
    def compose(self) -> ComposeResult:
        """Compose the notification widget."""
        yield Label(f"[{self.notification.title}] {self.notification.message}")

class QuestItem(Static):
    """Widget for displaying a single quest."""
    
    def __init__(self, quest: Quest):
        super().__init__()
        self.quest = quest
        
    def compose(self) -> ComposeResult:
        """Compose the quest item widget."""
        with Vertical():
            yield Label(f"[{'Main' if self.quest.is_main_quest else 'Side'}] {self.quest.title}")
            yield Label(self.quest.description)
            
            # Show current stage if any
            current_stage_id = self.app.game_engine.game_state.quest_state.get_active_stage(self.quest.id)
            if current_stage_id:
                current_stage = next((stage for stage in self.quest.stages 
                                    if stage.id == current_stage_id), None)
                if current_stage:
                    yield Label(f"Current Stage: {current_stage.title}")
                    yield Label(current_stage.description)
                    
                    # Show objectives
                    with Vertical():
                        for obj in current_stage.objectives:
                            is_completed = self.app.game_engine.game_state.quest_state.is_objective_completed(
                                self.quest.id, obj.get('id', '')
                            )
                            status = "✓" if is_completed else "○"
                            optional = "(Optional) " if obj.get('is_optional', False) else ""
                            yield Label(f"{status} {optional}{obj.get('description', '')}")

class QuestList(Static):
    """Widget for displaying a list of quests."""
    
    def __init__(self, quests: List[Quest], id: str = ""):
        """Initialize the quest list."""
        super().__init__()
        self.quests = quests
        self.id = id

    def compose(self):
        """Create child widgets for the quest list."""
        for quest in self.quests:
            yield Static(f"{quest.title} - {quest.status}", id=f"{self.id}-{quest.id}")

class QuestTab(Tab):
    """Tab for displaying quest information."""
    
    def __init__(self, quest_manager, game_state: GameState):
        """Initialize the quest tab."""
        super().__init__("Quests")
        self.quest_manager = quest_manager
        self.game_state = game_state
        self.last_quest_state = {
            'active': set(),
            'completed': set(),
            'failed': set()
        }

    def compose(self):
        """Create child widgets for the quest tab."""
        with Vertical():
            # Active Quests
            yield Static("Active Quests", classes="section-header")
            active_quests = self.game_state.get_active_quests()
            yield QuestList(active_quests, id="active-quests")

            # Completed Quests
            yield Static("Completed Quests", classes="section-header")
            completed_quests = self.game_state.get_completed_quests()
            yield QuestList(completed_quests, id="completed-quests")

            # Failed Quests
            yield Static("Failed Quests", classes="section-header")
            failed_quests = self.game_state.get_failed_quests()
            yield QuestList(failed_quests, id="failed-quests")

    def refresh_quests(self) -> None:
        """Refresh the quest display."""
        self.remove_children()
        self.compose()

    def on_mount(self) -> None:
        """Called when the widget is mounted to the screen."""
        # Set up a timer to periodically check for quest updates
        self.set_interval(1.0, self._check_quest_updates)

    def _check_quest_updates(self) -> None:
        """Check for quest updates and refresh if needed."""
        # Get current quest states
        current_active = set(quest.id for quest in self.game_state.get_active_quests())
        current_completed = set(quest.id for quest in self.game_state.get_completed_quests())
        current_failed = set(quest.id for quest in self.game_state.get_failed_quests())
        
        # Check if any quest states have changed
        if (current_active != self.last_quest_state['active'] or
            current_completed != self.last_quest_state['completed'] or
            current_failed != self.last_quest_state['failed']):
            
            # Update last state
            self.last_quest_state = {
                'active': current_active,
                'completed': current_completed,
                'failed': current_failed
            }
            
            # Refresh the display
            self.refresh_quests()

class QuestUI:
    """UI components for displaying quest information."""
    
    def __init__(self, game_state: GameState):
        """Initialize the quest UI."""
        self.game_state = game_state
        self.last_quest_state = {
            'active': set(),
            'completed': set(),
            'failed': set()
        }

    def get_quest_stage_info(self, quest: Quest) -> Optional[Dict[str, Any]]:
        """Get information about the current quest stage."""
        current_stage_id = self.game_state.get_active_stage(quest.id)
        if not current_stage_id:
            return None

        current_stage = next((stage for stage in quest.stages 
                            if stage.id == current_stage_id), None)
        if not current_stage:
            return None

        objectives = []
        for objective in current_stage.objectives:
            is_completed = self.game_state.is_objective_completed(
                quest.id, objective['id']
            )
            objectives.append({
                'id': objective['id'],
                'text': objective['text'],
                'is_completed': is_completed,
                'is_optional': objective.get('is_optional', False)
            })

        return {
            'id': current_stage.id,
            'title': current_stage.title,
            'description': current_stage.description,
            'objectives': objectives,
            'notification_text': current_stage.notification_text
        }

    def get_quest_list(self) -> Dict[str, List[Quest]]:
        """Get lists of quests by status."""
        return {
            'active': self.game_state.get_active_quests(),
            'completed': self.game_state.get_completed_quests(),
            'failed': self.game_state.get_failed_quests()
        }

    def get_quest_changes(self) -> Dict[str, Set[str]]:
        """Get changes in quest states since last check."""
        current_active = set(quest.id for quest in self.game_state.get_active_quests())
        current_completed = set(quest.id for quest in self.game_state.get_completed_quests())
        current_failed = set(quest.id for quest in self.game_state.get_failed_quests())

        changes = {
            'new_active': current_active - self.last_quest_state['active'],
            'new_completed': current_completed - self.last_quest_state['completed'],
            'new_failed': current_failed - self.last_quest_state['failed']
        }

        # Update last state
        self.last_quest_state = {
            'active': current_active,
            'completed': current_completed,
            'failed': current_failed
        }

        return changes

    def get_quest_details(self, quest_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a quest."""
        quest = self.game_state.get_quest(quest_id)
        if not quest:
            return None

        progress = self.game_state.get_quest_progress(quest_id)
        if not progress:
            return None

        return {
            'id': quest.id,
            'title': quest.title,
            'description': quest.description,
            'short_description': quest.short_description,
            'status': quest.status,
            'progress': progress,
            'is_main_quest': quest.is_main_quest
        } 