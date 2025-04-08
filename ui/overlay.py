"""Game overlay UI component."""
from typing import List
from textual.containers import Grid, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, TabPane, TabbedContent, Static
from textual.binding import Binding

class GameOverlay(ModalScreen):
    """Modal overlay for game menus."""

    BINDINGS = [
        Binding("escape", "app.close_overlay", "Close"),
        Binding("tab", "app.close_overlay", "Close"),
    ]

    DEFAULT_CSS = """
    GameOverlay {
        align: center middle;
    }

    #overlay-container {
        width: 80%;
        height: 80%;
        border: solid $primary;
        background: $surface;
        margin: 2 4;
    }

    TabbedContent {
        height: 100%;
        background: $surface;
    }

    TabPane {
        padding: 1 2;
        height: auto;
    }

    .skill-grid {
        grid-size: 2;
        grid-gutter: 1 2;
        padding: 1;
    }

    .skill-entry {
        height: 3;
        width: 100%;
        layout: grid;
        grid-size: 3;
        padding: 1;
        background: $boost;
        color: $text;
    }

    .quest-entry {
        padding: 1;
        background: $boost;
        margin-bottom: 1;
        color: $text;
    }

    .inventory-slot {
        width: 100%;
        padding: 1;
        background: $boost;
        color: $text;
    }
    """

    def compose(self):
        """Create child widgets for the overlay."""
        with Vertical(id="overlay-container"):
            with TabbedContent():
                # Inventory Tab
                with TabPane("Inventory", id="inventory"):
                    with Grid(classes="inventory-grid"):
                        for item in self.app.game_engine.game_state.inventory:
                            yield Static(f"{item.name} - {item.description}", 
                                       classes="inventory-slot")

                # Skills Tab
                with TabPane("Skills", id="skills"):
                    with Grid(classes="skill-grid") as grid:
                        skills = self.app.game_engine.game_state.skills
                        for skill_name, level in skills.items():
                            with Static(classes="skill-entry"):
                                yield Static(f"{skill_name.title()}")
                                yield Static(f"Level: {level}")
                                yield Button("+", id=f"skill_{skill_name}")

                # Quests Tab
                with TabPane("Quests", id="quests"):
                    with Vertical():
                        quests = self.app.game_engine.quest_manager.get_all_quests()
                        for quest in quests:
                            with Static(classes="quest-entry"):
                                yield Static(f"{quest.title} - {quest.status}")
                                yield Static(quest.description)

    def _create_skills_grid(self, grid: Grid) -> List[Static]:
        """Create and return skill entries for the grid."""
        skill_widgets = []
        skills = self.app.game_engine.game_state.skills

        for skill_name, level in skills.items():
            # Create the container and mount it to the grid first
            container = Static(classes="skill-entry")
            grid.mount(container)
            
            # Create widgets
            name_label = Static(f"{skill_name.title()}")
            level_label = Static(f"Level: {level}")
            upgrade_button = Button("+", id=f"skill_{skill_name}")
            
            # Now that container is mounted, we can mount child widgets
            container.mount(name_label, level_label, upgrade_button)
            
            skill_widgets.append(container)

        return skill_widgets

    def refresh_skills(self) -> None:
        """Refresh the skills display."""
        skills_pane = self.query_one("#skills", TabPane)
        old_grid = skills_pane.query_one(".skill-grid")
        
        with Grid(classes="skill-grid") as new_grid:
            skills = self.app.game_engine.game_state.skills
            for skill_name, level in skills.items():
                with Static(classes="skill-entry"):
                    new_grid.mount(Static(f"{skill_name.title()}"))
                    new_grid.mount(Static(f"Level: {level}"))
                    new_grid.mount(Button("+", id=f"skill_{skill_name}"))
        
        skills_pane.mount(new_grid)
        old_grid.remove()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id and event.button.id.startswith("skill_"):
            skill_name = event.button.id.replace("skill_", "")
            if self.app.game_engine.upgrade_skill(skill_name):
                self.refresh_skills()