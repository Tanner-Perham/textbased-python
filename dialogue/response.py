"""
Module for dialogue response data types.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Union

from dialogue.node import DialogueOption


class DialogueResponse:
    """Base class for dialogue responses."""

    @dataclass
    class Speech:
        """Dialogue speech from a character."""

        speaker: str
        text: str
        emotion: str = "Neutral"

    @dataclass
    class InnerVoice:
        """Inner voice comment."""

        voice_type: str
        text: str

    @dataclass
    class Options:
        """Dialogue options for the player."""

        options: List[DialogueOption]

    @dataclass
    class SkillCheck:
        """Skill check result."""

        success: bool
        skill: str
        player_skill: int
        roll: int
        difficulty: int
        dice_values: List[int] = field(default_factory=list)  # The individual dice values (2d6)
        critical_result: Optional[str] = None  # 'success', 'failure', or None for regular result

    @classmethod
    def from_dict(
        cls, data: dict
    ) -> Union["Speech", "InnerVoice", "Options", "SkillCheck"]:
        """Create a response object from a dictionary."""
        response_type = data.get("type")

        if response_type == "speech":
            return cls.Speech(
                speaker=data.get("speaker", ""),
                text=data.get("text", ""),
                emotion=data.get("emotion", "Neutral"),
            )

        elif response_type == "inner_voice":
            return cls.InnerVoice(
                voice_type=data.get("voice_type", ""), text=data.get("text", "")
            )

        elif response_type == "options":
            options = []
            for opt_data in data.get("options", []):
                option = DialogueOption(
                    id=opt_data.get("id", ""),
                    text=opt_data.get("text", ""),
                    next_node=opt_data.get("next_node", ""),
                    skill_check=opt_data.get("skill_check"),
                    emotional_impact=opt_data.get("emotional_impact", {}),
                    conditions=opt_data.get("conditions", {}),
                    consequences=opt_data.get("consequences", []),
                    inner_voice_reactions=opt_data.get("inner_voice_reactions", []),
                    success_node=opt_data.get("success_node", ""),
                    failure_node=opt_data.get("failure_node", ""),
                    critical_success_node=opt_data.get("critical_success_node", ""),
                    critical_failure_node=opt_data.get("critical_failure_node", ""),
                )
                options.append(option)

            return cls.Options(options=options)

        elif response_type == "skill_check":
            return cls.SkillCheck(
                success=data.get("success", False),
                skill=data.get("skill", ""),
                player_skill=data.get("player_skill", 0),
                roll=data.get("roll", 0),
                difficulty=data.get("difficulty", 0),
                dice_values=data.get("dice_values", []),
                critical_result=data.get("critical_result"),
            )

        # Default to empty speech if type is unknown
        return cls.Speech(
            speaker="System", text="Unknown response type", emotion="Neutral"
        )
