"""
This module manages the game state, including player attributes, inventory, quests, and world state.
"""
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple


class QuestStatus(Enum):
    """Status of a quest."""
    NotStarted = auto()
    InProgress = auto()
    Completed = auto()
    Failed = auto()


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
class GameState:
    """
    Maintains the current state of the game, including player attributes,
    inventory, quests, and world state.
    """
    current_location: str = ""
    previous_location: Optional[str] = None
    inventory: List[str] = field(default_factory=list)
    quests: Dict[str, str] = field(default_factory=dict)
    # Initialize skills with all available skills
    skills: Dict[str, int] = field(default_factory=lambda: {
        # Investigation skills
        "logic": 10,
        "empathy": 10,
        "perception": 10,
        "authority": 10,
        "suggestion": 10,
        "composure": 10,
        # Physical skills
        "strength": 1,
        "agility": 1,
        "endurance": 1,
        # Mental skills
        "intelligence": 1,
        "charisma": 1
    })
    skill_points: int = 0
    experience: int = 0

    def __post_init__(self):
        """Initialize additional state after dataclass initialization."""
        self.current_location = "starting_location"
        self.inventory = []
        self.quest_log: Dict[str, QuestStatus] = {}
        self.discovered_clues: List[Clue] = []
        self.time_of_day: TimeOfDay = TimeOfDay.Morning
        self.visited_locations: Set[str] = set()
        self.completed_objectives: Dict[str, Set[str]] = {}
        self.active_quest_stages: Dict[str, str] = {}
        self.taken_quest_branches: Dict[str, Set[str]] = {}
        self.npc_interactions: Dict[str, int] = {}
        self.quest_items: Dict[str, Set[str]] = {}
        self.relationship_values: Dict[str, int] = {}

    def add_item(self, item: Item) -> None:
        """Add an item to the player's inventory."""
        self.inventory.append(item)
    
    def remove_item(self, item_id: str) -> None:
        """Remove an item from the player's inventory by ID."""
        self.inventory = [item for item in self.inventory if item.id != item_id]
    
    def add_clue(self, clue: Clue) -> None:
        """Add a clue to the discovered clues."""
        self.discovered_clues.append(clue)
    
    def update_quest(self, quest_id: str, status: QuestStatus) -> None:
        """Update a quest's status in the quest log."""
        self.quest_log[quest_id] = status
    
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
    
    def update_quest_items(self, quest_id: str, item_id: str) -> None:
        """Update tracking of items related to a specific quest."""
        if quest_id not in self.quest_items:
            self.quest_items[quest_id] = set()
        self.quest_items[quest_id].add(item_id)
    
    def modify_relationship(self, npc_id: str, change: int) -> None:
        """Modify relationship value with an NPC."""
        self.relationship_values[npc_id] = self.relationship_values.get(npc_id, 0) + change
    
    def is_quest_stage_active(self, quest_id: str, stage_id: str) -> bool:
        """Check if a specific quest stage is active."""
        return self.active_quest_stages.get(quest_id) == stage_id
    
    def is_quest_objective_completed(self, quest_id: str, objective_id: str) -> bool:
        """Check if a specific quest objective is completed."""
        if quest_id not in self.completed_objectives:
            return False
        return objective_id in self.completed_objectives[quest_id]
    
    def is_quest_branch_taken(self, quest_id: str, branch_id: str) -> bool:
        """Check if a specific quest branch has been taken."""
        if quest_id not in self.taken_quest_branches:
            return False
        return branch_id in self.taken_quest_branches[quest_id]
    
    def get_relationship(self, npc_id: str) -> int:
        """Get the relationship value with an NPC."""
        return self.relationship_values.get(npc_id, 0)
    
    def has_visited_location(self, location_id: str) -> bool:
        """Check if a location has been visited."""
        return location_id in self.visited_locations
    
    def get_active_quests(self) -> List[str]:
        """Get IDs of all active quests."""
        return [quest_id for quest_id, status in self.quest_log.items() 
                if status == QuestStatus.InProgress]
    
    def get_completed_quests(self) -> List[str]:
        """Get IDs of all completed quests."""
        return [quest_id for quest_id, status in self.quest_log.items() 
                if status == QuestStatus.Completed]
    
    def get_failed_quests(self) -> List[str]:
        """Get IDs of all failed quests."""
        return [quest_id for quest_id, status in self.quest_log.items() 
                if status == QuestStatus.Failed]
