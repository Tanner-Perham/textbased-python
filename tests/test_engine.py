import pytest
from unittest.mock import MagicMock
from game.engine import GameEngine
from config.config_loader import GameConfig, GameSettings, Location

@pytest.fixture
def setup_engine():
    # Mock configuration and locations
    mock_config = MagicMock(spec=GameConfig)
    mock_config.locations = {
        "warehouse_entrance": Location(
            id="warehouse_entrance",
            name="Warehouse Entrance", 
            description="You are at the starting point.", 
            connected_locations=["warehouse_office", "town_square"]
        ),
        "warehouse_office": Location(
            id="warehouse_office",
            name="Warehouse Office", 
            description="A dusty office filled with old papers.", 
            connected_locations=["warehouse_entrance"]
        ),
        "town_square": Location(
            id="town_square",
            name="Town Square", 
            description="A bustling town square with shops and people.", 
            connected_locations=["warehouse_entrance"]
        ),
    }
    
    # Create a simple NPC class for testing
    class TestNPC:
        def __init__(self, id, name, location, gender):
            self.id = id
            self.name = name
            self.location = location
            self.gender = gender
    
    # Mock NPCs using the test class instead of MagicMock
    mock_config.npcs = {
        "worker_chen": TestNPC(
            id="worker_chen",
            name="Sarah Chen",
            location="warehouse_entrance",
            gender="female"
        ),
        "guard_martinez": TestNPC(
            id="guard_martinez",
            name="Officer Martinez",
            location="warehouse_office",
            gender="male"
        )
    }

    # Other mock config settings remain the same
    mock_config.game_settings = MagicMock(spec=GameSettings)
    mock_config.game_settings.title = "Test Game"
    mock_config.game_settings.default_time = "day"
    mock_config.game_settings.starting_location = "warehouse_entrance"
    mock_config.quests = {}
    mock_config.items = {}
    mock_config.clues = {}
    mock_config.dialogue_trees = {}
    mock_config.inner_voices = {}
    mock_config.thoughts = {}

    # Initialize GameEngine
    engine = GameEngine(mock_config)
    return engine, mock_config

def test_move_to_valid_location(setup_engine):
    engine, _ = setup_engine
    response = engine._handle_movement("warehouse_office")
    assert engine.current_location == "warehouse_office"
    assert engine.previous_location == "warehouse_entrance"

def test_move_to_invalid_location(setup_engine):
    engine, _ = setup_engine
    response = engine._handle_movement("ocean")
    assert response == "You can't go to the ocean from here. Valid exits are: Warehouse Office, Town Square."
    assert engine.current_location == "warehouse_entrance"

def test_move_back_to_previous_location(setup_engine):
    engine, _ = setup_engine
    engine.current_location = "warehouse_office"
    engine.previous_location = "warehouse_entrance"
    response = engine._handle_movement("back")
    print(engine.current_location)
    print(engine.previous_location)
    assert engine.current_location == "warehouse_entrance"
    assert engine.previous_location == "warehouse_office"

def test_ambiguous_direction(setup_engine):
    engine, mock_config = setup_engine
    # Both locations start with "Warehouse"
    mock_config.locations["warehouse_office"].name = "Warehouse Office"
    mock_config.locations["town_square"].name = "Warehouse Square"
    with pytest.raises(ValueError) as excinfo:
        engine._handle_movement("warehouse")
    assert engine.current_location == "warehouse_entrance"

def test_no_direction_provided(setup_engine):
    engine, _ = setup_engine
    response = engine._handle_movement("")
    assert response == "You need to specify a direction to move."
    assert engine.current_location == "warehouse_entrance"

def test_missing_current_location(setup_engine):
    engine, _ = setup_engine
    engine.current_location = "unknown"
    response = engine._handle_movement("warehouse_office")
    assert response == "ERROR: Current location not found."

def test_missing_target_location(setup_engine):
    engine, mock_config = setup_engine
    mock_config.locations["warehouse_entrance"].connected_locations = []
    response = engine._handle_movement("warehouse_office")
    assert response == "You can't go to the warehouse_office from here. There are no valid exits."

def test_find_closest_location_match_single_match(setup_engine):
    engine, _ = setup_engine
    connected_locations = ["warehouse_office", "town_square"]
    result = engine._find_closest_location_match("office", connected_locations)
    assert result == "warehouse_office"

def test_find_closest_location_match_multiple_matches(setup_engine):
    engine, mock_config = setup_engine
    mock_config.locations["warehouse_office"].name = "Warehouse Store"
    mock_config.locations["town_square"].name = "Warehouse Market"
    connected_locations = ["warehouse_office", "town_square"]
    with pytest.raises(ValueError) as excinfo:
        engine._find_closest_location_match("warehouse", connected_locations)
    assert "Ambiguous direction: multiple locations match 'warehouse'" in str(excinfo.value)

def test_find_closest_location_match_no_matches(setup_engine):
    engine, _ = setup_engine
    connected_locations = ["warehouse_office", "town_square"]
    result = engine._find_closest_location_match("ocean", connected_locations)
    assert result is None

def test_find_closest_location_match_partial_name(setup_engine):
    engine, _ = setup_engine
    connected_locations = ["warehouse_office", "town_square"]
    result = engine._find_closest_location_match("square", connected_locations)
    assert result == "town_square"

def test_find_closest_location_match_partial_id(setup_engine):
    engine, _ = setup_engine
    connected_locations = ["warehouse_office", "town_square"]
    result = engine._find_closest_location_match("office", connected_locations)
    assert result == "warehouse_office"

def test_find_closest_location_match_empty_connected_locations(setup_engine):
    engine, _ = setup_engine
    connected_locations = []
    result = engine._find_closest_location_match("warehouse_office", connected_locations)
    assert result is None

def test_find_closest_location_match_invalid_location_in_config(setup_engine):
    engine, mock_config = setup_engine
    mock_config.locations.pop("warehouse_office")  # Remove "warehouse_office" from config
    connected_locations = ["warehouse_office", "town_square"]
    result = engine._find_closest_location_match("warehouse_office", connected_locations)
    assert result is None

def test_movement_with_natural_language(setup_engine):
    engine, _ = setup_engine
    variations = [
        "go to warehouse office",
        "go to the warehouse office",
        "walk towards warehouse office",
        "move into warehouse office",
        "head to the warehouse office"
    ]
    for command in variations:
        engine.current_location = "warehouse_entrance"  # Reset location
        response = engine.process_input(command)
        assert engine.current_location == "warehouse_office", f"Failed on command: {command}"
        assert engine.previous_location == "warehouse_entrance"

def test_npc_pronoun_matching(setup_engine):
    engine, _ = setup_engine
    engine.current_location = "warehouse_entrance"
    
    # Test single female match
    matched_id, ambiguous = engine._find_matching_npc("her")
    assert matched_id == "worker_chen"
    assert not ambiguous

def test_npc_name_matching(setup_engine):
    engine, _ = setup_engine
    engine.current_location = "warehouse_entrance"
    
    # Test various name matches
    assert engine._find_matching_npc("sarah")[0] == "worker_chen"
    assert engine._find_matching_npc("chen")[0] == "worker_chen"
    assert engine._find_matching_npc("sarah chen")[0] == "worker_chen"
