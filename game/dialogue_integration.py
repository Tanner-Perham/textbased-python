"""
Integration of dialogue system with the game engine.
"""

from typing import List, Optional

from config.config_loader import GameConfig
from dialogue.manager import DialogueManager
from dialogue.response import DialogueResponse
from game.game_state import GameState
from ui.dialogue_ui import DialogueUI


class DialogueHandler:
    """Handles dialogue interactions in the game engine."""

    def __init__(self, dialogue_manager: DialogueManager):
        """Initialize dialogue handler with a dialogue manager."""
        self.dialogue_manager = dialogue_manager

    async def handle_dialogue(self, npc_id: str, game_state: GameState) -> str:
        """
        Handle dialogue interaction with an NPC.
        Returns a result message.
        """
        # Verify NPC exists in config
        try:
            # Use the actual NPC name from the configuration
            npc_name = (
                self.dialogue_manager.dialogue_tree.get(f"{npc_id}_default", {}).speaker
                or f"NPC {npc_id}"
            )
        except Exception:
            npc_name = npc_id

        # Record interaction with this NPC
        game_state.record_npc_interaction(npc_id)

        # Get initial dialogue
        try:
            responses = self.dialogue_manager.start_dialogue(npc_id, game_state)
            if not responses:
                return f"No dialogue available for {npc_name}"

            # Create dialogue UI
            dialogue_ui = DialogueUI(npc_name)

            # Set up initial dialogue state
            dialogue_ui.process_responses(responses)

            # Run the UI and get selected option
            selected_option = await dialogue_ui.run_async()

            # Handle end of conversation
            if not selected_option or selected_option == "end_conversation":
                return f"You ended the conversation with {npc_name}."

            # Process the selected option and get next responses
            next_responses = self.dialogue_manager.select_option(
                selected_option, game_state
            )

            if not next_responses:
                return f"Your conversation with {npc_name} has ended."

            # Process responses for the UI
            dialogue_ui.process_responses(next_responses)

            # Continue dialogue until it ends
            conversation_active = True
            while conversation_active:
                # Run the UI again to get the next selection
                selected_option = await dialogue_ui.run_async()

                # Check if the conversation is ending
                if not selected_option or selected_option == "end_conversation":
                    conversation_active = False
                    break

                # Process the selected option
                next_responses = self.dialogue_manager.select_option(
                    selected_option, game_state
                )

                # Check if there are no more responses
                if not next_responses:
                    conversation_active = False
                    break

                # Update the UI with new responses
                dialogue_ui.process_responses(next_responses)

            return f"You finished your conversation with {npc_name}."

        except Exception as e:
            return f"Error in dialogue with {npc_name}: {str(e)}"

    def _get_npc_name(self, npc_id: str, game_state: GameState) -> str:
        """Get NPC name from ID."""
        # Use the dialogue tree to find the speaker name
        dialogue_node = self.dialogue_manager.dialogue_tree.get(f"{npc_id}_default")
        if dialogue_node:
            return dialogue_node.speaker

        # Fallback to NPC ID if no speaker found
        return npc_id

    def find_npc_by_name(
        config: GameConfig, current_location: str, npc_name: str
    ) -> Optional[str]:
        """Find an NPC ID by name in the current location."""
        matches = []

        # First pass: exact name match in current location
        for npc_id, npc in config.npcs.items():
            if (
                npc.location == current_location
                and npc_name.lower() == npc.name.lower()
            ):
                return npc_id

        # Second pass: partial name match in current location
        for npc_id, npc in config.npcs.items():
            if (
                npc.location == current_location
                and npc_name.lower() in npc.name.lower()
            ):
                matches.append(npc_id)

        # Third pass: pronoun match
        for npc_id, npc in config.npcs.items():
            if npc.location == current_location and matches_pronoun(
                config, npc, npc_name, current_location
            ):
                matches.append(npc_id)

        # Return first match or None
        return matches[0] if matches else None
