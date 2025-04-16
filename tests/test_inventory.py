import pytest
from game.inventory import (
    ItemCategory,
    WearableSlot,
    Effect,
    ItemBase,
    Item,
    Wearable,
    Container,
    InventoryManager
)

# Test data
@pytest.fixture
def sample_effect():
    return Effect(
        attribute="strength",
        value=2.0,
        duration=30,
        condition="health > 50",
        description="Increases strength"
    )

@pytest.fixture
def sample_item():
    return Item(
        id="test_item",
        name="Test Item",
        description="A test item",
        categories={ItemCategory.TOOL},
        weight=1.0,
        effects=[],
        stackable=True,
        quantity=1
    )

@pytest.fixture
def sample_wearable():
    return Wearable(
        id="test_wearable",
        name="Test Wearable",
        description="A test wearable",
        categories={ItemCategory.WEARABLE},
        slot=WearableSlot.TORSO,
        set_id="test_set",
        weight=2.0,
        effects=[],
        style_rating=5,
        condition=100
    )

@pytest.fixture
def sample_container():
    return Container(
        id="test_container",
        name="Test Container",
        description="A test container",
        categories={ItemCategory.CONTAINER},
        capacity=10.0,
        allowed_categories={ItemCategory.TOOL},
        weight=1.0,
        effects=[],
        contents=[]
    )

@pytest.fixture
def inventory_manager():
    return InventoryManager(weight_capacity=50.0)

# Test ItemCategory enum
def test_item_category_values():
    assert ItemCategory.WEARABLE.value == "Wearable"
    assert ItemCategory.CONSUMABLE.value == "Consumable"
    assert ItemCategory.QUEST_ITEM.value == "Quest Item"
    assert ItemCategory.TOOL.value == "Tool"
    assert ItemCategory.EVIDENCE.value == "Evidence"

# Test WearableSlot enum
def test_wearable_slot_values():
    assert isinstance(WearableSlot.HEAD, WearableSlot)
    assert isinstance(WearableSlot.TORSO, WearableSlot)
    assert isinstance(WearableSlot.LEGS, WearableSlot)
    assert isinstance(WearableSlot.FEET, WearableSlot)
    assert isinstance(WearableSlot.HANDS, WearableSlot)
    assert isinstance(WearableSlot.NECK, WearableSlot)
    assert isinstance(WearableSlot.RING, WearableSlot)
    assert isinstance(WearableSlot.ACCESSORY, WearableSlot)

# Test Effect class
def test_effect_creation(sample_effect):
    assert sample_effect.attribute == "strength"
    assert sample_effect.value == 2.0
    assert sample_effect.duration == 30
    assert sample_effect.condition == "health > 50"
    assert sample_effect.description == "Increases strength"

# Test Item class
def test_item_creation(sample_item):
    assert sample_item.id == "test_item"
    assert sample_item.name == "Test Item"
    assert sample_item.description == "A test item"
    assert ItemCategory.TOOL in sample_item.categories
    assert sample_item.weight == 1.0
    assert sample_item.stackable
    assert sample_item.quantity == 1

def test_item_stackable_behavior(sample_item):
    sample_item.quantity = 5
    assert sample_item.quantity == 5

# Test Wearable class
def test_wearable_creation(sample_wearable):
    assert sample_wearable.id == "test_wearable"
    assert sample_wearable.slot == WearableSlot.TORSO
    assert sample_wearable.set_id == "test_set"
    assert sample_wearable.style_rating == 5
    assert sample_wearable.condition == 100

def test_wearable_condition(sample_wearable):
    sample_wearable.condition = 75
    assert sample_wearable.condition == 75

# Test Container class
def test_container_creation(sample_container):
    assert sample_container.id == "test_container"
    assert sample_container.capacity == 10.0
    assert ItemCategory.TOOL in sample_container.allowed_categories
    assert len(sample_container.contents) == 0

def test_container_add_item(sample_container, sample_item):
    assert sample_container.add_item(sample_item)
    assert len(sample_container.contents) == 1
    assert sample_container.contents[0] == sample_item

def test_container_remove_item(sample_container, sample_item):
    sample_container.contents.append(sample_item)
    removed_item = sample_container.remove_item(sample_item.id)
    assert removed_item == sample_item
    assert len(sample_container.contents) == 0

# Test InventoryManager class
def test_inventory_manager_initialization(inventory_manager):
    assert inventory_manager.weight_capacity == 50.0
    assert inventory_manager.current_weight == 0.0
    assert len(inventory_manager.items) == 0
    assert len(inventory_manager.equipped_items) == len(WearableSlot)
    assert all(slot is None for slot in inventory_manager.equipped_items.values())

def test_add_item(inventory_manager, sample_item):
    assert inventory_manager.add_item(sample_item)
    assert len(inventory_manager.items) == 1
    assert inventory_manager.current_weight == sample_item.weight

def test_add_item_exceeds_capacity(inventory_manager):
    heavy_item = Item(
        id="heavy_item",
        name="Heavy Item",
        description="Very heavy",
        categories={ItemCategory.TOOL},
        weight=60.0
    )
    assert not inventory_manager.add_item(heavy_item)
    assert len(inventory_manager.items) == 0
    assert inventory_manager.current_weight == 0.0

def test_remove_item(inventory_manager, sample_item):
    inventory_manager.add_item(sample_item)
    removed_item = inventory_manager.remove_item(sample_item.id)
    assert removed_item == sample_item
    assert len(inventory_manager.items) == 0
    assert inventory_manager.current_weight == 0.0

def test_equip_item(inventory_manager, sample_wearable):
    inventory_manager.add_item(sample_wearable)
    success, message = inventory_manager.equip_item(sample_wearable.id)
    assert success
    assert message == f"Equipped {sample_wearable.name}"
    assert inventory_manager.equipped_items[sample_wearable.slot] == sample_wearable
    assert sample_wearable not in inventory_manager.items

def test_unequip_item(inventory_manager, sample_wearable):
    inventory_manager.add_item(sample_wearable)
    inventory_manager.equip_item(sample_wearable.id)
    success, message = inventory_manager.unequip_item(sample_wearable.slot)
    assert success
    assert message == f"Unequipped {sample_wearable.name}"
    assert inventory_manager.equipped_items[sample_wearable.slot] is None
    assert sample_wearable in inventory_manager.items

def test_get_items_by_category(inventory_manager, sample_item):
    inventory_manager.add_item(sample_item)
    tools = inventory_manager.get_items_by_category(ItemCategory.TOOL)
    assert len(tools) == 1
    assert tools[0] == sample_item

def test_get_active_effects(inventory_manager, sample_wearable, sample_effect):
    sample_wearable.effects.append(sample_effect)
    inventory_manager.add_item(sample_wearable)
    inventory_manager.equip_item(sample_wearable.id)
    active_effects = inventory_manager.get_active_effects()
    assert len(active_effects) == 1
    assert active_effects[0] == sample_effect

def test_get_equipment_preview(inventory_manager, sample_wearable):
    inventory_manager.add_item(sample_wearable)
    preview = inventory_manager.get_equipment_preview(sample_wearable.id)
    assert isinstance(preview, dict)

def test_add_to_container(inventory_manager, sample_container, sample_item):
    inventory_manager.containers.append(sample_container)
    assert inventory_manager.add_to_container(sample_container.id, sample_item)
    assert sample_item in sample_container.contents

def test_remove_from_container(inventory_manager, sample_container, sample_item):
    inventory_manager.containers.append(sample_container)
    sample_container.contents.append(sample_item)
    removed_item = inventory_manager.remove_from_container(sample_container.id, sample_item.id)
    assert removed_item == sample_item
    assert sample_item not in sample_container.contents 