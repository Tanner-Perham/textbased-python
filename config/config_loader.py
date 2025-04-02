"""
This module is responsible for loading and parsing game configuration from YAML files.
"""

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class GameSettings:
    """Game settings configuration."""

    title: str
    starting_location: str
    default_time: str


@dataclass
class Item:
    """Game item."""

    id: str
    name: str
    description: str
    effects: Dict[str, int] = field(default_factory=dict)


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
    description: str
    notification_text: str = ""
    status: str = "NotStarted"
    objectives: List[Dict[str, Any]] = field(default_factory=list)
    completion_events: List[Dict[str, Any]] = field(default_factory=list)
    next_stages: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class QuestRewards:
    """Rewards for completing a quest."""

    items: List[Item] = field(default_factory=list)
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
    related_npcs: List[str] = field(default_factory=list)
    related_locations: List[str] = field(default_factory=list)


@dataclass
class GameConfig:
    """Main game configuration."""

    game_settings: GameSettings
    locations: Dict[str, Location] = field(default_factory=dict)
    npcs: Dict[str, NPC] = field(default_factory=dict)
    dialogue_trees: Dict[str, DialogueNode] = field(default_factory=dict)
    quests: Dict[str, Quest] = field(default_factory=dict)
    items: Dict[str, Item] = field(default_factory=dict)
    inner_voices: List[Dict[str, Any]] = field(default_factory=list)
    thoughts: Dict[str, Any] = field(default_factory=dict)

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

            # Create quest with processed stages and rewards
            quest = Quest(id=quest_id, **quest_data, stages=stages, rewards=rewards)
            quests[quest_id] = quest

        # Parse items
        print("Parsing Items")
        items = {}
        for item_id, item_data in config_data.get("items", {}).items():
            items[item_id] = Item(**item_data)

        # Create and return GameConfig
        return cls(
            game_settings=game_settings,
            locations=locations,
            npcs=npcs,
            dialogue_trees=dialogue_trees,
            quests=quests,
            items=items,
            inner_voices=config_data.get("inner_voices", []),
            thoughts=config_data.get("thoughts", {}),
        )
