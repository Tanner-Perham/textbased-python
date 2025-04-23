"""
Configuration loader that reads game data from SQLite database.
"""

import json
from typing import Any, Dict, List, Optional
from .database_manager import DatabaseManager
from game.quest_status import QuestStatus
from game.inventory import (
    Item, Wearable, Container, Effect, ItemCategory, WearableSlot,
    ItemBase
)

class SqliteConfigLoader:
    """Loads game configuration from SQLite database."""
    
    def __init__(self, db_path: str = "game_data.db"):
        """Initialize the configuration loader.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db = DatabaseManager(db_path)
        
    def load_game_config(self) -> Dict[str, Any]:
        """Load all game configuration from the database.
        
        Returns:
            Dictionary containing all game configuration
        """
        config = {}
        
        # Load game settings
        config["game_settings"] = self._load_game_settings()
        
        # Load locations
        config["locations"] = self._load_locations()
        
        # Load NPCs
        config["npcs"] = self._load_npcs()
        
        # Load dialogues
        config["dialogue_trees"] = self._load_dialogues()
        
        # Load quests
        config["quests"] = self._load_quests()
        
        # Load items
        config["items"] = self._load_items()
        
        # Load item sets
        config["item_sets"] = self._load_item_sets()
        
        # Load character archetypes
        config["character_archetypes"] = self._load_character_archetypes()
        
        return config
        
    def _load_game_settings(self) -> Dict[str, Any]:
        """Load game settings from the database.
        
        Returns:
            Dictionary containing game settings
        """
        settings = self.db.get_all("game_settings")[0]
        starting_inventory = self.db.get_all("starting_inventory")
        
        return {
            "title": settings["title"],
            "starting_location": settings["starting_location"],
            "default_time": settings["default_time"],
            "starting_inventory": [
                {"id": item["item_id"], "quantity": item["quantity"]}
                for item in starting_inventory
            ]
        }
        
    def _load_locations(self) -> Dict[str, Any]:
        """Load locations from the database.
        
        Returns:
            Dictionary mapping location IDs to location data
        """
        locations = {}
        
        for location in self.db.get_all("locations"):
            location_id = location["id"]
            
            # Get connected locations
            connections = self.db.get_related("location_connections", "location_id", location_id)
            connected_locations = [conn["connected_location_id"] for conn in connections]
            
            # Get location actions
            actions = self.db.get_related("location_actions", "location_id", location_id)
            available_actions = [
                {
                    "type": action["action_type"],
                    "data": json.loads(action["action_data"])
                }
                for action in actions
            ]
            
            locations[location_id] = {
                "id": location_id,
                "name": location["name"],
                "description": location["description"],
                "connected_locations": connected_locations,
                "available_actions": available_actions
            }
            
        return locations
        
    def _load_npcs(self) -> Dict[str, Any]:
        """Load NPCs from the database.
        
        Returns:
            Dictionary mapping NPC IDs to NPC data
        """
        npcs = {}
        
        for npc in self.db.get_all("npcs"):
            npc_id = npc["id"]
            
            # Get NPC schedule
            schedule_entries = self.db.get_related("npc_schedules", "npc_id", npc_id)
            schedule = {
                entry["time"]: entry["location"]
                for entry in schedule_entries
            }
            
            npcs[npc_id] = {
                "id": npc_id,
                "name": npc["name"],
                "dialogue_entry_point": npc["dialogue_entry_point"],
                "disposition": npc["disposition"],
                "location": npc["location"],
                "gender": npc["gender"],
                "schedule": schedule
            }
            
        return npcs
        
    def _load_dialogues(self) -> Dict[str, Any]:
        """Load dialogues from the database.
        
        Returns:
            Dictionary mapping dialogue node IDs to dialogue data
        """
        dialogues = {}
        
        for node in self.db.get_all("dialogue_nodes"):
            node_id = node["id"]
            
            # Get dialogue options
            options = self.db.get_related("dialogue_options", "node_id", node_id)
            dialogue_options = [
                {
                    "text": option["text"],
                    "next_node_id": option["next_node_id"]
                }
                for option in options
            ]
            
            # Get dialogue conditions
            conditions = self.db.get_related("dialogue_conditions", "node_id", node_id)
            dialogue_conditions = {
                condition["condition_type"]: json.loads(condition["condition_data"])
                for condition in conditions
            }
            
            # Get dialogue effects
            effects = self.db.get_related("dialogue_effects", "node_id", node_id)
            dialogue_effects = [
                {
                    "type": effect["effect_type"],
                    "data": json.loads(effect["effect_data"])
                }
                for effect in effects
            ]
            
            dialogues[node_id] = {
                "id": node_id,
                "text": node["text"],
                "speaker": node["speaker"],
                "emotional_state": node["emotional_state"],
                "options": dialogue_options,
                "conditions": dialogue_conditions,
                "effects": dialogue_effects
            }
            
        return dialogues
        
    def _load_quests(self) -> Dict[str, Any]:
        """Load quests from the database.
        
        Returns:
            Dictionary mapping quest IDs to quest data
        """
        quests = {}
        
        for quest in self.db.get_all("quests"):
            quest_id = quest["id"]
            
            # Get quest stages
            stages = self.db.get_related("quest_stages", "quest_id", quest_id)
            quest_stages = []
            
            for stage in stages:
                stage_id = stage["id"]
                
                # Get stage objectives
                objectives = self.db.get_related("quest_objectives", "stage_id", stage_id)
                stage_objectives = [
                    {
                        "type": objective["objective_type"],
                        "data": json.loads(objective["objective_data"])
                    }
                    for objective in objectives
                ]
                
                quest_stages.append({
                    "id": stage_id,
                    "title": stage["title"],
                    "description": stage["description"],
                    "notification_text": stage["notification_text"],
                    "status": stage["status"],
                    "objectives": stage_objectives
                })
                
            # Get quest rewards
            rewards = self.db.get_related("quest_rewards", "quest_id", quest_id)
            quest_rewards = {}
            
            for reward in rewards:
                reward_type = reward["reward_type"]
                reward_data = json.loads(reward["reward_data"])
                
                if reward_type == "item":
                    if "items" not in quest_rewards:
                        quest_rewards["items"] = []
                    quest_rewards["items"].append(reward_data)
                else:
                    quest_rewards[reward_type] = reward_data
                    
            quests[quest_id] = {
                "id": quest_id,
                "title": quest["title"],
                "description": quest["description"],
                "short_description": quest["short_description"],
                "importance": quest["importance"],
                "is_hidden": bool(quest["is_hidden"]),
                "is_main_quest": bool(quest["is_main_quest"]),
                "status": quest["status"],
                "stages": quest_stages,
                "rewards": quest_rewards
            }
            
        return quests
        
    def _load_items(self) -> Dict[str, Any]:
        """Load items from the database.
        
        Returns:
            Dictionary mapping item IDs to item data
        """
        items = {}
        
        for item in self.db.get_all("items"):
            item_id = item["id"]
            
            items[item_id] = {
                "id": item_id,
                "name": item["name"],
                "description": item["description"],
                "category": item["category"],
                "value": item["value"],
                "weight": item["weight"],
                "is_stackable": bool(item["is_stackable"]),
                "is_consumable": bool(item["is_consumable"]),
                "is_equippable": bool(item["is_equippable"]),
                "slot": item["slot"],
                "effects": json.loads(item["effects"])
            }
            
        return items
        
    def _load_item_sets(self) -> Dict[str, Any]:
        """Load item sets from the database.
        
        Returns:
            Dictionary mapping item set IDs to item set data
        """
        item_sets = {}
        
        for item_set in self.db.get_all("item_sets"):
            set_id = item_set["id"]
            
            # Get set pieces
            pieces = self.db.get_related("item_set_pieces", "set_id", set_id)
            required_pieces = [piece["item_id"] for piece in pieces]
            
            # Get set bonuses
            bonuses = self.db.get_related("item_set_bonuses", "set_id", set_id)
            set_bonus = [
                {
                    "attribute": bonus["attribute"],
                    "value": bonus["value"],
                    "description": bonus["description"]
                }
                for bonus in bonuses
            ]
            
            item_sets[set_id] = {
                "id": set_id,
                "name": item_set["name"],
                "description": item_set["description"],
                "required_pieces": required_pieces,
                "set_bonus": set_bonus
            }
            
        return item_sets
        
    def _load_character_archetypes(self) -> Dict[str, Any]:
        """Load character archetypes from the database.
        
        Returns:
            Dictionary mapping archetype IDs to archetype data
        """
        archetypes = {}
        
        for archetype in self.db.get_all("character_archetypes"):
            archetype_id = archetype["id"]
            
            # Get archetype skills
            skills = self.db.get_related("archetype_skills", "archetype_id", archetype_id)
            starting_skills = {
                skill["skill_name"]: skill["skill_value"]
                for skill in skills
            }
            
            # Get archetype equipment
            equipment = self.db.get_related("archetype_equipment", "archetype_id", archetype_id)
            starting_equipment_ids = [item["item_id"] for item in equipment]
            
            archetypes[archetype_id] = {
                "id": archetype_id,
                "name": archetype["name"],
                "description": archetype["description"],
                "starting_skills": starting_skills,
                "starting_equipment_ids": starting_equipment_ids
            }
            
        return archetypes 