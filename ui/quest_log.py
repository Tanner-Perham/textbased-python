from textual.widgets import TreeControl
from textual.screen import ModalScreen

class QuestLog(ModalScreen):
    """Quest log window."""
    
    def compose(self) -> ComposeResult:
        yield TreeControl("Quests", {})

    def on_mount(self) -> None:
        """Populate quest data."""
        tree = self.query_one(TreeControl)
        for quest in self.app.game_engine.quest_manager.get_all_quests():
            tree.add(quest.title, quest.description)