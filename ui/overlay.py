"""Game overlay UI component."""
from typing import List, Optional, Dict, Any
from textual.containers import Grid, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, TabPane, TabbedContent, Static
from textual.binding import Binding
from ui.quest_ui import QuestTab
from game.game_state import GameState
from config.config_loader import Quest

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

    .debug-quest {
        padding: 1;
        margin-bottom: 1;
        background: $boost;
        color: $text;
    }

    .debug-stage {
        padding-left: 2;
        margin-bottom: 1;
        background: $boost;
        color: $text;
    }

    .debug-objective {
        padding-left: 4;
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
                    yield QuestTab(self.app.game_engine.quest_manager, self.app.game_engine.game_state)

                # Debug Tab
                with TabPane("Debug", id="debug"):
                    yield Static("Quest Status Debug", classes="section-header")
                    with Vertical(id="debug-quests"):
                        for quest in self.app.game_engine.game_state.get_all_quests().values():
                            with Static(classes="debug-quest"):
                                yield Static(f"Quest: {quest.title} (ID: {quest.id}) - Status: {quest.status}")
                                if quest.stages:
                                    yield Static("Stages:")
                                    for stage in quest.stages:
                                        yield Static(f"  - {stage.title} (ID: {stage.id}) - Status: {stage.status}")
                                        if stage.objectives:
                                            yield Static("    Objectives:")
                                            for obj in stage.objectives:
                                                status = "✓" if self.app.game_engine.game_state.is_objective_completed(quest.id, obj.get('id', '')) else "○"
                                                optional = "(Optional) " if obj.get('is_optional', False) else ""
                                                yield Static(f"      {status} {optional}{obj.get('description', '')}")

    def on_mount(self) -> None:
        """Called when the widget is mounted to the screen."""
        # Set up a timer to periodically check for quest updates
        self.set_interval(1.0, self._check_quest_updates)

    def _check_quest_updates(self) -> None:
        """Check for quest updates and refresh if needed."""
        # Get current quest states
        current_quests = self.app.game_engine.game_state.get_all_quests()
        
        # Get previous quest states from the UI
        debug_quests = self.query_one("#debug-quests", Vertical)
        if debug_quests:
            # Check for changes in quest states
            needs_refresh = False
            
            # Check if any quests have been added or removed
            ui_quest_ids = set(quest.id for quest in debug_quests.query(".debug-quest"))
            current_quest_ids = set(current_quests.keys())
            
            if ui_quest_ids != current_quest_ids:
                needs_refresh = True
            
            # Check if any quest statuses have changed
            if not needs_refresh:
                for quest_id, quest in current_quests.items():
                    ui_quest = next((q for q in debug_quests.query(".debug-quest") 
                                   if q.id == quest_id), None)
                    if ui_quest and ui_quest.status != quest.status:
                        needs_refresh = True
                        break
            
            # Check if any quest stages have changed
            if not needs_refresh:
                for quest_id, quest in current_quests.items():
                    current_stage = self.app.game_engine.game_state.get_active_stage(quest_id)
                    ui_quest = next((q for q in debug_quests.query(".debug-quest") 
                                   if q.id == quest_id), None)
                    if ui_quest and ui_quest.active_stage != current_stage:
                        needs_refresh = True
                        break
            
            if needs_refresh:
                self.refresh_debug_panel()

    def refresh_debug_panel(self) -> None:
        """Refresh the debug panel content."""
        debug_pane = self.query_one("#debug", TabPane)
        debug_quests = debug_pane.query_one("#debug-quests", Vertical)
        
        if debug_quests:
            debug_quests.remove_children()
            
            for quest in self.app.game_engine.game_state.get_all_quests().values():
                # Create quest container
                quest_container = Static(classes="debug-quest")
                debug_quests.mount(quest_container)
                
                # Add quest header
                quest_container.mount(Static(f"Quest: {quest.title} (ID: {quest.id}) - Status: {quest.status}"))
                
                if quest.stages:
                    # Add stages header
                    quest_container.mount(Static("Stages:"))
                    
                    for stage in quest.stages:
                        # Add stage info
                        quest_container.mount(Static(f"  - {stage.title} (ID: {stage.id}) - Status: {stage.status}"))
                        
                        if stage.objectives:
                            # Add objectives header
                            quest_container.mount(Static("    Objectives:"))
                            
                            for obj in stage.objectives:
                                status = "✓" if self.app.game_engine.game_state.is_objective_completed(quest.id, obj.get('id', '')) else "○"
                                optional = "(Optional) " if obj.get('is_optional', False) else ""
                                quest_container.mount(Static(f"      {status} {optional}{obj.get('description', '')}"))

    def _create_debug_view(self) -> Vertical:
        """Create the debug view showing quest states."""
        debug_view = Vertical()
        
        # Quest Status Section
        debug_view.mount(Static("Quest Status Debug", classes="section-header"))
        
        # Get all quests from the game state
        for quest in self.app.game_engine.game_state.get_all_quests().values():
            with Static(classes="debug-quest") as quest_container:
                # Quest header with status
                quest_container.mount(Static(
                    f"Quest: {quest.title} (ID: {quest.id}) - Status: {quest.status}"
                ))
                
                # Current stage if any
                current_stage_id = self.app.game_engine.game_state.get_active_stage(quest.id)
                if current_stage_id:
                    stage = next((s for s in quest.stages if s.id == current_stage_id), None)
                    if stage:
                        with Static(classes="debug-stage") as stage_container:
                            stage_container.mount(Static(
                                f"Current Stage: {stage.title} (ID: {stage.id}) - Status: {stage.status}"
                            ))
                            
                            # Objectives
                            for obj in stage.objectives:
                                is_completed = self.app.game_engine.game_state.is_objective_completed(quest.id, obj.id)
                                status = "✓" if is_completed else "○"
                                with Static(classes="debug-objective") as obj_container:
                                    obj_container.mount(Static(
                                        f"{status} {obj.description} (ID: {obj.id})"
                                    ))
        
        return debug_view

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

class OverlayUI:
    """UI components for displaying game overlay information."""
    
    def __init__(self, game_state: GameState):
        """Initialize the overlay UI."""
        self.game_state = game_state

    def get_active_quests(self) -> List[Dict[str, Any]]:
        """Get information about active quests for the overlay."""
        quests = []
        for quest in self.game_state.get_active_quests():
            current_stage = self.game_state.get_active_stage(quest.id)
            if current_stage:
                quests.append({
                    'id': quest.id,
                    'title': quest.title,
                    'current_stage': current_stage,
                    'is_main_quest': quest.is_main_quest
                })
        return quests

    def get_quest_progress(self, quest_id: str) -> Optional[Dict[str, Any]]:
        """Get progress information for a specific quest."""
        return self.game_state.get_quest_progress(quest_id)

    def get_all_quests_summary(self) -> Dict[str, int]:
        """Get summary of all quests by status."""
        return {
            'active': len(self.game_state.get_active_quests()),
            'completed': len(self.game_state.get_completed_quests()),
            'failed': len(self.game_state.get_failed_quests())
        }