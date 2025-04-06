import pytest
from unittest.mock import MagicMock
from dialogue.manager import DialogueManager
from dialogue.node import DialogueNode, DialogueOption
from dialogue.response import DialogueResponse
from game.game_state import GameState
from pprint import pprint

@pytest.fixture
def setup_manager():
    """Fixture to set up the DialogueManager and mock data."""
    manager = DialogueManager()
    game_state = MagicMock(spec=GameState)

    # Mock dialogue tree
    dialogue_tree = {
        "npc1_default": DialogueNode(
            id="npc1_default",
            text="Hello, traveler!",
            speaker="npc1",
            emotional_state="Neutral",
            options=[
                DialogueOption(
                    id="greet",
                    text="Greet the NPC",
                    next_node="npc1_greet",
                    conditions=None,
                )
            ],
        ),
        "npc1_greet": DialogueNode(
            id="npc1_greet",
            text="Good to see you!",
            speaker="npc1",
            emotional_state="Happy",
            options=[],
        ),
    }
    manager.set_dialogue_tree(dialogue_tree)
    return manager, game_state, dialogue_tree

def test_set_dialogue_tree(setup_manager):
    """Test setting the dialogue tree."""
    manager, _, dialogue_tree = setup_manager
    assert manager.dialogue_tree == dialogue_tree

def test_start_dialogue_with_valid_npc(setup_manager):
    """Test starting dialogue with a valid NPC."""
    manager, game_state, _ = setup_manager
    responses = manager.start_dialogue("npc1", game_state)
    assert len(responses) == 2
    assert isinstance(responses[0], DialogueResponse.Speech)
    assert responses[0].text == "Hello, traveler!"
    assert isinstance(responses[1], DialogueResponse.Options)
    assert len(responses[1].options) == 1
    assert responses[1].options[0].id == "greet"

def test_start_dialogue_with_invalid_npc(setup_manager):
    """Test starting dialogue with an invalid NPC."""
    manager, game_state, _ = setup_manager
    responses = manager.start_dialogue("invalid", game_state)
    pprint(responses)
    assert len(responses) == 1
    assert isinstance(responses[0], DialogueResponse.Speech)

def test_process_node(setup_manager):
    """Test processing a dialogue node."""
    manager, game_state, _ = setup_manager
    responses = manager.process_node("npc1_default", game_state)
    assert len(responses) == 2
    assert isinstance(responses[0], DialogueResponse.Speech)
    assert responses[0].text == "Hello, traveler!"
    assert isinstance(responses[1], DialogueResponse.Options)
    assert len(responses[1].options) == 1

def test_select_option_valid(setup_manager):
    """Test selecting a valid dialogue option."""
    manager, game_state, _ = setup_manager
    manager.current_node = "npc1_default"
    responses = manager.select_option("greet", game_state)
    assert len(responses) == 1
    assert isinstance(responses[0], DialogueResponse.Speech)
    assert responses[0].text == "Good to see you!"
    assert manager.current_node == "npc1_greet"

def test_select_option_invalid(setup_manager):
    """Test selecting an invalid dialogue option."""
    manager, game_state, _ = setup_manager
    manager.current_node = "npc1_default"
    responses = manager.select_option("invalid_option", game_state)
    assert len(responses) == 0

def test_debug_state(setup_manager):
    """Test the debug_state method."""
    manager, _, _ = setup_manager
    debug_info = manager.debug_state()
    assert "Current node:" in debug_info
    assert "Available nodes:" in debug_info
    assert "Active nodes:" in debug_info
    assert "Locked nodes:" in debug_info