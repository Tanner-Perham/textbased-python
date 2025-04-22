"""
This module is responsible for loading and parsing game configuration from YAML files.
"""

import os
import glob
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
    location_items: List[Dict[str, Any]] = field(default_factory=list)
    location_containers: List[Dict[str, Any]] = field(default_factory=list)


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
    conditions: Dict[str, Any] = field(default_factory=dict)
    effects: List[Dict[str, Any]] = field(default_factory=list)


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
class CharacterArchetype:
    """Configuration for a character archetype."""
    id: str
    name: str
    description: str
    starting_skills: Dict[str, float]
    starting_equipment_ids: List[str]


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
    character_archetypes: Dict[str, CharacterArchetype] = field(default_factory=dict)  # Added character_archetypes
    inner_voices: List[Dict[str, Any]] = field(default_factory=list)
    thoughts: Dict[str, Any] = field(default_factory=dict)

    def get_quest(self, quest_id: str) -> Optional[Quest]:
        """Get a quest by its ID."""
        return self.quests.get(quest_id)

    @classmethod
    def load(cls, path: str) -> "GameConfig":
        """Load game configuration from YAML files.
        
        Args:
            path: Either a path to a single YAML file or a directory containing multiple YAML files
        
        Returns:
            A GameConfig instance with configuration loaded from the specified file(s).
        """
        config_loader = ConfigLoader()
        
        # Check if path is a directory
        if os.path.isdir(path):
            # Look for a main configuration file
            main_config_path = os.path.join(path, "main.yaml")
            if os.path.exists(main_config_path):
                return config_loader.load_split_config(main_config_path)
            else:
                # If no main file, load the content directory structure
                return config_loader.load_content_directory(path)
        elif not os.path.exists(path):
            raise FileNotFoundError(f"Configuration file not found: {path}")
        else:
            # Path is a single file, load it directly
            return config_loader.load_single_config(path)


class ConfigLoader:
    """Loads and validates game configuration."""

    @staticmethod
    def load_config(config_path: str) -> Dict:
        """Load the game configuration from a YAML file."""
        with open(config_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file) or {}  # Return empty dict if file is empty

    def load_single_config(self, config_path: str) -> GameConfig:
        """Load game configuration from a single YAML file."""
        print(f"Loading configuration from {config_path}")
        config_data = self.load_config(config_path)
        return self._process_config_data(config_data, os.path.dirname(config_path))

    def load_split_config(self, main_config_path: str) -> GameConfig:
        """Load a split configuration using a main config file that includes other files."""
        print(f"Loading split configuration from {main_config_path}")
        main_config = self.load_config(main_config_path)
        
        # If there's no include directive, treat as a single config
        if "include" not in main_config:
            return self._process_config_data(main_config, os.path.dirname(main_config_path))
        
        # Merge all included configuration files
        base_dir = os.path.dirname(main_config_path)
        merged_config = {}
        
        for included_file in main_config["include"]:
            include_path = os.path.join(base_dir, included_file)
            print(f"Including configuration from {include_path}")
            
            if not os.path.exists(include_path):
                print(f"Warning: Included config file not found: {include_path}")
                continue
                
            included_config = self.load_config(include_path)
            if included_config:
                # Merge the included configuration into the main configuration
                merged_config.update(included_config)
        
        return self._process_config_data(merged_config, base_dir)

    def load_config_directory(self, config_dir: str) -> GameConfig:
        """Load all YAML files from a directory and merge them."""
        print(f"Loading configuration from directory {config_dir}")
        
        # Find all YAML files in the directory
        yaml_files = glob.glob(os.path.join(config_dir, "*.yaml")) + glob.glob(os.path.join(config_dir, "*.yml"))
        
        merged_config = {}
        for yaml_file in yaml_files:
            print(f"Including configuration from {yaml_file}")
            config_data = self.load_config(yaml_file)
            if config_data:
                merged_config.update(config_data)
        
        return self._process_config_data(merged_config, config_dir)

    def load_content_directory(self, content_dir: str) -> GameConfig:
        """Load game configuration from a structured content directory.
        
        Expected structure:
            content/
                game_settings.yaml
                locations/
                    location1.yaml
                    location2.yaml
                npcs/
                    npc1.yaml
                    npc2.yaml
                quests/
                    quest1.yaml
                    quest2.yaml
                items/
                    category1.yaml
                    category2.yaml
                dialogues/
                    dialogue1.yaml
                    dialogue2.yaml
        """
        print(f"Loading content from directory structure: {content_dir}")
        
        # Initialize empty config sections
        merged_config = {
            "game_settings": {},
            "locations": {},
            "npcs": {},
            "dialogue_trees": {},
            "quests": {},
            "items": {},
            "item_sets": {},
            "character_archetypes": {},
            "inner_voices": [],
            "thoughts": {}
        }
        
        # Load game settings (core settings file)
        game_settings_path = os.path.join(content_dir, "game_settings.yaml")
        if os.path.exists(game_settings_path):
            print(f"Loading game settings from {game_settings_path}")
            settings_data = self.load_config(game_settings_path)
            if "game_settings" in settings_data:
                merged_config["game_settings"] = settings_data["game_settings"]
            else:
                # The file might contain the settings directly without a "game_settings" key
                merged_config["game_settings"] = settings_data
        
        # Load locations (one per file)
        locations_dir = os.path.join(content_dir, "content/locations/")
        if os.path.exists(locations_dir):
            print(f"Loading locations from {locations_dir}")
            location_files = glob.glob(os.path.join(locations_dir, "*.yaml")) + glob.glob(os.path.join(locations_dir, "*.yml"))
            
            for loc_file in location_files:
                loc_data = self.load_config(loc_file)
                # Location files might have a single location or multiple locations
                if loc_data:
                    if "id" in loc_data:
                        # Single location format
                        loc_id = loc_data["id"]
                        merged_config["locations"][loc_id] = loc_data
                    else:
                        # Multiple locations format or nested under a key
                        for key, value in loc_data.items():
                            if isinstance(value, dict) and "id" in value:
                                merged_config["locations"][key] = value
        
        # Load NPCs (one per file)
        npcs_dir = os.path.join(content_dir, "content/npcs/")
        if os.path.exists(npcs_dir):
            print(f"Loading NPCs from {npcs_dir}")
            npc_files = glob.glob(os.path.join(npcs_dir, "*.yaml")) + glob.glob(os.path.join(npcs_dir, "*.yml"))
            
            for npc_file in npc_files:
                npc_data = self.load_config(npc_file)
                if npc_data:
                    if "id" in npc_data:
                        # Single NPC format
                        npc_id = npc_data["id"]
                        merged_config["npcs"][npc_id] = npc_data
                    else:
                        # Multiple NPCs format or nested under a key
                        for key, value in npc_data.items():
                            if isinstance(value, dict) and "id" in value:
                                merged_config["npcs"][key] = value
        
        # Load dialogues (one file per NPC or dialogue tree)
        dialogues_dir = os.path.join(content_dir, "content/dialogues/")
        if os.path.exists(dialogues_dir):
            print(f"Loading dialogues from {dialogues_dir}")
            dialogue_files = glob.glob(os.path.join(dialogues_dir, "*.yaml")) + glob.glob(os.path.join(dialogues_dir, "*.yml"))
            
            for dialogue_file in dialogue_files:
                dialogue_data = self.load_config(dialogue_file)
                if dialogue_data:
                    # Each dialogue file can contain multiple dialogue nodes
                    for node_id, node_data in dialogue_data.items():
                        if isinstance(node_data, dict):
                            merged_config["dialogue_trees"][node_id] = node_data
        
        # Load quests (one per file)
        quests_dir = os.path.join(content_dir, "content/quests/")
        if os.path.exists(quests_dir):
            print(f"Loading quests from {quests_dir}")
            quest_files = glob.glob(os.path.join(quests_dir, "*.yaml")) + glob.glob(os.path.join(quests_dir, "*.yml"))
            
            for quest_file in quest_files:
                quest_data = self.load_config(quest_file)
                if quest_data:
                    if "id" in quest_data:
                        # Single quest format
                        quest_id = quest_data["id"]
                        merged_config["quests"][quest_id] = quest_data
                    else:
                        # Multiple quests format or nested under a key
                        for key, value in quest_data.items():
                            if isinstance(value, dict) and "id" in value:
                                merged_config["quests"][key] = value
        
        # Load items (by category)
        items_dir = os.path.join(content_dir, "content/items/")
        if os.path.exists(items_dir):
            print(f"Loading items from {items_dir}")
            item_files = glob.glob(os.path.join(items_dir, "*.yaml")) + glob.glob(os.path.join(items_dir, "*.yml"))
            
            for item_file in item_files:
                item_data = self.load_config(item_file)
                if item_data:
                    # Check if this is an item sets file
                    if "item_sets" in item_data:
                        merged_config["item_sets"].update(item_data["item_sets"])
                    
                    # Check if this is an items file
                    if "items" in item_data:
                        merged_config["items"].update(item_data["items"])
                    else:
                        # File may contain items directly without an "items" key
                        for key, value in item_data.items():
                            if isinstance(value, dict) and "name" in value and "description" in value:
                                # This looks like an item definition
                                merged_config["items"][key] = value
        
        # Load character archetypes if they exist
        archetypes_path = os.path.join(content_dir, "content/character_archetypes.yaml")
        if os.path.exists(archetypes_path):
            print(f"Loading character archetypes from {archetypes_path}")
            archetypes_data = self.load_config(archetypes_path)
            if "character_archetypes" in archetypes_data:
                merged_config["character_archetypes"] = archetypes_data["character_archetypes"]
            else:
                # The file might contain archetypes directly
                merged_config["character_archetypes"] = archetypes_data
        
        # Load inner voices if they exist
        inner_voices_path = os.path.join(content_dir, "content/inner_voices.yaml")
        if os.path.exists(inner_voices_path):
            print(f"Loading inner voices from {inner_voices_path}")
            inner_voices_data = self.load_config(inner_voices_path)
            if "inner_voices" in inner_voices_data:
                merged_config["inner_voices"] = inner_voices_data["inner_voices"]
            else:
                merged_config["inner_voices"] = inner_voices_data
        
        # Load thoughts if they exist
        thoughts_path = os.path.join(content_dir, "content/thoughts.yaml")
        if os.path.exists(thoughts_path):
            print(f"Loading thoughts from {thoughts_path}")
            thoughts_data = self.load_config(thoughts_path)
            if "thoughts" in thoughts_data:
                merged_config["thoughts"] = thoughts_data["thoughts"]
            else:
                merged_config["thoughts"] = thoughts_data
        
        return self._process_config_data(merged_config, content_dir)

    def _process_config_data(self, config_data: Dict, base_dir: str) -> GameConfig:
        """Process the loaded configuration data into a GameConfig object."""
        # Parse game settings
        game_settings_data = config_data.get("game_settings", {})
        game_settings = GameSettings(**game_settings_data)

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

        # Parse character archetypes
        print("Parsing Character Archetypes")
        character_archetypes = {}
        for archetype_id, archetype_data in config_data.get("character_archetypes", {}).items():
            character_archetypes[archetype_id] = CharacterArchetype(**archetype_data)

        # Parse items using the ConfigLoader
        print("Parsing Items")
        processed_items = self.load_game_config(config_data)
        items = processed_items['processed_items']
        item_sets = processed_items['processed_item_sets']

        # Create and return GameConfig
        return GameConfig(
            game_settings=game_settings,
            locations=locations,
            npcs=npcs,
            dialogue_trees=dialogue_trees,
            quests=quests,
            items=items,
            item_sets=item_sets,
            character_archetypes=character_archetypes,
            inner_voices=config_data.get("inner_voices", []),
            thoughts=config_data.get("thoughts", {}),
        )

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

    def load_game_config(self, config_data: Dict) -> Dict:
        """Process the items and item sets from the config data."""
        try:
            # Process item sets
            item_sets = {
                set_id: self.create_item_set(set_id, set_data)
                for set_id, set_data in config_data.get('item_sets', {}).items()
            }

            # Process items
            items = {}
            for item_id, item_data in config_data.get('items', {}).items():
                try:
                    items[item_id] = self.create_item(item_id, item_data)
                except Exception as e:
                    print(f"Error processing item {item_id}: {str(e)}")
                    continue

            # Return processed data
            return {
                'processed_item_sets': item_sets,
                'processed_items': items
            }
        except Exception as e:
            print(f"Error loading configuration: {str(e)}")
            raise
