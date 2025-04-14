from dataclasses import dataclass, field
from typing import Dict, Set, Optional
from game.quest_status import QuestStatus
from config.config_loader import Quest, QuestStage

@dataclass
class QuestState:
    """Centralized quest state management."""
    quests: Dict[str, Quest] = field(default_factory=dict)
    completed_objectives: Dict[str, Set[str]] = field(default_factory=dict)
    active_stages: Dict[str, str] = field(default_factory=dict)
    taken_branches: Dict[str, Set[str]] = field(default_factory=dict)
    quest_items: Dict[str, Set[str]] = field(default_factory=dict)

    def add_quest(self, quest: Quest) -> None:
        """Add a quest to the state or update an existing quest."""
        # If quest exists, update it
        if quest.id in self.quests:
            self.quests[quest.id] = quest
            # Initialize collections if they don't exist
            if quest.id not in self.completed_objectives:
                self.completed_objectives[quest.id] = set()
            if quest.id not in self.active_stages:
                self.active_stages[quest.id] = None
            if quest.id not in self.taken_branches:
                self.taken_branches[quest.id] = set()
            if quest.id not in self.quest_items:
                self.quest_items[quest.id] = set()
        else:
            # Add new quest
            self.quests[quest.id] = quest
            self.completed_objectives[quest.id] = set()
            self.active_stages[quest.id] = None
            self.taken_branches[quest.id] = set()
            self.quest_items[quest.id] = set()

    def get_quest(self, quest_id: str) -> Optional[Quest]:
        """Get a quest by ID."""
        return self.quests.get(quest_id)

    def get_quest_status(self, quest_id: str) -> Optional[QuestStatus]:
        """Get a quest's status."""
        quest = self.get_quest(quest_id)
        return quest.status if quest else None

    def update_quest_status(self, quest_id: str, status: QuestStatus) -> bool:
        """Update a quest's status."""
        if quest_id not in self.quests:
            print(f"Quest {quest_id} not found")
            return False
        self.quests[quest_id].status = status
        print(f"Quest {quest_id} status updated to {status}")
        return True

    def set_active_stage(self, quest_id: str, stage_id: str) -> bool:
        """Set the active stage for a quest."""
        if quest_id not in self.quests:
            return False
        self.active_stages[quest_id] = stage_id
        return True

    def get_active_stage(self, quest_id: str) -> Optional[str]:
        """Get the active stage ID for a quest."""
        return self.active_stages.get(quest_id)

    def add_completed_objective(self, quest_id: str, objective_id: str) -> bool:
        """Mark an objective as completed."""
        if quest_id not in self.quests:
            return False
        objectives = []
        for stage in self.quests[quest_id].stages:
            for objective in stage.objectives:
                objectives.append(objective['id'])
        if objective_id not in objectives:
            return False
        self.completed_objectives[quest_id].add(objective_id)
        return True

    def is_objective_completed(self, quest_id: str, objective_id: str) -> bool:
        """Check if an objective is completed."""
        return (quest_id in self.completed_objectives and 
                objective_id in self.completed_objectives[quest_id])

    def add_quest_branch(self, quest_id: str, branch_id: str) -> bool:
        """Add a quest branch to the taken branches."""
        if quest_id not in self.quests:
            return False
        self.taken_branches[quest_id].add(branch_id)
        return True

    def has_taken_branch(self, quest_id: str, branch_id: str) -> bool:
        """Check if a quest branch has been taken."""
        return (quest_id in self.taken_branches and 
                branch_id in self.taken_branches[quest_id])

    def add_quest_item(self, quest_id: str, item_id: str) -> bool:
        """Add an item to a quest's item set."""
        if quest_id not in self.quests:
            return False
        self.quest_items[quest_id].add(item_id)
        return True

    def remove_quest_item(self, quest_id: str, item_id: str) -> bool:
        """Remove an item from a quest's item set."""
        if quest_id not in self.quests:
            return False
        self.quest_items[quest_id].discard(item_id)
        return True

    def has_quest_item(self, quest_id: str, item_id: str) -> bool:
        """Check if a quest has a specific item."""
        return (quest_id in self.quest_items and 
                item_id in self.quest_items[quest_id])

    def get_active_quests(self) -> Dict[str, Quest]:
        """Get all active quests."""
        return {qid: quest for qid, quest in self.quests.items() 
                if quest.status == QuestStatus.InProgress}

    def get_completed_quests(self) -> Dict[str, Quest]:
        """Get all completed quests."""
        return {qid: quest for qid, quest in self.quests.items() 
                if quest.status == QuestStatus.Completed}

    def get_failed_quests(self) -> Dict[str, Quest]:
        """Get all failed quests."""
        return {qid: quest for qid, quest in self.quests.items() 
                if quest.status == QuestStatus.Failed} 
    
    def check_all_quest_updates(self) -> None:
        """Check for all quest updates."""
