import pytest
from game.inventory import Effect, Item, Wearable, WearableSlot, ItemCategory
from game.game_state import GameState


def test_equip_unequip_skill_modifiers():
    """Test that equipping and unequipping items correctly applies/removes skill modifiers."""
    game_state = GameState()
    
    # Initialize test skill
    game_state.player.skills["stealth"] = 5
    
    # Create a test wearable with a skill effect
    test_item = Wearable(
        id="test_boots",
        name="Sneaky Boots",
        description="Boots that make you sneaky",
        categories={ItemCategory.WEARABLE},
        slot=WearableSlot.FEET,
        set_id=None,
        effects=[Effect(attribute="stealth", value=3.0)]
    )
    
    # Add the item and check initial state
    game_state.add_item(test_item)
    assert game_state.player.skills["stealth"] == 5
    
    # Equip the item and verify skill is increased
    game_state.equip_item("test_boots")
    assert game_state.player.skills["stealth"] == 8  # Should be 5 (base) + 3 (boots)
    
    # Unequip the item and verify the skill modifier is removed
    game_state.unequip_item(WearableSlot.FEET)
    assert game_state.player.skills["stealth"] == 5  # Should now be back to base of 5
    
    # Verify that repeated equipping doesn't stack modifiers
    game_state.equip_item("test_boots")
    assert game_state.player.skills["stealth"] == 8  # Should still be 5 + 3
    game_state.unequip_item(WearableSlot.FEET)
    assert game_state.player.skills["stealth"] == 5  # Should be back to base of 5


def test_modify_skill_with_equipment():
    """Test that skill modifications persist when equipping/unequipping items."""
    game_state = GameState()
    
    # Initialize test skill
    game_state.player.skills["agility"] = 3
    
    # Create a test wearable with a skill effect
    test_item = Wearable(
        id="test_gloves",
        name="Dexterous Gloves",
        description="Gloves that improve agility",
        categories={ItemCategory.WEARABLE},
        slot=WearableSlot.HANDS,
        set_id=None,
        effects=[Effect(attribute="agility", value=2.0)]
    )
    
    # Add the item and equip it
    game_state.add_item(test_item)
    game_state.equip_item("test_gloves")
    assert game_state.player.skills["agility"] == 5  # 3 (base) + 2 (gloves)
    
    # Modify the skill while the item is equipped
    game_state.modify_skill("agility", 1)
    assert game_state.player.skills["agility"] == 6  # 4 (modified base) + 2 (gloves)
    
    # Unequip to verify base skill value is preserved
    game_state.unequip_item(WearableSlot.HANDS)
    assert game_state.player.skills["agility"] == 4  # Modified base value
    
    # Re-equip to verify the equipment bonus still applies correctly
    game_state.equip_item("test_gloves")
    assert game_state.player.skills["agility"] == 6  # 4 (base) + 2 (gloves)
    
    # Modify the skill again
    game_state.modify_skill("agility", 2)
    assert game_state.player.skills["agility"] == 8  # 6 (modified base) + 2 (gloves)
    
    # Unequip again to confirm base value
    game_state.unequip_item(WearableSlot.HANDS)
    assert game_state.player.skills["agility"] == 6  # Final modified base value 