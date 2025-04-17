"""
Character creation system for text-based adventure game.
"""

from typing import Dict


def apply_archetype(game_state, archetype_id: str) -> bool:
    """
    Apply a character archetype to the player, setting starting skills and equipment.
    
    Args:
        game_state: The current game state
        archetype_id: The ID of the archetype to apply
        
    Returns:
        bool: True if the archetype was successfully applied
    """
    # Get the character archetype from the config
    if archetype_id not in game_state.config.character_archetypes:
        return False
    
    archetype = game_state.config.character_archetypes[archetype_id]
    
    # Set player skills
    for skill_name, skill_value in archetype.starting_skills.items():
        game_state.player.skills[skill_name] = skill_value
    
    # Add starting equipment
    for item_id in archetype.starting_equipment_ids:
        if item_id in game_state.config.items:
            item = game_state.config.items[item_id]
            game_state.add_item(item)
    
    return True 