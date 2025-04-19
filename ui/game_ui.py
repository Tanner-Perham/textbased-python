from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer, Vertical, Horizontal
from textual.widgets import Header, Footer, Input, Static, Log
from textual.reactive import reactive
from textual.binding import Binding
from textual.screen import Screen
from textual.keys import Keys
from .overlay import GameOverlay
from .dialogue_ui import DialogueMode
import asyncio

class GameOutput(ScrollableContainer):
    """Widget for game output with scrolling."""
    
    DEFAULT_CSS = """
    GameOutput {
        height: 100%;
        border: solid white;
        padding: 1 2;
        background: $boost;
        color: $text;
        overflow-y: auto;
        width: 100%;
    }
    
    GameOutput > Static {
        text-wrap: wrap;
        width: 100%;
        margin-bottom: 1;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.output_widgets = []
        self._text_lines = []  # Store the text content of each widget
        self._pending_text = ["Welcome to the game! Type 'help' for a list of commands."]

    @property
    def lines(self):
        """Get all text lines as a list - maintains compatibility with Log widget."""
        return self._text_lines.copy()

    def write(self, text: str) -> None:
        """Write text to the output with proper wrapping."""
        if not self.is_mounted:
            # Store text until we're mounted
            self._pending_text.append(text)
            return
        
        # For an empty string or just whitespace, create an empty line
        if not text.strip() and text:
            static = Static("")
            self.output_widgets.append(static)
            self._text_lines.append("")  # Add empty line to text lines
            self.mount(static)
            return
            
        # Escape any characters that could be interpreted as Rich markup
        escaped_text = text.replace("[", "\\[").replace("]", "]").replace(":", ":")
            
        # Create a Static widget for the text
        static = Static(escaped_text)
        self.output_widgets.append(static)
        self._text_lines.append(text)  # Store the original text content
        self.mount(static)
        self.scroll_end(animate=False)  # Ensure we scroll to the new text

    def clear(self) -> None:
        """Clear all output text."""
        for widget in self.output_widgets[:]:
            widget.remove()
        self.output_widgets.clear()
        self._text_lines.clear()  # Clear the text lines as well

    def compose(self) -> ComposeResult:
        """Initially empty."""
        # No initial widgets
        yield from []

    def on_mount(self) -> None:
        """Called when widget is added to the app."""
        # Display any pending text
        for text in self._pending_text:
            if not text.strip() and text:
                # Empty line for spacing
                static = Static("")
                self.output_widgets.append(static)
                self._text_lines.append("")  # Add empty line to text lines
            else:
                # Escape any characters that could be interpreted as Rich markup
                escaped_text = text.replace("[", "\\[").replace("]", "\\]").replace(":", "\\:")
                
                # Create a Static widget for the text
                static = Static(escaped_text)
                self.output_widgets.append(static)
                self._text_lines.append(text)  # Store the original text content
            self.mount(static)
        self._pending_text = []
        self.scroll_end(animate=False)

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
        layout: vertical;
        height: 100%;
        width: 100%;
    }

    Header {
        height: 3;
    }

    LocationBar {
        height: 3;
        width: 100%;
    }

    #game-output {
        height: 1fr;
        width: 100%;
    }

    #input-container {
        height: 3;
        width: 100%;
    }

    Input {
        width: 100%;
    }

    Footer {
        height: 1;
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

        # Echo command with spacing
        self.game_output.write("")  # Empty line for spacing
        self.game_output.write(f"> {command}")
        self.game_output.write("")  # Empty line for spacing
        
        try:
            # Process command through game engine
            response = self.game_engine.process_input(command)
            
            # Check for quit command
            if response == "__quit__":
                self.exit()
            else:
                # Split response by double newlines and write each paragraph separately
                paragraphs = response.split('\n\n')
                for paragraph in paragraphs:
                    if paragraph.strip():  # Only write non-empty paragraphs
                        self.game_output.write(paragraph)
                        self.game_output.write("")  # Empty line for spacing
                
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
                print(f"GameUI: Selecting option {selected_option_id}")
                responses = self.game_engine.dialogue_handler.select_option(
                    selected_option_id, self.game_engine.game_state
                )
                # Create an async task to process responses since process_responses is now async
                asyncio.create_task(self._async_process_dialogue_responses(responses))
            # Keep focus on the input box
            self.game_input.focus()
    
    async def _async_process_dialogue_responses(self, responses):
        """Process dialogue responses asynchronously."""
        # Process the responses (will wait for any skill checks to complete)
        await self.dialogue_mode.process_responses(responses)
        # Update the display after all responses are processed
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
        # If in dialogue mode and input is focused, handle keys
        if self.dialogue_mode.is_active and self.game_input.has_focus:
            # First check if the dialogue mode itself wants to handle this key
            if self.dialogue_mode.handle_key(event):
                return
                
            # Handle other dialogue-specific keys
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