import pytest
from unittest.mock import MagicMock
from quest.quest_manager import QuestManager, NotificationType
from game.game_state import GameState, QuestStatus
from config.config_loader import Quest, QuestStage

@pytest.fixture
def setup_quest_manager():
    """Fixture to set up the QuestManager and mock data."""
    # Create game state
    game_state = GameState()
    
    # Create mock quests
    quests = {
        "main_quest": Quest(
            id="main_quest",
            title="The Main Quest",
            short_description="A quest to test the quest system",
            description="A quest to test the quest system",
            importance="High",
            is_main_quest=True,
            is_hidden=False,
            stages=[
                QuestStage(
                    id="stage1",
                    title="First Stage",
                    description="Complete the first objective",
                    notification_text="You've started the main quest!",
                    status="NotStarted",
                    objectives=[
                        {
                            "id": "obj1",
                            "description": "Find the clue",
                            "is_completed": False,
                            "is_optional": False,
                            "completion_events": []
                        }
                    ]
                ),
                QuestStage(
                    id="stage2",
                    title="Second Stage",
                    description="Complete the second objective",
                    notification_text="You've progressed to stage 2!",
                    status="NotStarted",
                    objectives=[
                        {
                            "id": "obj2",
                            "description": "Talk to the NPC",
                            "is_completed": False,
                            "is_optional": False,
                            "completion_events": []
                        }
                    ]
                )
            ]
        ),
        "side_quest": Quest(
            id="side_quest",
            title="A Side Quest",
            short_description="A side quest to test the quest system",
            description="An optional quest to test the quest system",
            importance="Medium",
            is_main_quest=False,
            is_hidden=False,
            stages=[
                QuestStage(
                    id="stage1",
                    title="First Stage",
                    description="Complete the side objective",
                    notification_text="You've started the side quest!",
                    status="NotStarted",
                    objectives=[
                        {
                            "id": "obj1",
                            "description": "Find the item",
                            "is_completed": False,
                            "is_optional": False,
                            "completion_events": []
                        }
                    ]
                )
            ]
        )
    }
    
    # Add quests to game state
    for quest in quests.values():
        game_state.add_quest(quest)
    
    manager = QuestManager(game_state)
    return manager, game_state, quests

def test_get_all_quests(setup_quest_manager):
    """Test getting all quests."""
    manager, game_state, quests = setup_quest_manager
    assert manager.get_all_quests() == game_state.quests

def test_get_quest(setup_quest_manager):
    """Test getting a specific quest."""
    manager, _, _ = setup_quest_manager
    quest = manager.get_quest("main_quest")
    assert quest is not None
    assert quest.id == "main_quest"
    assert quest.title == "The Main Quest"

def test_get_active_quests(setup_quest_manager):
    """Test getting active quests."""
    manager, _, _ = setup_quest_manager
    # Start a quest
    manager.start_quest("main_quest")
    active_quests = manager.get_active_quests()
    assert len(active_quests) == 1
    assert active_quests[0].id == "main_quest"

def test_start_quest(setup_quest_manager):
    """Test starting a quest."""
    manager, game_state, _ = setup_quest_manager
    assert manager.start_quest("main_quest")
    assert game_state.get_quest_status("main_quest") == QuestStatus.InProgress
    assert game_state.get_active_stage("main_quest") == "stage1"
    
    # Check notifications
    notifications = manager.get_active_notifications()
    assert len(notifications) == 1
    assert notifications[0].notification_type == NotificationType.QuestStarted

def test_complete_objective(setup_quest_manager):
    """Test completing a quest objective."""
    manager, game_state, _ = setup_quest_manager
    # Start the quest first
    manager.start_quest("main_quest")
    
    # Complete the objective
    assert manager.complete_objective("main_quest", "obj1")
    assert game_state.is_quest_objective_completed("main_quest", "obj1")
    
    # Check notifications
    notifications = manager.get_active_notifications()
    assert len(notifications) == 2  # One for start, one for completion
    assert notifications[1].notification_type == NotificationType.ObjectiveCompleted

def test_advance_quest(setup_quest_manager):
    """Test advancing a quest to the next stage."""
    manager, game_state, _ = setup_quest_manager
    # Start the quest and complete first objective
    manager.start_quest("main_quest")
    manager.complete_objective("main_quest", "obj1")
    
    # Advance to next stage
    assert manager.advance_quest("main_quest", "stage2")
    assert game_state.get_active_stage("main_quest") == "stage2"
    
    # Check notifications
    notifications = manager.get_active_notifications()
    assert len(notifications) == 3  # Start, complete, advance
    assert notifications[2].notification_type == NotificationType.QuestUpdated

def test_fail_quest(setup_quest_manager):
    """Test failing a quest."""
    manager, game_state, _ = setup_quest_manager
    # Start the quest first
    manager.start_quest("main_quest")
    
    # Fail the quest
    manager.fail_quest("main_quest")
    assert game_state.get_quest_status("main_quest") == "Failed"
    
    # Check notifications
    notifications = manager.get_active_notifications()
    assert len(notifications) == 2  # Start and fail
    assert notifications[1].notification_type == NotificationType.QuestFailed

def test_check_quest_updates(setup_quest_manager):
    """Test checking for quest updates."""
    manager, _, _ = setup_quest_manager
    # Start the quest
    manager.start_quest("main_quest")
    
    # Check updates
    manager.check_all_quest_updates()
    
    # Verify notifications are still present
    notifications = manager.get_active_notifications()
    assert len(notifications) > 0

def test_clear_old_notifications(setup_quest_manager):
    """Test clearing old notifications."""
    manager, _, _ = setup_quest_manager
    # Start a quest to generate notifications
    manager.start_quest("main_quest")
    
    # Clear old notifications
    manager.clear_old_notifications(0)  # Clear all notifications
    
    # Verify notifications are cleared
    notifications = manager.get_active_notifications()
    assert len(notifications) == 0 