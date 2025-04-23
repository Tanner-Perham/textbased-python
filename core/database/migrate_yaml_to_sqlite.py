"""
Script to migrate YAML game data to SQLite database.
"""

import os
import yaml
import json
from typing import Any, Dict, List
from .database_manager import DatabaseManager

class YamlToSqliteMigrator:
    """Handles migration of YAML game data to SQLite."""
    
    def __init__(self, yaml_dir: str, db_path: str = "game_data.db"):
        """Initialize the migrator.
        
        Args:
            yaml_dir: Directory containing YAML game data
            db_path: Path to the SQLite database file
        """
        self.yaml_dir = yaml_dir
        self.db = DatabaseManager(db_path)
        
    def migrate(self) -> None:
        """Perform the migration of all YAML data to SQLite."""
        print("Initializing database...")
        self.db.initialize_database()
        
        print("Dropping existing tables...")
        self.db.drop_all_tables()
        
        print("Creating tables with new schema...")
        self.db.create_tables()
        
        print("Starting migration...")
        try:
            # Migrate each type of data
            print("Migrating game settings...")
            self._migrate_game_settings()
            
            print("Migrating locations...")
            self._migrate_locations()
            
            print("Migrating NPCs...")
            self._migrate_npcs()
            
            print("Migrating dialogues...")
            self._migrate_dialogues()
            
            print("Migrating quests...")
            self._migrate_quests()
            
            print("Migrating items...")
            self._migrate_items()
            
            print("Migrating item sets...")
            self._migrate_item_sets()
            
            print("Migrating character archetypes...")
            self._migrate_character_archetypes()
            
            print("Migration completed successfully!")
        except Exception as e:
            print(f"Error during migration: {str(e)}")
            raise
        
    def _load_yaml(self, path: str) -> Dict[str, Any]:
        """Load a YAML file.
        
        Args:
            path: Path to the YAML file
            
        Returns:
            Dictionary containing the YAML data
        """
        with open(path, 'r') as f:
            return yaml.safe_load(f)
            
    def _migrate_game_settings(self) -> None:
        """Migrate game settings from YAML to SQLite."""
        settings_path = os.path.join(self.yaml_dir, "game_settings.yaml")
        if not os.path.exists(settings_path):
            return
            
        settings = self._load_yaml(settings_path)
        
        # Insert game settings
        self.db.insert_data("game_settings", {
            "title": settings.get("title", ""),
            "starting_location": settings.get("starting_location", ""),
            "default_time": settings.get("default_time", "")
        })
        
        # Insert starting inventory
        for item in settings.get("starting_inventory", []):
            self.db.insert_data("starting_inventory", {
                "item_id": item.get("id", ""),
                "quantity": item.get("quantity", 1)
            })
            
    def _migrate_locations(self) -> None:
        """Migrate locations from YAML to SQLite."""
        locations_dir = os.path.join(self.yaml_dir, "locations")
        if not os.path.exists(locations_dir):
            return
            
        for filename in os.listdir(locations_dir):
            if not filename.endswith(".yaml"):
                continue
                
            location_path = os.path.join(locations_dir, filename)
            location = self._load_yaml(location_path)
            
            # Get the location data (first key in the YAML)
            location_id = list(location.keys())[0]
            location_data = location[location_id]
            
            # Insert location
            self.db.insert_data("locations", {
                "id": location_id,
                "name": location_data["name"],
                "description": location_data["description"]
            })
            
            # Insert location connections
            for connected_location in location_data.get("connected_locations", []):
                self.db.insert_data("location_connections", {
                    "location_id": location_id,
                    "connected_location_id": connected_location
                })
                
            # Insert location actions
            for action in location_data.get("available_actions", []):
                self.db.insert_data("location_actions", {
                    "location_id": location_id,
                    "action_type": action["name"],
                    "action_data": json.dumps({
                        "description": action["description"],
                        "requirements": action.get("requirements", {}),
                        "consequences": action.get("consequences", [])
                    })
                })
                
            # Insert location items
            for item in location_data.get("location_items", []):
                self.db.insert_data("location_items", {
                    "location_id": location_id,
                    "item_id": item["id"],
                    "is_obvious": 1 if item.get("is_obvious", True) else 0,
                    "perception_difficulty": item.get("perception_difficulty", 0)
                })
                
            # Insert location containers and their contents
            for container in location_data.get("location_containers", []):
                # Insert container reference
                self.db.insert_data("location_containers", {
                    "location_id": location_id,
                    "container_id": container["id"],
                    "is_obvious": 1 if container.get("is_obvious", True) else 0
                })
                
                # Insert container contents
                for content in container.get("contents", []):
                    self.db.insert_data("container_contents", {
                        "container_id": container["id"],
                        "item_id": content["id"],
                        "quantity": content.get("quantity", 1)
                    })
            
    def _migrate_npcs(self) -> None:
        """Migrate NPCs from YAML to SQLite."""
        npcs_dir = os.path.join(self.yaml_dir, "npcs")
        if not os.path.exists(npcs_dir):
            return
            
        for filename in os.listdir(npcs_dir):
            if not filename.endswith(".yaml"):
                continue
                
            npc_path = os.path.join(npcs_dir, filename)
            print(f"Loading NPC from {filename}...")
            npc_data = self._load_yaml(npc_path)
            print(f"Loaded data: {npc_data}")
            
            # Handle two possible YAML structures:
            # 1. Data at root level (like martinez.yaml)
            # 2. Data nested under NPC ID (like worker_chen.yaml)
            if isinstance(npc_data, dict) and len(npc_data) == 1 and isinstance(list(npc_data.values())[0], dict):
                # Case 2: Data is nested under NPC ID
                npc_id = list(npc_data.keys())[0]
                npc = npc_data[npc_id]
            else:
                # Case 1: Data is at root level
                npc = npc_data
                npc_id = npc["id"]
            
            print(f"Processing NPC {npc_id}: {npc}")
            
            # Insert NPC
            self.db.insert_data("npcs", {
                "id": npc_id,
                "name": npc["name"],
                "dialogue_entry_point": npc["dialogue_entry_point"],
                "disposition": npc["disposition"],
                "location": npc["location"],
                "gender": npc["gender"]
            })
            
            # Insert NPC schedule
            if "schedule" in npc:
                for time, location in npc["schedule"].items():
                    self.db.insert_data("npc_schedules", {
                        "npc_id": npc_id,
                        "time": time,
                        "location": location
                    })
                
    def _migrate_dialogues(self) -> None:
        """Migrate dialogues from YAML to SQLite."""
        dialogues_dir = os.path.join(self.yaml_dir, "dialogues")
        if not os.path.exists(dialogues_dir):
            return
            
        for filename in os.listdir(dialogues_dir):
            if not filename.endswith(".yaml"):
                continue
                
            dialogue_path = os.path.join(dialogues_dir, filename)
            print(f"Loading dialogue from {filename}...")
            dialogue_data = self._load_yaml(dialogue_path)
            print(f"Loaded data: {dialogue_data}")
            
            # Handle the nested YAML structure
            for dialogue_id, dialogue in dialogue_data.items():
                print(f"Processing dialogue {dialogue_id}: {dialogue}")
                
                # Insert dialogue
                self.db.insert_data("dialogues", {
                    "id": dialogue_id,
                    "text": dialogue["text"],
                    "speaker": dialogue["speaker"],
                    "emotional_state": dialogue["emotional_state"]
                })
                
                # Insert dialogue effects if present
                if "effects" in dialogue:
                    for effect in dialogue["effects"]:
                        if isinstance(effect, dict) and "type" in effect:
                            self.db.insert_data("dialogue_effects", {
                                "dialogue_id": dialogue_id,
                                "effect_type": effect["type"],
                                "effect_data": json.dumps(effect["data"])
                            })
                
                # Insert dialogue conditions if present
                if "conditions" in dialogue:
                    for condition in dialogue["conditions"]:
                        if isinstance(condition, dict) and "type" in condition:
                            self.db.insert_data("dialogue_conditions", {
                                "dialogue_id": dialogue_id,
                                "condition_type": condition["type"],
                                "condition_data": json.dumps(condition["data"])
                            })
                
                # Insert dialogue options
                if "options" in dialogue:
                    for option in dialogue["options"]:
                        # First insert the dialogue option
                        option_id = self.db.insert_data("dialogue_options", {
                            "dialogue_id": dialogue_id,
                            "text": option["text"],
                            "next_dialogue_id": option.get("next_node", ""),
                            "success_node": option.get("success_node", ""),
                            "failure_node": option.get("failure_node", ""),
                            "critical_success_node": option.get("critical_success_node", ""),
                            "critical_failure_node": option.get("critical_failure_node", "")
                        })
                        
                        # Insert skill check if present
                        if "skill_check" in option and option["skill_check"] is not None:
                            skill_check = option["skill_check"]
                            skill_check_id = self.db.insert_data("dialogue_skill_checks", {
                                "dialogue_option_id": option_id,
                                "base_difficulty": skill_check["base_difficulty"],
                                "primary_skill": skill_check["primary_skill"],
                                "supporting_skills": json.dumps(skill_check.get("supporting_skills", [])),
                                "emotional_modifiers": json.dumps(skill_check.get("emotional_modifiers", {})),
                                "is_white_check": 1 if skill_check.get("white_check", False) else 0,
                                "is_hidden": 1 if skill_check.get("hidden", False) else 0
                            })
                            
                            # Update the dialogue option with the skill check ID
                            self.db.update_data("dialogue_options", option_id, {
                                "skill_check_id": skill_check_id
                            })
                            
                            # Insert supporting skills
                            for skill, multiplier in skill_check.get("supporting_skills", []):
                                self.db.insert_data("dialogue_supporting_skills", {
                                    "skill_check_id": skill_check_id,
                                    "skill_name": skill,
                                    "skill_multiplier": multiplier
                                })
                            
                            # Insert emotional modifiers
                            for state, modifier in skill_check.get("emotional_modifiers", {}).items():
                                self.db.insert_data("dialogue_emotional_modifiers", {
                                    "skill_check_id": skill_check_id,
                                    "emotional_state": state,
                                    "modifier_value": modifier
                                })
                        
                        # Insert option effects if present (both consequences and effects)
                        if "consequences" in option and option["consequences"] is not None:
                            for effect in option["consequences"]:
                                if isinstance(effect, dict) and "type" in effect:
                                    self.db.insert_data("dialogue_effects", {
                                        "dialogue_id": dialogue_id,
                                        "dialogue_option_id": option_id,
                                        "effect_type": effect["type"],
                                        "effect_data": json.dumps(effect["data"])
                                    })
                        elif "effects" in option and option["effects"] is not None:
                            for effect in option["effects"]:
                                if isinstance(effect, dict) and "type" in effect:
                                    self.db.insert_data("dialogue_effects", {
                                        "dialogue_id": dialogue_id,
                                        "dialogue_option_id": option_id,
                                        "effect_type": effect["type"],
                                        "effect_data": json.dumps(effect["data"])
                                    })
                        
                        # Insert option conditions if present
                        if "conditions" in option:
                            conditions = option["conditions"]
                            # Handle any_of conditions
                            if "any_of" in conditions:
                                for condition in conditions["any_of"]:
                                    self.db.insert_data("dialogue_conditions", {
                                        "dialogue_id": dialogue_id,
                                        "condition_type": "any_of",
                                        "condition_data": json.dumps(condition)
                                    })
                            # Handle required skills
                            if "required_skills" in conditions:
                                self.db.insert_data("dialogue_conditions", {
                                    "dialogue_id": dialogue_id,
                                    "condition_type": "required_skills",
                                    "condition_data": json.dumps(conditions["required_skills"])
                                })
                            # Handle other direct conditions
                            for key, value in conditions.items():
                                if key not in ["any_of", "required_skills"]:
                                    self.db.insert_data("dialogue_conditions", {
                                        "dialogue_id": dialogue_id,
                                        "condition_type": key,
                                        "condition_data": json.dumps(value)
                                    })
                
    def _migrate_quests(self) -> None:
        """Migrate quests from YAML to SQLite."""
        quests_dir = os.path.join(self.yaml_dir, "quests")
        if not os.path.exists(quests_dir):
            return
            
        for filename in os.listdir(quests_dir):
            if not filename.endswith(".yaml"):
                continue
                
            quest_path = os.path.join(quests_dir, filename)
            quest_data = self._load_yaml(quest_path)
            
            # Handle the nested YAML structure
            for quest_id, quest in quest_data.items():
                # Insert quest
                self.db.insert_data("quests", {
                    "id": quest_id,
                    "title": quest.get("title", ""),
                    "description": quest.get("description", ""),
                    "short_description": quest.get("short_description", ""),
                    "importance": quest.get("importance", ""),
                    "is_hidden": 1 if quest.get("is_hidden", False) else 0,
                    "is_main_quest": 1 if quest.get("is_main_quest", False) else 0,
                    "status": quest.get("status", "NotStarted")
                })
                
                # Insert quest stages
                for stage in quest.get("stages", []):
                    self.db.insert_data("quest_stages", {
                        "id": stage.get("id", ""),
                        "quest_id": quest_id,
                        "title": stage.get("title", ""),
                        "description": stage.get("description", ""),
                        "notification_text": stage.get("notification_text", ""),
                        "status": stage.get("status", "NotStarted")
                    })
                    
                    # Insert quest objectives
                    for objective in stage.get("objectives", []):
                        self.db.insert_data("quest_objectives", {
                            "stage_id": stage["id"],
                            "objective_type": objective.get("type", "TASK"),
                            "objective_data": json.dumps({
                                "id": objective.get("id", ""),
                                "description": objective.get("description", ""),
                                "is_completed": objective.get("is_completed", False),
                                "is_optional": objective.get("is_optional", False),
                                "completion_events": objective.get("completion_events", [])
                            })
                        })
                        
                # Insert quest rewards
                rewards = quest.get("rewards", {})
                for reward_type, reward_data in rewards.items():
                    if reward_type == "relationship_changes":
                        for npc_id, value in reward_data.items():
                            self.db.insert_data("quest_rewards", {
                                "quest_id": quest_id,
                                "reward_type": "relationship",
                                "reward_data": json.dumps({
                                    "npc_id": npc_id,
                                    "value": value
                                })
                            })
                    elif reward_type == "experience":
                        self.db.insert_data("quest_rewards", {
                            "quest_id": quest_id,
                            "reward_type": "experience",
                            "reward_data": json.dumps({"value": reward_data})
                        })
                    
    def _migrate_items(self) -> None:
        """Migrate items from YAML to SQLite."""
        items_dir = os.path.join(self.yaml_dir, "items")
        if not os.path.exists(items_dir):
            print("Items directory not found, skipping item migration")
            return

        for filename in os.listdir(items_dir):
            if not filename.endswith(".yaml"):
                continue

            filepath = os.path.join(items_dir, filename)
            with open(filepath, "r") as f:
                data = yaml.safe_load(f)
                if not data or "items" not in data:
                    print(f"No items found in {filename}, skipping")
                    continue

                items_data = data["items"]
                # Handle both dictionary and list formats
                if isinstance(items_data, dict):
                    items_iter = items_data.items()
                else:
                    items_iter = enumerate(items_data)

                for item_id, item_data in items_iter:
                    # If item_data is a list item, use its name as ID if available
                    if isinstance(item_data, dict):
                        item_id = item_data.get("id", str(item_id))
                    else:
                        item_id = str(item_id)
                        item_data = {"id": item_id}

                    # Convert categories array to comma-separated string
                    categories = item_data.get("categories", [])
                    category_str = ",".join(categories) if categories else ""

                    # Determine flags based on categories
                    is_stackable = item_data.get("stackable", False)
                    is_consumable = "CONSUMABLE" in categories
                    is_equippable = "WEARABLE" in categories

                    # Insert item
                    self.db.insert_data("items", {
                        "id": item_id,
                        "name": item_data.get("name", ""),
                        "description": item_data.get("description", ""),
                        "category": category_str,
                        "value": item_data.get("value", 0),
                        "weight": item_data.get("weight", 0.0),
                        "is_stackable": is_stackable,
                        "is_consumable": is_consumable,
                        "is_equippable": is_equippable,
                        "slot": item_data.get("slot", ""),
                        "effects": json.dumps(item_data.get("effects", [])),
                        "style_rating": item_data.get("style_rating", 0),
                        "hidden_clues": json.dumps(item_data.get("hidden_clues", [])),
                        "hidden_usage": item_data.get("hidden_usage", ""),
                        "perception_difficulty": item_data.get("perception_difficulty", 0),
                        "set_id": item_data.get("set_id", "")
                    })
            
    def _migrate_item_sets(self) -> None:
        """Migrate item sets from YAML to SQLite."""
        # First try the dedicated item_sets.yaml file
        item_sets_path = os.path.join(self.yaml_dir, "item_sets.yaml")
        if os.path.exists(item_sets_path):
            item_sets = self._load_yaml(item_sets_path)
            self._process_item_sets(item_sets)
            
        # Then look for item sets in the items directory
        items_dir = os.path.join(self.yaml_dir, "items")
        if os.path.exists(items_dir):
            for filename in os.listdir(items_dir):
                if not filename.endswith(".yaml"):
                    continue
                    
                filepath = os.path.join(items_dir, filename)
                data = self._load_yaml(filepath)
                
                # Check if the file contains item sets
                if "item_sets" in data:
                    self._process_item_sets(data["item_sets"])
                    
    def _process_item_sets(self, item_sets: Dict[str, Any]) -> None:
        """Process and insert item sets into the database.
        
        Args:
            item_sets: Dictionary containing item set data
        """
        for set_id, set_data in item_sets.items():
            # Insert item set
            self.db.insert_data("item_sets", {
                "id": set_id,
                "name": set_data.get("name", ""),
                "description": set_data.get("description", "")
            })
            
            # Insert item set pieces
            for item_id in set_data.get("required_pieces", []):
                self.db.insert_data("item_set_pieces", {
                    "set_id": set_id,
                    "item_id": item_id
                })
                
            # Insert item set bonuses
            for bonus in set_data.get("set_bonus", []):
                self.db.insert_data("item_set_bonuses", {
                    "set_id": set_id,
                    "attribute": bonus.get("attribute", ""),
                    "value": bonus.get("value", 0.0),
                    "description": bonus.get("description", "")
                })
                
    def _migrate_character_archetypes(self) -> None:
        """Migrate character archetypes from YAML to SQLite."""
        archetypes_path = os.path.join(self.yaml_dir, "character_archetypes.yaml")
        if not os.path.exists(archetypes_path):
            return
            
        data = self._load_yaml(archetypes_path)
        archetypes = data.get("character_archetypes", {})
        
        for archetype_id, archetype_data in archetypes.items():
            # Insert archetype
            self.db.insert_data("character_archetypes", {
                "id": archetype_id,
                "name": archetype_data["name"],
                "description": archetype_data["description"]
            })
            
            # Insert archetype skills
            for skill_name, skill_value in archetype_data.get("starting_skills", {}).items():
                self.db.insert_data("archetype_skills", {
                    "archetype_id": archetype_id,
                    "skill_name": skill_name,
                    "skill_value": skill_value
                })
                
            # Insert archetype equipment
            for item_id in archetype_data.get("starting_equipment_ids", []):
                self.db.insert_data("archetype_equipment", {
                    "archetype_id": archetype_id,
                    "item_id": item_id
                })

def main():
    """Main function to run the migration."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate YAML game data to SQLite")
    parser.add_argument("yaml_dir", help="Directory containing YAML game data")
    parser.add_argument("--db", default="game_data.db", help="Path to SQLite database file")
    
    args = parser.parse_args()
    
    migrator = YamlToSqliteMigrator(args.yaml_dir, args.db)
    migrator.migrate()
    
if __name__ == "__main__":
    main() 