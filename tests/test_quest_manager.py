"""Unit tests for the quest manager."""

import pytest
from unittest.mock import MagicMock
from quest.quest_manager import QuestManager, NotificationType, QuestNotification
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
            status="NotStarted",
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
                        },
                        {
                            "id": "obj2",
                            "description": "Talk to the NPC",
                            "is_completed": False,
                            "is_optional": True,
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
                            "id": "obj3",
                            "description": "Solve the puzzle",
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
            status="NotStarted",
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

def test_quest_manager_initialization(setup_quest_manager):
    """Test quest manager initialization."""
    manager, game_state, quests = setup_quest_manager
    assert manager.game_state == game_state
    assert len(manager.notifications) == 0

def test_get_all_quests(setup_quest_manager):
    """Test getting all quests."""
    manager, game_state, quests = setup_quest_manager
    all_quests = manager.get_all_quests()
    assert len(all_quests) == 2
    assert "main_quest" in all_quests
    assert "side_quest" in all_quests

def test_get_quest(setup_quest_manager):
    """Test getting a specific quest."""
    manager, _, _ = setup_quest_manager
    quest = manager.get_quest("main_quest")
    assert quest is not None
    assert quest.id == "main_quest"
    assert quest.title == "The Main Quest"
    assert len(quest.stages) == 2

def test_get_quest_status(setup_quest_manager):
    """Test getting quest status."""
    manager, _, _ = setup_quest_manager
    assert manager.get_quest_status("main_quest") == QuestStatus.NotStarted
    assert manager.get_quest_status("nonexistent_quest") is None

def test_start_quest(setup_quest_manager):
    """Test starting a quest."""
    manager, game_state, _ = setup_quest_manager
    
    # Test starting a valid quest
    assert manager.start_quest("main_quest")
    assert game_state.get_quest_status("main_quest") == QuestStatus.InProgress
    assert game_state.get_active_stage("main_quest") == "stage1"
    
    # Test starting a non-existent quest
    # Since we don't have access to config in tests, this should return False
    assert not manager.start_quest("nonexistent_quest")
    
    # Test starting an already started quest, this should return True but not change the quest
    assert manager.start_quest("main_quest")
    assert game_state.get_quest_status("main_quest") == QuestStatus.InProgress
    
    # Check notifications
    notifications = manager.get_active_notifications()
    assert len(notifications) == 1
    assert notifications[0].type == NotificationType.QuestStarted
    assert notifications[0].quest_id == "main_quest"

def test_complete_quest(setup_quest_manager):
    """Test completing a quest."""
    manager, game_state, _ = setup_quest_manager
    
    # Start the quest first
    manager.start_quest("main_quest")
    
    # Test completing a valid quest
    assert manager.complete_quest("main_quest")
    assert game_state.get_quest_status("main_quest") == QuestStatus.Completed
    
    # Test completing a non-existent quest
    assert not manager.complete_quest("nonexistent_quest")
    
    # Check notifications
    notifications = manager.get_active_notifications()
    assert notifications[-1].type == NotificationType.QuestCompleted

def test_fail_quest(setup_quest_manager):
    """Test failing a quest."""
    manager, game_state, _ = setup_quest_manager
    
    # Start the quest first
    manager.start_quest("main_quest")
    
    # Test failing a valid quest
    assert manager.fail_quest("main_quest")
    assert game_state.get_quest_status("main_quest") == QuestStatus.Failed
    
    # Test failing a non-existent quest
    assert not manager.fail_quest("nonexistent_quest")
    
    # Check notifications
    notifications = manager.get_active_notifications()
    assert notifications[-1].type == NotificationType.QuestFailed

def test_complete_objective(setup_quest_manager):
    """Test completing quest objectives."""
    manager, game_state, _ = setup_quest_manager
    
    # Start the quest first
    manager.start_quest("main_quest")
    
    # Test completing a valid objective
    assert manager.complete_objective("main_quest", "obj1")
    assert game_state.is_objective_completed("main_quest", "obj1")
    
    # Test completing a non-existent objective
    assert not manager.complete_objective("main_quest", "nonexistent_obj")
    
    # Test completing an objective for a non-existent quest
    assert not manager.complete_objective("nonexistent_quest", "obj1")
    
    # Check notifications
    notifications = manager.get_active_notifications()
    assert notifications[-1].type == NotificationType.ObjectiveCompleted

def test_advance_quest(setup_quest_manager):
    """Test advancing a quest to the next stage."""
    manager, game_state, _ = setup_quest_manager
    
    # Start the quest first
    manager.start_quest("main_quest")
    
    # Test advancing to a valid stage
    assert manager.advance_quest("main_quest", "stage2")
    assert game_state.get_active_stage("main_quest") == "stage2"
    
    # Test advancing to an invalid stage
    assert not manager.advance_quest("main_quest", "nonexistent_stage")
    
    # Test advancing a non-existent quest
    assert not manager.advance_quest("nonexistent_quest", "stage2")
    
    # Check notifications
    notifications = manager.get_active_notifications()
    assert notifications[-1].type == NotificationType.QuestUpdated

def test_quest_branches(setup_quest_manager):
    """Test quest branching functionality."""
    manager, game_state, _ = setup_quest_manager
    
    # Start the quest first
    manager.start_quest("main_quest")
    
    # Test taking a valid branch
    assert manager.take_quest_branch("main_quest", "alternative_path")
    assert game_state.has_taken_branch("main_quest", "alternative_path")
    
    # Test taking a branch for a non-existent quest
    assert not manager.take_quest_branch("nonexistent_quest", "branch")

def test_quest_items(setup_quest_manager):
    """Test quest item management."""
    manager, game_state, _ = setup_quest_manager
    
    # Start the quest first
    manager.start_quest("main_quest")
    
    # Test adding a quest item
    assert manager.add_quest_item("main_quest", "key_item")
    assert game_state.has_quest_item("main_quest", "key_item")
    
    # Test removing a quest item
    assert manager.remove_quest_item("main_quest", "key_item")
    assert not game_state.has_quest_item("main_quest", "key_item")
    
    # Test item operations on non-existent quest
    assert not manager.add_quest_item("nonexistent_quest", "item")
    assert not manager.remove_quest_item("nonexistent_quest", "item")

def test_notification_management(setup_quest_manager):
    """Test notification management."""
    manager, _, _ = setup_quest_manager
    
    # Generate some notifications
    manager.start_quest("main_quest")
    manager.complete_objective("main_quest", "obj1")
    
    # Test getting active notifications
    notifications = manager.get_active_notifications()
    assert len(notifications) == 2
    assert all(n.is_new for n in notifications)
    
    # Test clearing old notifications
    manager.clear_old_notifications(0)  # Clear all notifications
    assert len(manager.get_active_notifications()) == 0

def test_quest_progress_tracking(setup_quest_manager):
    """Test quest progress tracking."""
    manager, _, _ = setup_quest_manager
    
    # Start the quest
    manager.start_quest("main_quest")
    
    # Get initial progress
    progress = manager.get_quest_progress("main_quest")
    assert progress is not None
    assert progress["status"] == QuestStatus.InProgress
    assert progress["active_stage"] == "stage1"
    assert len(progress["completed_objectives"]) == 0
    
    # Complete an objective and check progress
    manager.complete_objective("main_quest", "obj1")
    progress = manager.get_quest_progress("main_quest")
    assert len(progress["completed_objectives"]) == 1
    assert "obj1" in progress["completed_objectives"]
    
    # Test progress for non-existent quest
    assert manager.get_quest_progress("nonexistent_quest") is None

def test_quest_stage_management(setup_quest_manager):
    """Test quest stage management."""
    manager, game_state, _ = setup_quest_manager
    
    # Start the quest
    manager.start_quest("main_quest")
    
    # Get current stage
    stage = manager.get_quest_stage("main_quest")
    assert stage is not None
    assert stage.id == "stage1"
    
    # Test getting stage for non-existent quest
    assert manager.get_quest_stage("nonexistent_quest") is None

def test_quest_validation(setup_quest_manager):
    """Test quest validation and error handling."""
    manager, _, _ = setup_quest_manager
    
    # Test operations on non-existent quest
    assert not manager.is_quest_active("nonexistent_quest")
    assert not manager.is_objective_completed("nonexistent_quest", "obj1")
    assert not manager.has_taken_branch("nonexistent_quest", "branch")
    
    # Test operations on quest that hasn't started
    assert not manager.is_quest_active("side_quest")
    assert not manager.is_objective_completed("side_quest", "obj1")
    assert not manager.has_taken_branch("side_quest", "branch") 