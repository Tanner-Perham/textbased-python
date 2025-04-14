"""
This module manages the game state, including player attributes, inventory, quests, and world state.
"""
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple
from game.quest_status import QuestStatus
from quest.quest_state import QuestState
from config.config_loader import Quest, QuestStage, Item, Clue


@dataclass
class TimeOfDay(Enum):
    """Time of day in the game world."""
    Morning = auto()
    Afternoon = auto()
    Evening = auto()
    Night = auto()


@dataclass
class Player:
    """Player character information."""
    name: str = "Detective"
    inner_voices: List[Any] = field(default_factory=list)
    thought_cabinet: List[Any] = field(default_factory=list)
    health: int = 100
    morale: int = 100


@dataclass
class Item:
    """Item in the game world or inventory."""
    id: str
    name: str
    description: str
    effects: Dict[str, int] = field(default_factory=dict)


@dataclass
class Clue:
    """Clue discovered during investigation."""
    id: str
    description: str
    related_quest: str
    discovered: bool = False


@dataclass
class Quest:
    """Information about a quest."""
    id: str
    title: str
    description: str
    short_description: str
    objectives: List[str]
    status: QuestStatus


@dataclass
class GameState:
    """Manages the current state of the game."""
    
    def __init__(self):
        """Initialize the game state."""
        self.player = None
        self.current_location = None
        self.previous_location = None
        self.inventory = []
        self._quest_state = QuestState()  # Make QuestState private
        self.discovered_clues = []
        self.time_of_day = TimeOfDay.Morning
        self.visited_locations = set()
        self.npc_interactions = {}  # Maps NPC ID to interaction count
        self.relationship_values = {}  # Maps NPC ID to relationship value
        self.skills = {}  # Maps skill name to skill level

    # Quest State Access Methods
    def add_quest(self, quest: Quest) -> None:
        """Add a quest to the game state."""
        print(f"GameState: Adding quest {quest.id}")
        self._quest_state.add_quest(quest)

    def get_quest(self, quest_id: str) -> Optional[Quest]:
        """Get a quest by ID."""
        return self._quest_state.get_quest(quest_id)

    def get_quest_status(self, quest_id: str) -> Optional[QuestStatus]:
        """Get a quest's status."""
        return self._quest_state.get_quest_status(quest_id)

    def update_quest_status(self, quest_id: str, status: QuestStatus) -> bool:
        """Update a quest's status. Returns True if successful."""
        print(f"GameState: Updating quest {quest_id} to {status}")
        return self._quest_state.update_quest_status(quest_id, status)

    def check_all_quest_updates(self) -> None:
        """Check for all quest updates."""
        self._quest_state.check_all_quest_updates()

    def start_quest(self, quest_id: str) -> bool:
        """Start a quest. Returns True if successful."""
        print(f"GameState: Starting quest {quest_id}")
        return self._quest_state.update_quest_status(quest_id, QuestStatus.InProgress)

    def complete_quest(self, quest_id: str) -> bool:
        """Complete a quest. Returns True if successful."""
        print(f"GameState: Completing quest {quest_id}")
        return self._quest_state.update_quest_status(quest_id, QuestStatus.Completed)

    def fail_quest(self, quest_id: str) -> bool:
        """Fail a quest. Returns True if successful."""
        print(f"GameState: Failing quest {quest_id}")
        return self._quest_state.update_quest_status(quest_id, QuestStatus.Failed)

    def get_active_quests(self) -> List[Quest]:
        """Get all active quests."""
        return list(self._quest_state.get_active_quests().values())

    def get_completed_quests(self) -> List[Quest]:
        """Get all completed quests."""
        return list(self._quest_state.get_completed_quests().values())

    def get_failed_quests(self) -> List[Quest]:
        """Get all failed quests."""
        return list(self._quest_state.get_failed_quests().values())

    def set_active_stage(self, quest_id: str, stage_id: str) -> None:
        """Set the active stage for a quest."""
        self._quest_state.set_active_stage(quest_id, stage_id)

    def get_active_stage(self, quest_id: str) -> Optional[str]:
        """Get the active stage ID for a quest."""
        return self._quest_state.get_active_stage(quest_id)

    def add_completed_objective(self, quest_id: str, objective_id: str) -> None:
        """Mark an objective as completed."""
        return self._quest_state.add_completed_objective(quest_id, objective_id)

    def is_objective_completed(self, quest_id: str, objective_id: str) -> bool:
        """Check if an objective is completed."""
        return self._quest_state.is_objective_completed(quest_id, objective_id)

    def add_quest_branch(self, quest_id: str, branch_id: str) -> None:
        """Add a quest branch to the taken branches."""
        return self._quest_state.add_quest_branch(quest_id, branch_id)

    def has_taken_branch(self, quest_id: str, branch_id: str) -> bool:
        """Check if a quest branch has been taken."""
        return self._quest_state.has_taken_branch(quest_id, branch_id)

    def add_quest_item(self, quest_id: str, item_id: str) -> None:
        """Add an item to a quest's item set."""
        return self._quest_state.add_quest_item(quest_id, item_id)

    def remove_quest_item(self, quest_id: str, item_id: str) -> None:
        """Remove an item from a quest's item set."""
        return self._quest_state.remove_quest_item(quest_id, item_id)

    def has_quest_item(self, quest_id: str, item_id: str) -> bool:
        """Check if a quest has a specific item."""
        return self._quest_state.has_quest_item(quest_id, item_id)

    def get_quest_progress(self, quest_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed progress for a quest."""
        quest = self._quest_state.get_quest(quest_id)
        if not quest:
            return None
            
        return {
            'status': self._quest_state.get_quest_status(quest_id),
            'active_stage': self._quest_state.get_active_stage(quest_id),
            'completed_objectives': list(self._quest_state.completed_objectives.get(quest_id, set())),
            'taken_branches': list(self._quest_state.taken_branches.get(quest_id, set())),
            'quest_items': list(self._quest_state.quest_items.get(quest_id, set()))
        }

    def get_all_quests(self) -> Dict[str, Quest]:
        """Get all available quests."""
        return self._quest_state.quests.copy()  # Return a copy to prevent direct modification

    def get_main_quests(self) -> List[Quest]:
        """Get all main quests."""
        return [quest for quest in self._quest_state.quests.values() 
                if quest.is_main_quest]
    
    def get_side_quests(self) -> List[Quest]:
        """Get all side quests."""
        return [quest for quest in self._quest_state.quests.values() 
                if not quest.is_main_quest]

    # Rest of the GameState methods...
    def add_item(self, item: Item) -> None:
        """Add an item to the player's inventory."""
        self.inventory.append(item)
    
    def remove_item(self, item_id: str) -> None:
        """Remove an item from the player's inventory by ID."""
        self.inventory = [item for item in self.inventory if item.id != item_id]
    
    def add_clue(self, clue: Clue) -> None:
        """Add a clue to the discovered clues."""
        self.discovered_clues.append(clue)
    
    def modify_skill(self, skill_name: str, amount: int) -> bool:
        """Modify a skill by the given amount. Returns True if successful."""
        if skill_name in self.skills:
            self.skills[skill_name] += amount
            return True
        return False

    def get_skill(self, skill_name: str) -> int:
        """Get the current value of a skill."""
        return self.skills.get(skill_name, 0)
    
    def change_location(self, location_id: str) -> None:
        """Change the player's current location."""
        self.previous_location = self.current_location
        self.current_location = location_id
        self.visited_locations.add(location_id)
    
    def record_npc_interaction(self, npc_id: str) -> None:
        """Record an interaction with an NPC."""
        self.npc_interactions[npc_id] = self.npc_interactions.get(npc_id, 0) + 1
    
    def modify_relationship(self, npc_id: str, change: int) -> None:
        """Modify relationship value with an NPC."""
        self.relationship_values[npc_id] = self.relationship_values.get(npc_id, 0) + change
    
    def get_relationship(self, npc_id: str) -> int:
        """Get the relationship value with an NPC."""
        return self.relationship_values.get(npc_id, 0)
    
    def has_visited_location(self, location_id: str) -> bool:
        """Check if a location has been visited."""
        return location_id in self.visited_locations
