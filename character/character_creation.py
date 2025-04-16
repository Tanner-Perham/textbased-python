"""
Character creation system for text-based adventure game.
"""

from typing import Dict, List, Tuple

from game.inventory import Item, Effect


class CharacterArchetype:
    """Represents a playable character archetype with starting skills and equipment."""
    
    def __init__(self, 
                 id: str, 
                 name: str, 
                 description: str, 
                 starting_skills: Dict[str, float],
                 starting_equipment_ids: List[str]):
        """Initialize a character archetype."""
        self.id = id
        self.name = name
        self.description = description
        self.starting_skills = starting_skills
        self.starting_equipment_ids = starting_equipment_ids


# Define the character archetypes
ARCHETYPES = {
    "analytical": CharacterArchetype(
        id="analytical",
        name="Analytical Detective",
        description=(
            "You solve cases through careful observation and deductive reasoning. "
            "Your analytical mind excels at connecting evidence and spotting inconsistencies. "
            "You prefer to let the facts speak for themselves rather than relying on social pressure."
        ),
        starting_skills={
            "logic": 3,
            "perception": 3,
            "memory": 2,
            "empathy": 1,
            "authority": 1,
            "suggestion": 0,
            "composure": 1,
            "agility": 0,
            "endurance": 1
        },
        starting_equipment_ids=[
            "notebook",
            "magnifying_glass",
            "crime_scene_kit"
        ]
    ),
    
    "persuasive": CharacterArchetype(
        id="persuasive", 
        name="Persuasive Detective",
        description=(
            "Your exceptional people skills make you a master at extracting information through conversation. "
            "You can read emotions, gain trust, and apply pressure when needed. "
            "You rely on witness testimony more than physical evidence."
        ),
        starting_skills={
            "logic": 1,
            "perception": 1,
            "memory": 0,
            "empathy": 3,
            "authority": 2,
            "suggestion": 3,
            "composure": 1,
            "agility": 0,
            "endurance": 1
        },
        starting_equipment_ids=[
            "professional_attire",
            "confidence_charm",
            "voice_recorder"
        ]
    ),
    
    "field": CharacterArchetype(
        id="field",
        name="Field Detective",
        description=(
            "You excel in the field, able to chase down suspects, maintain composure in dangerous situations, "
            "and tough out long hours. Your instincts are sharp, though you might miss subtle details or social cues."
        ),
        starting_skills={
            "logic": 1,
            "perception": 2,
            "memory": 0,
            "empathy": 0,
            "authority": 1,
            "suggestion": 1,
            "composure": 3,
            "agility": 2,
            "endurance": 2
        },
        starting_equipment_ids=[
            "sturdy_boots",
            "weatherproof_jacket",
            "first_aid_kit"
        ]
    )
}


def apply_archetype(game_state, archetype_id: str) -> bool:
    """
    Apply a character archetype to the player, setting starting skills and equipment.
    
    Args:
        game_state: The current game state
        archetype_id: The ID of the archetype to apply
        
    Returns:
        bool: True if the archetype was successfully applied
    """
    if archetype_id not in ARCHETYPES:
        return False
    
    archetype = ARCHETYPES[archetype_id]
    
    # Set player skills
    for skill_name, skill_value in archetype.starting_skills.items():
        game_state.player.skills[skill_name] = skill_value
    
    # Add starting equipment
    for item_id in archetype.starting_equipment_ids:
        if item_id in game_state.config.items:
            item = game_state.config.items[item_id]
            game_state.add_item(item)
    
    return True


def get_archetype_descriptions() -> List[Tuple[str, str, str]]:
    """
    Get descriptions of all available archetypes.
    
    Returns:
        List of tuples containing (id, name, description) for each archetype
    """
    return [(a.id, a.name, a.description) for a in ARCHETYPES.values()] 