"""
This module is responsible for loading and parsing game configuration from YAML files.
"""

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml
from game.quest_status import QuestStatus
from game.inventory import (
    Item, Wearable, Container, Effect, ItemCategory, WearableSlot,
    ItemBase  # Add ItemBase to imports
)


@dataclass
class GameSettings:
    """Game settings configuration."""

    title: str
    starting_location: str
    default_time: str
    starting_inventory: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Clue:
    """Game clue."""

    id: str
    description: str
    related_quest: str
    discovered: bool = False


@dataclass
class Location:
    """Game location."""

    id: str
    name: str
    description: str
    available_actions: List[Dict[str, Any]] = field(default_factory=list)
    connected_locations: List[str] = field(default_factory=list)


@dataclass
class NPC:
    """Non-player character."""

    id: str
    name: str
    dialogue_entry_point: str
    disposition: int
    location: str
    gender: str


@dataclass
class DialogueNode:
    """Dialogue node for conversations."""

    id: str
    text: str
    speaker: str
    emotional_state: str
    inner_voice_comments: List[Dict[str, Any]] = field(default_factory=list)
    options: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class QuestStage:
    """Stage within a quest."""

    id: str
    title: str
    description: str
    notification_text: str = ""
    status: str = "NotStarted"
    objectives: List[Dict[str, Any]] = field(default_factory=list)
    completion_events: List[Dict[str, Any]] = field(default_factory=list)
    next_stages: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        """Convert status string to QuestStatus enum."""
        self.status = QuestStatus[self.status]


@dataclass
class QuestRewards:
    """Rewards for completing a quest."""

    items: List[ItemBase] = field(default_factory=list)  # Updated to use ItemBase
    skill_rewards: Dict[str, int] = field(default_factory=dict)
    relationship_changes: Dict[str, int] = field(default_factory=dict)
    experience: Optional[int] = None
    unlocked_locations: List[str] = field(default_factory=list)
    unlocked_dialogues: List[str] = field(default_factory=list)


@dataclass
class Quest:
    """Game quest."""

    id: str
    title: str
    description: str
    short_description: str
    importance: str
    stages: List[QuestStage]
    rewards: QuestRewards = field(default_factory=QuestRewards)
    is_hidden: bool = False
    is_main_quest: bool = False
    status: str = "NotStarted"
    related_npcs: List[str] = field(default_factory=list)
    related_locations: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Convert status string to QuestStatus enum."""
        self.status = QuestStatus[self.status]


@dataclass
class ItemSetBonus:
    """Bonus effects for completing an item set."""
    attribute: str
    value: float
    description: str


@dataclass
class ItemSet:
    """Configuration for an item set."""
    id: str
    name: str
    description: str
    required_pieces: List[str]
    set_bonus: List[ItemSetBonus]


@dataclass
class GameConfig:
    """Main game configuration."""

    game_settings: GameSettings
    locations: Dict[str, Location] = field(default_factory=dict)
    npcs: Dict[str, NPC] = field(default_factory=dict)
    dialogue_trees: Dict[str, DialogueNode] = field(default_factory=dict)
    quests: Dict[str, Quest] = field(default_factory=dict)
    items: Dict[str, ItemBase] = field(default_factory=dict)  # Updated to use ItemBase
    item_sets: Dict[str, ItemSet] = field(default_factory=dict)  # Added item_sets
    inner_voices: List[Dict[str, Any]] = field(default_factory=list)
    thoughts: Dict[str, Any] = field(default_factory=dict)

    def get_quest(self, quest_id: str) -> Optional[Quest]:
        """Get a quest by its ID."""
        return self.quests.get(quest_id)

    @classmethod
    def load(cls, path: str) -> "GameConfig":
        """Load game configuration from YAML file."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with open(path, "r", encoding="utf-8") as file:
            config_data = yaml.safe_load(file)

        # Parse game settings
        game_settings = GameSettings(**config_data.get("game_settings", {}))

        # Parse locations
        print("Parsing Locations")
        locations = {}
        for loc_id, loc_data in config_data.get("locations", {}).items():
            locations[loc_id] = Location(**loc_data)

        # Parse NPCs
        print("Parsing NPCs")
        npcs = {}
        for npc_id, npc_data in config_data.get("npcs", {}).items():
            npcs[npc_id] = NPC(**npc_data)

        # Parse dialogue trees
        print("Parsing Dialogue Trees")
        dialogue_trees = {}
        for node_id, node_data in config_data.get("dialogue_trees", {}).items():
            dialogue_trees[node_id] = DialogueNode(**node_data)

        # Parse quests with stages
        print("Parsing Quests")
        quests = {}
        for quest_id, quest_data in config_data.get("quests", {}).items():
            # Handle stages separately
            stages_data = quest_data.pop("stages", [])
            stages = []

            for stage_data in stages_data:
                stages.append(QuestStage(**stage_data))

            # Handle rewards separately
            rewards_data = quest_data.pop("rewards", {})
            rewards = QuestRewards(**rewards_data)

            # Remove id from quest_data to avoid duplicate
            quest_data.pop("id", None)

            # Create quest with processed stages and rewards
            quest = Quest(id=quest_id, **quest_data, stages=stages, rewards=rewards)
            quests[quest_id] = quest

        # Parse items using the ConfigLoader
        print("Parsing Items")
        config_loader = ConfigLoader()
        processed_config = config_loader.load_game_config(path)
        items = processed_config['processed_items']
        item_sets = processed_config['processed_item_sets']

        # Create and return GameConfig
        return cls(
            game_settings=game_settings,
            locations=locations,
            npcs=npcs,
            dialogue_trees=dialogue_trees,
            quests=quests,
            items=items,
            item_sets=item_sets,
            inner_voices=config_data.get("inner_voices", []),
            thoughts=config_data.get("thoughts", {}),
        )


class ConfigLoader:
    """Loads and validates game configuration."""

    @staticmethod
    def load_config(config_path: str) -> Dict:
        """Load the game configuration from a YAML file."""
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)

    @staticmethod
    def create_effect(effect_data: Dict) -> Effect:
        """Create an Effect instance from configuration data."""
        return Effect(
            attribute=effect_data['attribute'],
            value=float(effect_data['value']),
            duration=effect_data.get('duration'),
            condition=effect_data.get('condition'),
            description=effect_data.get('description', '')
        )

    @staticmethod
    def create_item_set(set_id: str, set_data: Dict) -> ItemSet:
        """Create an ItemSet instance from configuration data."""
        set_bonus = [
            ItemSetBonus(
                attribute=bonus['attribute'],
                value=float(bonus['value']),
                description=bonus['description']
            )
            for bonus in set_data.get('set_bonus', [])
        ]

        return ItemSet(
            id=set_id,
            name=set_data['name'],
            description=set_data['description'],
            required_pieces=set_data['required_pieces'],
            set_bonus=set_bonus
        )

    @staticmethod
    def create_item(item_id: str, item_data: Dict) -> ItemBase:
        """Create an appropriate Item instance from configuration data."""
        # Convert category strings to ItemCategory enums
        categories = set()
        for cat in item_data.get('categories', []):
            try:
                categories.add(ItemCategory[cat.upper()])
            except KeyError:
                print(f"Warning: Unknown item category '{cat}' for item {item_id}")
                continue
        
        # Create effects list
        effects = [
            ConfigLoader.create_effect(effect_data)
            for effect_data in item_data.get('effects', [])
        ]

        # Base item attributes
        base_attrs = {
            'id': item_id,
            'name': item_data['name'],
            'description': item_data['description'],
            'categories': categories,
            'weight': float(item_data.get('weight', 0.0)),
            'effects': effects,
            'stackable': bool(item_data.get('stackable', False)),
            'quantity': int(item_data.get('quantity', 1))
        }

        # Create specific item type based on categories
        if ItemCategory.WEARABLE in categories:
            try:
                slot = WearableSlot[item_data['slot'].upper()]
            except KeyError:
                print(f"Warning: Invalid slot '{item_data.get('slot')}' for wearable item {item_id}")
                slot = WearableSlot.ACCESSORY  # Default to accessory if invalid
            
            return Wearable(
                **base_attrs,
                slot=slot,
                style_rating=int(item_data.get('style_rating', 0)),
                condition=int(item_data.get('condition', 100)),
                set_id=item_data.get('set_id')
            )
        elif ItemCategory.CONTAINER in categories:
            # Convert allowed categories strings to enums
            allowed_categories = set()
            for cat in item_data.get('allowed_categories', []):
                try:
                    allowed_categories.add(ItemCategory[cat.upper()])
                except KeyError:
                    print(f"Warning: Unknown allowed category '{cat}' for container {item_id}")
                    continue

            return Container(
                **base_attrs,
                capacity=float(item_data.get('capacity', 10.0)),  # Default capacity of 10
                allowed_categories=allowed_categories
            )
        else:
            return Item(**base_attrs)

    @classmethod
    def load_game_config(cls, config_path: str) -> Dict:
        """Load and process the full game configuration."""
        try:
            config = cls.load_config(config_path)
            
            # Process item sets
            item_sets = {
                set_id: cls.create_item_set(set_id, set_data)
                for set_id, set_data in config.get('item_sets', {}).items()
            }

            # Process items
            items = {}
            for item_id, item_data in config.get('items', {}).items():
                try:
                    items[item_id] = cls.create_item(item_id, item_data)
                except Exception as e:
                    print(f"Error processing item {item_id}: {str(e)}")
                    continue

            # Update config with processed data
            config['processed_item_sets'] = item_sets
            config['processed_items'] = items

            return config
        except Exception as e:
            print(f"Error loading configuration: {str(e)}")
            raise
