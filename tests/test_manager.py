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
    
    # Set up common game state attributes
    inventory_manager_mock = MagicMock()
    inventory_manager_mock.items = []  # Empty list of items to start
    game_state.inventory_manager = inventory_manager_mock
    
    game_state.discovered_clues = []
    game_state.quest_log = {}
    game_state.get_relationship_value = MagicMock(return_value=0)
    game_state.is_objective_completed = MagicMock(return_value=False)
    game_state.time_of_day = "Morning"
    
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
    
    # Mock the random roll to be high for guaranteed success
    # Now using 2d6 system instead of d20
    mock_randint.side_effect = [5, 5]  # Total 10 (high roll)
    
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
    assert result.success is True  # 10 (roll) + 2 (skill) = 12, which is >= 10
    assert result.skill == "perception"
    assert result.roll == 10
    assert result.dice_values == [5, 5]
    assert result.difficulty == 10
    assert result.critical_result is None  # Not a critical result

@patch('random.randint')
def test_process_skill_check_failure(mock_randint, setup_manager):
    """Test processing a skill check that fails."""
    manager, game_state, _ = setup_manager
    
    # Mock the random roll to be low for guaranteed failure
    # Now using 2d6 system instead of d20
    mock_randint.side_effect = [2, 2]  # Total 4 (low roll, but not critical)
    
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
    assert result.success is False  # 4 (roll) + 3 (skill) = 7, which is < 15
    assert result.skill == "logic"
    assert result.roll == 4
    assert result.dice_values == [2, 2]
    assert result.difficulty == 15
    assert result.critical_result is None  # Not a critical result

@patch('random.randint')
def test_process_skill_check_with_supporting_skills(mock_randint, setup_manager):
    """Test processing a skill check with supporting skills."""
    manager, game_state, _ = setup_manager
    
    # Mock the random roll
    # Now using 2d6 system instead of d20
    mock_randint.side_effect = [3, 3]  # Total 6
    
    # Configure game state with player skills
    game_state.player.skills = {
        "empathy": 3,
        "suggestion": 4,
        "authority": 2
    }
    
    # Create a skill check with supporting skills
    skill_check = EnhancedSkillCheck(
        base_difficulty=12,
        primary_skill="empathy",
        supporting_skills=[("suggestion", 0.5), ("authority", 0.25)],
        emotional_modifiers={}
    )
    
    # Process the skill check
    result = manager._process_skill_check(skill_check, game_state)
    
    # Calculate expected total: roll(6) + empathy(3) + suggestion(4*0.5=2) + authority(2*0.25=0) = 11
    expected_success = (6 + 3 + 2 + 0) >= 12
    
    # Assertions
    assert isinstance(result, DialogueResponse.SkillCheck)
    assert result.success is expected_success
    assert result.skill == "empathy"
    assert result.roll == 6
    assert result.dice_values == [3, 3]
    assert result.difficulty == 12

@patch('random.randint')
def test_process_skill_check_with_emotional_modifiers(mock_randint, setup_manager):
    """Test processing a skill check with emotional modifiers."""
    manager, game_state, _ = setup_manager
    
    # Set the current node's emotional state
    manager.current_node = "test_node"
    manager.emotional_states = {"test_node": "Angry"}
    
    # Mock the random roll
    # Now using 2d6 system instead of d20
    mock_randint.side_effect = [3, 3]  # Total 6
    
    # Configure game state with player skills
    game_state.player.skills = {"authority": 5}
    
    # Create a skill check with emotional modifiers
    skill_check = EnhancedSkillCheck(
        base_difficulty=8,
        primary_skill="authority",
        supporting_skills=[],
        emotional_modifiers={"Angry": 3, "Happy": -2}  # Angry makes it harder
    )
    
    # Process the skill check
    result = manager._process_skill_check(skill_check, game_state)
    
    # Assertions
    assert isinstance(result, DialogueResponse.SkillCheck)
    assert result.difficulty == 11  # 8 (base) + 3 (angry modifier)
    assert result.skill == "authority"
    assert result.roll == 6
    assert result.dice_values == [3, 3]
    
    # Roll(6) + skill(5) = 11, which equals the modified difficulty(11)
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
    
    # Process the skill check with a fixed random dice rolls
    with patch('random.randint', side_effect=[3, 3]):  # Total 6
        result = manager._process_skill_check(skill_check, game_state)
    
    # Assertions - should use 0 for the missing skill
    assert isinstance(result, DialogueResponse.SkillCheck)
    assert result.skill == "perception"
    assert result.roll == 6
    assert result.dice_values == [3, 3]
    assert result.difficulty == 10
    assert result.success is False  # Roll of 6 with no skill bonus is less than difficulty 10

@patch('random.randint')
def test_select_option_with_skill_check_success(mock_randint, setup_manager):
    """Test selecting an option with a successful skill check."""
    manager, game_state, _ = setup_manager
    
    # Mock the random roll for a success
    # Now using 2d6 system instead of d20
    mock_randint.side_effect = [5, 5]  # Total 10 (high roll, not critical)
    
    # Configure game state with player skills
    game_state.player.skills = {"empathy": 3}
    
    # Add skill check dialogue nodes to the dialogue tree
    skill_check = EnhancedSkillCheck(
        base_difficulty=12,
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
    assert skill_check_response.success is True  # 10 (roll) + 3 (skill) = 13, which is >= 12
    assert skill_check_response.skill == "empathy"
    assert skill_check_response.dice_values == [5, 5]
    assert skill_check_response.critical_result is None
    
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
    # Now using 2d6 system instead of d20
    mock_randint.side_effect = [2, 2]  # Total 4 (low roll, not critical)
    
    # Configure game state with player skills
    game_state.player.skills = {"empathy": 3}
    
    # Add skill check dialogue nodes to the dialogue tree (reusing the setup from the success test)
    skill_check = EnhancedSkillCheck(
        base_difficulty=12,
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
    assert skill_check_response.success is False  # 4 (roll) + 3 (skill) = 7, which is < 12
    assert skill_check_response.skill == "empathy"
    assert skill_check_response.dice_values == [2, 2]
    assert skill_check_response.critical_result is None
    
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
    # Now using 2d6 system instead of d20
    mock_randint.side_effect = [4, 4]  # Total 8
    
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
    
    # Find the skill check and speech responses
    skill_check_response = next((r for r in responses if isinstance(r, DialogueResponse.SkillCheck)), None)
    speech_response = next((r for r in responses if isinstance(r, DialogueResponse.Speech)), None)
    
    # Check skill check result
    assert skill_check_response is not None
    assert skill_check_response.success is True  # 8 (roll) + 2 (skill) = 10, which equals the difficulty(10)
    assert skill_check_response.dice_values == [4, 4]
    assert skill_check_response.critical_result is None
    
    # Check we got the default node regardless of success/failure
    assert speech_response is not None
    assert speech_response.text == "Interesting approach, regardless of whether you succeeded or failed."
    
    # Confirm the current node was updated to the default next_node
    assert manager.current_node == "default_response"

# Test cases for enhanced dialogue entry point determination

def test_determine_entry_point_default(setup_manager):
    """Test that _determine_entry_point returns the default entry point when no conditions are met."""
    manager, game_state, _ = setup_manager
    
    # Add dialogue nodes for an NPC
    manager.dialogue_tree.update({
        "npc2_default": DialogueNode(
            id="npc2_default",
            text="Hello stranger.",
            speaker="npc2",
            emotional_state="Neutral",
            options=[]
        )
    })
    
    # Determine entry point
    entry_point = manager._determine_entry_point("npc2", game_state)
    
    # Assert we get the default
    assert entry_point == "npc2_default"
    
def test_determine_entry_point_with_item_condition(setup_manager):
    """Test that _determine_entry_point selects a conditional entry point when an item condition is met."""
    manager, game_state, _ = setup_manager
    
    # Create DialogueConditions object for the conditional node
    from dialogue.node import DialogueConditions
    conditions = DialogueConditions()
    conditions.required_items = ["special_item"]
    
    # Add dialogue nodes for an NPC with conditions
    manager.dialogue_tree.update({
        "npc2_default": DialogueNode(
            id="npc2_default",
            text="Hello stranger.",
            speaker="npc2",
            emotional_state="Neutral",
            options=[]
        ),
        "npc2_special": DialogueNode(
            id="npc2_special",
            text="I see you have the special item!",
            speaker="npc2",
            emotional_state="Impressed",
            options=[],
            conditions=conditions
        )
    })
    
    # Properly set up the inventory_manager mock
    item_mock = MagicMock(id="special_item")
    game_state.inventory_manager = MagicMock()
    game_state.inventory_manager.items = [item_mock]
    
    # Mock the check_dialogue_conditions method
    with patch.object(manager, '_check_dialogue_conditions', return_value=True):
        # Determine entry point
        entry_point = manager._determine_entry_point("npc2", game_state)
        
        # Assert we get the conditional entry point
        assert entry_point == "npc2_special"

def test_determine_entry_point_with_quest_condition(setup_manager):
    """Test that _determine_entry_point selects a conditional entry point when a quest condition is met."""
    manager, game_state, _ = setup_manager
    
    # Create DialogueConditions object for the conditional node
    from dialogue.node import DialogueConditions
    conditions = DialogueConditions()
    conditions.required_quests = {"test_quest": "Completed"}
    
    # Add dialogue nodes for an NPC with quest condition
    manager.dialogue_tree.update({
        "npc2_default": DialogueNode(
            id="npc2_default",
            text="Hello stranger.",
            speaker="npc2",
            emotional_state="Neutral",
            options=[]
        ),
        "npc2_quest_complete": DialogueNode(
            id="npc2_quest_complete",
            text="You've completed the quest! Well done!",
            speaker="npc2",
            emotional_state="Happy",
            options=[],
            conditions=conditions
        )
    })
    
    # Configure game state with completed quest
    game_state.quest_log = {"test_quest": "Completed"}
    
    # Mock the check_dialogue_conditions method
    with patch.object(manager, '_check_dialogue_conditions', return_value=True):
        # Determine entry point
        entry_point = manager._determine_entry_point("npc2", game_state)
        
        # Assert we get the conditional entry point
        assert entry_point == "npc2_quest_complete"

def test_check_dialogue_conditions_items(setup_manager):
    """Test the _check_dialogue_conditions method with item requirements."""
    manager, game_state, _ = setup_manager
    
    # Create conditions requiring items
    from dialogue.node import DialogueConditions
    conditions = DialogueConditions()
    conditions.required_items = ["special_item", "rare_item"]
    
    # Configure game state to have the required items
    item1 = MagicMock(id="special_item")
    item2 = MagicMock(id="rare_item")
    item3 = MagicMock(id="common_item")
    game_state.inventory_manager = MagicMock()
    game_state.inventory_manager.items = [item1, item2, item3]
    
    # Test condition check - should pass
    assert manager._check_dialogue_conditions(conditions, game_state) is True
    
    # Change conditions to require an item the player doesn't have
    conditions.required_items = ["special_item", "missing_item"]
    
    # Test condition check - should fail
    assert manager._check_dialogue_conditions(conditions, game_state) is False

def test_check_dialogue_conditions_quests(setup_manager):
    """Test the _check_dialogue_conditions method with quest requirements."""
    manager, game_state, _ = setup_manager
    
    # Create conditions requiring quest statuses
    from dialogue.node import DialogueConditions
    conditions = DialogueConditions()
    conditions.required_quests = {"main_quest": "Completed", "side_quest": "InProgress"}
    
    # Configure game state with required quest statuses
    game_state.quest_log = {"main_quest": "Completed", "side_quest": "InProgress"}
    
    # Test condition check - should pass
    assert manager._check_dialogue_conditions(conditions, game_state) is True
    
    # Change game state to have a different quest status
    game_state.quest_log = {"main_quest": "Completed", "side_quest": "NotStarted"}
    
    # Test condition check - should fail
    assert manager._check_dialogue_conditions(conditions, game_state) is False

def test_check_dialogue_conditions_npc_relationship(setup_manager):
    """Test the _check_dialogue_conditions method with NPC relationship requirements."""
    manager, game_state, _ = setup_manager
    
    # Create conditions requiring minimum relationship value
    from dialogue.node import DialogueConditions
    conditions = DialogueConditions()
    conditions.npc_relationship_value = {"npc_id": "friendly_npc", "min_value": 70}
    
    # Configure game state with relationship value
    game_state.get_relationship_value.return_value = 75
    
    # Test condition check - should pass (75 >= 70)
    assert manager._check_dialogue_conditions(conditions, game_state) is True
    
    # Change relationship value to be too low
    game_state.get_relationship_value.return_value = 65
    
    # Test condition check - should fail (65 < 70)
    assert manager._check_dialogue_conditions(conditions, game_state) is False

def test_check_dialogue_conditions_quest_objective(setup_manager):
    """Test the _check_dialogue_conditions method with quest objective completion requirements."""
    manager, game_state, _ = setup_manager
    
    # Create conditions requiring quest objective completion
    from dialogue.node import DialogueConditions
    conditions = DialogueConditions()
    conditions.quest_objective_completed = ("main_quest", "find_artifact")
    
    # Configure game state to have completed the objective
    game_state.is_objective_completed.return_value = True
    
    # Test condition check - should pass
    assert manager._check_dialogue_conditions(conditions, game_state) is True
    
    # Change game state to not have completed the objective
    game_state.is_objective_completed.return_value = False
    
    # Test condition check - should fail
    assert manager._check_dialogue_conditions(conditions, game_state) is False

def test_start_dialogue_with_conditional_entry_point(setup_manager):
    """Test starting dialogue with conditional entry points."""
    manager, game_state, _ = setup_manager
    
    # Set up conditions in game state
    item_mock = MagicMock(id="silver_locket")
    game_state.inventory_manager = MagicMock()
    # Create a list with the mock item - this is already iterable
    game_state.inventory_manager.items = [item_mock]
    game_state.quest_log = {"missing_locket": "InProgress"}
    
    # Create DialogueConditions object for the conditional node
    from dialogue.node import DialogueConditions
    conditions = DialogueConditions()
    conditions.required_items = ["silver_locket"]
    conditions.required_quests = {"missing_locket": "InProgress"}
    
    # Add dialogue nodes for an NPC with conditions
    manager.dialogue_tree.update({
        "eliza_default": DialogueNode(
            id="eliza_default",
            text="Hello there. It's nice to meet you.",
            speaker="eliza",
            emotional_state="Neutral",
            options=[]
        ),
        "eliza_found_locket": DialogueNode(
            id="eliza_found_locket",
            text="Oh! You're back! Have you found anything?",
            speaker="eliza",
            emotional_state="Hopeful",
            options=[],
            conditions=conditions
        )
    })
    
    # Mock the check_dialogue_conditions method to properly handle the conditions
    with patch.object(manager, '_check_dialogue_conditions', return_value=True):
        # Start dialogue - should use conditional entry point
        responses = manager.start_dialogue("eliza", game_state)
        
        # Assert we get the right dialogue
        assert len(responses) >= 1
        assert isinstance(responses[0], DialogueResponse.Speech)
        assert responses[0].text == "Oh! You're back! Have you found anything?"
        assert responses[0].emotion == "Hopeful"

def test_check_dialogue_conditions(setup_manager):
    """Test the _check_dialogue_conditions method with various conditions."""
    manager, game_state, _ = setup_manager
    
    # Create basic conditions
    from dialogue.node import DialogueConditions
    conditions = DialogueConditions()
    
    # Empty conditions should pass
    assert manager._check_dialogue_conditions(conditions, game_state) == True
    
    # Add item requirement
    conditions.required_items = ["test_item"]
    game_state.inventory_manager = MagicMock()
    game_state.inventory_manager.items = []
    assert manager._check_dialogue_conditions(conditions, game_state) == False
    
    # Mock inventory to have the required item
    item_mock = MagicMock(id="test_item")
    game_state.inventory_manager.items = [item_mock]
    
    # Test with the item - should pass now
    assert manager._check_dialogue_conditions(conditions, game_state) == True

def test_determine_entry_point_basic(setup_manager):
    """Test the basic functionality of _determine_entry_point."""
    manager, game_state, _ = setup_manager
    
    # Test with default node
    entry_point = manager._determine_entry_point("npc1", game_state)
    assert entry_point == "npc1_default"
    
    # Test with non-existent NPC
    entry_point = manager._determine_entry_point("non_existent_npc", game_state)
    assert entry_point == "non_existent_npc_default"

def test_determine_entry_point_multiple_conditions(setup_manager):
    """Test that _determine_entry_point selects the most specific entry point when multiple conditions are met."""
    manager, game_state, _ = setup_manager
    
    # Set up conditions in game state
    game_state.inventory_manager = MagicMock()
    # Create lists with mock items - these are already iterable
    item1 = MagicMock(id="special_item")
    item2 = MagicMock(id="rare_item")
    game_state.inventory_manager.items = [item1, item2]
    
    game_state.quest_log = {"test_quest": "Completed", "rare_quest": "InProgress"}
    
    clue = MagicMock(id="important_clue")
    game_state.discovered_clues = [clue]
    
    # Create DialogueConditions objects for the conditional nodes
    from dialogue.node import DialogueConditions
    
    # First condition set - just one required item
    conditions1 = DialogueConditions()
    conditions1.required_items = ["special_item"]
    
    # Second condition set - more specific with item and quest
    conditions2 = DialogueConditions()
    conditions2.required_items = ["special_item"]
    conditions2.required_quests = {"test_quest": "Completed"}
    
    # Third condition set - most specific with item, quest, and clue
    conditions3 = DialogueConditions()
    conditions3.required_items = ["special_item", "rare_item"]
    conditions3.required_quests = {"test_quest": "Completed", "rare_quest": "InProgress"}
    conditions3.required_clues = ["important_clue"]
    
    # Add dialogue nodes for an NPC with multiple conditional options
    manager.dialogue_tree.update({
        "npc2_default": DialogueNode(
            id="npc2_default",
            text="Hello stranger.",
            speaker="npc2",
            emotional_state="Neutral",
            options=[]
        ),
        "npc2_item": DialogueNode(
            id="npc2_item",
            text="I see you have the special item.",
            speaker="npc2",
            emotional_state="Interested",
            options=[],
            conditions=conditions1
        ),
        "npc2_quest": DialogueNode(
            id="npc2_quest",
            text="You completed the quest and have the special item!",
            speaker="npc2",
            emotional_state="Pleased",
            options=[],
            conditions=conditions2
        ),
        "npc2_full": DialogueNode(
            id="npc2_full",
            text="You have everything - completed quest, rare items, and important clues!",
            speaker="npc2",
            emotional_state="Impressed",
            options=[],
            conditions=conditions3
        )
    })
    
    # Mock the check_dialogue_conditions method to properly handle the complex conditions
    def mock_check_conditions(conditions, _):
        # For simplicity in testing, we'll actually implement a basic version here
        if "rare_item" in conditions.required_items and len(conditions.required_clues) > 0:
            return True
        if "test_quest" in conditions.required_quests and len(conditions.required_items) == 1:
            return True
        if len(conditions.required_items) == 1 and "special_item" in conditions.required_items:
            return True
        return False
    
    # Apply the mock
    with patch.object(manager, '_check_dialogue_conditions', side_effect=mock_check_conditions):
        # Determine entry point
        entry_point = manager._determine_entry_point("npc2", game_state)
        
        # Assert we get the most specific entry point (the one with most conditions)
        assert entry_point == "npc2_full"

@patch('random.randint')
def test_process_skill_check_with_2d6_dice(mock_randint, setup_manager):
    """Test processing a skill check with the new 2d6 dice system."""
    manager, game_state, _ = setup_manager
    
    # Mock the dice rolls to return 3 and 4 (total 7)
    mock_randint.side_effect = [3, 4]
    
    # Configure game state with player skills
    game_state.player.skills = {"perception": 2}
    
    # Create a skill check
    skill_check = EnhancedSkillCheck(
        base_difficulty=8,
        primary_skill="perception",
        supporting_skills=[],
        emotional_modifiers={}
    )
    
    # Process the skill check
    result = manager._process_skill_check(skill_check, game_state)
    
    # Assertions
    assert isinstance(result, DialogueResponse.SkillCheck)
    assert result.dice_values == [3, 4]
    assert result.roll == 7  # Sum of dice values
    assert result.skill == "perception"
    assert result.difficulty == 8
    assert result.success is True  # 7 (roll) + 2 (skill) = 9, which is >= 8
    assert result.critical_result is None  # Not a critical result

@patch('random.randint')
def test_process_skill_check_critical_success(mock_randint, setup_manager):
    """Test processing a skill check with a critical success (double 6)."""
    manager, game_state, _ = setup_manager
    
    # Mock the dice rolls to return double 6 (critical success)
    mock_randint.side_effect = [6, 6]
    
    # Configure game state with player skills
    game_state.player.skills = {"logic": 1}
    
    # Create a difficult skill check that would normally fail
    skill_check = EnhancedSkillCheck(
        base_difficulty=20,  # Very high difficulty
        primary_skill="logic",
        supporting_skills=[],
        emotional_modifiers={}
    )
    
    # Process the skill check
    result = manager._process_skill_check(skill_check, game_state)
    
    # Assertions
    assert isinstance(result, DialogueResponse.SkillCheck)
    assert result.dice_values == [6, 6]
    assert result.roll == 12  # Sum of dice values
    assert result.skill == "logic"
    assert result.difficulty == 20
    assert result.success is True  # Critical success always succeeds
    assert result.critical_result == "success"

@patch('random.randint')
def test_process_skill_check_critical_failure(mock_randint, setup_manager):
    """Test processing a skill check with a critical failure (double 1)."""
    manager, game_state, _ = setup_manager
    
    # Mock the dice rolls to return double 1 (critical failure)
    mock_randint.side_effect = [1, 1]
    
    # Configure game state with player skills
    game_state.player.skills = {"empathy": 10}
    
    # Create an easy skill check that would normally succeed
    skill_check = EnhancedSkillCheck(
        base_difficulty=5,  # Very low difficulty
        primary_skill="empathy",
        supporting_skills=[],
        emotional_modifiers={}
    )
    
    # Process the skill check
    result = manager._process_skill_check(skill_check, game_state)
    
    # Assertions
    assert isinstance(result, DialogueResponse.SkillCheck)
    assert result.dice_values == [1, 1]
    assert result.roll == 2  # Sum of dice values
    assert result.skill == "empathy"
    assert result.difficulty == 5
    assert result.success is False  # Critical failure always fails
    assert result.critical_result == "failure"

@patch('random.randint')
def test_select_option_with_critical_success_node(mock_randint, setup_manager):
    """Test selecting an option with a critical success that has a specific critical success node."""
    manager, game_state, _ = setup_manager
    
    # Mock the dice rolls to return double 6 (critical success)
    mock_randint.side_effect = [6, 6]
    
    # Configure game state with player skills
    game_state.player.skills = {"suggestion": 2}
    
    # Add dialogue nodes including critical success/failure nodes
    skill_check = EnhancedSkillCheck(
        base_difficulty=10,
        primary_skill="suggestion",
        supporting_skills=[]
    )
    
    manager.dialogue_tree.update({
        "critical_test": DialogueNode(
            id="critical_test",
            text="This is a very important moment.",
            speaker="npc1",
            emotional_state="Neutral",
            options=[
                DialogueOption(
                    id="critical_option",
                    text="Make a critical attempt",
                    next_node="neutral_response",  # Default if no special node applies
                    skill_check=skill_check,
                    success_node="success_response",
                    failure_node="failure_response",
                    critical_success_node="critical_success_response",
                    critical_failure_node="critical_failure_response"
                )
            ]
        ),
        "success_response": DialogueNode(
            id="success_response",
            text="You did well.",
            speaker="npc1",
            emotional_state="Pleased",
            options=[]
        ),
        "failure_response": DialogueNode(
            id="failure_response",
            text="You failed.",
            speaker="npc1",
            emotional_state="Disappointed",
            options=[]
        ),
        "critical_success_response": DialogueNode(
            id="critical_success_response",
            text="That was amazing! A legendary performance!",
            speaker="npc1",
            emotional_state="Ecstatic",
            options=[]
        ),
        "critical_failure_response": DialogueNode(
            id="critical_failure_response",
            text="That was catastrophically bad!",
            speaker="npc1",
            emotional_state="Furious",
            options=[]
        ),
        "neutral_response": DialogueNode(
            id="neutral_response",
            text="Nothing special happened.",
            speaker="npc1",
            emotional_state="Neutral",
            options=[]
        )
    })
    
    # Set current node
    manager.current_node = "critical_test"
    
    # Select the option
    responses = manager.select_option("critical_option", game_state)
    
    # Assertions
    assert len(responses) >= 2  # At least a skill check response and a speech response
    
    # Find the skill check and speech responses
    skill_check_response = next((r for r in responses if isinstance(r, DialogueResponse.SkillCheck)), None)
    speech_response = next((r for r in responses if isinstance(r, DialogueResponse.Speech)), None)
    
    # Check skill check result
    assert skill_check_response is not None
    assert skill_check_response.success is True
    assert skill_check_response.critical_result == "success"
    assert skill_check_response.dice_values == [6, 6]
    
    # Check we got the critical success node response
    assert speech_response is not None
    assert speech_response.text == "That was amazing! A legendary performance!"
    assert speech_response.emotion == "Ecstatic"
    
    # Confirm the current node was updated
    assert manager.current_node == "critical_success_response"

@patch('random.randint')
def test_select_option_with_critical_failure_node(mock_randint, setup_manager):
    """Test selecting an option with a critical failure that has a specific critical failure node."""
    manager, game_state, _ = setup_manager
    
    # Mock the dice rolls to return double 1 (critical failure)
    mock_randint.side_effect = [1, 1]
    
    # Configure game state with player skills
    game_state.player.skills = {"suggestion": 2}
    
    # Add dialogue nodes including critical success/failure nodes (reuse from previous test)
    skill_check = EnhancedSkillCheck(
        base_difficulty=10,
        primary_skill="suggestion",
        supporting_skills=[]
    )
    
    manager.dialogue_tree.update({
        "critical_test": DialogueNode(
            id="critical_test",
            text="This is a very important moment.",
            speaker="npc1",
            emotional_state="Neutral",
            options=[
                DialogueOption(
                    id="critical_option",
                    text="Make a critical attempt",
                    next_node="neutral_response",  # Default if no special node applies
                    skill_check=skill_check,
                    success_node="success_response",
                    failure_node="failure_response",
                    critical_success_node="critical_success_response",
                    critical_failure_node="critical_failure_response"
                )
            ]
        ),
        "success_response": DialogueNode(
            id="success_response",
            text="You did well.",
            speaker="npc1",
            emotional_state="Pleased",
            options=[]
        ),
        "failure_response": DialogueNode(
            id="failure_response",
            text="You failed.",
            speaker="npc1",
            emotional_state="Disappointed",
            options=[]
        ),
        "critical_success_response": DialogueNode(
            id="critical_success_response",
            text="That was amazing! A legendary performance!",
            speaker="npc1",
            emotional_state="Ecstatic",
            options=[]
        ),
        "critical_failure_response": DialogueNode(
            id="critical_failure_response",
            text="That was catastrophically bad!",
            speaker="npc1",
            emotional_state="Furious",
            options=[]
        ),
        "neutral_response": DialogueNode(
            id="neutral_response",
            text="Nothing special happened.",
            speaker="npc1",
            emotional_state="Neutral",
            options=[]
        )
    })
    
    # Set current node
    manager.current_node = "critical_test"
    
    # Select the option
    responses = manager.select_option("critical_option", game_state)
    
    # Assertions
    assert len(responses) >= 2  # At least a skill check response and a speech response
    
    # Find the skill check and speech responses
    skill_check_response = next((r for r in responses if isinstance(r, DialogueResponse.SkillCheck)), None)
    speech_response = next((r for r in responses if isinstance(r, DialogueResponse.Speech)), None)
    
    # Check skill check result
    assert skill_check_response is not None
    assert skill_check_response.success is False
    assert skill_check_response.critical_result == "failure"
    assert skill_check_response.dice_values == [1, 1]
    
    # Check we got the critical failure node response
    assert speech_response is not None
    assert speech_response.text == "That was catastrophically bad!"
    assert speech_response.emotion == "Furious"
    
    # Confirm the current node was updated
    assert manager.current_node == "critical_failure_response"

@patch('random.randint')
def test_critical_success_with_no_critical_node(mock_randint, setup_manager):
    """Test a critical success when no critical_success_node is specified (should use success_node)."""
    manager, game_state, _ = setup_manager
    
    # Mock the dice rolls to return double 6 (critical success)
    mock_randint.side_effect = [6, 6]
    
    # Configure game state with player skills
    game_state.player.skills = {"logic": 2}
    
    # Add dialogue nodes with success/failure nodes but NO critical nodes
    skill_check = EnhancedSkillCheck(
        base_difficulty=10,
        primary_skill="logic",
        supporting_skills=[]
    )
    
    manager.dialogue_tree.update({
        "non_critical_test": DialogueNode(
            id="non_critical_test",
            text="This is an important but not critical moment.",
            speaker="npc1",
            emotional_state="Neutral",
            options=[
                DialogueOption(
                    id="non_critical_option",
                    text="Make an attempt",
                    next_node="neutral_response",
                    skill_check=skill_check,
                    success_node="success_response",
                    failure_node="failure_response"
                    # No critical nodes specified
                )
            ]
        ),
        "success_response": DialogueNode(
            id="success_response",
            text="You did well.",
            speaker="npc1",
            emotional_state="Pleased",
            options=[]
        ),
        "failure_response": DialogueNode(
            id="failure_response",
            text="You failed.",
            speaker="npc1",
            emotional_state="Disappointed",
            options=[]
        ),
        "neutral_response": DialogueNode(
            id="neutral_response",
            text="Nothing special happened.",
            speaker="npc1",
            emotional_state="Neutral",
            options=[]
        )
    })
    
    # Set current node
    manager.current_node = "non_critical_test"
    
    # Select the option
    responses = manager.select_option("non_critical_option", game_state)
    
    # Assertions
    skill_check_response = next((r for r in responses if isinstance(r, DialogueResponse.SkillCheck)), None)
    speech_response = next((r for r in responses if isinstance(r, DialogueResponse.Speech)), None)
    
    # Check skill check result
    assert skill_check_response is not None
    assert skill_check_response.success is True
    assert skill_check_response.critical_result == "success"
    
    # Check we got the regular success node response (not critical)
    assert speech_response is not None
    assert speech_response.text == "You did well."
    
    # Confirm the current node was updated to success_node
    assert manager.current_node == "success_response"