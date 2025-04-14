"""
This module handles quest management, including tracking quest progress, objectives, 
and generating notifications for quest events.
"""
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple

from config.config_loader import Quest, QuestStage
from game.game_state import GameState, QuestStatus


class NotificationType(Enum):
    """Types of quest notifications."""
    QuestStarted = auto()
    QuestUpdated = auto()
    QuestCompleted = auto()
    ObjectiveCompleted = auto()
    ObjectiveAdded = auto()
    QuestFailed = auto()


@dataclass
class QuestNotification:
    """Represents a quest notification."""
    quest_id: str
    title: str
    message: str
    type: NotificationType
    timestamp: float = field(default_factory=time.time)
    is_new: bool = field(default=True)


class QuestManager:
    """Manages quests and their progression."""
    
    def __init__(self, game_state: GameState):
        """Initialize the quest manager."""
        self.game_state = game_state
        self.notifications = []

    def start_quest(self, quest_id: str) -> bool:
        """Start a quest. Returns True if successful."""
        # First ensure the quest exists in the state
        quest = self.game_state.get_quest(quest_id)
        if not quest:
            # Try to get the quest from the game config
            quest_config = self.game_state.config.get_quest(quest_id)
            if quest_config:
                # Convert config quest to Quest object and add it
                quest = Quest(
                    id=quest_config.id,
                    title=quest_config.title,
                    description=quest_config.description,
                    short_description=quest_config.short_description,
                    objectives=[],
                    status=QuestStatus.NotStarted
                )
                self.game_state.add_quest(quest)
            else:
                return False
        
        # Now update the quest status
        if self.game_state.start_quest(quest_id):
            # Set the first stage as active if there are stages
            if quest.stages:
                self.game_state.set_active_stage(quest_id, quest.stages[0].id)
            
            # Add notification
            self._add_notification(
                quest_id,
                quest.title,
                "Quest started",
                NotificationType.QuestStarted
            )
            return True
        return False

    def complete_quest(self, quest_id: str) -> bool:
        """Complete a quest. Returns True if successful."""
        if self.game_state.complete_quest(quest_id):
            quest = self.game_state.get_quest(quest_id)
            if quest:
                self._add_notification(
                    quest_id,
                    quest.title,
                    "Quest completed",
                    NotificationType.QuestCompleted
                )
            return True
        return False

    def fail_quest(self, quest_id: str) -> bool:
        """Fail a quest. Returns True if successful."""
        if self.game_state.fail_quest(quest_id):
            quest = self.game_state.get_quest(quest_id)
            if quest:
                self._add_notification(
                    quest_id,
                    quest.title,
                    "Quest failed",
                    NotificationType.QuestFailed
                )
            return True
        return False

    def check_all_quest_updates(self) -> None:
        """Check for all quest updates."""
        self.game_state.check_all_quest_updates()

    def get_quest(self, quest_id: str) -> Optional[Quest]:
        """Get a quest by ID."""
        return self.game_state.get_quest(quest_id)

    def get_quest_status(self, quest_id: str) -> Optional[QuestStatus]:
        """Get a quest's status."""
        return self.game_state.get_quest_status(quest_id)

    def get_active_quests(self) -> List[Quest]:
        """Get all active quests."""
        return self.game_state.get_active_quests()

    def get_completed_quests(self) -> List[Quest]:
        """Get all completed quests."""
        return self.game_state.get_completed_quests()

    def get_failed_quests(self) -> List[Quest]:
        """Get all failed quests."""
        return self.game_state.get_failed_quests()

    def advance_quest(self, quest_id: str, stage_id: str) -> bool:
        """Advance a quest to the next stage."""
        quest = self.game_state.get_quest(quest_id)
        if not quest or self.game_state.get_quest_status(quest_id) != QuestStatus.InProgress:
            return False
            
        # Find the current stage index
        current_stage = self.game_state.get_active_stage(quest_id)
        if not current_stage:
            return False
            
        current_index = next((i for i, stage in enumerate(quest.stages) 
                            if stage.id == current_stage), -1)
        if current_index == -1:
            return False
            
        # Find the target stage index
        target_index = next((i for i, stage in enumerate(quest.stages) 
                           if stage.id == stage_id), -1)
        if target_index == -1 or target_index <= current_index:
            return False
            
        self.game_state.set_active_stage(quest_id, stage_id)
        
        # Add notification for quest advancement
        self._add_notification(
            quest_id,
            quest.title,
            f"Quest advanced to stage: {stage_id}",
            NotificationType.QuestUpdated
        )
        return True

    def complete_objective(self, quest_id: str, objective_id: str) -> bool:
        """Mark an objective as completed."""
        if self.game_state.get_quest_status(quest_id) != QuestStatus.InProgress:
            return False
            
        if self.game_state.add_completed_objective(quest_id, objective_id):
            quest = self.game_state.get_quest(quest_id)
            if quest:
                self._add_notification(
                    quest_id,
                    quest.title,
                    f"Objective completed: {objective_id}",
                    NotificationType.ObjectiveCompleted
                )
            return True
        return False

    def take_quest_branch(self, quest_id: str, branch_id: str) -> bool:
        """Take a quest branch."""
        if self.game_state.get_quest_status(quest_id) != QuestStatus.InProgress:
            return False
            
        return self.game_state.add_quest_branch(quest_id, branch_id)

    def add_quest_item(self, quest_id: str, item_id: str) -> bool:
        """Add an item to a quest."""
        if self.game_state.get_quest_status(quest_id) != QuestStatus.InProgress:
            return False
            
        return self.game_state.add_quest_item(quest_id, item_id)

    def remove_quest_item(self, quest_id: str, item_id: str) -> bool:
        """Remove an item from a quest."""
        if self.game_state.get_quest_status(quest_id) != QuestStatus.InProgress:
            return False
            
        return self.game_state.remove_quest_item(quest_id, item_id)

    def get_quest_progress(self, quest_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed progress for a quest."""
        return self.game_state.get_quest_progress(quest_id)

    def get_all_quests(self) -> Dict[str, Quest]:
        """Get all available quests."""
        return self.game_state.get_all_quests()
    
    def get_main_quests(self) -> List[Quest]:
        """Get all main quests."""
        return self.game_state.get_main_quests()
    
    def get_side_quests(self) -> List[Quest]:
        """Get all side quests."""
        return self.game_state.get_side_quests()
    
    def is_quest_active(self, quest_id: str) -> bool:
        """Check if a quest is active."""
        return self.game_state.get_quest_status(quest_id) == QuestStatus.InProgress
    
    def get_quest_stage(self, quest_id: str) -> Optional[QuestStage]:
        """Get the current stage of a quest."""
        quest = self.game_state.get_quest(quest_id)
        if not quest:
            return None
        
        active_stage_id = self.game_state.get_active_stage(quest_id)
        if not active_stage_id:
            return None
            
        return next((stage for stage in quest.stages if stage.id == active_stage_id), None)
    
    def is_objective_completed(self, quest_id: str, objective_id: str) -> bool:
        """Check if a quest objective is completed."""
        return self.game_state.is_objective_completed(quest_id, objective_id)
    
    def has_taken_branch(self, quest_id: str, branch_id: str) -> bool:
        """Check if a quest branch has been taken."""
        return self.game_state.has_taken_branch(quest_id, branch_id)

    def _add_notification(self, quest_id: str, title: str, message: str, 
                         notification_type: NotificationType) -> None:
        """Add a quest notification."""
        self.notifications.append(
            QuestNotification(
                quest_id=quest_id,
                title=title,
                message=message,
                type=notification_type
            )
        )

    def get_active_notifications(self) -> List[QuestNotification]:
        """Get all active notifications."""
        return [n for n in self.notifications if n.is_new]

    def clear_old_notifications(self, max_age: int) -> None:
        """Clear notifications older than max_age seconds."""
        current_time = time.time()
        self.notifications = [
            n for n in self.notifications 
            if current_time - n.timestamp < max_age
        ]
