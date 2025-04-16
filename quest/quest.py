from dataclasses import dataclass, field
from typing import List, Optional
from game.quest_status import QuestStatus
from config.config_loader import QuestStage

@dataclass
class Quest:
    """Information about a quest."""
    id: str
    title: str
    description: str
    objectives: List[str]
    status: QuestStatus = QuestStatus.NotStarted
    is_main_quest: bool = False
    stages: List[QuestStage] = field(default_factory=list)

    def __post_init__(self):
        """Initialize quest after creation."""
        if not self.stages:
            # Create a default stage if none provided
            self.stages = [
                QuestStage(
                    id="default",
                    title="Default Stage",
                    description="Complete the quest objectives",
                    objectives=self.objectives
                )
            ]

    def get_current_stage(self) -> Optional[QuestStage]:
        """Get the current active stage."""
        # This method is a fallback, as the game_state.get_active_stage should normally be used
        # We're maintaining it for backward compatibility
        for stage in self.stages:
            if stage.status == QuestStatus.InProgress:
                return stage
        return None

    def advance_to_next_stage(self) -> bool:
        """Advance to the next stage. Returns True if successful."""
        current_stage = self.get_current_stage()
        if not current_stage:
            return False
            
        current_index = self.stages.index(current_stage)
        if current_index + 1 < len(self.stages):
            current_stage.status = "Completed"
            next_stage = self.stages[current_index + 1]
            next_stage.status = "InProgress"
            return True
        return False 