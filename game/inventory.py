from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict


class ItemCategory(Enum):
    """Categories of items in the game."""
    WEARABLE = auto()
    CONSUMABLE = auto()
    QUEST_ITEM = auto()
    TOOL = auto()
    EVIDENCE = auto()


class WearableSlot(Enum):
    """Available slots for wearable items."""
    HEAD = auto()
    TORSO = auto()
    LEGS = auto()
    FEET = auto()
    HANDS = auto()
    NECK = auto()
    RING = auto()
    ACCESSORY = auto()


@dataclass
class Effect:
    """Represents an effect that can be applied to the player."""
    attribute: str
    value: float
    duration: Optional[int] = None  # None means permanent
    condition: Optional[str] = None  # Python expression to evaluate
    description: str = ""


@dataclass
class ItemBase:
    """Base class containing common item attributes."""
    id: str
    name: str
    description: str
    categories: Set[ItemCategory]
    weight: float = 0.0
    effects: List[Effect] = field(default_factory=list)
    stackable: bool = False
    quantity: int = 1


@dataclass(init=False)
class Item(ItemBase):
    """Standard item implementation."""
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        categories: Set[ItemCategory],
        weight: float = 0.0,
        effects: List[Effect] = None,
        stackable: bool = False,
        quantity: int = 1
    ):
        super().__init__(
            id=id,
            name=name,
            description=description,
            categories=categories,
            weight=weight,
            effects=effects if effects is not None else [],
            stackable=stackable,
            quantity=quantity
        )


@dataclass(init=False)
class Wearable(ItemBase):
    """An item that can be worn in specific slots."""
    slot: WearableSlot
    set_id: Optional[str]
    style_rating: int = 0
    condition: int = 100

    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        categories: Set[ItemCategory],
        slot: WearableSlot,
        set_id: Optional[str],
        weight: float = 0.0,
        effects: List[Effect] = None,
        style_rating: int = 0,
        condition: int = 100,
        stackable: bool = False,
        quantity: int = 1
    ):
        super().__init__(
            id=id,
            name=name,
            description=description,
            categories=categories,
            weight=weight,
            effects=effects if effects is not None else [],
            stackable=stackable,
            quantity=quantity
        )
        self.slot = slot
        self.set_id = set_id
        self.style_rating = style_rating
        self.condition = condition


@dataclass(init=False)
class Container(ItemBase):
    """A special item that can hold other items."""
    capacity: float
    allowed_categories: Set[ItemCategory]
    contents: List[ItemBase] = field(default_factory=list)

    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        categories: Set[ItemCategory],
        capacity: float,
        allowed_categories: Set[ItemCategory],
        weight: float = 0.0,
        effects: List[Effect] = None,
        contents: List[ItemBase] = None,
        stackable: bool = False,
        quantity: int = 1
    ):
        super().__init__(
            id=id,
            name=name,
            description=description,
            categories=categories,
            weight=weight,
            effects=effects if effects is not None else [],
            stackable=stackable,
            quantity=quantity
        )
        self.capacity = capacity
        self.allowed_categories = allowed_categories
        self.contents = contents if contents is not None else []


class InventoryManager:
    """Manages the player's inventory and equipped items."""
    
    def __init__(self, weight_capacity: float = 50.0):
        self.items: List[Item] = []
        self.equipped_items: Dict[WearableSlot, Optional[Wearable]] = {
            slot: None for slot in WearableSlot
        }
        self.containers: List[Container] = []
        self.weight_capacity = weight_capacity
        self.current_weight = 0.0
        self._active_effects: List[Effect] = []
        self._set_bonuses: Dict[str, List[Effect]] = {}

    def add_item(self, item: Item) -> bool:
        """Add an item to the inventory if there's capacity."""
        new_weight = self.current_weight + (item.weight * item.quantity)
        if new_weight > self.weight_capacity:
            return False
        
        # Handle stackable items
        if item.stackable:
            for existing_item in self.items:
                if existing_item.id == item.id:
                    existing_item.quantity += item.quantity
                    self.current_weight = new_weight
                    return True
        
        self.items.append(item)
        self.current_weight = new_weight
        return True

    def remove_item(self, item_id: str, quantity: int = 1) -> Optional[Item]:
        """Remove an item from inventory."""
        for i, item in enumerate(self.items):
            if item.id == item_id:
                if item.stackable and item.quantity > quantity:
                    item.quantity -= quantity
                    self.current_weight -= item.weight * quantity
                    return item
                else:
                    self.current_weight -= item.weight * item.quantity
                    return self.items.pop(i)
        return None

    def equip_item(self, item_id: str) -> Tuple[bool, str]:
        """Attempt to equip a wearable item."""
        item = next((item for item in self.items if item.id == item_id), None)
        if not item or not isinstance(item, Wearable):
            return False, "Item not found or not wearable"

        # Check if slot is occupied
        if self.equipped_items[item.slot]:
            self.unequip_item(item.slot)

        # Equip the item
        self.equipped_items[item.slot] = item
        self.items.remove(item)
        self._update_active_effects()
        self._check_set_bonuses()
        
        return True, f"Equipped {item.name}"

    def unequip_item(self, slot: WearableSlot) -> Tuple[bool, str]:
        """Remove an item from an equipment slot."""
        item = self.equipped_items[slot]
        if not item:
            return False, "No item equipped in that slot"

        if self.add_item(item):
            self.equipped_items[slot] = None
            self._update_active_effects()
            self._check_set_bonuses()
            return True, f"Unequipped {item.name}"
        return False, "Inventory full"

    def get_active_effects(self) -> List[Effect]:
        """Get all currently active effects from equipped items."""
        return self._active_effects.copy()

    def get_equipment_preview(self, item_id: str) -> Dict[str, float]:
        """Preview how equipping an item would change stats."""
        item = next((item for item in self.items if item.id == item_id), None)
        if not item or not isinstance(item, Wearable):
            return {}

        # Get current stats
        current_stats = self._calculate_total_stats()
        
        # Simulate equipping the new item
        if self.equipped_items[item.slot]:
            current_stats = self._remove_item_stats(current_stats, self.equipped_items[item.slot])
        
        # Add new item's stats
        new_stats = self._add_item_stats(current_stats.copy(), item)
        
        # Calculate and return the differences
        return {
            stat: new_stats[stat] - current_stats[stat]
            for stat in new_stats
            if stat in current_stats and new_stats[stat] != current_stats[stat]
        }

    def _calculate_total_stats(self) -> Dict[str, float]:
        """Calculate total stats from all equipped items."""
        stats = defaultdict(float)
        for effect in self._active_effects:
            if self._is_effect_active(effect):
                stats[effect.attribute] += effect.value
        return dict(stats)

    def _add_item_stats(self, stats: Dict[str, float], item: Wearable) -> Dict[str, float]:
        """Add an item's stats to the total."""
        for effect in item.effects:
            if self._is_effect_active(effect):
                stats[effect.attribute] = stats.get(effect.attribute, 0) + effect.value
        return stats

    def _remove_item_stats(self, stats: Dict[str, float], item: Wearable) -> Dict[str, float]:
        """Remove an item's stats from the total."""
        for effect in item.effects:
            if self._is_effect_active(effect):
                stats[effect.attribute] = stats.get(effect.attribute, 0) - effect.value
        return stats

    def _is_effect_active(self, effect: Effect) -> bool:
        """Check if an effect is currently active based on its condition."""
        if not effect.condition:
            return True
        # Here you would evaluate the condition based on game state
        # For now, we'll just return True
        return True

    def _update_active_effects(self):
        """Update the list of active effects from equipped items."""
        self._active_effects.clear()
        for item in self.equipped_items.values():
            if item:
                self._active_effects.extend(item.effects)

    def _check_set_bonuses(self):
        """Check and apply set bonuses based on equipped items."""
        # Group equipped items by set
        sets = defaultdict(list)
        for item in self.equipped_items.values():
            if item and item.set_id:
                sets[item.set_id].append(item)

        # Clear current set bonuses
        self._set_bonuses.clear()

        # Apply new set bonuses (would be defined in game config)
        # This is a placeholder for the actual set bonus logic
        pass

    def get_items_by_category(self, category: ItemCategory) -> List[Item]:
        """Get all items of a specific category."""
        return [item for item in self.items if category in item.categories]

    def get_container_contents(self, container_id: str) -> List[Item]:
        """Get the contents of a specific container."""
        container = next((c for c in self.containers if c.id == container_id), None)
        return container.contents if container else []

    def add_to_container(self, container_id: str, item: Item) -> bool:
        """Add an item to a specific container."""
        container = next((c for c in self.containers if c.id == container_id), None)
        if not container:
            return False

        if any(cat not in container.allowed_categories for cat in item.categories):
            return False

        current_weight = sum(i.weight * i.quantity for i in container.contents)
        if current_weight + (item.weight * item.quantity) > container.capacity:
            return False

        container.contents.append(item)
        return True

    def remove_from_container(self, container_id: str, item_id: str) -> Optional[Item]:
        """Remove an item from a specific container."""
        container = next((c for c in self.containers if c.id == container_id), None)
        if not container:
            return None

        for i, item in enumerate(container.contents):
            if item.id == item_id:
                return container.contents.pop(i)
        return None 