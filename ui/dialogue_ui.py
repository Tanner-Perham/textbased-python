"""
Dialogue UI module for handling NPC conversations.
"""

from typing import List, Optional, Tuple

from textual import events
from textual.app import App, ComposeResult
from textual.containers import Container, ScrollableContainer
from textual.reactive import reactive
from textual.widgets import Footer, Static

from dialogue.response import DialogueResponse
from ui.dialogue_components import DialogueOption, InnerVoice, SkillCheckResult, SpeechBubble


class DialogueUI(App):
    """Interactive dialogue UI for NPC conversations."""

    CSS_PATH = "dialogue_styles.css"
    BINDINGS = [
        ("up", "select_previous", "Previous"),
        ("down", "select_next", "Next"),
        ("enter", "select", "Select"),
        ("escape", "quit", "Exit"),
    ]

    selected_index = reactive(0)
    options = reactive([])

    def __init__(self, npc_name: str):
        """Initialize dialogue UI with NPC name."""
        super().__init__()
        self.npc_name = npc_name
        self.dialogue_history = []

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        with Container(id="dialogue-container"):
            with ScrollableContainer(id="dialogue-history"):
                yield Static(id="history-content")

            with Container(id="dialogue-options"):
                # Options will be added dynamically
                pass

        yield Footer()

    def on_mount(self) -> None:
        """Handle app mount event."""
        self.update_title(f"Conversation with {self.npc_name}")

    def action_select_previous(self) -> None:
        """Select the previous dialogue option."""
        if not self.options:
            return

        self.selected_index = (self.selected_index - 1) % len(self.options)
        self.update_options()

    def action_select_next(self) -> None:
        """Select the next dialogue option."""
        if not self.options:
            return

        self.selected_index = (self.selected_index + 1) % len(self.options)
        self.update_options()

    def action_select(self) -> None:
        """Select the current dialogue option."""
        if not self.options:
            return

        selected_option = self.options[self.selected_index]
        self.exit(selected_option.id)

    def update_options(self) -> None:
        """Update the display of dialogue options."""
        options_container = self.query_one("#dialogue-options")
        options_container.remove_children()

        for i, option in enumerate(self.options):
            is_selected = i == self.selected_index
            option_widget = DialogueOption(option.id, option.text, is_selected)
            options_container.mount(option_widget)

    def add_to_history(self, response: DialogueResponse) -> None:
        """Add a dialogue response to the history."""
        history_content = self.query_one("#history-content")

        if isinstance(response, DialogueResponse.Speech):
            bubble = SpeechBubble(
                speaker=response.speaker, text=response.text, emotion=response.emotion
            )
            history_content.mount(bubble)

        elif isinstance(response, DialogueResponse.InnerVoice):
            inner_voice = InnerVoice(voice_type=response.voice_type, text=response.text)
            history_content.mount(inner_voice)

        elif isinstance(response, DialogueResponse.SkillCheck):
            skill_check = SkillCheckResult(
                skill=response.skill,
                success=response.success,
                roll=response.roll,
                difficulty=response.difficulty,
            )
            history_content.mount(skill_check)

        # Keep history in view by scrolling to bottom
        history = self.query_one("#dialogue-history")
        history.scroll_end(animate=False)

    def process_responses(self, responses: List[DialogueResponse]) -> None:
        """Process a list of dialogue responses."""
        new_options = []

        for response in responses:
            if isinstance(response, DialogueResponse.Options):
                # Extract the options list
                new_options = response.options
            else:
                self.add_to_history(response)

        # Update options if new ones were provided
        if new_options:
            self.options = new_options
            self.selected_index = 0
            self.update_options()
        elif not self.options:
            # Add an "End conversation" option if no options are available
            from dialogue.node import DialogueOption

            end_option = DialogueOption(
                id="end_conversation",
                text="End conversation",
                next_node="",
                skill_check=None,
                emotional_impact={},
                conditions={},
                consequences=[],
                inner_voice_reactions=[],
                success_node="",
                failure_node="",
            )

            self.options = [end_option]
            self.update_options()
