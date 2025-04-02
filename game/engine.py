"""
Core game engine that processes player input and coordinates game systems.
"""

import random
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from config.config_loader import GameConfig
from dialogue.manager import DialogueManager
from game.dialogue_integration import DialogueHandler
from game.game_state import GameState, QuestStatus
from quest.quest_manager import QuestManager
from save.save_load import SaveManager


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

        # Initialize quest manager with quests from config
        self.quest_manager = QuestManager(config.quests)

        # Initialize save manager
        self.save_manager = SaveManager()

        # Dialogue system (will be set externally)
        self.dialogue_handler = None

        # Notification system
        self.pending_notifications = []
        self.notification_timer = time.time()
        self.show_notification_indicator = False

        # Start time for playtime tracking
        self.start_time = time.time()

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

        # Process commands
        if parts[0] == "look" and len(parts) > 1 and parts[1] == "around":
            return self._handle_look_around()

        elif parts[0] == "examine" and len(parts) > 1:
            item = parts[1]
            return f"You examine the {item} closely."

        elif parts[0] in ["talk", "speak"] and len(parts) > 1:
            npc = parts[1]
            return f"Use the dialogue system for talking to NPCs"

        elif parts[0] in ["go", "walk", "move", "head"] and len(parts) > 1:
            direction = parts[1]
            return self._handle_movement(direction)

        elif parts[0] in ["exits", "directions", "connections"] or (
            len(parts) >= 3
            and parts[0] == "where"
            and parts[1] == "can"
            and parts[2] == "i"
            and parts[3] == "go"
        ):
            return self._handle_show_exits()

        elif parts[0] == "save":
            save_name = " ".join(parts[1:]) if len(parts) > 1 else ""
            return self._handle_save_command(save_name)

        elif parts[0] == "quicksave" or (
            len(parts) == 2 and parts[0] == "quick" and parts[1] == "save"
        ):
            return self._handle_quick_save_command()

        elif parts[0] == "load" and len(parts) > 1:
            load_identifier = " ".join(parts[1:])
            return self._handle_load_command(load_identifier)

        elif parts[0] == "quickload" or (
            len(parts) == 2 and parts[0] == "quick" and parts[1] == "load"
        ):
            return self._handle_quick_load_command()

        elif parts[0] == "saves" or (
            len(parts) == 2 and parts[0] == "list" and parts[1] == "saves"
        ):
            return self._handle_list_saves_command()

        elif parts[0] in ["quests", "journal"] or (
            len(parts) == 2 and parts[0] == "quest" and parts[1] == "log"
        ):
            return self._handle_show_quests()

        elif len(parts) == 3 and parts[0] == "quest" and parts[1] == "track":
            quest_id = parts[2]
            return self._handle_track_quest(quest_id)

        elif len(parts) == 3 and parts[0] == "quest" and parts[1] == "info":
            quest_id = parts[2]
            return self._handle_quest_info(quest_id)

        elif len(parts) == 2 and parts[0] == "active" and parts[1] == "quests":
            return self._handle_show_active_quests()

        elif parts[0] == "help":
            return self._help_command()

        else:
            return "Unknown command. Type 'help' for a list of commands."

    def check_quest_updates(self) -> None:
        """Check for quest updates."""
        self.quest_manager.check_all_quest_updates(self.game_state)

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
        return self.quest_manager.start_quest(quest_id, self.game_state)

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
            for loc_id in current_location.connected_locations:
                connected_loc = self.config.locations.get(loc_id)
                if not connected_loc:
                    continue

                # Match by partial name or ID
                if (
                    direction.lower() in connected_loc.name.lower()
                    or direction.lower() in loc_id.lower()
                ):
                    target_location_id = loc_id
                    break

                # Match by cardinal direction
                if direction in ["north", "south", "east", "west"]:
                    if (
                        direction in connected_loc.name.lower()
                        or direction in loc_id.lower()
                    ):
                        target_location_id = loc_id
                        break

        if not target_location_id:
            return f"You can't go to the {direction} from here."

        # Move to new location
        self.previous_location = self.current_location
        self.current_location = target_location_id

        # Update game state
        self.game_state.change_location(target_location_id)

        # Get description
        new_location = self.config.locations.get(target_location_id)
        return self._get_movement_response(new_location.name, new_location.description)

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
        """Handle the 'quests' command."""
        # Check for quest updates before showing
        self.check_quest_updates()

        # This would be replaced with actual quest UI
        return "Opened quest log. (UI not implemented yet)"

    def _handle_track_quest(self, quest_id: str) -> str:
        """Handle the 'quest track' command."""
        quest = self.quest_manager.get_quest(quest_id)
        if not quest:
            return f"No quest found with ID: {quest_id}"

        # Actual tracking would be implemented in the UI
        return f"Now tracking: {quest.title}"

    def _handle_quest_info(self, quest_id: str) -> str:
        """Handle the 'quest info' command."""
        quest = self.quest_manager.get_quest(quest_id)
        if not quest:
            return f"No quest found with ID: {quest_id}"

        # Find current stage
        current_stage = None
        for stage in quest.stages:
            if stage.status == "InProgress":
                current_stage = stage
                break

        current_stage_desc = (
            current_stage.description if current_stage else "No active stage"
        )

        # Calculate progress percentage
        completed_stages = sum(
            1 for stage in quest.stages if stage.status == "Completed"
        )
        total_stages = len(quest.stages)
        progress = (completed_stages / total_stages) * 100 if total_stages > 0 else 0

        return (
            f"Quest: {quest.title}\n\n"
            f"{quest.description}\n\n"
            f"Current Objective: {current_stage_desc}\n"
            f"Progress: {progress:.1f}%"
        )

    def _handle_show_active_quests(self) -> str:
        """Handle the 'active quests' command."""
        active_quests = self.quest_manager.get_active_quests()

        if not active_quests:
            return "You don't have any active quests."

        response = "Active Quests:\n"

        for quest in active_quests:
            # Calculate progress percentage
            completed_stages = sum(
                1 for stage in quest.stages if stage.status == "Completed"
            )
            total_stages = len(quest.stages)
            progress = (
                (completed_stages / total_stages) * 100 if total_stages > 0 else 0
            )

            response += f"- {quest.title} ({progress:.1f}% complete)\n"

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
                "  help - Display this list of commands",
            ]
        )
