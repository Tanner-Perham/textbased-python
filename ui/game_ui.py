from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer, Vertical, Horizontal
from textual.widgets import Header, Footer, Input, Static, Log
from textual.reactive import reactive
from textual.binding import Binding
from textual.screen import Screen
from textual.keys import Keys
from .overlay import GameOverlay
from .dialogue_ui import DialogueMode

class GameOutput(Log):
    """Widget for game output with scrolling."""
    
    DEFAULT_CSS = """
    GameOutput {
        height: 1fr;
        border: solid white;
        padding: 1 2;
        background: $boost;
        color: $text;
        min-height: 50vh;
        margin: 1;
        text-wrap: wrap;  /* Enable text wrapping */
        overflow-y: scroll;  /* Enable vertical scrolling */
        overflow-x: hidden; /* Hide horizontal scrollbar */
    }
    """

    def write(self, text: str) -> None:
        """Write text to the log with proper wrapping."""
        # Remove any existing line breaks to allow proper wrapping
        # text = text.replace("\n\n", "[br][br]")  # Preserve paragraph breaks
        # text = text.replace("[br]", "\n")  # Restore paragraph breaks
        
        # Add the text to the log
        super().write(text)

    def on_mount(self) -> None:
        """Called when widget is added to the app."""
        self.write("Welcome to the game! Type 'help' for a list of commands.\n\n")

class LocationBar(Static):
    """Shows current location."""
    location = reactive("Unknown")

    DEFAULT_CSS = """
    LocationBar {
        height: auto;  /* Allow height to adjust to content */
        min-height: 3;
        content-align: center middle;
        background: $boost;
        color: $text;
        text-wrap: wrap;  /* Enable text wrapping */
        overflow-y: auto;  /* Enable vertical scrolling if needed */
        padding: 0 1;  /* Add some horizontal padding */
    }
    """

    def watch_location(self, new_value: str) -> None:
        """Update displayed location."""
        self.update(f"Location: {new_value}")

class GameUI(App):
    """Main game interface."""
    
    # Define key bindings with key combinations instead of single keys
    BINDINGS = [
        ("ctrl+o", "toggle_overlay", "Menu"),
        ("escape", "close_overlay", "Close"),
        ("up", "select_previous", "Previous"),
        ("down", "select_next", "Next"),
        ("enter", "select", "Select"),
    ]

    CSS = """
    Screen {
        layout: grid;
        grid-size: 1;
        padding: 1;
    }

    GameOutput {
        width: 100%;
    }

    LocationBar {
        width: 100%;
    }

    #input-container {
        height: 3;
        dock: bottom;
        width: 100%;
    }

    Input {
        dock: bottom;
        width: 100%;
        content-align: left middle;
    }
    """

    def __init__(self):
        super().__init__()
        self.overlay = None
        self.dialogue_mode = DialogueMode(self)

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=True)
        yield LocationBar()
        yield GameOutput(id="game-output")
        yield Horizontal(
            Input(placeholder="Enter your command...", id="game-input"),
            id="input-container"
        )
        yield Footer()

    def on_mount(self) -> None:
        """Called when app is mounted."""
        self.game_output = self.query_one("#game-output", GameOutput)
        self.game_input = self.query_one("#game-input", Input)
        self.location_bar = self.query_one(LocationBar)
        
        # Set initial location
        if hasattr(self, 'game_engine'):
            self.location_bar.location = self.game_engine.current_location
        
        # Give input focus
        self.game_input.focus()

    def on_input_submitted(self, message: Input.Submitted) -> None:
        """Handle input submission."""
        command = message.value.strip()
        self.game_input.value = ""  # Clear input

        if not command:
            return

        # If in dialogue mode, handle enter key as option selection
        if self.dialogue_mode.is_active:
            self.action_select()
            return

        # Echo command
        self.game_output.write("\n\n")
        self.game_output.write(f"> {command}")
        self.game_output.write("\n\n")
        
        try:
            # Process command through game engine
            response = self.game_engine.process_input(command)
            
            # Check for quit command
            if response == "__quit__":
                self.exit()
            else:
                self.game_output.write(response)
                self.game_output.write("\n\n")
                
            # Update location if it changed
            self.location_bar.location = self.game_engine.current_location
        except Exception as e:
            self.game_output.write(f"Error: {str(e)}")

    def action_select_previous(self) -> None:
        """Select the previous dialogue option."""
        if self.dialogue_mode.is_active:
            self.dialogue_mode.select_previous()
            # Keep focus on the input box
            self.game_input.focus()

    def action_select_next(self) -> None:
        """Select the next dialogue option."""
        if self.dialogue_mode.is_active:
            self.dialogue_mode.select_next()
            # Keep focus on the input box
            self.game_input.focus()

    def action_select(self) -> None:
        """Select the current dialogue option."""
        if self.dialogue_mode.is_active:
            selected_option_id = self.dialogue_mode.select_current()
            if selected_option_id == "end_conversation":
                self.dialogue_mode.end_dialogue()
            else:
                # Process the selected option through the dialogue handler
                responses = self.game_engine.dialogue_handler.select_option(
                    selected_option_id, self.game_engine.game_state
                )
                self.dialogue_mode.process_responses(responses)
                self.dialogue_mode.update_display()
            # Keep focus on the input box
            self.game_input.focus()

    def action_toggle_overlay(self) -> None:
        """Toggle the game overlay."""
        if isinstance(self.screen, GameOverlay):
            self.pop_screen()
        else:
            self.push_screen(GameOverlay())

    def action_close_overlay(self) -> None:
        """Close the overlay if it's open."""
        if isinstance(self.screen, GameOverlay):
            self.pop_screen()
        elif self.dialogue_mode.is_active:
            self.dialogue_mode.end_dialogue()
            # Keep focus on the input box
            self.game_input.focus()

    def on_key(self, event) -> None:
        """Handle key events."""
        # If in dialogue mode and input is focused, handle arrow keys and enter
        if self.dialogue_mode.is_active and self.game_input.has_focus:
            if event.key == "up":
                event.prevent_default()
                self.action_select_previous()
            elif event.key == "down":
                event.prevent_default()
                self.action_select_next()
            elif event.key == "enter":
                event.prevent_default()
                self.action_select()
            elif event.key == "tab":
                event.prevent_default()
                self.action_toggle_overlay()
            return

        # Handle tab key for overlay
        if event.key == "tab":
            event.prevent_default()
            self.action_toggle_overlay()