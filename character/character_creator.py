"""
Character creation UI for the text-based adventure game.
"""

from typing import Callable, List, Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Label, Static, Footer

from character.character_creation import ARCHETYPES, apply_archetype


class SkillDisplay(Static):
    """Display for a character's skills."""
    
    def __init__(self, skills: dict, **kwargs):
        """Initialize the skill display."""
        super().__init__(**kwargs)
        self.skills = skills
    
    def compose(self) -> ComposeResult:
        """Compose the skill display."""
        with Vertical(classes="skill-list"):
            # Group skills by category
            cognitive = ["logic", "perception", "memory"]
            social = ["empathy", "authority", "suggestion"]
            physical = ["composure", "agility", "endurance"]
            
            yield Label("Cognitive Skills", classes="skill-category")
            for skill in cognitive:
                if skill in self.skills:
                    yield Label(f"{skill.title()}: {self.skills[skill]}", classes="skill-value")
                else:
                    yield Label(f"{skill.title()}: 0", classes="skill-value")
            
            yield Label("Social Skills", classes="skill-category")
            for skill in social:
                if skill in self.skills:
                    yield Label(f"{skill.title()}: {self.skills[skill]}", classes="skill-value")
                else:
                    yield Label(f"{skill.title()}: 0", classes="skill-value")
            
            yield Label("Physical Skills", classes="skill-category")
            for skill in physical:
                if skill in self.skills:
                    yield Label(f"{skill.title()}: {self.skills[skill]}", classes="skill-value")
                else:
                    yield Label(f"{skill.title()}: 0", classes="skill-value")


class ArchetypeCard(Static):
    """A card displaying information about a character archetype."""
    
    def __init__(self, archetype_id: str, **kwargs):
        """Initialize the archetype card."""
        super().__init__(**kwargs)
        self.archetype_id = archetype_id
        self.archetype = ARCHETYPES[archetype_id]
        self.add_class("archetype-card")
    
    def compose(self) -> ComposeResult:
        """Compose the archetype card."""
        with Vertical():
            yield Label(self.archetype.name, classes="archetype-name")
            yield Static(self.archetype.description, classes="archetype-description")
            
            yield SkillDisplay(self.archetype.starting_skills, classes="archetype-skills")
            
            yield Label("Starting Equipment:", classes="equipment-header")
            for item_id in self.archetype.starting_equipment_ids:
                yield Label(f"• {item_id.replace('_', ' ').title()}", classes="equipment-item")


class CharacterCreationScreen(Screen):
    """Character creation screen for selecting a detective archetype."""
    
    BINDINGS = [
        ("1", "select_archetype('analytical')", "Choose Analytical Detective"),
        ("2", "select_archetype('persuasive')", "Choose Persuasive Detective"),
        ("3", "select_archetype('field')", "Choose Field Detective"),
    ]
    
    CSS = """
    CharacterCreationScreen {
        background: $surface;
        padding: 2 4;
        height: 100%;
        overflow-y: auto;
    }
    
    .title {
        text-align: center;
        text-style: bold;
        width: 100%;
        margin-bottom: 1;
        background: $accent;
        color: $text;
        padding: 1;
    }
    
    .subtitle {
        text-align: center;
        width: 100%;
        margin-bottom: 2;
    }
    
    .key-instructions {
        text-align: center;
        width: 100%;
        margin-bottom: 2;
        background: $primary-darken-1;
        padding: 1;
    }
    
    .archetype-container {
        width: 100%;
        height: 95%;
        margin: 1 0;
        overflow-y: auto;
    }
    
    .archetype-card {
        width: 1fr;
        height: auto;
        border: heavy $accent;
        padding: 1;
        margin: 0 0;
        overflow-y: auto;
    }
    
    .archetype-name {
        text-style: bold;
        text-align: center;
        width: 100%;
        margin-bottom: 1;
        color: $text-muted;
        background: $primary;
        padding: 1;
    }
    
    .archetype-description {
        margin-bottom: 1;
    }
    
    .skill-category {
        text-style: bold;
        margin-top: 1;
    }
    
    .skill-value {
        margin-left: 1;
    }
    
    .equipment-header {
        text-style: bold;
        margin-top: 1;
    }
    
    .equipment-item {
        margin-left: 1;
    }
    
    .button-container {
        width: 100%;
        height: auto;
        margin-top: 2;
        margin-bottom: 1;
        dock: bottom;
        padding: 1;
        background: $surface;
    }
    
    .selection-button {
        width: 1fr;
        height: 5;
        background: $success;
        color: $text;
        text-style: bold;
        content-align: center middle;
        margin: 0 1;
        padding: 1;
    }
    
    .selection-button:hover {
        background: $accent;
    }
    """
    
    def __init__(self, on_complete: Callable[[str], None]):
        """Initialize the character creation screen."""
        super().__init__()
        self.on_complete = on_complete
    
    def compose(self) -> ComposeResult:
        """Compose the character creation screen."""
        yield Label("CHARACTER CREATION", classes="title")
        yield Label("Choose your detective archetype", classes="subtitle")
        # yield Label("Or press: 1 for Analytical, 2 for Persuasive, 3 for Field", classes="key-instructions")
        
        # Display archetype info cards
        with Horizontal(classes="archetype-container"):
            for archetype_id in ARCHETYPES:
                yield ArchetypeCard(archetype_id)
        
        # Add large selection buttons at the bottom
        with Horizontal(classes="button-container"):
            yield Button("SELECT ANALYTICAL DETECTIVE", id="select_analytical", classes="selection-button")
            yield Button("SELECT PERSUASIVE DETECTIVE", id="select_persuasive", classes="selection-button")
            yield Button("SELECT FIELD DETECTIVE", id="select_field", classes="selection-button")
        
        # Add footer with key bindings
        yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        if button_id and button_id.startswith("select_"):
            archetype_id = button_id.replace("select_", "")
            if archetype_id in ARCHETYPES:
                self.select_archetype(archetype_id)
    
    def action_select_archetype(self, archetype_id: str) -> None:
        """Action to select an archetype by ID."""
        if archetype_id in ARCHETYPES:
            self.select_archetype(archetype_id)
    
    def select_archetype(self, archetype_id: str) -> None:
        """Handle archetype selection."""
        self.on_complete(archetype_id)
        self.app.pop_screen()


def create_character(game_engine) -> None:
    """Launch the character creation process."""
    def on_archetype_selected(archetype_id: str) -> None:
        # Apply the selected archetype to the player
        apply_archetype(game_engine.game_state, archetype_id)
        
        # Replace the character creation screen with the game screen
        game_engine.start_game()
    
    # Show the character creation screen
    character_screen = CharacterCreationScreen(on_archetype_selected)
    game_engine.app.push_screen(character_screen) 