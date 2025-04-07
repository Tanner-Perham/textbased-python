from textual.containers import Vertical
from textual.widgets import Static, Button
from textual.screen import ModalScreen

class DialogueWindow(ModalScreen):
    """Modal dialogue window."""
    
    def __init__(self, dialogue_data):
        super().__init__()
        self.dialogue_data = dialogue_data

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(self.dialogue_data.text, id="dialogue-text")
            for option in self.dialogue_data.options:
                yield Button(option.text, id=f"option-{option.id}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle dialogue option selection."""
        option_id = event.button.id.replace("option-", "")
        self.dismiss(option_id)