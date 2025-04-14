"""Integration tests for the quest system."""

import pytest
from game.engine import GameEngine
from game.game_state import GameState, QuestStatus
from config.config_loader import GameConfig
from dialogue.manager import DialogueManager
from dialogue.converter import convert_dialogue_trees
from ui.quest_ui import QuestTab, QuestList
from textual.app import App
from quest.quest_manager import QuestManager
from quest.quest import Quest, QuestStage

@pytest.fixture
def game_engine():
    """Create a test game engine instance."""
    config = GameConfig.load("game_config.yaml")
    engine = GameEngine(config)
    return engine

@pytest.fixture
def dialogue_manager(game_engine):
    """Create a test dialogue manager instance."""
    manager = DialogueManager()
    manager.game_engine = game_engine
    manager.set_dialogue_tree(convert_dialogue_trees(game_engine.config))
    game_engine.dialogue_handler = manager
    return manager

@pytest.fixture
def game_state():
    """Create a test game state instance."""
    return GameState()

@pytest.fixture
def quest_manager(game_state):
    """Create a test quest manager instance."""
    return QuestManager(game_state)

@pytest.fixture
def test_quest():
    """Create a test quest matching the missing_locket structure."""
    return Quest(
        id="missing_locket",
        title="The Missing Locket",
        description="Help Eliza find her missing silver locket.",
        short_description="Find Eliza's lost locket",
        importance="Optional",
        is_main_quest=False,
        is_hidden=False,
        status="NotStarted",
        stages=[
            QuestStage(
                id="search_town",
                title="Search the Town",
                description="Look for clues about the missing locket.",
                status="NotStarted",
                objectives=[
                    {
                        "id": "talk_to_eliza",
                        "description": "Get more information from Eliza about the locket",
                        "is_completed": False,
                        "is_optional": False
                    },
                    {
                        "id": "search_fountain",
                        "description": "Search around the town square fountain",
                        "is_completed": False,
                        "is_optional": False
                    }
                ]
            ),
            QuestStage(
                id="find_locket",
                title="Find the Locket",
                description="Follow the clues to find the missing locket.",
                status="NotStarted",
                objectives=[
                    {
                        "id": "search_garden",
                        "description": "Search the garden for the locket",
                        "is_completed": False,
                        "is_optional": False
                    },
                    {
                        "id": "return_locket",
                        "description": "Return the locket to Eliza",
                        "is_completed": False,
                        "is_optional": False
                    }
                ]
            )
        ]
    )

def test_quest_initialization(game_state, quest_manager, test_quest):
    """Test that a quest is properly initialized."""
    game_state.add_quest(test_quest)
    quest = game_state.get_quest("missing_locket")
    
    assert quest is not None
    assert quest.id == "missing_locket"
    assert quest.status == QuestStatus.NotStarted
    assert len(quest.stages) == 2
    assert quest.stages[0].id == "search_town"
    assert quest.stages[1].id == "find_locket"

def test_quest_start(game_state, quest_manager, test_quest):
    """Test starting a quest."""
    game_state.add_quest(test_quest)
    game_state.update_quest_status("missing_locket", QuestStatus.InProgress)
    
    quest = game_state.get_quest("missing_locket")
    assert quest.status == QuestStatus.InProgress
    assert quest.stages[0].status == QuestStatus.InProgress

def test_quest_objective_completion(game_state, quest_manager, test_quest):
    """Test completing quest objectives."""
    game_state.add_quest(test_quest)
    game_state.update_quest_status("missing_locket", QuestStatus.InProgress)
    
    # Complete first objective
    game_state.add_completed_objective("missing_locket", "talk_to_eliza")
    assert game_state.is_objective_completed("missing_locket", "talk_to_eliza")
    
    # Complete second objective
    game_state.add_completed_objective("missing_locket", "search_fountain")
    assert game_state.is_objective_completed("missing_locket", "search_fountain")

def test_quest_stage_advancement(game_state, quest_manager, test_quest):
    """Test advancing through quest stages."""
    game_state.add_quest(test_quest)
    game_state.update_quest_status("missing_locket", QuestStatus.InProgress)
    
    # Complete all objectives in first stage
    game_state.add_completed_objective("missing_locket", "talk_to_eliza")
    game_state.add_completed_objective("missing_locket", "search_fountain")
    
    # Advance to next stage
    game_state.set_active_stage("missing_locket", "find_locket")
    assert game_state.get_active_stage("missing_locket") == "find_locket"

def test_quest_completion(game_state, quest_manager, test_quest):
    """Test completing a quest."""
    game_state.add_quest(test_quest)
    game_state.update_quest_status("missing_locket", QuestStatus.InProgress)
    
    # Complete all objectives
    game_state.add_completed_objective("missing_locket", "talk_to_eliza")
    game_state.add_completed_objective("missing_locket", "search_fountain")
    game_state.set_active_stage("missing_locket", "find_locket")
    game_state.add_completed_objective("missing_locket", "search_garden")
    game_state.add_completed_objective("missing_locket", "return_locket")
    
    # Complete quest
    game_state.update_quest_status("missing_locket", QuestStatus.Completed)
    quest = game_state.get_quest("missing_locket")
    assert quest.status == QuestStatus.Completed

def test_quest_ui_updates(game_state, quest_manager, test_quest):
    """Test that the quest UI updates when quests change."""
    game_state.add_quest(test_quest)
    
    # Create a test UI
    class TestApp(App):
        def compose(self):
            yield QuestTab(quest_manager, game_state)
    
    app = TestApp()
    quest_tab = app.query_one(QuestTab)
    
    # Start quest and verify UI update
    game_state.update_quest_status("missing_locket", QuestStatus.InProgress)
    app.refresh()
    
    active_quests = quest_tab.query("#active-quests")
    assert "missing_locket" in [quest.id for quest in active_quests]
    
    # Complete quest and verify UI update
    game_state.update_quest_status("missing_locket", QuestStatus.Completed)
    app.refresh()
    
    completed_quests = quest_tab.query("#completed-quests")
    assert "missing_locket" in [quest.id for quest in completed_quests]

def test_quest_initialization(game_engine):
    """Test that quests are properly initialized."""
    # Check that main quest exists but is not started
    main_quest = game_engine.quest_manager.get_quest("main_investigation")
    assert main_quest is not None
    # The main quest should be started automatically
    assert game_engine.game_state.get_quest_status("main_investigation") == "In Progress"

def test_quest_stage_advancement(game_engine):
    """Test advancing through quest stages."""
    # Start the main quest
    game_engine.start_quest("main_investigation")
    
    # Complete all objectives in first stage
    quest = game_engine.quest_manager.get_quest("main_investigation")
    stage = quest.stages[0]
    for objective in stage.objectives:
        game_engine.quest_manager.complete_objective("main_investigation", objective["id"])
    
    # Verify stage advanced
    current_stage = game_engine.quest_manager.get_current_stage("main_investigation")
    assert current_stage["id"] == "search_office" 