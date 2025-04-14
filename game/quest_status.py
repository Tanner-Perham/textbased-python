from enum import Enum, auto

class QuestStatus(Enum):
    """Enum representing the possible states of a quest."""
    NotStarted = auto()
    InProgress = auto()
    Completed = auto()
    Failed = auto() 