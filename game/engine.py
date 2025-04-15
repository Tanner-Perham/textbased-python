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

        # Initialize quest manager with game state
        self.quest_manager = QuestManager(self.game_state)

        # Add quests from config to game state
        for quest in config.quests.values():
            self.game_state.add_quest(quest)

        # Start the main quest automatically
        main_quests = [quest for quest in config.quests.values() if quest.is_main_quest]
        if main_quests:
            self.start_quest(main_quests[0].id)

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

        # Add starting items to inventory
        for item_data in config.game_settings.starting_inventory:
            try:
                item = ConfigLoader.create_item(item_data['id'], item_data)
                self.game_state.inventory_manager.add_item(item)
            except Exception as e:
                print(f"Error adding starting item {item_data.get('id', 'unknown')}: {str(e)}")

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
            item = parts[1]
            response = f"You examine the {item} closely."
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

        elif parts[0] == "equip" and len(parts) > 1:
            item_name = " ".join(parts[1:])
            response = self._handle_equip_item(item_name)
            return self._format_response(response, notifications)

        elif parts[0] == "unequip" and len(parts) > 1:
            slot_name = " ".join(parts[1:])
            response = self._handle_unequip_item(slot_name)
            return self._format_response(response, notifications)

        elif parts[0] == "examine" and len(parts) > 1:
            item_name = " ".join(parts[1:])
            response = self._handle_examine_item(item_name)
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
        all_quests = self.quest_manager.game_state.get_all_quests()
        active_quests = self.quest_manager.game_state.get_active_quests()
        completed_quests = self.quest_manager.game_state.get_completed_quests()
        failed_quests = self.quest_manager.game_state.get_failed_quests()

        response = "Quest Log:\n\n"

        if all_quests:
            response += "All Quests:\n"
            for quest in all_quests:
                response += f"- {quest.title}\n"
            response += "\n"

        if active_quests:
            response += "Active Quests:\n"
            for quest in active_quests:
                response += f"- {quest.title}\n"
                current_stage = next((stage for stage in quest.stages 
                                    if stage.status == "InProgress"), None)
                if current_stage:
                    response += f"  Current Stage: {current_stage.title}\n"
                    response += f"  {current_stage.description}\n"
                    for obj in current_stage.objectives:
                        status = "✓" if self.quest_manager.is_objective_completed(quest.id, obj.id) else "○"
                        optional = "(Optional) " if obj.get("is_optional", False) else ""
                        response += f"  {status} {optional}{obj.get('description', '')}\n"
                response += "\n"

        if completed_quests:
            response += "Completed Quests:\n"
            for quest in completed_quests:
                response += f"- {quest.title}\n"
            response += "\n"

        if failed_quests:
            response += "Failed Quests:\n"
            for quest in failed_quests:
                response += f"- {quest.title}\n"
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

        current_stage = next((stage for stage in quest.stages 
                            if stage.status == "InProgress"), None)
        if not current_stage:
            return f"Quest '{quest.title}' has no active stage."

        response = f"Tracking Quest: {quest.title}\n"
        response += f"Current Stage: {current_stage.title}\n"
        response += f"{current_stage.description}\n\n"
        response += "Objectives:\n"
        for obj in current_stage.objectives:
            status = "✓" if obj.get("is_completed", False) else "○"
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
        response += f"Status: {self.game_state.quest_log.get(quest_id, QuestStatus.NotStarted).name}\n\n"
        response += f"Description:\n{quest.description}\n\n"

        if quest.stages:
            response += "Stages:\n"
            for stage in quest.stages:
                response += f"- {stage.title}\n"
                response += f"  {stage.description}\n"
                if stage.objectives:
                    response += "  Objectives:\n"
                    for obj in stage.objectives:
                        status = "✓" if obj.get("is_completed", False) else "○"
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
            current_stage = next((stage for stage in quest.stages 
                                if stage.status == "InProgress"), None)
            if current_stage:
                response += f"  Current Stage: {current_stage.title}\n"
                response += f"  {current_stage.description}\n"
                for obj in current_stage.objectives:
                    status = "✓" if obj.get("is_completed", False) else "○"
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
                "  examine <item> - Get a detailed description of an item",
                "  talk to <NPC> - Engage in conversation with an NPC",
                "  go/walk <direction> - Move in the specified direction",
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
            if hasattr(self, 'ui') and self.ui:
                self.ui.dialogue_mode.start_dialogue(npc_display_name, responses)
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
        
        # Show carried items
        carried = inventory.items
        if carried:
            response += "\nCarried Items:\n"
            for item in carried:
                response += f"- {item.name}"
                if item.quantity > 1:
                    response += f" (x{item.quantity})"
                response += "\n"
        
        # Show containers
        containers = inventory.containers
        if containers:
            response += "\nContainers:\n"
            for container in containers:
                response += f"- {container.name}"
                if container.contents:
                    response += f" ({sum(item.weight * item.quantity for item in container.contents)}/{container.capacity} weight)"
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
        
        success, message = self.game_state.unequip_item(slot)
        return message

    def _handle_examine_item(self, item_name: str) -> str:
        """Handle examining an item."""
        item = self._find_item_in_inventory(item_name)
        if not item:
            return f"You don't have '{item_name}' in your inventory."
        
        response = f"{item.name}:\n{item.description}\n"
        
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
            if item.current_weight > 0:
                response += f"\nCurrent weight: {item.current_weight}"
            if item.contents:
                response += "\nContents:"
                for content in item.contents:
                    response += f"\n- {content.name}"
        
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
        all_items = (
            list(inventory.equipped_items.values()) +
            inventory.get_items_by_category(ItemCategory.WEARABLE)
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
