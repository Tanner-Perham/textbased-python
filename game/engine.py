"""
Core game engine that processes player input and coordinates game systems.
"""

import random
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from config.config_loader import GameConfig, ConfigLoader
from dialogue.manager import DialogueManager
from game.game_state import GameState, QuestStatus
from game.inventory import Container, Item, ItemCategory, Wearable, WearableSlot
from quest.quest_manager import QuestManager
from save.save_load import SaveManager
from ui.dialogue_ui import DialogueMode
from dialogue.response import DialogueResponse
from character.character_creator import create_character


class GameEngine:
    """
    The core game engine that coordinates all game systems and processes player input.
    """

    def __init__(self, config: GameConfig):
        """Initialize the game engine with configuration."""
        self.config = config
        self.current_location = config.game_settings.starting_location
        self.previous_location = None
        self.game_state = GameState()
        self.game_state.current_location = self.current_location
        self.game_state.config = config  # Store config in game state for access in other modules

        # Initialize quest manager with game state
        self.quest_manager = QuestManager(self.game_state)

        # Add quests from config to game state
        for quest in config.quests.values():
            self.game_state.add_quest(quest)

        # Initialize save manager
        self.save_manager = SaveManager()

        # Dialogue system (will be set externally)
        self.dialogue_handler: Optional[DialogueManager] = None

        # Notification system
        self.pending_notifications = []
        self.notification_timer = time.time()
        self.show_notification_indicator = False

        # Start time for playtime tracking
        self.start_time = time.time()
        
        # Reference to the UI application, set externally
        self.app = None
        
        # Flag to track if character creation has been completed
        self.character_created = False
        
        # Load location items from config
        self._load_location_items()

    def _load_location_items(self) -> None:
        """Load items from the config into the game state's locations."""
        print("Loading location items...")
        for location_id, location in self.config.locations.items():
            # Load regular items in the location
            if hasattr(location, 'location_items') and location.location_items:
                print(f"  Found {len(location.location_items)} items in location {location_id}")
                for item_data in location.location_items:
                    # Create a copy of the item to avoid modifying the config
                    # First check if this is a reference to an existing item
                    if 'id' in item_data and item_data['id'] in self.config.items:
                        # Use the existing item as a template
                        template_item = self.config.items[item_data['id']]
                        # Create a deep copy of the item
                        if isinstance(template_item, Container):
                            item_copy = Container(
                                id=template_item.id,
                                name=template_item.name,
                                description=template_item.description,
                                categories=template_item.categories,
                                weight=template_item.weight,
                                capacity=template_item.capacity,
                                allowed_categories=template_item.allowed_categories
                            )
                        elif isinstance(template_item, Wearable):
                            item_copy = Wearable(
                                id=template_item.id,
                                name=template_item.name,
                                description=template_item.description,
                                categories=template_item.categories,
                                weight=template_item.weight,
                                slot=template_item.slot,
                                effects=template_item.effects,
                                set_id=template_item.set_id
                            )
                        else:
                            item_copy = Item(
                                id=template_item.id,
                                name=template_item.name,
                                description=template_item.description,
                                categories=template_item.categories,
                                weight=template_item.weight,
                                stackable=getattr(template_item, 'stackable', False),
                                quantity=getattr(template_item, 'quantity', 1)
                            )
                        
                        # Add attributes from the location-specific item data that might override defaults
                        if 'is_obvious' in item_data:
                            item_copy.is_obvious = item_data['is_obvious']
                        else:
                            item_copy.is_obvious = True
                            
                        if 'perception_difficulty' in item_data:
                            item_copy.perception_difficulty = item_data['perception_difficulty']
                            
                        if 'hidden_clues' in item_data:
                            item_copy.hidden_clues = item_data['hidden_clues']
                            
                    else:
                        # Create a new item from scratch
                        categories = []
                        if 'categories' in item_data:
                            categories = [ItemCategory[cat] if isinstance(cat, str) else cat 
                                        for cat in item_data['categories']]
                                        
                        item_copy = Item(
                            id=item_data['id'],
                            name=item_data['name'],
                            description=item_data['description'],
                            categories=categories,
                            weight=item_data.get('weight', 0.1),
                            stackable=item_data.get('stackable', False),
                            quantity=item_data.get('quantity', 1)
                        )
                        
                        # Add perception difficulty if applicable
                        if 'perception_difficulty' in item_data:
                            item_copy.perception_difficulty = item_data['perception_difficulty']
                        
                        # Add obviousness flag
                        if 'is_obvious' in item_data:
                            item_copy.is_obvious = item_data['is_obvious']
                        else:
                            item_copy.is_obvious = True
                            
                        # Add hidden clues if applicable
                        if 'hidden_clues' in item_data:
                            item_copy.hidden_clues = item_data['hidden_clues']
                        
                        # Add hidden lore if applicable
                        if 'hidden_lore' in item_data:
                            item_copy.hidden_lore = item_data['hidden_lore']
                            
                        # Add hidden usage if applicable
                        if 'hidden_usage' in item_data:
                            item_copy.hidden_usage = item_data['hidden_usage']
                    
                    # Add to the location
                    self.game_state.add_item_to_location(location_id, item_copy)
            
            # Load containers and their contents
            if hasattr(location, 'location_containers') and location.location_containers:
                for container_data in location.location_containers:
                    # First check if this is a reference to an existing container
                    if 'id' in container_data and container_data['id'] in self.config.items:
                        template_container = self.config.items[container_data['id']]
                        if isinstance(template_container, Container):
                            container = Container(
                                id=template_container.id,
                                name=template_container.name,
                                description=template_container.description,
                                categories=template_container.categories,
                                weight=template_container.weight,
                                capacity=template_container.capacity,
                                allowed_categories=template_container.allowed_categories
                            )
                        else:
                            # Create a new container if the template isn't a Container
                            container = Container(
                                id=container_data['id'],
                                name=container_data['name'],
                                description=container_data['description'],
                                categories=[ItemCategory.CONTAINER],
                                weight=container_data.get('weight', 1.0),
                                capacity=container_data.get('capacity', 10.0),
                                allowed_categories=container_data.get('allowed_categories')
                            )
                    else:
                        # Create a new container from scratch
                        categories = []
                        if 'categories' in container_data:
                            categories = [ItemCategory[cat] if isinstance(cat, str) else cat 
                                        for cat in container_data['categories']]
                                        
                        container = Container(
                            id=container_data['id'],
                            name=container_data['name'],
                            description=container_data['description'],
                            categories=categories or [ItemCategory.CONTAINER],
                            weight=container_data.get('weight', 1.0),
                            capacity=container_data.get('capacity', 10.0),
                            allowed_categories=container_data.get('allowed_categories')
                        )
                    
                    # Add container to the location
                    self.game_state.add_item_to_location(location_id, container)
                    
                    # Add contents to the container
                    if 'contents' in container_data and container_data['contents']:
                        for content_data in container_data['contents']:
                            if 'id' in content_data and content_data['id'] in self.config.items:
                                # Use existing item as template
                                template_item = self.config.items[content_data['id']]
                                # Create a deep copy
                                if isinstance(template_item, Item):
                                    content_item = Item(
                                        id=template_item.id,
                                        name=template_item.name,
                                        description=template_item.description,
                                        categories=template_item.categories,
                                        weight=template_item.weight,
                                        stackable=getattr(template_item, 'stackable', False),
                                        quantity=getattr(template_item, 'quantity', 1)
                                    )
                                else:
                                    # Create generic item if template isn't an Item
                                    content_item = Item(
                                        id=content_data['id'],
                                        name=content_data['name'],
                                        description=content_data['description'],
                                        categories=[],
                                        weight=content_data.get('weight', 0.1),
                                        stackable=content_data.get('stackable', False),
                                        quantity=content_data.get('quantity', 1)
                                    )
                            else:
                                # Create from scratch
                                categories = []
                                if 'categories' in content_data:
                                    categories = [ItemCategory[cat] if isinstance(cat, str) else cat 
                                                for cat in content_data['categories']]
                                                
                                content_item = Item(
                                    id=content_data['id'],
                                    name=content_data['name'],
                                    description=content_data['description'],
                                    categories=categories,
                                    weight=content_data.get('weight', 0.1),
                                    stackable=content_data.get('stackable', False),
                                    quantity=content_data.get('quantity', 1)
                                )
                            
                            # Add to the container
                            self.game_state.add_item_to_location_container(location_id, container.id, content_item)

    def start_game(self) -> None:
        """Start the game after character creation."""
        self.character_created = True
        
        # Start the main quest automatically
        main_quests = [quest for quest in self.config.quests.values() if quest.is_main_quest]
        if main_quests:
            self.start_quest(main_quests[0].id)
            
        # Set the starting location
        self.navigate_to(self.config.game_settings.starting_location)
            
        # Give starting inventory items if defined in config
        if hasattr(self.config.game_settings, 'starting_inventory'):
            for item_def in self.config.game_settings.starting_inventory:
                # If item_def is a string, it's directly the item ID
                if isinstance(item_def, str):
                    item_id = item_def
                # Otherwise, it's a dictionary with an 'id' key
                else:
                    item_id = item_def.get('id')
                
                if item_id and item_id in self.config.items:
                    self.game_state.add_item(self.config.items[item_id])

    def start_character_creation(self) -> None:
        """Start the character creation process."""
        create_character(self)

    def current_location_info(self) -> str:
        """Return the current location name."""
        return self.current_location

    def process_input(self, input_text: str) -> str:
        """Process player input and return response."""
        # Normalize input: trim and convert to lowercase
        input_text = input_text.strip().lower()

        # Split input into words
        parts = input_text.split()

        if not parts:
            return "Please enter a command. Type 'help' for a list of commands."

        # Add quit command handling at the start
        if parts[0] in ["quit"]:
            return "__quit__"

        # Check for quest updates and get notifications
        self._check_quest_updates()
        notifications = self._get_notifications()
        
        # Process commands
        if parts[0] == "look" and len(parts) > 1 and parts[1] == "around":
            response = self._handle_look_around()
            return self._format_response(response, notifications)

        elif parts[0] == "examine" and len(parts) > 1:
            item_name = " ".join(parts[1:])
            response = self._handle_examine_item(item_name)
            return self._format_response(response, notifications)

        elif parts[0] == "look" and len(parts) > 2 and parts[1] == "at":
            item_name = " ".join(parts[2:])
            response = self._handle_examine_item(item_name)
            return self._format_response(response, notifications)

        elif parts[0] == "search" and len(parts) > 1:
            # Handle search <area> command
            area_name = " ".join(parts[1:])
            response = self._handle_search_area(area_name)
            return self._format_response(response, notifications)

        elif parts[0] == "search" and len(parts) == 1:
            # Handle general search command without specific area
            response = self._handle_search()
            return self._format_response(response, notifications)

        elif parts[0] in ["talk", "speak"] and len(parts) > 1:
            npc_parts = parts[1:]
            connecting_words = ["to", "with", "the", "about"]
            npc_name = " ".join(word for word in npc_parts if word.lower() not in connecting_words)
            if not npc_name:
                return "Who would you like to talk to?"
            
            response = self._handle_talk_to_npc(npc_name)
            return self._format_response(response, notifications)

        elif parts[0] in ["go", "walk", "move", "head"]:
            direction_parts = parts[1:]
            connecting_words = ["to", "the", "towards", "into", "inside"]
            direction = " ".join(word for word in direction_parts if word.lower() not in connecting_words)
            
            if not direction:
                return "Where would you like to go?"
                
            response = self._handle_movement(direction)
            return self._format_response(response, notifications)

        elif parts[0] == "back":
            response = self._handle_movement("back")
            return self._format_response(response, notifications)

        elif parts[0] in ["take", "pick", "grab", "get"] and len(parts) > 1:
            # Handle 'pick up' command format
            if parts[0] == "pick" and len(parts) > 2 and parts[1] == "up":
                item_name = " ".join(parts[2:])
            # Handle 'take from container' format
            elif parts[0] == "take" and len(parts) > 3 and "from" in parts:
                from_index = parts.index("from")
                item_name = " ".join(parts[1:from_index])
                container_name = " ".join(parts[from_index+1:])
                return self._format_response(self._handle_take_from_location_container(item_name, container_name), notifications)
            else:
                item_name = " ".join(parts[1:])
            
            response = self._handle_take_item(item_name)
            return self._format_response(response, notifications)

        elif parts[0] in ["drop", "put", "place", "leave"] and len(parts) > 1:
            # Handle 'put in container' format in location
            if parts[0] == "put" and len(parts) > 3 and "in" in parts:
                in_index = parts.index("in")
                item_name = " ".join(parts[1:in_index])
                container_name = " ".join(parts[in_index+1:])
                return self._format_response(self._handle_put_in_location_container(item_name, container_name), notifications)
            else:
                item_name = " ".join(parts[1:])
                
            response = self._handle_drop_item(item_name)
            return self._format_response(response, notifications)

        elif parts[0] in ["exits", "directions", "connections"] or (
            len(parts) >= 3
            and parts[0] == "where"
            and parts[1] == "can"
            and parts[2] == "i"
            and parts[3] == "go"
        ):
            response = self._handle_show_exits()
            return self._format_response(response, notifications)

        elif parts[0] == "save":
            save_name = " ".join(parts[1:]) if len(parts) > 1 else ""
            response = self._handle_save_command(save_name)
            return self._format_response(response, notifications)

        elif parts[0] == "quicksave" or (
            len(parts) == 2 and parts[0] == "quick" and parts[1] == "save"
        ):
            response = self._handle_quick_save_command()
            return self._format_response(response, notifications)

        elif parts[0] == "load" and len(parts) > 1:
            load_identifier = " ".join(parts[1:])
            response = self._handle_load_command(load_identifier)
            return self._format_response(response, notifications)

        elif parts[0] == "quickload" or (
            len(parts) == 2 and parts[0] == "quick" and parts[1] == "load"
        ):
            response = self._handle_quick_load_command()
            return self._format_response(response, notifications)

        elif parts[0] == "saves" or (
            len(parts) == 2 and parts[0] == "list" and parts[1] == "saves"
        ):
            response = self._handle_list_saves_command()
            return self._format_response(response, notifications)

        elif parts[0] in ["quests", "journal"] or (
            len(parts) == 2 and parts[0] == "quest" and parts[1] == "log"
        ):
            response = self._handle_show_quests()
            return self._format_response(response, notifications)

        # Inventory commands
        elif parts[0] in ["inventory", "inv", "i"]:
            response = self._handle_show_inventory()
            return self._format_response(response, notifications)

        elif parts[0] in ["equip", "wear", "put on", "don"] and len(parts) > 1:
            item_name = " ".join(parts[1:])
            response = self._handle_equip_item(item_name)
            return self._format_response(response, notifications)

        elif parts[0] == "unequip" and len(parts) > 1:
            slot_name = " ".join(parts[1:])
            response = self._handle_unequip_item(slot_name)
            return self._format_response(response, notifications)

        elif parts[0] == "use" and len(parts) > 1:
            item_name = " ".join(parts[1:])
            response = self._handle_use_item(item_name)
            return self._format_response(response, notifications)

        elif parts[0] == "open" and len(parts) > 1:
            container_name = " ".join(parts[1:])
            response = self._handle_open_container(container_name)
            return self._format_response(response, notifications)

        elif parts[0] == "put" and len(parts) > 3 and parts[2] == "in":
            item_name = parts[1]
            container_name = " ".join(parts[3:])
            response = self._handle_put_in_container(item_name, container_name)
            return self._format_response(response, notifications)

        elif parts[0] == "take" and len(parts) > 3 and parts[2] == "from":
            item_name = parts[1]
            container_name = " ".join(parts[3:])
            response = self._handle_take_from_container(item_name, container_name)
            return self._format_response(response, notifications)

        elif len(parts) == 3 and parts[0] == "quest" and parts[1] == "track":
            quest_id = parts[2]
            response = self._handle_track_quest(quest_id)
            return self._format_response(response, notifications)

        elif len(parts) == 3 and parts[0] == "quest" and parts[1] == "info":
            quest_id = parts[2]
            response = self._handle_quest_info(quest_id)
            return self._format_response(response, notifications)

        elif len(parts) == 2 and parts[0] == "active" and parts[1] == "quests":
            response = self._handle_show_active_quests()
            return self._format_response(response, notifications)

        elif parts[0] == "help":
            response = self._help_command()
            return self._format_response(response, notifications)

        else:
            response = "Unknown command. Type 'help' for a list of commands."
            return self._format_response(response, notifications)

    def _format_response(self, response: str, notifications: List[str]) -> str:
        """Format the response with any pending notifications."""
        if notifications:
            notification_text = "\n".join(notifications)
            return f"{notification_text}\n\n{response}"
        return response

    def _get_notifications(self) -> List[str]:
        """Get and clear any pending notifications."""
        notifications = self.quest_manager.get_active_notifications()
        self.quest_manager.clear_old_notifications(0)  # Clear all notifications
        return [notification.message for notification in notifications]

    def _check_quest_updates(self) -> None:
        """Check for quest updates and process them."""
        self.quest_manager.check_all_quest_updates()

        # Check for new notifications
        notifications = self.quest_manager.get_active_notifications()
        if notifications:
            # Set notification indicator
            self.show_notification_indicator = True

            # Add newest notification to pending display
            if notifications and notifications[0].is_new:
                self.pending_notifications.append(notifications[0].message)
                self.notification_timer = time.time()

            # Reset notification age timer
            self.quest_manager.clear_old_notifications(300)  # 5 minutes

    def start_quest(self, quest_id: str) -> bool:
        """Start a quest by ID."""
        return self.quest_manager.start_quest(quest_id)

    def fail_quest(self, quest_id: str) -> None:
        """Fail a quest by ID."""
        self.quest_manager.fail_quest(quest_id, self.game_state)

    def get_playtime(self) -> int:
        """Get total playtime in seconds."""
        return int(time.time() - self.start_time)

    def _handle_look_around(self) -> str:
        """Handle the 'look around' command."""
        location = self.config.locations.get(self.current_location)
        if not location:
            return "You look around but see nothing of interest."

        response = location.description

        # Find NPCs in the current location
        npcs_here = [
            npc
            for npc in self.config.npcs.values()
            if npc.location == self.current_location
        ]

        if npcs_here:
            response += "\n\nYou see:"
            for npc in npcs_here:
                response += f"\n- {npc.name}"

        # Add obvious items in the location
        obvious_items = self.game_state.get_obvious_items(self.current_location)
        if obvious_items:
            if not npcs_here:  # Only add the "You see:" header if we didn't already add it for NPCs
                response += "\n\nYou see:"
            for item in obvious_items:
                if item.quantity > 1:
                    response += f"\n- {item.name} (x{item.quantity})"
                else:
                    response += f"\n- {item.name}"

        # Add connected locations
        if location.connected_locations:
            response += "\n\nFrom here, you can see:"
            for loc_id in location.connected_locations:
                if connected_loc := self.config.locations.get(loc_id):
                    response += f"\n- The {connected_loc.name}"

        return response

    def _handle_movement(self, direction: str) -> str:
        """Handle movement commands."""
        if not direction:
            return "You need to specify a direction to move."
        current_location = self.config.locations.get(self.current_location)
        if not current_location:
            return "ERROR: Current location not found."

        # Find target location
        target_location_id = None

        # Handle "back" command
        if direction == "back" and self.previous_location:
            target_location_id = self.previous_location

        # Try to match direction with a connected location
        else:
            target_location_id = self._find_closest_location_match(
                direction, current_location.connected_locations
            )
            print(f"Target location ID: {target_location_id}")

            if not target_location_id:
                valid_exits = [
                    self.config.locations[loc_id].name
                    for loc_id in current_location.connected_locations
                    if loc_id in self.config.locations
                ]
                if valid_exits:
                    return f"You can't go to the {direction} from here. Valid exits are: {', '.join(valid_exits)}."
                else:
                    return f"You can't go to the {direction} from here. There are no valid exits."

        # Move to new location
        # Get description
        new_location = self.config.locations.get(target_location_id)
        if new_location is None:
            return "You move, but the destination seems to be missing. Please check the game configuration."
        self.previous_location = self.current_location
        self.current_location = target_location_id
        return self._get_movement_response(new_location.name, new_location.description)

    def _find_closest_location_match(self, partial: str, connected_locations: List[str]) -> Optional[str]:
        """Find the closest matching location ID or name."""
        matches = []
        for loc_id in connected_locations:
            connected_loc = self.config.locations.get(loc_id)
            if not connected_loc:
                continue

            # Match by partial name or ID
            if (
                partial.lower() in connected_loc.name.lower()
                or partial.lower() in loc_id.lower()
            ):
                matches.append(loc_id)

        if len(matches) > 1:
            matching_names = [self.config.locations[loc_id].name for loc_id in matches]
            raise ValueError(
                f"Ambiguous direction: multiple locations match '{partial}'. Matches: {', '.join(matching_names)}. Please be more specific."
            )
        elif len(matches) == 1:
            return matches[0]
        return None

    def _handle_show_exits(self) -> str:
        """Handle the 'exits' command."""
        current_location = self.config.locations.get(self.current_location)
        if not current_location:
            return "ERROR: Current location not found."

        if not current_location.connected_locations:
            return "There are no obvious exits from here."

        # Collect names of connected locations
        location_names = []
        for loc_id in current_location.connected_locations:
            if connected_loc := self.config.locations.get(loc_id):
                location_names.append(connected_loc.name)

        # Format list naturally
        if not location_names:
            return "There are no obvious exits from here."

        if len(location_names) == 1:
            return f"From here, you can go to the {location_names[0]}."

        last = location_names.pop()
        return f"From here, you can go to the {', the '.join(location_names)} or the {last}."

    def _handle_save_command(self, save_name: str) -> str:
        """Handle the 'save' command."""
        # Update game state with current location before saving
        self.game_state.current_location = self.current_location
        self.game_state.previous_location = self.previous_location

        # Use provided name or "Unnamed Save"
        name = save_name if save_name else "Unnamed Save"

        try:
            self.save_manager.save_game(self.game_state, name, self.get_playtime())
            return f"Game saved as '{name}'."
        except Exception as e:
            return f"Failed to save game: {e}"

    def _handle_quick_save_command(self) -> str:
        """Handle the 'quicksave' command."""
        # Update game state with current location before saving
        self.game_state.current_location = self.current_location
        self.game_state.previous_location = self.previous_location

        try:
            self.save_manager.quick_save(self.game_state, self.get_playtime())
            return "Game quick-saved."
        except Exception as e:
            return f"Failed to quick-save game: {e}"

    def _handle_load_command(self, load_identifier: str) -> str:
        """Handle the 'load' command."""
        try:
            # Try to parse as a number (index)
            index = int(load_identifier)
            save_data = self.save_manager.get_save_by_index(index)

            # Update game state
            self.game_state = save_data.game_state

            # Update location
            self.current_location = self.game_state.current_location
            self.previous_location = self.game_state.previous_location

            return f"Loaded save #{index}: {save_data.metadata.save_name}"

        except ValueError:
            # Not a number, try as name or filename
            try:
                save_data = self.save_manager.load_game(load_identifier)

                # Update game state
                self.game_state = save_data.game_state

                # Update location
                self.current_location = self.game_state.current_location
                self.previous_location = self.game_state.previous_location

                return f"Loaded save: {save_data.metadata.save_name}"
            except Exception as e:
                return f"Failed to load game: {e}"

    def _handle_quick_load_command(self) -> str:
        """Handle the 'quickload' command."""
        try:
            save_data = self.save_manager.quick_load()

            # Update game state
            self.game_state = save_data.game_state

            # Update location
            self.current_location = self.game_state.current_location
            self.previous_location = self.game_state.previous_location

            return "Quick save loaded successfully."
        except Exception as e:
            return f"Failed to quick-load game: {e}"

    def _handle_list_saves_command(self) -> str:
        """Handle the 'saves' command."""
        try:
            saves = self.save_manager.list_saves()

            if not saves:
                return "No saved games found."

            response = "Saved games:\n"

            for i, save in enumerate(saves, 1):
                playtime = self.save_manager.format_playtime(save.playtime)
                response += f"{i}. {save.save_name} - {save.timestamp:%Y-%m-%d %H:%M} - {save.current_location} - {playtime}\n"

            response += "\nTo load a game, type 'load <save name>'"
            return response

        except Exception as e:
            return f"Failed to list saves: {e}"

    def _handle_show_quests(self) -> str:
        """Handle the quest log command."""
        active_quests = self.quest_manager.game_state.get_active_quests()
        completed_quests = self.quest_manager.game_state.get_completed_quests()
        failed_quests = self.quest_manager.game_state.get_failed_quests()

        response = "Quest Log:\n"

        if active_quests:
            response += "Active Quests:\n"
            for quest in active_quests:
                response += f"- {quest.title}: {quest.description}\n"
                # Get active stage ID using game_state method
                active_stage_id = self.game_state.get_active_stage(quest.id)
                if active_stage_id:
                    # Find the stage with the active stage ID
                    current_stage = next((stage for stage in quest.stages 
                                        if stage.id == active_stage_id), None)
                    if current_stage:
                        response += f"  Current Stage: {current_stage.title}\n"
                        response += f"  {current_stage.description}\n"
                        
                        # Show objectives with completion status
                        incomplete_objectives = []
                        for obj in current_stage.objectives:
                            is_completed = self.quest_manager.is_objective_completed(quest.id, obj.get('id', ''))
                            status = "✓" if is_completed else "○"
                            optional = "(Optional) " if obj.get("is_optional", False) else ""
                            response += f"  {status} {optional}{obj.get('description', '')}\n"
                            
                            # Track incomplete objectives for next steps
                            if not is_completed and not obj.get("is_optional", False):
                                incomplete_objectives.append(obj)
                        
                        # Show next objective(s)
                        if incomplete_objectives:
                            response += "  Next Steps:\n"
                            for obj in incomplete_objectives[:2]:  # Show up to 2 next objectives
                                response += f"  → {obj.get('description', '')}\n"
                response += "\n"

        if completed_quests:
            response += "Completed Quests:\n"
            for quest in completed_quests:
                response += f"- {quest.title}: {quest.description[:50]}...\n"
            response += "\n"

        if failed_quests:
            response += "Failed Quests:\n"
            for quest in failed_quests:
                response += f"- {quest.title}: {quest.description[:50]}...\n"
            response += "\n"

        if not active_quests and not completed_quests and not failed_quests:
            response += "No quests available.\n"

        return response

    def _handle_track_quest(self, quest_id: str) -> str:
        """Handle tracking a specific quest."""
        quest = self.quest_manager.get_quest(quest_id)
        if not quest:
            return f"Quest '{quest_id}' not found."

        if quest_id not in self.game_state.quest_log:
            return f"Quest '{quest.title}' is not active."

        # Get active stage ID using game_state method
        active_stage_id = self.game_state.get_active_stage(quest_id)
        if not active_stage_id:
            return f"Quest '{quest.title}' has no active stage."
            
        # Find the stage with the active stage ID
        current_stage = next((stage for stage in quest.stages 
                            if stage.id == active_stage_id), None)
        if not current_stage:
            return f"Quest '{quest.title}' has no active stage."

        response = f"Tracking Quest: {quest.title}\n"
        response += f"Current Stage: {current_stage.title}\n"
        response += f"{current_stage.description}\n\n"
        response += "Objectives:\n"
        for obj in current_stage.objectives:
            is_completed = self.quest_manager.is_objective_completed(quest_id, obj.get('id', ''))
            status = "✓" if is_completed else "○"
            optional = "(Optional) " if obj.get("is_optional", False) else ""
            response += f"{status} {optional}{obj.get('description', '')}\n"

        return response

    def _handle_quest_info(self, quest_id: str) -> str:
        """Handle showing detailed information about a quest."""
        quest = self.quest_manager.get_quest(quest_id)
        if not quest:
            return f"Quest '{quest_id}' not found."

        response = f"Quest: {quest.title}\n"
        response += f"Type: {'Main Quest' if quest.is_main_quest else 'Side Quest'}\n"
        response += f"Status: {self.game_state.get_quest_status(quest_id).name}\n\n"
        response += f"Description:\n{quest.description}\n\n"

        if quest.stages:
            response += "Stages:\n"
            for stage in quest.stages:
                # Get a marker to show the current active stage
                active_marker = ""
                active_stage_id = self.game_state.get_active_stage(quest_id)
                if active_stage_id and stage.id == active_stage_id:
                    active_marker = " [CURRENT]"
                    
                response += f"- {stage.title}{active_marker}\n"
                response += f"  {stage.description}\n"
                if stage.objectives:
                    response += "  Objectives:\n"
                    for obj in stage.objectives:
                        is_completed = self.game_state.is_objective_completed(quest_id, obj.get('id', ''))
                        status = "✓" if is_completed else "○"
                        optional = "(Optional) " if obj.get("is_optional", False) else ""
                        response += f"  {status} {optional}{obj.get('description', '')}\n"
                response += "\n"

        return response

    def _handle_show_active_quests(self) -> str:
        """Handle showing only active quests."""
        active_quests = self.quest_manager.get_active_quests()
        if not active_quests:
            return "No active quests."

        response = "Active Quests:\n\n"
        for quest in active_quests:
            response += f"- {quest.title}\n"
            # Get active stage ID using game_state method
            active_stage_id = self.game_state.get_active_stage(quest.id)
            if active_stage_id:
                # Find the stage with the active stage ID
                current_stage = next((stage for stage in quest.stages 
                                    if stage.id == active_stage_id), None)
                if current_stage:
                    response += f"  Current Stage: {current_stage.title}\n"
                    response += f"  {current_stage.description}\n"
                    for obj in current_stage.objectives:
                        is_completed = self.quest_manager.is_objective_completed(quest.id, obj.get('id', ''))
                        status = "✓" if is_completed else "○"
                        optional = "(Optional) " if obj.get("is_optional", False) else ""
                        response += f"  {status} {optional}{obj.get('description', '')}\n"
            response += "\n"

        return response

    def _get_movement_response(self, location_name: str, description: str) -> str:
        """Get a randomized response for moving to a new location."""
        responses = [
            f"You make your way to the {location_name}.\n\n{description}",
            f"You head over to the {location_name}.\n\n{description}",
            f"You arrive at the {location_name}.\n\n{description}",
            f"You enter the {location_name}.\n\n{description}",
        ]

        return random.choice(responses)

    def _help_command(self) -> str:
        """Display help information."""
        return "\n".join(
            [
                "Available commands:",
                "  look around - Observe your surroundings",
                "  examine <item> or look at <item> - Examine an item closely, possibly discovering hidden details",
                "  talk to <NPC> - Engage in conversation with an NPC",
                "  go/walk <direction> - Move in the specified direction",
                "  take/pick up <item> - Pick up an item from the current location",
                "  take <item> from <container> - Take an item from a container in the location",
                "  drop <item> - Drop an item at the current location",
                "  put <item> in <container> - Put an item in a container in the location",
                "  search - Carefully search the current location for hidden items",
                "  search <area> - Search a specific area or container for hidden items",
                "  quests - Open the quest log",
                "  active quests - List all active quests",
                "  quest info <id> - Get details about a specific quest",
                "  quest track <id> - Mark a quest as your current focus",
                "  save [name] - Save the game with optional name",
                "  quicksave - Quickly save the game",
                "  load <name or #> - Load a saved game by name or number from the saves list",
                "  quickload - Load the most recent quicksave",
                "  saves - List all saved games",
                "  inventory/inv/i - View your inventory",
                "  equip <item> - Equip a wearable item",
                "  unequip <slot> - Unequip an item from a specific slot",
                "  use <item> - Use a consumable item",
                "  open <container> - Open a container to view its contents",
                "  put <item> in <container> - Place an item in a container",
                "  take <item> from <container> - Take an item from a container",
                "  quit/exit - Exit the game",
                "  help - Display this list of commands",
            ]
        )

    def _find_matching_npc(self, npc_descriptor: str) -> tuple[Optional[str], list[str]]:
        """
        Find matching NPC(s) based on a descriptor (name, role, or pronoun).
        Returns tuple of (matched_npc_id, list_of_ambiguous_npcs).
        """
        # Get NPCs in current location
        npcs_here = [
            npc for npc in self.config.npcs.values()
            if npc.location == self.current_location
        ]
        
        if not npcs_here:
            return None, []

        # Check for pronoun matches (using gender field)
        npc_descriptor = npc_descriptor.lower()
        if npc_descriptor in ['he', 'him', 'his']:
            matching_npcs = [npc for npc in npcs_here if npc.gender == 'male']
            if len(matching_npcs) == 1:
                return matching_npcs[0].id, []
            elif len(matching_npcs) > 1:
                return None, [npc.name for npc in matching_npcs]
        elif npc_descriptor in ['she', 'her', 'hers']:
            matching_npcs = [npc for npc in npcs_here if npc.gender == 'female']
            if len(matching_npcs) == 1:
                return matching_npcs[0].id, []
            elif len(matching_npcs) > 1:
                return None, [npc.name for npc in matching_npcs]

        # Check for name matches
        matching_npcs = []
        for npc in npcs_here:
            # Check full name match (case insensitive)
            if npc_descriptor in npc.name.lower():
                matching_npcs.append(npc)
                continue
            
            # Check first/last name matches for NPCs with multiple name parts
            name_parts = npc.name.lower().split()
            matches = [part for part in name_parts if npc_descriptor in part]
            if len(matches) > 0:
                matching_npcs.append(npc)
                continue

        if len(matching_npcs) == 1:
            return matching_npcs[0].id, []
        elif len(matching_npcs) > 1:
            return None, [npc.name for npc in matching_npcs]
        
        return None, []

    def _handle_talk_to_npc(self, npc_name: str) -> str:
        """Handle talking to an NPC."""
        if not npc_name:
            return "Who would you like to talk to?"

        # Try to find matching NPC
        matched_npc_id, ambiguous_npcs = self._find_matching_npc(npc_name)
        
        # Handle ambiguous matches
        if ambiguous_npcs:
            return f"Who would you like to talk to? {' or '.join(ambiguous_npcs)}?"
        
        # Handle no matches
        if not matched_npc_id:
            # Get list of NPCs in current location for helpful message
            npcs_here = [
                npc.name for npc in self.config.npcs.values()
                if npc.location == self.current_location
            ]
            if npcs_here:
                return f"I don't see anyone like that here. You can talk to: {', '.join(npcs_here)}."
            return "There's no one here to talk to."

        # Proceed with dialogue
        if self.dialogue_handler:
            # Get the NPC's display name for the UI
            npc = self.config.npcs.get(matched_npc_id)
            npc_display_name = npc.name if npc else matched_npc_id
            
            # Get dialogue responses
            responses = self.dialogue_handler.start_dialogue(matched_npc_id, self.game_state)
            
            # Start dialogue mode in the UI
            if hasattr(self, 'app') and self.app:
                self.app.dialogue_mode.start_dialogue(npc_display_name, responses)
                return ""  # Empty response since UI will handle display
            else:
                # Fallback to text-based display if UI is not available
                dialogue_text = []
                for response in responses:
                    if isinstance(response, DialogueResponse.Speech):
                        dialogue_text.append(f"{response.speaker}: {response.text}")
                    elif isinstance(response, DialogueResponse.Options):
                        dialogue_text.append("\nOptions:")
                        for option in response.options:
                            dialogue_text.append(f"- {option.text}")
                    elif isinstance(response, DialogueResponse.InnerVoice):
                        dialogue_text.append(f"[{response.voice_type}] {response.text}")
                    elif isinstance(response, DialogueResponse.SkillCheck):
                        result = "Success" if response.success else "Failure"
                        dialogue_text.append(f"[Skill Check: {response.skill} - {result}]")
                
                return "\n".join(dialogue_text)
        return f"You try to talk to {npc_name}, but they don't respond."

    def upgrade_skill(self, skill_name: str) -> bool:
        """Attempt to upgrade a skill using skill points."""
        if (
            skill_name in self.game_state.skills
            and self.game_state.skill_points > 0
        ):
            self.game_state.skills[skill_name] += 1
            self.game_state.skill_points -= 1
            return True
        return False

    def add_experience(self, amount: int) -> None:
        """Add experience points and handle level ups."""
        self.game_state.experience += amount
        # Every 100 XP grants a skill point
        new_skill_points = self.game_state.experience // 100
        if new_skill_points > 0:
            self.game_state.skill_points += new_skill_points
            self.game_state.experience %= 100

    def _handle_show_inventory(self) -> str:
        """Handle showing the player's inventory."""
        inventory = self.game_state.inventory_manager
        response = "Inventory:\n"
        
        # Show equipped items
        equipped = inventory.equipped_items
        if any(equipped.values()):
            response += "\nEquipped Items:\n"
            for slot, item in equipped.items():
                if item:
                    response += f"- {slot.name}: {item.name}\n"
                    response += f"  Description: {item.description}\n"
                    response += f"  Type: {next(iter(item.categories)).value}\n"
                    response += f"  Weight: {item.weight}\n"
                    if hasattr(item, 'effects') and item.effects:
                        response += "  Effects:\n"
                        for effect in item.effects:
                            response += f"    • {effect.attribute.title()}: {effect.value:+g}"
                            if effect.description:
                                response += f" ({effect.description})"
                            response += "\n"
                    response += "\n"
        
        # Show carried items
        carried = inventory.items
        if carried:
            response += "\nCarried Items:\n"
            for item in carried:
                response += f"- {item.name}"
                if item.quantity > 1:
                    response += f" (x{item.quantity})"
                response += f"\n  Description: {item.description}\n"
                response += f"  Type: {next(iter(item.categories)).value}\n"
                response += f"  Weight: {item.weight}\n"
                if hasattr(item, 'effects') and item.effects:
                    response += "  Effects:\n"
                    for effect in item.effects:
                        response += f"    • {effect.attribute.title()}: {effect.value:+g}"
                        if effect.description:
                            response += f" ({effect.description})"
                        response += "\n"
                response += "\n"
        
        # Show containers
        containers = inventory.containers
        if containers:
            response += "\nContainers:\n"
            for container in containers:
                response += f"- {container.name}\n"
                response += f"  Description: {container.description}\n"
                response += f"  Type: {next(iter(container.categories)).value}\n"
                response += f"  Weight: {container.weight}\n"
                response += f"  Capacity: {container.capacity}\n"
                if container.contents:
                    current_weight = sum(item.weight * item.quantity for item in container.contents)
                    response += f"  Current Weight: {current_weight}/{container.capacity}\n"
                    response += "  Contents:\n"
                    for item in container.contents:
                        response += f"    • {item.name}"
                        if item.quantity > 1:
                            response += f" (x{item.quantity})"
                        response += "\n"
                response += "\n"
        
        if not any(equipped.values()) and not carried and not containers:
            response += "Your inventory is empty."
        
        return response

    def _handle_equip_item(self, item_name: str) -> str:
        """Handle equipping an item."""
        item = self._find_item_in_inventory(item_name)
        if not item:
            return f"You don't have '{item_name}' in your inventory."
        
        if not isinstance(item, Wearable):
            return f"You can't equip {item.name} - it's not wearable."
        
        success, message = self.game_state.equip_item(item.id)
        return message

    def _handle_unequip_item(self, slot_name: str) -> str:
        """Handle unequipping an item from a slot."""
        try:
            slot = WearableSlot[slot_name.upper()]
        except KeyError:
            return f"Invalid slot: {slot_name}. Valid slots are: {', '.join(s.name for s in WearableSlot)}"
        
        # Get the currently equipped item before unequipping
        equipped_item = self.game_state.inventory_manager.equipped_items.get(slot)
        
        # # If there's an item equipped in this slot, remove its effects from player stats
        # if equipped_item and hasattr(equipped_item, 'effects') and equipped_item.effects:
        #     for effect in equipped_item.effects:
        #         # Remove the effect by applying the negative value
        #         self.game_state.player.modify_attribute(effect.attribute, -effect.value)
        
        success, message = self.game_state.unequip_item(slot)
        return message

    def _handle_examine_item(self, item_name: str) -> str:
        """Handle examining an item."""
        item = self._find_item_in_inventory(item_name)
        if not item:
            return f"You don't have '{item_name}' in your inventory."
        
        # Start with basic description
        response = f"{item.name}:\n{item.description}\n"
        
        # Add type-specific information
        if isinstance(item, Wearable):
            response += f"\nSlot: {item.slot.name}"
            if item.set_id:
                response += f"\nPart of set: {item.set_id}"
            if item.effects:
                response += "\nEffects:"
                for effect in item.effects:
                    response += f"\n- {effect.description}"
        
        elif isinstance(item, Container):
            response += f"\nCapacity: {item.capacity}"
            if hasattr(item, 'current_weight') and item.current_weight > 0:
                response += f"\nCurrent weight: {item.current_weight}"
            if item.contents:
                response += "\nContents:"
                for content in item.contents:
                    response += f"\n- {content.name}"
        
        # If the item already has discovered hidden information, just show it
        if item.discovered:
            if item.hidden_lore:
                response += f"\n\nLore: {item.hidden_lore}"
            if item.hidden_clues:
                response += "\n\nClues:"
                for clue in item.hidden_clues:
                    response += f"\n- {clue}"
            if item.hidden_usage:
                response += f"\n\nUsage: {item.hidden_usage}"
            return response
        
        # Try to discover hidden information through skill checks
        discovered_something = False
        
        # Only perform checks if there's something to discover
        has_hidden_info = bool(item.hidden_lore or item.hidden_clues or item.hidden_usage)
        
        # Perform perception check if needed
        if item.perception_difficulty > 0 and has_hidden_info:
            perception_success, roll, difficulty = self._perform_skill_check("perception", item.perception_difficulty)
            
            if perception_success:
                # Notify player of successful check
                response += f"\n\n[Perception Check: Success (Roll: {roll}/{difficulty})]"
                discovered_something = True
                
                # Reveal hidden clues on successful perception check
                if item.hidden_clues:
                    response += "\n\nYou notice:"
                    for clue in item.hidden_clues:
                        response += f"\n- {clue}"
        
        # Perform wisdom check if needed
        if item.wisdom_difficulty > 0 and has_hidden_info:
            wisdom_success, roll, difficulty = self._perform_skill_check("wisdom", item.wisdom_difficulty)
            
            if wisdom_success:
                # Notify player of successful check
                response += f"\n\n[Wisdom Check: Success (Roll: {roll}/{difficulty})]"
                discovered_something = True
                
                # Reveal lore and usage hints on successful wisdom check
                if item.hidden_lore:
                    response += f"\n\nYou recall: {item.hidden_lore}"
                
                if item.hidden_usage:
                    response += f"\n\nYou realize: {item.hidden_usage}"
        
        # Mark as discovered if any checks succeeded
        if discovered_something:
            item.discovered = True
        
        return response

    def _handle_use_item(self, item_name: str) -> str:
        """Handle using a consumable item."""
        item = self._find_item_in_inventory(item_name)
        if not item:
            return f"You don't have '{item_name}' in your inventory."
        
        if ItemCategory.CONSUMABLE not in item.categories:
            return f"You can't use {item.name} - it's not a consumable item."
        
        # Apply effects
        for effect in item.effects:
            if effect.attribute in self.game_state.player.attributes:
                self.game_state.player.attributes[effect.attribute] += effect.value
        
        # Remove item if it's not stackable or if it's the last one
        if not item.stackable or item.quantity == 1:
            self.game_state.remove_item(item.id)
        else:
            item.quantity -= 1
        
        return f"You use {item.name}. {item.use_text}"

    def _handle_open_container(self, container_name: str) -> str:
        """Handle opening a container to view its contents."""
        container = self._find_item_in_inventory(container_name)
        if not container:
            return f"You don't have '{container_name}' in your inventory."
        
        if not isinstance(container, Container):
            return f"You can't open {container.name} - it's not a container."
        
        response = f"Contents of {container.name}:\n"
        if container.contents:
            for item in container.contents:
                response += f"- {item.name}"
                if item.quantity > 1:
                    response += f" (x{item.quantity})"
                response += "\n"
        else:
            response += "The container is empty."
        
        return response

    def _handle_put_in_container(self, item_name: str, container_name: str) -> str:
        """Handle putting an item in a container."""
        item = self._find_item_in_inventory(item_name)
        if not item:
            return f"You don't have '{item_name}' in your inventory."
        
        container = self._find_item_in_inventory(container_name)
        if not container:
            return f"You don't have '{container_name}' in your inventory."
        
        if not isinstance(container, Container):
            return f"You can't put items in {container.name} - it's not a container."
        
        if item in container.contents:
            return f"{item.name} is already in {container.name}."
        
        if container.current_weight + item.weight > container.capacity:
            return f"{container.name} doesn't have enough space for {item.name}."
        
        if not container.is_allowed_category(item.categories):
            return f"You can't put {item.name} in {container.name} - it's not allowed."
        
        success = self.game_state.add_to_container(container.id, item)
        if success:
            return f"You put {item.name} in {container.name}."
        return f"Failed to put {item.name} in {container.name}."

    def _handle_take_from_container(self, item_name: str, container_name: str) -> str:
        """Handle taking an item from a container."""
        container = self._find_item_in_inventory(container_name)
        if not container:
            return f"You don't have '{container_name}' in your inventory."
        
        if not isinstance(container, Container):
            return f"You can't take items from {container.name} - it's not a container."
        
        item = next((i for i in container.contents if i.name.lower() == item_name.lower()), None)
        if not item:
            return f"{item_name} is not in {container.name}."
        
        success = self.game_state.remove_from_container(container.id, item.id)
        if success:
            return f"You take {item.name} from {container.name}."
        return f"Failed to take {item.name} from {container.name}."

    def _find_item_in_inventory(self, item_name: str) -> Optional[Item]:
        """Find an item in the inventory by name."""
        inventory = self.game_state.inventory_manager
        
        # Combine all items from equipped, inventory, and containers
        all_items = (
            list(filter(None, inventory.equipped_items.values())) +  # Equipped items
            inventory.items +  # Regular inventory items
            inventory.containers  # Containers
        )
        
        # First try exact match
        for item in all_items:
            if item and item.name.lower() == item_name.lower():
                return item
        
        # Then try partial match
        for item in all_items:
            if item and item_name.lower() in item.name.lower():
                return item
        
        return None

    def _perform_skill_check(self, skill_name: str, difficulty: int) -> tuple[bool, int, int]:
        """
        Perform a skill check for a given skill and difficulty.
        
        Args:
            skill_name: The name of the skill to check
            difficulty: The difficulty level of the check
            
        Returns:
            tuple[bool, int, int]: Success result, roll value, difficulty
        """
        player_skill = 0
        if skill_name in self.game_state.player.skills:
            player_skill = self.game_state.player.skills[skill_name]
        
        # Roll a d20
        roll = random.randint(1, 20)
        
        # Check if roll + skill meets or exceeds difficulty
        success = (roll + player_skill) >= difficulty
        
        return success, roll, difficulty

    def navigate_to(self, location_id: str) -> None:
        """
        Navigate the player to a new location.
        
        Args:
            location_id: The ID of the location to navigate to
        """
        if location_id in self.config.locations:
            # Store previous location before changing
            self.previous_location = self.current_location
            
            # Update current location
            self.current_location = location_id
            self.game_state.current_location = location_id
            
            # Mark as visited
            self.game_state.visited_locations.add(location_id)
            
            # Check if any quest updates should trigger based on the new location
            self.quest_manager.check_all_quest_updates()
        else:
            print(f"Warning: Tried to navigate to unknown location: {location_id}")

    def _handle_take_item(self, item_name: str) -> str:
        """Handle taking an item from the current location."""
        if not item_name:
            return "What would you like to take?"
            
        # Get all items in the current location
        location_items = self.game_state.get_location_items(self.current_location)
        
        # Try to find the item by name
        target_item = None
        target_item_id = None
        
        for item in location_items:
            if item_name.lower() in item.name.lower():
                target_item = item
                target_item_id = item.id
                break
                
        if not target_item:
            return f"You don't see any {item_name} here."
            
        # Check if the item has a perception difficulty
        perception_difficulty = getattr(target_item, 'perception_difficulty', 0)
        if perception_difficulty > 0:
            # If the item is hidden, perform a perception check
            perception_success, roll, difficulty = self._perform_skill_check("perception", perception_difficulty)
            if not perception_success:
                return f"You don't see any {item_name} here."
                
        # Check if player has enough inventory space
        if target_item.weight + self.game_state.get_inventory_weight() > self.game_state.get_max_inventory_weight():
            return f"You can't carry any more. Your inventory is full."
            
        # Remove item from location and add to inventory
        removed_item = self.game_state.remove_item_from_location(self.current_location, target_item_id)
        if removed_item:
            self.game_state.add_item(removed_item)
            
            # Generate response message
            if removed_item.quantity > 1:
                return f"You take {removed_item.quantity} {removed_item.name}."
            else:
                return f"You take the {removed_item.name}."
        else:
            return f"Failed to take the {item_name}."
    
    def _handle_drop_item(self, item_name: str) -> str:
        """Handle dropping an item in the current location."""
        if not item_name:
            return "What would you like to drop?"
            
        # Find the item in the player's inventory
        item = self._find_item_in_inventory(item_name)
        if not item:
            return f"You don't have any {item_name} to drop."
            
        # Remove the item from inventory
        removed_item = self.game_state.remove_item(item.id)
        if removed_item:
            # Add it to the current location
            self.game_state.add_item_to_location(self.current_location, removed_item)
            
            if removed_item.quantity > 1:
                return f"You drop {removed_item.quantity} {removed_item.name}."
            else:
                return f"You drop the {removed_item.name}."
        else:
            return f"Failed to drop the {item_name}."
    
    def _handle_take_from_location_container(self, item_name: str, container_name: str) -> str:
        """Handle taking an item from a container in the current location."""
        if not item_name or not container_name:
            return "Please specify both an item and a container."
            
        # First, find the container in the current location
        location_items = self.game_state.get_location_items(self.current_location)
        
        container = None
        container_id = None
        
        for item in location_items:
            if container_name.lower() in item.name.lower() and isinstance(item, Container):
                container = item
                container_id = item.id
                break
                
        if not container:
            return f"You don't see any {container_name} here."
            
        # Get items in the container
        container_items = self.game_state.get_location_container_items(self.current_location, container_id)
        
        # Try to find the item by name
        target_item = None
        target_item_id = None
        
        for item in container_items:
            if item_name.lower() in item.name.lower():
                target_item = item
                target_item_id = item.id
                break
                
        if not target_item:
            return f"There's no {item_name} in the {container.name}."
            
        # Check if player has enough inventory space
        if target_item.weight + self.game_state.get_inventory_weight() > self.game_state.get_max_inventory_weight():
            return f"You can't carry any more. Your inventory is full."
            
        # Remove item from container and add to inventory
        removed_item = self.game_state.remove_item_from_location_container(
            self.current_location, container_id, target_item_id)
            
        if removed_item:
            self.game_state.add_item(removed_item)
            
            if removed_item.quantity > 1:
                return f"You take {removed_item.quantity} {removed_item.name} from the {container.name}."
            else:
                return f"You take the {removed_item.name} from the {container.name}."
        else:
            return f"Failed to take the {item_name} from the {container.name}."
    
    def _handle_put_in_location_container(self, item_name: str, container_name: str) -> str:
        """Handle putting an item in a container in the current location."""
        if not item_name or not container_name:
            return "Please specify both an item and a container."
            
        # Find the item in the player's inventory
        item = self._find_item_in_inventory(item_name)
        if not item:
            return f"You don't have any {item_name} to put in the {container_name}."
            
        # Find the container in the current location
        location_items = self.game_state.get_location_items(self.current_location)
        
        container = None
        container_id = None
        
        for loc_item in location_items:
            if container_name.lower() in loc_item.name.lower() and isinstance(loc_item, Container):
                container = loc_item
                container_id = loc_item.id
                break
                
        if not container:
            return f"You don't see any {container_name} here."
            
        # Check if container allows this type of item
        if not container.is_allowed_category(item.categories):
            return f"You can't put {item.name} in the {container.name}."
            
        # Check if container has enough space
        container_items = self.game_state.get_location_container_items(self.current_location, container_id)
        current_weight = sum(i.weight * i.quantity for i in container_items)
        
        if current_weight + item.weight > container.capacity:
            return f"The {container.name} doesn't have enough space for {item.name}."
            
        # Remove item from inventory
        removed_item = self.game_state.remove_item(item.id)
        if removed_item:
            # Add to container
            success = self.game_state.add_item_to_location_container(
                self.current_location, container_id, removed_item)
                
            if success:
                if removed_item.quantity > 1:
                    return f"You put {removed_item.quantity} {removed_item.name} in the {container.name}."
                else:
                    return f"You put the {removed_item.name} in the {container.name}."
            else:
                # If failed to add to container, return to inventory
                self.game_state.add_item(removed_item)
                return f"Failed to put the {item.name} in the {container.name}."
        else:
            return f"Failed to get the {item.name} from your inventory."

    def _handle_search(self) -> str:
        """Handle a general search of the current location."""
        response = "You search the current area thoroughly...\n\n"
        hidden_items_found = []
        
        # Get all items in the current location
        location_items = self.game_state.get_location_items(self.current_location)
        
        # Look for hidden items
        for item in location_items:
            # Skip obvious items
            if getattr(item, 'is_obvious', True):
                continue
                
            # Check if item has perception difficulty
            perception_difficulty = getattr(item, 'perception_difficulty', 0)
            if perception_difficulty > 0:
                # Perform perception check
                perception_success, roll, difficulty = self._perform_skill_check("perception", perception_difficulty)
                if perception_success:
                    hidden_items_found.append(item)
                    item.is_obvious = True  # Item is now obvious
        
        if hidden_items_found:
            response += "You discovered:\n"
            for item in hidden_items_found:
                response += f"- {item.name}: {item.description}\n"
        else:
            response += "You didn't find anything of interest."
            
        return response
        
    def _handle_search_area(self, area_name: str) -> str:
        """Handle searching a specific area in the current location."""
        response = f"You search the {area_name} carefully...\n\n"
        
        # Get all items in the current location
        location_items = self.game_state.get_location_items(self.current_location)
        
        # Try to find container that matches area name
        container = None
        container_id = None
        
        for item in location_items:
            if area_name.lower() in item.name.lower() and isinstance(item, Container):
                container = item
                container_id = item.id
                break
                
        if container:
            # Get contents of the container
            container_items = self.game_state.get_location_container_items(
                self.current_location, container_id)
                
            if container_items:
                response += f"Inside the {container.name}, you find:\n"
                for item in container_items:
                    response += f"- {item.name}\n"
            else:
                response += f"The {container.name} is empty."
                
            return response
        
        # If not a container, look for hidden items related to the area
        found_items = []
        
        for item in location_items:
            # Skip obvious items unless they're related to the area
            if getattr(item, 'is_obvious', True) and area_name.lower() not in item.name.lower():
                continue
                
            # Check if item matches the area
            area_matches = False
            
            # Check name
            if area_name.lower() in item.name.lower():
                area_matches = True
                
            # Check description
            if area_name.lower() in item.description.lower():
                area_matches = True
                
            # If it matches, check perception
            if area_matches:
                perception_difficulty = getattr(item, 'perception_difficulty', 0)
                if perception_difficulty > 0:
                    # Perform perception check
                    perception_success, roll, difficulty = self._perform_skill_check("perception", perception_difficulty)
                    if perception_success:
                        found_items.append(item)
                        item.is_obvious = True  # Item is now obvious
                else:
                    found_items.append(item)
        
        if found_items:
            response += "You found:\n"
            for item in found_items:
                response += f"- {item.name}: {item.description}\n"
        else:
            response += f"You didn't find anything interesting in the {area_name}."
            
        return response
