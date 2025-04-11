"""
Dialogue UI module for handling NPC conversations.
"""

from typing import List, Optional, Tuple

from textual import events
from textual.containers import Container, ScrollableContainer
from textual.reactive import reactive
from textual.widgets import Static, Input

from dialogue.response import DialogueResponse
from ui.dialogue_components import DialogueOption, InnerVoice, SkillCheckResult, SpeechBubble


class DialogueMode:
    """Interactive dialogue mode for NPC conversations within the main game UI."""

    def __init__(self, game_ui):
        """Initialize dialogue mode with reference to the main game UI."""
        self.game_ui = game_ui
        self.npc_name = ""
        self.selected_index = 0
        self.options = []
        self.dialogue_history = []
        self.is_active = False

    def start_dialogue(self, npc_name: str, responses: List[DialogueResponse]) -> None:
        """Start a dialogue with an NPC."""
        self.npc_name = npc_name
        self.is_active = True
        self.selected_index = 0
        self.dialogue_history = []
        self.process_responses(responses)
        self.update_display()
        # Set focus to the input box
        self.game_ui.game_input.focus()

    def end_dialogue(self) -> None:
        """End the current dialogue."""
        if self.is_active:
            # Add conversation end marker to history
            self.game_ui.game_output.write("\n=== Conversation ended ===\n\n")
            
            # Reset dialogue state
            self.is_active = False
            self.npc_name = ""
            self.selected_index = 0
            self.options = []
            self.dialogue_history = []
            self.game_ui.game_input.placeholder = "Enter your command..."
            # Keep focus on the input box
            self.game_ui.game_input.focus()

    def process_responses(self, responses: List[DialogueResponse]) -> None:
        """Process a list of dialogue responses."""
        new_options = []

        for response in responses:
            if isinstance(response, DialogueResponse.Options):
                new_options = response.options
            else:
                self.add_to_history(response)

        # Update options if new ones were provided
        if new_options:
            self.options = new_options
            self.selected_index = 0
        else:
            # No options means conversation should end
            self.end_dialogue()

    def add_to_history(self, response: DialogueResponse) -> None:
        """Add a dialogue response to the history."""
        if isinstance(response, DialogueResponse.Speech):
            self.dialogue_history.append(f"{response.speaker}: {response.text}")
        elif isinstance(response, DialogueResponse.InnerVoice):
            self.dialogue_history.append(f"[{response.voice_type}] {response.text}")
        elif isinstance(response, DialogueResponse.SkillCheck):
            result = "Success" if response.success else "Failure"
            self.dialogue_history.append(f"[Skill Check: {response.skill} - {result}]")

    def select_previous(self) -> None:
        """Select the previous dialogue option."""
        if not self.options:
            return
        self.selected_index = (self.selected_index - 1) % len(self.options)
        self.update_display()
        # Keep focus on the input box
        self.game_ui.game_input.focus()

    def select_next(self) -> None:
        """Select the next dialogue option."""
        if not self.options:
            return
        self.selected_index = (self.selected_index + 1) % len(self.options)
        self.update_display()
        # Keep focus on the input box
        self.game_ui.game_input.focus()

    def select_current(self) -> str:
        """Select the current dialogue option and return its ID."""
        if not self.options:
            return ""
        selected_option = self.options[self.selected_index]
        
        # Add the selected option to history
        self.add_to_history(DialogueResponse.Speech(
            speaker="You",
            text=selected_option.text,
            emotion="Neutral"
        ))
        
        return selected_option.id

    def update_display(self) -> None:
        """Update the game UI to show current dialogue state."""
        if not self.is_active:
            return

        # Clear the game output
        self.game_ui.game_output.clear()

        # Update input placeholder to show current selection
        if self.options:
            selected_text = self.options[self.selected_index].text
            self.game_ui.game_input.placeholder = f"Selected: {selected_text} (↑/↓ to change, Enter to select)"
        else:
            self.game_ui.game_input.placeholder = "No options available"

        # Show dialogue history and options in the game output
        output = []
        
        # Add a header for the conversation
        output.append(f"=== Conversation with {self.npc_name} ===\n")
        
        # Add dialogue history
        output.extend(self.dialogue_history)
        
        # Add options if available
        if self.options:
            output.append("\nOptions:")
            for i, option in enumerate(self.options):
                prefix = "> " if i == self.selected_index else "  "
                output.append(f"{prefix}{option.text}")
        
        # Write the formatted output
        self.game_ui.game_output.write("\n".join(output))
        self.game_ui.game_output.write("\n")
