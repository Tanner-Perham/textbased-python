"""
This module handles quest management, including tracking quest progress, objectives, 
and generating notifications for quest events.
"""
import time
from dataclasses import dataclass
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
    """Notification for quest-related events."""
    quest_id: str
    title: str
    message: str
    is_new: bool
    notification_type: NotificationType
    timestamp: float  # Using timestamp instead of Instant


class QuestManager:
    """
    Manages quests, including starting quests, tracking progress,
    completing objectives, and generating notifications.
    """
    
    def __init__(self, quests: Dict[str, Quest]):
        """Initialize the quest manager with the available quests."""
        self.quests = quests
        self.active_notifications: List[QuestNotification] = []

    def get_all_quests(self) -> Dict[str, Quest]:
        """Get all available quests."""
        return self.quests
    
    def get_quest(self, quest_id: str) -> Optional[Quest]:
        """Get a specific quest by ID."""
        return self.quests.get(quest_id)
    
    def get_active_quests(self) -> List[Quest]:
        """Get all active quests."""
        return [quest for quest in self.quests.values() 
                if not quest.is_hidden and any(
                    stage.status == "InProgress" for stage in quest.stages
                )]
    
    def get_completed_quests(self) -> List[Quest]:
        """Get all completed quests."""
        return [quest for quest in self.quests.values() 
                if self._is_quest_completed(quest)]
    
    def get_main_quests(self) -> List[Quest]:
        """Get all main quests."""
        return [quest for quest in self.quests.values() 
                if quest.is_main_quest]
    
    def get_side_quests(self) -> List[Quest]:
        """Get all side quests."""
        return [quest for quest in self.quests.values() 
                if not quest.is_main_quest]
    
    def is_quest_active(self, quest_id: str, game_state: GameState) -> bool:
        """Check if a quest is active."""
        return game_state.quest_log.get(quest_id) == QuestStatus.InProgress
    
    def get_quest_stage(self, quest_id: str) -> Optional[QuestStage]:
        """Get the current stage of a quest."""
        quest = self.quests.get(quest_id)
        if not quest:
            return None
        
        for stage in quest.stages:
            if stage.status == "InProgress":
                return stage
        
        return None
    
    def is_objective_completed(self, quest_id: str, objective_id: str, 
                              game_state: GameState) -> bool:
        """Check if a quest objective is completed."""
        return game_state.is_quest_objective_completed(quest_id, objective_id)
    
    def has_taken_branch(self, quest_id: str, branch_id: str, 
                         game_state: GameState) -> bool:
        """Check if a quest branch has been taken."""
        return game_state.is_quest_branch_taken(quest_id, branch_id)
    
    def start_quest(self, quest_id: str, game_state: GameState) -> bool:
        """Start a quest."""
        if quest_id not in self.quests:
            return False
        
        if quest_id in game_state.quest_log:
            return False
        
        quest = self.quests[quest_id]
        should_start = False
        quest_title = ""
        
        # Check if no stages are in progress yet
        if not any(stage.status == "InProgress" for stage in quest.stages):
            if quest.stages:
                first_stage = quest.stages[0]
                first_stage.status = "InProgress"
                should_start = True
                quest_title = quest.title
                
                # Update game state
                game_state.quest_log[quest_id] = QuestStatus.InProgress
                game_state.active_quest_stages[quest_id] = first_stage.id
        
        # Add notification if quest was started
        if should_start:
            self._add_notification(
                quest_id,
                quest_title,
                f"New quest started: {quest_id}",
                NotificationType.QuestStarted
            )
            return True
        
        return False
    
    def advance_quest(self, quest_id: str, stage_id: str, game_state: GameState) -> bool:
        """Advance a quest to a specific stage."""
        if quest_id not in self.quests or game_state.quest_log.get(quest_id) != QuestStatus.InProgress:
            return False
        
        quest = self.quests[quest_id]
        updated = False
        quest_title = quest.title
        notification_text = ""
        
        # Find current stage index
        current_stage_idx = next((i for i, stage in enumerate(quest.stages) 
                                 if stage.status == "InProgress"), None)
        
        # Find target stage index
        target_stage_idx = next((i for i, stage in enumerate(quest.stages) 
                                if stage.id == stage_id), None)
        
        if current_stage_idx is not None and target_stage_idx is not None:
            # Mark current stage as completed
            quest.stages[current_stage_idx].status = "Completed"
            
            # Mark target stage as in progress
            quest.stages[target_stage_idx].status = "InProgress"
            
            # Update game state
            game_state.active_quest_stages[quest_id] = stage_id
            
            # Get notification text
            notification_text = quest.stages[target_stage_idx].notification_text
            updated = True
        
        if updated and notification_text:
            self._add_notification(
                quest_id,
                quest_title,
                f"Quest updated: {notification_text}",
                NotificationType.QuestUpdated
            )
        
        return updated
    
    def complete_objective(self, quest_id: str, objective_id: str, 
                          game_state: GameState) -> bool:
        """Complete a quest objective."""
        if quest_id not in self.quests or game_state.quest_log.get(quest_id) != QuestStatus.InProgress:
            return False
        
        quest = self.quests[quest_id]
        completed = False
        quest_title = quest.title
        objective_description = ""
        completion_events = []
        should_update_progress = False
        
        # Find the current stage
        current_stage_idx = next((i for i, stage in enumerate(quest.stages) 
                                 if stage.status == "InProgress"), None)
        
        if current_stage_idx is not None:
            stage = quest.stages[current_stage_idx]
            
            # Find the objective
            objective_idx = next((i for i, obj in enumerate(stage.objectives) 
                                 if obj.get('id') == objective_id), None)
            
            if objective_idx is not None:
                objective = stage.objectives[objective_idx]
                
                # Mark as completed
                objective['is_completed'] = True
                
                # Update game state tracking
                if quest_id not in game_state.completed_objectives:
                    game_state.completed_objectives[quest_id] = set()
                
                game_state.completed_objectives[quest_id].add(objective_id)
                
                # Capture necessary data
                completed = True
                objective_description = objective.get('description', '')
                completion_events = objective.get('completion_events', [])
                
                # Check if stage is completed
                if not any(not obj.get('is_completed', False) and not obj.get('is_optional', False) 
                          for obj in stage.objectives):
                    should_update_progress = True
        
        # Process completion events
        for event in completion_events:
            self._execute_game_event(event, game_state)
        
        # Add notification
        if completed:
            self._add_notification(
                quest_id,
                quest_title,
                f"Objective completed: {objective_description}",
                NotificationType.ObjectiveCompleted
            )
            
            # Check if stage is completed and update quest progress if needed
            if should_update_progress:
                self.update_quest_progress(quest_id, game_state)
        
        return completed
    
    def fail_quest(self, quest_id: str, game_state: GameState) -> None:
        """Fail a quest."""
        if quest_id not in self.quests:
            return
        
        quest = self.quests[quest_id]
        quest_title = quest.title
        should_fail = False
        
        # Update all in-progress stages to failed
        for stage in quest.stages:
            if stage.status == "InProgress":
                stage.status = "Failed"
                should_fail = True
        
        if should_fail:
            # Update quest log
            game_state.quest_log[quest_id] = QuestStatus.Failed
            
            # Add notification
            self._add_notification(
                quest_id,
                quest_title,
                f"Quest failed: {quest_title}",
                NotificationType.QuestFailed
            )
    
    def unlock_quest_branch(self, quest_id: str, branch_id: str, game_state: GameState) -> bool:
        """Unlock a quest branch."""
        if quest_id not in self.quests:
            return False
        
        if quest_id not in game_state.taken_quest_branches:
            game_state.taken_quest_branches[quest_id] = set()
        
        game_state.taken_quest_branches[quest_id].add(branch_id)
        return True
    
    def update_quest_progress(self, quest_id: str, game_state: GameState) -> bool:
        """Update quest progress based on completed objectives."""
        if quest_id not in self.quests:
            return False
        
        quest = self.quests[quest_id]
        quest_title = quest.title
        stage_updated = False
        complete_stage = False
        next_stage_id = None
        stage_notification_text = ""
        quest_completed = False
        completion_events = []
        
        # Find current in-progress stage
        current_stage_idx = next((i for i, stage in enumerate(quest.stages) 
                                 if stage.status == "InProgress"), None)
        
        if current_stage_idx is not None:
            current_stage = quest.stages[current_stage_idx]
            stage_notification_text = current_stage.notification_text
            
            # Check all required objectives
            all_required_completed = not any(
                not obj.get('is_completed', False) and not obj.get('is_optional', False)
                for obj in current_stage.objectives
            )
            
            if all_required_completed:
                # Complete this stage
                current_stage.status = "Completed"
                complete_stage = True
                
                # Determine next stage based on conditions
                for next_option in current_stage.next_stages:
                    condition = next_option.get('condition')
                    
                    if not condition or self._check_condition(condition, game_state):
                        next_stage_id = next_option.get('stage_id')
                        break
                
                # Process completion events
                completion_events = current_stage.completion_events
                
                # Check if quest is completed (no next stage)
                if not next_stage_id:
                    quest_completed = True
            
            stage_updated = complete_stage
        
        # Process completion events
        for event in completion_events:
            self._execute_game_event(event, game_state)
        
        # Add stage completion notification
        if stage_updated:
            self._add_notification(
                quest_id,
                quest_title,
                f"Quest updated: {stage_notification_text}",
                NotificationType.QuestUpdated
            )
        
        # Start next stage if available
        if next_stage_id:
            next_stage_idx = next((i for i, stage in enumerate(quest.stages) 
                                  if stage.id == next_stage_id), None)
            
            if next_stage_idx is not None:
                next_stage = quest.stages[next_stage_idx]
                next_stage.status = "InProgress"
                
                # Update game state
                game_state.active_quest_stages[quest_id] = next_stage_id
                
                # Add notification
                if next_stage.notification_text:
                    self._add_notification(
                        quest_id,
                        quest_title,
                        f"New objective: {next_stage.notification_text}",
                        NotificationType.ObjectiveAdded
                    )
        
        # Mark quest as completed if needed
        if quest_completed:
            game_state.quest_log[quest_id] = QuestStatus.Completed
            
            # Give rewards
            self._give_quest_rewards(quest_id, game_state)
            
            # Final notification
            self._add_notification(
                quest_id,
                quest_title,
                f"Quest completed: {quest_id}",
                NotificationType.QuestCompleted
            )
        
        return complete_stage
    
    def check_all_quest_updates(self, game_state: GameState) -> None:
        """Check updates for all active quests."""
        active_quest_ids = [
            quest.id for quest in self.get_active_quests()
        ]
        
        for quest_id in active_quest_ids:
            self.update_quest_progress(quest_id, game_state)
    
    def get_active_notifications(self) -> List[QuestNotification]:
        """Get all active notifications and mark them as seen."""
        for notification in self.active_notifications:
            notification.is_new = False
        
        return self.active_notifications
    
    def clear_old_notifications(self, max_age_secs: int) -> None:
        """Clear notifications older than the specified age."""
        current_time = time.time()
        self.active_notifications = [
            n for n in self.active_notifications 
            if (current_time - n.timestamp) < max_age_secs
        ]
    
    def _add_notification(self, quest_id: str, title: str, message: str, 
                        notification_type: NotificationType) -> None:
        """Add a quest notification."""
        self.active_notifications.append(QuestNotification(
            quest_id=quest_id,
            title=title,
            message=message,
            is_new=True,
            notification_type=notification_type,
            timestamp=time.time()
        ))
    
    def _check_condition(self, condition: Dict[str, Any], game_state: GameState) -> bool:
        """Check if a condition is met."""
        condition_type = condition.get('condition_type')
        target_id = condition.get('target_id', '')
        value = condition.get('value')
        
        if condition_type == 'HasItem':
            return any(item.id == target_id for item in game_state.inventory)
        
        elif condition_type == 'HasClue':
            return any(clue.id == target_id for clue in game_state.discovered_clues)
        
        elif condition_type == 'LocationVisited':
            return game_state.has_visited_location(target_id)
        
        elif condition_type == 'NPCRelationship':
            if value is not None:
                return game_state.get_relationship(target_id) >= value
        
        elif condition_type == 'SkillValue':
            if value is not None and hasattr(game_state.player.skills, target_id):
                return getattr(game_state.player.skills, target_id) >= value
        
        elif condition_type == 'DialogueChoice':
            # This would need more context to implement fully
            pass
        
        return False
    
    def _execute_game_event(self, event: Dict[str, Any], game_state: GameState) -> None:
        """Execute a game event based on its type."""
        event_type = event.get('event_type')
        data = event.get('data')
        
        if not event_type or data is None:
            return
        
        if event_type == 'AddItem':
            # Convert data to Item and add to inventory
            if isinstance(data, dict):
                from config.config_loader import Item
                item = Item(**data)
                game_state.add_item(item)
        
        elif event_type == 'RemoveItem':
            # Remove item from inventory by ID
            if isinstance(data, str):
                game_state.remove_item(data)
        
        elif event_type == 'AddClue':
            # Convert data to Clue and add to discovered clues
            if isinstance(data, dict):
                from config.config_loader import Clue
                clue = Clue(**data)
                game_state.add_clue(clue)
        
        elif event_type == 'UpdateQuest':
            # Update quest status
            if isinstance(data, list) and len(data) == 2:
                quest_id, status_str = data
                status = QuestStatus[status_str]
                game_state.update_quest(quest_id, status)
        
        elif event_type == 'ModifySkill':
            # Modify player skill
            if isinstance(data, list) and len(data) == 2:
                skill_name, amount = data
                game_state.modify_skill(skill_name, amount)
        
        elif event_type == 'ChangeLocation':
            # Change player location
            if isinstance(data, str):
                game_state.change_location(data)
        
        elif event_type == 'ModifyRelationship':
            # Modify NPC relationship
            if isinstance(data, list) and len(data) == 2:
                npc_id, amount = data
                game_state.modify_relationship(npc_id, amount)
    
    def _give_quest_rewards(self, quest_id: str, game_state: GameState) -> None:
        """Give rewards for completing a quest."""
        quest = self.quests.get(quest_id)
        if not quest:
            return
        
        # Add items to inventory
        for item in quest.rewards.items:
            game_state.add_item(item)
        
        # Apply skill rewards
        for skill, value in quest.rewards.skill_rewards.items():
            game_state.modify_skill(skill, value)
        
        # Apply relationship changes
        for npc_id, value in quest.rewards.relationship_changes.items():
            game_state.modify_relationship(npc_id, value)
    
    def _is_quest_completed(self, quest: Quest) -> bool:
        """Check if a quest is completed."""
        return all(stage.status in ["Completed", "Failed"] for stage in quest.stages)
