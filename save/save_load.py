"""
This module handles saving and loading game states.
"""
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from game.game_state import (Clue, GameState, Item, Player, QuestStatus,
                             TimeOfDay, Container, Wearable, ItemCategory, WearableSlot)

# The directory where saves will be stored
SAVE_DIR = "saves"


@dataclass
class SaveMetadata:
    """Metadata for saved games."""
    filename: str
    save_name: str
    timestamp: datetime
    current_location: str
    playtime: int  # in seconds


@dataclass
class SaveData:
    """Wrapper for game state and metadata."""
    game_state: GameState
    metadata: SaveMetadata


class GameStateEncoder(json.JSONEncoder):
    """Custom JSON encoder for GameState objects."""
    
    def default(self, obj):
        if isinstance(obj, GameState):
            return {
                "player": self.encode_player(obj.player),
                "current_location": obj.current_location,
                "previous_location": obj.previous_location,
                "inventory": [self.encode_item(item) for item in obj.inventory],
                "quest_log": {k: v.name for k, v in obj.quest_log.items()},
                "discovered_clues": [self.encode_clue(clue) for clue in obj.discovered_clues],
                "time_of_day": obj.time_of_day.name,
                "visited_locations": list(obj.visited_locations),
                "completed_objectives": {k: list(v) for k, v in obj.completed_objectives.items()},
                "active_quest_stages": obj.active_quest_stages,
                "taken_quest_branches": {k: list(v) for k, v in obj.taken_quest_branches.items()},
                "npc_interactions": obj.npc_interactions,
                "quest_items": {k: list(v) for k, v in obj.quest_items.items()},
                "relationship_values": obj.relationship_values,
                "location_items": {
                    loc_id: [self.encode_item(item) for item in items]
                    for loc_id, items in obj.location_items.items()
                },
                "location_containers": {
                    loc_id: {
                        container_id: [self.encode_item(item) for item in items]
                        for container_id, items in containers.items()
                    }
                    for loc_id, containers in obj.location_containers.items()
                }
            }
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, (QuestStatus, TimeOfDay)):
            return obj.name
        elif isinstance(obj, set):
            return list(obj)
        return super().default(obj)
    
    def encode_player(self, player: Player) -> Dict[str, Any]:
        """Encode player object."""
        return {
            "name": player.name,
            "skills": {
                "logic": player.skills.logic,
                "empathy": player.skills.empathy,
                "perception": player.skills.perception,
                "authority": player.skills.authority,
                "suggestion": player.skills.suggestion,
                "composure": player.skills.composure,
            },
            "inner_voices": player.inner_voices,
            "thought_cabinet": player.thought_cabinet,
            "health": player.health,
            "morale": player.morale,
        }
    
    def encode_item(self, item: Item) -> Dict[str, Any]:
        """Encode item object."""
        item_data = {
            "id": item.id,
            "name": item.name,
            "description": item.description,
            "categories": [cat.name if hasattr(cat, 'name') else str(cat) for cat in getattr(item, 'categories', [])],
            "weight": getattr(item, 'weight', 0.1),
            "value": getattr(item, 'value', 0),
            "stackable": getattr(item, 'stackable', False),
            "quantity": getattr(item, 'quantity', 1),
            "effects": getattr(item, 'effects', []),
        }
        
        # Add additional properties for special item types
        if hasattr(item, 'slot'):
            item_data["slot"] = item.slot.name if hasattr(item.slot, 'name') else str(item.slot)
        
        if hasattr(item, 'capacity'):
            item_data["capacity"] = item.capacity
            
        if hasattr(item, 'allowed_categories'):
            item_data["allowed_categories"] = item.allowed_categories
            
        if hasattr(item, 'is_obvious'):
            item_data["is_obvious"] = item.is_obvious
            
        if hasattr(item, 'perception_difficulty'):
            item_data["perception_difficulty"] = item.perception_difficulty
            
        if hasattr(item, 'hidden_clues'):
            item_data["hidden_clues"] = item.hidden_clues
            
        if hasattr(item, 'hidden_lore'):
            item_data["hidden_lore"] = item.hidden_lore
            
        if hasattr(item, 'hidden_usage'):
            item_data["hidden_usage"] = item.hidden_usage
            
        if hasattr(item, 'discovered'):
            item_data["discovered"] = item.discovered
            
        return item_data
    
    def encode_clue(self, clue: Clue) -> Dict[str, Any]:
        """Encode clue object."""
        return {
            "id": clue.id,
            "description": clue.description,
            "related_quest": clue.related_quest,
            "discovered": clue.discovered,
        }


def game_state_decoder(obj: Dict[str, Any]) -> Any:
    """Custom decoder for GameState objects."""
    if "player" in obj and "current_location" in obj:
        # It's a game state
        game_state = GameState()
        
        # Decode player
        player_data = obj["player"]
        game_state.player = Player(
            name=player_data.get("name", "Detective"),
            skills=Skills(
                logic=player_data["skills"].get("logic", 10),
                empathy=player_data["skills"].get("empathy", 10),
                perception=player_data["skills"].get("perception", 10),
                authority=player_data["skills"].get("authority", 10),
                suggestion=player_data["skills"].get("suggestion", 10),
                composure=player_data["skills"].get("composure", 10),
            ),
            inner_voices=player_data.get("inner_voices", []),
            thought_cabinet=player_data.get("thought_cabinet", []),
            health=player_data.get("health", 100),
            morale=player_data.get("morale", 100),
        )
        
        # Basic properties
        game_state.current_location = obj["current_location"]
        game_state.previous_location = obj["previous_location"]
        
        # Inventory
        game_state.inventory = [
            Item(**item_data) for item_data in obj.get("inventory", [])
        ]
        
        # Convert quest log strings back to enum
        for quest_id, status_str in obj.get("quest_log", {}).items():
            game_state.quest_log[quest_id] = QuestStatus[status_str]
        
        # Clues
        game_state.discovered_clues = [
            Clue(**clue_data) for clue_data in obj.get("discovered_clues", [])
        ]
        
        # Time of day
        game_state.time_of_day = TimeOfDay[obj.get("time_of_day", "Morning")]
        
        # Sets and dictionaries
        game_state.visited_locations = set(obj.get("visited_locations", []))
        
        # Convert lists back to sets in dictionaries
        for quest_id, objectives in obj.get("completed_objectives", {}).items():
            game_state.completed_objectives[quest_id] = set(objectives)
        
        game_state.active_quest_stages = obj.get("active_quest_stages", {})
        
        for quest_id, branches in obj.get("taken_quest_branches", {}).items():
            game_state.taken_quest_branches[quest_id] = set(branches)
        
        game_state.npc_interactions = obj.get("npc_interactions", {})
        
        for quest_id, items in obj.get("quest_items", {}).items():
            game_state.quest_items[quest_id] = set(items)
        
        game_state.relationship_values = obj.get("relationship_values", {})
        
        # Location items
        location_items = obj.get("location_items", {})
        for loc_id, items_data in location_items.items():
            if loc_id not in game_state.location_items:
                game_state.location_items[loc_id] = []
            
            for item_data in items_data:
                # Convert string categories to proper enum if needed
                if "categories" in item_data:
                    try:
                        item_data["categories"] = [ItemCategory[cat] if isinstance(cat, str) else cat 
                                                for cat in item_data["categories"]]
                    except KeyError:
                        # If we can't convert to enum, just use the strings
                        pass
                
                # Convert string slot to enum if needed
                if "slot" in item_data and isinstance(item_data["slot"], str):
                    try:
                        item_data["slot"] = WearableSlot[item_data["slot"]]
                    except KeyError:
                        pass
                
                # Create the appropriate item type
                if "capacity" in item_data:
                    item = Container(**item_data)
                elif "slot" in item_data:
                    item = Wearable(**item_data)
                else:
                    item = Item(**item_data)
                
                game_state.location_items[loc_id].append(item)
        
        # Location containers
        location_containers = obj.get("location_containers", {})
        for loc_id, containers_data in location_containers.items():
            if loc_id not in game_state.location_containers:
                game_state.location_containers[loc_id] = {}
            
            for container_id, items_data in containers_data.items():
                if container_id not in game_state.location_containers[loc_id]:
                    game_state.location_containers[loc_id][container_id] = []
                
                for item_data in items_data:
                    # Convert string categories to proper enum if needed
                    if "categories" in item_data:
                        try:
                            item_data["categories"] = [ItemCategory[cat] if isinstance(cat, str) else cat 
                                                    for cat in item_data["categories"]]
                        except KeyError:
                            # If we can't convert to enum, just use the strings
                            pass
                    
                    # Convert string slot to enum if needed
                    if "slot" in item_data and isinstance(item_data["slot"], str):
                        try:
                            item_data["slot"] = WearableSlot[item_data["slot"]]
                        except KeyError:
                            pass
                    
                    # Create the appropriate item type
                    if "capacity" in item_data:
                        item = Container(**item_data)
                    elif "slot" in item_data:
                        item = Wearable(**item_data)
                    else:
                        item = Item(**item_data)
                    
                    game_state.location_containers[loc_id][container_id].append(item)
        
        return game_state
    
    # Handle metadata separately
    if "timestamp" in obj and isinstance(obj["timestamp"], str):
        obj["timestamp"] = datetime.fromisoformat(obj["timestamp"])
    
    return obj


class SaveManager:
    """Manages saving and loading game states."""
    
    def __init__(self):
        """Initialize the save manager."""
        self.save_dir = SAVE_DIR
        
        # Create save directory if it doesn't exist
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
    
    def save_game(self, game_state: GameState, save_name: str, playtime: int) -> None:
        """Save current game state with a custom name."""
        # Create filename from save name (sanitize to be safe)
        sanitized_name = re.sub(r'[\\/*?:"<>|]', "_", save_name)
        sanitized_name = sanitized_name.replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"{sanitized_name}-{timestamp}.save"
        
        save_path = os.path.join(self.save_dir, filename)
        
        # Create metadata
        metadata = SaveMetadata(
            filename=filename,
            save_name=save_name,
            timestamp=datetime.now(),
            current_location=game_state.current_location,
            playtime=playtime
        )
        
        # Bundle state and metadata
        save_data = SaveData(
            game_state=game_state,
            metadata=metadata
        )
        
        # Serialize to JSON
        with open(save_path, 'w', encoding='utf-8') as file:
            json.dump(save_data, file, cls=GameStateEncoder, indent=2)
    
    def load_game(self, name_or_filename: str) -> SaveData:
        """Load a game from filename or save name."""
        # First try direct filename approach
        direct_path = os.path.join(self.save_dir, name_or_filename)
        
        if os.path.exists(direct_path):
            # Read file contents
            with open(direct_path, 'r', encoding='utf-8') as file:
                contents = file.read()
            
            # Deserialize JSON
            save_data = json.loads(contents, object_hook=game_state_decoder)
            return save_data
        
        # If direct path doesn't exist, try to find by save name
        saves = self.list_saves()
        
        # Try to find a save with matching save_name
        for save in saves:
            if save.save_name.lower() == name_or_filename.lower():
                # Found matching save name, read that file
                return self.load_game(save.filename)
        
        # No matching save found
        raise FileNotFoundError(f"No save file found with name or filename '{name_or_filename}'")
    
    def list_saves(self) -> List[SaveMetadata]:
        """Get list of all saves with metadata."""
        saves = []
        
        # List all .save files in the save directory
        if not os.path.exists(self.save_dir):
            return saves
        
        for filename in os.listdir(self.save_dir):
            if filename.endswith('.save'):
                path = os.path.join(self.save_dir, filename)
                try:
                    metadata = self.get_save_metadata(path)
                    saves.append(metadata)
                except Exception as e:
                    print(f"Error loading save metadata from {filename}: {e}")
        
        # Sort by timestamp (newest first)
        saves.sort(key=lambda x: x.timestamp, reverse=True)
        
        return saves
    
    def delete_save(self, filename: str) -> None:
        """Delete a save file."""
        save_path = os.path.join(self.save_dir, filename)
        if os.path.exists(save_path):
            os.remove(save_path)
        else:
            raise FileNotFoundError(f"Save file not found: {filename}")
    
    def get_save_metadata(self, path: str) -> SaveMetadata:
        """Extract metadata from a save file."""
        with open(path, 'r', encoding='utf-8') as file:
            contents = file.read()
        
        # Extract just the metadata portion
        save_data = json.loads(contents, object_hook=game_state_decoder)
        
        # Handle old save format or invalid files
        if not hasattr(save_data, 'metadata') or not save_data.metadata:
            # Try to generate metadata from filename
            filename = os.path.basename(path)
            match = re.match(r'(.+)-(\d{8}-\d{6})\.save', filename)
            
            if match:
                save_name = match.group(1).replace('_', ' ')
                timestamp_str = match.group(2)
                try:
                    timestamp = datetime.strptime(timestamp_str, "%Y%m%d-%H%M%S")
                except ValueError:
                    timestamp = datetime.now()
                
                return SaveMetadata(
                    filename=filename,
                    save_name=save_name,
                    timestamp=timestamp,
                    current_location="unknown",
                    playtime=0
                )
            
            # Last resort
            return SaveMetadata(
                filename=filename,
                save_name="Unknown Save",
                timestamp=datetime.fromtimestamp(os.path.getmtime(path)),
                current_location="unknown",
                playtime=0
            )
        
        return save_data.metadata
    
    def save_exists(self, filename: str) -> bool:
        """Check if a save exists."""
        return os.path.exists(os.path.join(self.save_dir, filename))
    
    def quick_save(self, game_state: GameState, playtime: int) -> None:
        """Create a quick save with an automatic name."""
        self.save_game(game_state, "QuickSave", playtime)
    
    def get_save_by_index(self, index: int) -> SaveData:
        """Get a save by index number (from the list_saves output)."""
        saves = self.list_saves()
        
        # Check if index is valid
        if index == 0 or index > len(saves):
            raise IndexError(f"Invalid save index: {index}. Valid range is 1-{len(saves)}")
        
        # Index is 1-based in the UI, so subtract 1
        save = saves[index - 1]
        return self.load_game(save.filename)
    
    def quick_load(self) -> SaveData:
        """Load the most recent quick save."""
        saves = self.list_saves()
        
        # Find all quicksaves
        quick_saves = [save for save in saves if save.save_name.lower() == "quicksave"]
        
        # Return the most recent one
        if quick_saves:
            return self.load_game(quick_saves[0].filename)
        
        raise FileNotFoundError("No quick save found")
    
    @staticmethod
    def format_playtime(seconds: int) -> str:
        """Format save time as a human readable string."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours == 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{hours}h {minutes}m {secs}s"
