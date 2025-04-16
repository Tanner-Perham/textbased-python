import pytest
from unittest.mock import MagicMock, patch
from dialogue.manager import DialogueManager
from dialogue.node import DialogueNode, DialogueOption, EnhancedSkillCheck
from dialogue.response import DialogueResponse
from game.game_state import GameState
from pprint import pprint

@pytest.fixture
def setup_manager():
    """Fixture to set up the DialogueManager and mock data."""
    manager = DialogueManager()
    game_state = MagicMock(spec=GameState)
    
    # Set up mock player with skills attribute
    player_mock = MagicMock()
    player_mock.skills = {}
    game_state.player = player_mock
    
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

@patch('random.randint')
def test_process_skill_check_success(mock_randint, setup_manager):
    """Test processing a skill check that succeeds."""
    manager, game_state, _ = setup_manager
    
    # Mock the random roll to be high (20) for guaranteed success
    mock_randint.return_value = 20
    
    # Configure game state with player skills
    game_state.player.skills = {"perception": 2}
    
    # Create a skill check
    skill_check = EnhancedSkillCheck(
        base_difficulty=10,
        primary_skill="perception",
        supporting_skills=[],
        emotional_modifiers={}
    )
    
    # Process the skill check
    result = manager._process_skill_check(skill_check, game_state)
    
    # Assertions
    assert isinstance(result, DialogueResponse.SkillCheck)
    assert result.success is True
    assert result.skill == "perception"
    assert result.roll == 20
    assert result.difficulty == 10

@patch('random.randint')
def test_process_skill_check_failure(mock_randint, setup_manager):
    """Test processing a skill check that fails."""
    manager, game_state, _ = setup_manager
    
    # Mock the random roll to be low (1) for guaranteed failure
    mock_randint.return_value = 1
    
    # Configure game state with player skills
    game_state.player.skills = {"logic": 3}
    
    # Create a skill check
    skill_check = EnhancedSkillCheck(
        base_difficulty=15,
        primary_skill="logic",
        supporting_skills=[],
        emotional_modifiers={}
    )
    
    # Process the skill check
    result = manager._process_skill_check(skill_check, game_state)
    
    # Assertions
    assert isinstance(result, DialogueResponse.SkillCheck)
    assert result.success is False
    assert result.skill == "logic"
    assert result.roll == 1
    assert result.difficulty == 15

@patch('random.randint')
def test_process_skill_check_with_supporting_skills(mock_randint, setup_manager):
    """Test processing a skill check with supporting skills."""
    manager, game_state, _ = setup_manager
    
    # Mock the random roll
    mock_randint.return_value = 10
    
    # Configure game state with player skills
    game_state.player.skills = {
        "empathy": 3,
        "suggestion": 4,
        "authority": 2
    }
    
    # Create a skill check with supporting skills
    skill_check = EnhancedSkillCheck(
        base_difficulty=18,
        primary_skill="empathy",
        supporting_skills=[("suggestion", 0.5), ("authority", 0.25)],
        emotional_modifiers={}
    )
    
    # Process the skill check
    result = manager._process_skill_check(skill_check, game_state)
    
    # Calculate expected total: roll(10) + empathy(3) + suggestion(4*0.5=2) + authority(2*0.25=0) = 15
    expected_success = (10 + 3 + 2 + 0) >= 18
    
    # Assertions
    assert isinstance(result, DialogueResponse.SkillCheck)
    assert result.success is expected_success
    assert result.skill == "empathy"
    assert result.roll == 10
    assert result.difficulty == 18

@patch('random.randint')
def test_process_skill_check_with_emotional_modifiers(mock_randint, setup_manager):
    """Test processing a skill check with emotional modifiers."""
    manager, game_state, _ = setup_manager
    
    # Set the current node's emotional state
    manager.current_node = "test_node"
    manager.emotional_states = {"test_node": "Angry"}
    
    # Mock the random roll
    mock_randint.return_value = 10
    
    # Configure game state with player skills
    game_state.player.skills = {"authority": 5}
    
    # Create a skill check with emotional modifiers
    skill_check = EnhancedSkillCheck(
        base_difficulty=12,
        primary_skill="authority",
        supporting_skills=[],
        emotional_modifiers={"Angry": 3, "Happy": -2}  # Angry makes it harder
    )
    
    # Process the skill check
    result = manager._process_skill_check(skill_check, game_state)
    
    # Assertions
    assert isinstance(result, DialogueResponse.SkillCheck)
    assert result.difficulty == 15  # 12 (base) + 3 (angry modifier)
    assert result.skill == "authority"
    assert result.roll == 10
    
    # Roll(10) + skill(5) = 15, which equals the modified difficulty(15)
    assert result.success is True

def test_process_skill_check_missing_skill(setup_manager):
    """Test processing a skill check with a skill the player doesn't have."""
    manager, game_state, _ = setup_manager
    
    # Configure game state with no relevant skills
    game_state.player.skills = {"logic": 3}  # Player has logic but not perception
    
    # Create a skill check
    skill_check = EnhancedSkillCheck(
        base_difficulty=10,
        primary_skill="perception",  # Player doesn't have this skill
        supporting_skills=[],
        emotional_modifiers={}
    )
    
    # Process the skill check with a fixed random seed for consistency
    with patch('random.randint', return_value=10):
        result = manager._process_skill_check(skill_check, game_state)
    
    # Assertions - should use 0 for the missing skill
    assert isinstance(result, DialogueResponse.SkillCheck)
    assert result.skill == "perception"
    assert result.roll == 10
    assert result.difficulty == 10
    assert result.success == (10 >= 10)  # Roll of 10 with no skill bonus equals difficulty

@patch('random.randint')
def test_select_option_with_skill_check_success(mock_randint, setup_manager):
    """Test selecting an option with a successful skill check."""
    manager, game_state, _ = setup_manager
    
    # Mock the random roll for a success
    mock_randint.return_value = 20
    
    # Configure game state with player skills
    game_state.player.skills = {"empathy": 3}
    
    # Add skill check dialogue nodes to the dialogue tree
    skill_check = EnhancedSkillCheck(
        base_difficulty=15,
        primary_skill="empathy",
        supporting_skills=[]
    )
    
    manager.dialogue_tree.update({
        "skill_test": DialogueNode(
            id="skill_test",
            text="I need to know if you're being honest.",
            speaker="npc1",
            emotional_state="Suspicious",
            options=[
                DialogueOption(
                    id="persuade",
                    text="Try to persuade them",
                    next_node="neutral_response",  # Default if no success/failure node
                    skill_check=skill_check,
                    success_node="success_response",
                    failure_node="failure_response"
                )
            ]
        ),
        "success_response": DialogueNode(
            id="success_response",
            text="I believe you.",
            speaker="npc1",
            emotional_state="Trusting",
            options=[]
        ),
        "failure_response": DialogueNode(
            id="failure_response",
            text="I don't trust you.",
            speaker="npc1",
            emotional_state="Angry",
            options=[]
        ),
        "neutral_response": DialogueNode(
            id="neutral_response",
            text="I'm not sure what to think.",
            speaker="npc1",
            emotional_state="Neutral",
            options=[]
        )
    })
    
    # Set current node
    manager.current_node = "skill_test"
    
    # Select the option
    responses = manager.select_option("persuade", game_state)
    
    # Assertions
    assert len(responses) >= 2  # At least a skill check response and a speech response
    assert any(isinstance(r, DialogueResponse.SkillCheck) for r in responses)
    assert any(isinstance(r, DialogueResponse.Speech) for r in responses)
    
    # Find the skill check and speech responses
    skill_check_response = next((r for r in responses if isinstance(r, DialogueResponse.SkillCheck)), None)
    speech_response = next((r for r in responses if isinstance(r, DialogueResponse.Speech)), None)
    
    # Check skill check result
    assert skill_check_response is not None
    assert skill_check_response.success is True
    assert skill_check_response.skill == "empathy"
    
    # Check we got the success node
    assert speech_response is not None
    assert speech_response.text == "I believe you."
    assert speech_response.emotion == "Trusting"
    
    # Confirm the current node was updated
    assert manager.current_node == "success_response"

@patch('random.randint')
def test_select_option_with_skill_check_failure(mock_randint, setup_manager):
    """Test selecting an option with a failed skill check."""
    manager, game_state, _ = setup_manager
    
    # Mock the random roll for a failure
    mock_randint.return_value = 1
    
    # Configure game state with player skills
    game_state.player.skills = {"empathy": 3}
    
    # Add skill check dialogue nodes to the dialogue tree (reusing the setup from the success test)
    skill_check = EnhancedSkillCheck(
        base_difficulty=15,
        primary_skill="empathy",
        supporting_skills=[]
    )
    
    manager.dialogue_tree.update({
        "skill_test": DialogueNode(
            id="skill_test",
            text="I need to know if you're being honest.",
            speaker="npc1",
            emotional_state="Suspicious",
            options=[
                DialogueOption(
                    id="persuade",
                    text="Try to persuade them",
                    next_node="neutral_response",  # Default if no success/failure node
                    skill_check=skill_check,
                    success_node="success_response",
                    failure_node="failure_response"
                )
            ]
        ),
        "success_response": DialogueNode(
            id="success_response",
            text="I believe you.",
            speaker="npc1",
            emotional_state="Trusting",
            options=[]
        ),
        "failure_response": DialogueNode(
            id="failure_response",
            text="I don't trust you.",
            speaker="npc1",
            emotional_state="Angry",
            options=[]
        ),
        "neutral_response": DialogueNode(
            id="neutral_response",
            text="I'm not sure what to think.",
            speaker="npc1",
            emotional_state="Neutral",
            options=[]
        )
    })
    
    # Set current node
    manager.current_node = "skill_test"
    
    # Select the option
    responses = manager.select_option("persuade", game_state)
    
    # Assertions
    assert len(responses) >= 2  # At least a skill check response and a speech response
    assert any(isinstance(r, DialogueResponse.SkillCheck) for r in responses)
    assert any(isinstance(r, DialogueResponse.Speech) for r in responses)
    
    # Find the skill check and speech responses
    skill_check_response = next((r for r in responses if isinstance(r, DialogueResponse.SkillCheck)), None)
    speech_response = next((r for r in responses if isinstance(r, DialogueResponse.Speech)), None)
    
    # Check skill check result
    assert skill_check_response is not None
    assert skill_check_response.success is False
    assert skill_check_response.skill == "empathy"
    
    # Check we got the failure node
    assert speech_response is not None
    assert speech_response.text == "I don't trust you."
    assert speech_response.emotion == "Angry"
    
    # Confirm the current node was updated
    assert manager.current_node == "failure_response"

@patch('random.randint')
def test_select_option_with_skill_check_no_special_nodes(mock_randint, setup_manager):
    """Test selecting an option with a skill check but no special success/failure nodes."""
    manager, game_state, _ = setup_manager
    
    # Mock the random roll
    mock_randint.return_value = 15  # This could be success or failure depending on the test
    
    # Configure game state with player skills
    game_state.player.skills = {"logic": 2}
    
    # Add skill check dialogue node without special success/failure nodes
    skill_check = EnhancedSkillCheck(
        base_difficulty=10,
        primary_skill="logic",
        supporting_skills=[]
    )
    
    manager.dialogue_tree.update({
        "skill_test_basic": DialogueNode(
            id="skill_test_basic",
            text="Let me test your reasoning abilities.",
            speaker="npc1",
            emotional_state="Curious",
            options=[
                DialogueOption(
                    id="reason",
                    text="Apply logic to the problem",
                    next_node="default_response",
                    skill_check=skill_check
                    # No success_node or failure_node defined
                )
            ]
        ),
        "default_response": DialogueNode(
            id="default_response",
            text="Interesting approach, regardless of whether you succeeded or failed.",
            speaker="npc1",
            emotional_state="Neutral",
            options=[]
        )
    })
    
    # Set current node
    manager.current_node = "skill_test_basic"
    
    # Select the option
    responses = manager.select_option("reason", game_state)
    
    # Assertions
    assert len(responses) >= 2  # At least a skill check response and a speech response
    assert any(isinstance(r, DialogueResponse.SkillCheck) for r in responses)
    assert any(isinstance(r, DialogueResponse.Speech) for r in responses)
    
    # Find the speech response
    speech_response = next((r for r in responses if isinstance(r, DialogueResponse.Speech)), None)
    
    # Check we got the default node regardless of success/failure
    assert speech_response is not None
    assert speech_response.text == "Interesting approach, regardless of whether you succeeded or failed."
    
    # Confirm the current node was updated to the default next_node
    assert manager.current_node == "default_response"