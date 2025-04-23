"""
SQLite schema for the game database.
"""

CREATE_TABLES = [
    # Game Settings
    """
    CREATE TABLE IF NOT EXISTS game_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        starting_location TEXT NOT NULL,
        default_time TEXT NOT NULL
    )
    """,
    
    # Starting Inventory (as a separate table since it's a list in the YAML)
    """
    CREATE TABLE IF NOT EXISTS starting_inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id TEXT NOT NULL,
        quantity INTEGER DEFAULT 1
    )
    """,
    
    # Locations
    """
    CREATE TABLE IF NOT EXISTS locations (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT NOT NULL
    )
    """,
    
    # Location Connections
    """
    CREATE TABLE IF NOT EXISTS location_connections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        location_id TEXT NOT NULL,
        connected_location_id TEXT NOT NULL,
        FOREIGN KEY (location_id) REFERENCES locations(id),
        FOREIGN KEY (connected_location_id) REFERENCES locations(id)
    )
    """,
    
    # Location Actions
    """
    CREATE TABLE IF NOT EXISTS location_actions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        location_id TEXT NOT NULL,
        action_type TEXT NOT NULL,
        action_data TEXT NOT NULL,
        FOREIGN KEY (location_id) REFERENCES locations(id)
    )
    """,
    
    # Location Items
    """
    CREATE TABLE IF NOT EXISTS location_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        location_id TEXT NOT NULL,
        item_id TEXT NOT NULL,
        is_obvious BOOLEAN DEFAULT 1,
        perception_difficulty INTEGER DEFAULT 0,
        FOREIGN KEY (location_id) REFERENCES locations(id),
        FOREIGN KEY (item_id) REFERENCES items(id)
    )
    """,
    
    # Location Containers
    """
    CREATE TABLE IF NOT EXISTS location_containers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        location_id TEXT NOT NULL,
        container_id TEXT NOT NULL,
        is_obvious BOOLEAN DEFAULT 1,
        FOREIGN KEY (location_id) REFERENCES locations(id),
        FOREIGN KEY (container_id) REFERENCES items(id)
    )
    """,
    
    # Container Contents
    """
    CREATE TABLE IF NOT EXISTS container_contents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        container_id TEXT NOT NULL,
        item_id TEXT NOT NULL,
        quantity INTEGER DEFAULT 1,
        FOREIGN KEY (container_id) REFERENCES items(id),
        FOREIGN KEY (item_id) REFERENCES items(id)
    )
    """,
    
    # NPCs
    """
    CREATE TABLE IF NOT EXISTS npcs (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        dialogue_entry_point TEXT NOT NULL,
        disposition INTEGER NOT NULL,
        location TEXT NOT NULL,
        gender TEXT NOT NULL,
        FOREIGN KEY (location) REFERENCES locations(id)
    )
    """,
    
    # NPC Schedules
    """
    CREATE TABLE IF NOT EXISTS npc_schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        npc_id TEXT NOT NULL,
        time TEXT NOT NULL,
        location TEXT NOT NULL,
        FOREIGN KEY (npc_id) REFERENCES npcs(id),
        FOREIGN KEY (location) REFERENCES locations(id)
    )
    """,
    
    # Dialogues
    """
    CREATE TABLE IF NOT EXISTS dialogues (
        id TEXT PRIMARY KEY,
        text TEXT NOT NULL,
        speaker TEXT NOT NULL,
        emotional_state TEXT NOT NULL
    )
    """,
    
    # Dialogue Options
    """
    CREATE TABLE IF NOT EXISTS dialogue_options (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dialogue_id TEXT NOT NULL,
        text TEXT NOT NULL,
        next_dialogue_id TEXT,
        success_node TEXT,
        failure_node TEXT,
        critical_success_node TEXT,
        critical_failure_node TEXT,
        skill_check_id INTEGER,
        FOREIGN KEY (dialogue_id) REFERENCES dialogues(id),
        FOREIGN KEY (next_dialogue_id) REFERENCES dialogues(id),
        FOREIGN KEY (success_node) REFERENCES dialogues(id),
        FOREIGN KEY (failure_node) REFERENCES dialogues(id),
        FOREIGN KEY (critical_success_node) REFERENCES dialogues(id),
        FOREIGN KEY (critical_failure_node) REFERENCES dialogues(id),
        FOREIGN KEY (skill_check_id) REFERENCES dialogue_skill_checks(id)
    )
    """,
    
    # Dialogue Skill Checks
    """
    CREATE TABLE IF NOT EXISTS dialogue_skill_checks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dialogue_option_id INTEGER NOT NULL,
        base_difficulty INTEGER NOT NULL,
        primary_skill TEXT NOT NULL,
        supporting_skills TEXT,
        emotional_modifiers TEXT,
        is_white_check BOOLEAN DEFAULT 0,
        is_hidden BOOLEAN DEFAULT 0,
        FOREIGN KEY (dialogue_option_id) REFERENCES dialogue_options(id)
    )
    """,
    
    # Dialogue Supporting Skills
    """
    CREATE TABLE IF NOT EXISTS dialogue_supporting_skills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        skill_check_id INTEGER NOT NULL,
        skill_name TEXT NOT NULL,
        skill_multiplier REAL NOT NULL,
        FOREIGN KEY (skill_check_id) REFERENCES dialogue_skill_checks(id)
    )
    """,
    
    # Dialogue Emotional Modifiers
    """
    CREATE TABLE IF NOT EXISTS dialogue_emotional_modifiers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        skill_check_id INTEGER NOT NULL,
        emotional_state TEXT NOT NULL,
        modifier_value INTEGER NOT NULL,
        FOREIGN KEY (skill_check_id) REFERENCES dialogue_skill_checks(id)
    )
    """,
    
    # Dialogue Conditions
    """
    CREATE TABLE IF NOT EXISTS dialogue_conditions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dialogue_id TEXT NOT NULL,
        condition_type TEXT NOT NULL,
        condition_data TEXT NOT NULL,
        FOREIGN KEY (dialogue_id) REFERENCES dialogues(id)
    )
    """,
    
    # Dialogue Effects
    """
    CREATE TABLE IF NOT EXISTS dialogue_effects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dialogue_id TEXT NOT NULL,
        effect_type TEXT NOT NULL,
        effect_data TEXT NOT NULL,
        FOREIGN KEY (dialogue_id) REFERENCES dialogues(id)
    )
    """,
    
    # Quests
    """
    CREATE TABLE IF NOT EXISTS quests (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        short_description TEXT NOT NULL,
        importance TEXT NOT NULL,
        is_hidden BOOLEAN DEFAULT 0,
        is_main_quest BOOLEAN DEFAULT 0,
        status TEXT DEFAULT 'NotStarted'
    )
    """,
    
    # Quest Stages
    """
    CREATE TABLE IF NOT EXISTS quest_stages (
        id TEXT PRIMARY KEY,
        quest_id TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        notification_text TEXT,
        status TEXT DEFAULT 'NotStarted',
        FOREIGN KEY (quest_id) REFERENCES quests(id)
    )
    """,
    
    # Quest Objectives
    """
    CREATE TABLE IF NOT EXISTS quest_objectives (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stage_id TEXT NOT NULL,
        objective_type TEXT NOT NULL,
        objective_data TEXT NOT NULL,
        FOREIGN KEY (stage_id) REFERENCES quest_stages(id)
    )
    """,
    
    # Quest Rewards
    """
    CREATE TABLE IF NOT EXISTS quest_rewards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quest_id TEXT NOT NULL,
        reward_type TEXT NOT NULL,
        reward_data TEXT NOT NULL,
        FOREIGN KEY (quest_id) REFERENCES quests(id)
    )
    """,
    
    # Items
    """
    CREATE TABLE IF NOT EXISTS items (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        category TEXT NOT NULL,
        value INTEGER NOT NULL,
        weight REAL NOT NULL,
        is_stackable BOOLEAN DEFAULT 0,
        is_consumable BOOLEAN DEFAULT 0,
        is_equippable BOOLEAN DEFAULT 0,
        slot TEXT,
        effects TEXT,
        style_rating INTEGER DEFAULT 0,
        hidden_clues TEXT,
        hidden_usage TEXT,
        perception_difficulty INTEGER DEFAULT 0,
        set_id TEXT,
        FOREIGN KEY (set_id) REFERENCES item_sets(id)
    )
    """,
    
    # Item Sets
    """
    CREATE TABLE IF NOT EXISTS item_sets (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT NOT NULL
    )
    """,
    
    # Item Set Pieces
    """
    CREATE TABLE IF NOT EXISTS item_set_pieces (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        set_id TEXT NOT NULL,
        item_id TEXT NOT NULL,
        FOREIGN KEY (set_id) REFERENCES item_sets(id),
        FOREIGN KEY (item_id) REFERENCES items(id)
    )
    """,
    
    # Item Set Bonuses
    """
    CREATE TABLE IF NOT EXISTS item_set_bonuses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        set_id TEXT NOT NULL,
        attribute TEXT NOT NULL,
        value REAL NOT NULL,
        description TEXT NOT NULL,
        FOREIGN KEY (set_id) REFERENCES item_sets(id)
    )
    """,
    
    # Character Archetypes
    """
    CREATE TABLE IF NOT EXISTS character_archetypes (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT NOT NULL
    )
    """,
    
    # Character Archetype Skills
    """
    CREATE TABLE IF NOT EXISTS archetype_skills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        archetype_id TEXT NOT NULL,
        skill_name TEXT NOT NULL,
        skill_value REAL NOT NULL,
        FOREIGN KEY (archetype_id) REFERENCES character_archetypes(id)
    )
    """,
    
    # Character Archetype Equipment
    """
    CREATE TABLE IF NOT EXISTS archetype_equipment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        archetype_id TEXT NOT NULL,
        item_id TEXT NOT NULL,
        FOREIGN KEY (archetype_id) REFERENCES character_archetypes(id),
        FOREIGN KEY (item_id) REFERENCES items(id)
    )
    """
] 