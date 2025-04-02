"""
Module for dialogue node data structures.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class DialogueConditions:
    """Conditions for dialogue options to be available."""

    required_items: List[str] = field(default_factory=list)
    required_clues: List[str] = field(default_factory=list)
    required_quests: Dict[str, str] = field(default_factory=dict)
    required_skills: Dict[str, int] = field(default_factory=dict)
    required_thoughts: List[str] = field(default_factory=list)
    required_emotional_state: Optional[str] = None
    time_of_day: Optional[List[str]] = None
    quest_stage_active: Optional[tuple] = None  # (quest_id, stage_id)
    quest_objective_completed: Optional[tuple] = None  # (quest_id, objective_id)
    quest_branch_taken: Optional[tuple] = None  # (quest_id, branch_id)


@dataclass
class InnerVoiceComment:
    """An inner voice comment during dialogue."""

    voice_type: str
    text: str
    trigger_condition: Optional[DialogueConditions] = None
    skill_requirement: Optional[int] = None


@dataclass
class EnhancedSkillCheck:
    """A skill check for dialogue options."""

    base_difficulty: int
    primary_skill: str
    supporting_skills: List[tuple] = field(
        default_factory=list
    )  # [(skill_name, factor)]
    emotional_modifiers: Dict[str, int] = field(default_factory=dict)
    white_check: bool = False  # Can be retried
    hidden: bool = False  # Not shown to player


@dataclass
class DialogueEffect:
    """An effect triggered by dialogue."""

    effect_type: str
    data: Any = None


@dataclass
class DialogueOption:
    """A dialogue option selectable by the player."""

    id: str
    text: str
    next_node: str = ""
    skill_check: Optional[EnhancedSkillCheck] = None
    emotional_impact: Dict[str, int] = field(default_factory=dict)
    conditions: Dict[str, Any] = field(default_factory=dict)
    consequences: List[Dict[str, Any]] = field(default_factory=list)
    inner_voice_reactions: List[InnerVoiceComment] = field(default_factory=list)
    success_node: str = ""  # Node to go to on successful skill check
    failure_node: str = ""  # Node to go to on failed skill check


@dataclass
class DialogueNode:
    """A node in a dialogue tree."""

    id: str
    text: str
    speaker: str
    emotional_state: str
    inner_voice_comments: List[InnerVoiceComment] = field(default_factory=list)
    options: List[DialogueOption] = field(default_factory=list)
    conditions: DialogueConditions = field(default_factory=DialogueConditions)
    effects: List[DialogueEffect] = field(default_factory=list)

    def add_option(self, option: DialogueOption) -> None:
        """Add an option to this dialogue node."""
        self.options.append(option)

    def add_inner_voice_comment(self, comment: InnerVoiceComment) -> None:
        """Add an inner voice comment to this dialogue node."""
        self.inner_voice_comments.append(comment)
