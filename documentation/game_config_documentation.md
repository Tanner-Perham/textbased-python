# Game Configuration Documentation

## Overview
This document provides a comprehensive guide to the structure and components of the `game_config.yaml` file, which defines the core mechanics, story elements, characters, and world of a game written for the "Tequilla Sunrise" text-based adventure game engine.

## Table of Contents
- [Game Settings](#game-settings)
- [Character Archetypes](#character-archetypes)
- [Item Sets](#item-sets)
- [Items](#items)
- [Locations](#locations)
- [NPCs](#npcs)
- [Dialogue Trees](#dialogue-trees)
- [Quests](#quests)

## Game Settings
The `game_settings` section defines the fundamental parameters of the game world:

```yaml
game_settings:
  title: "The Warehouse Mystery"
  starting_location: "warehouse_entrance"
  default_time: "Morning"
  starting_inventory:
    - "police_badge"
    - "notebook"
    - "pen"
    - "flashlight"
    - "evidence_bag"
    # Additional items by ID only
```

Key components:
- **title**: The name of the game
- **starting_location**: The location ID where the player begins
- **default_time**: The starting time of day
- **starting_inventory**: List of items the player begins with

## Character Archetypes
The `character_archetypes` section defines the different types of player characters available in the game:

```yaml
character_archetypes:
  analytical:
    id: "analytical"
    name: "Analytical Detective"
    description: "You solve cases through careful observation..."
    starting_skills:
      logic: 3
      perception: 3
      # Other skills with ratings
    starting_equipment_ids:
      - "notebook"
      - "magnifying_glass"
      # Other equipment IDs
```

Key components:
- **id**: Unique identifier for the archetype
- **name**: Display name
- **description**: Character background and approach
- **starting_skills**: Numerical values for various abilities
- **starting_equipment_ids**: References to items from the items section

## Item Sets
The `item_sets` section defines collections of items that provide bonuses when worn together:

```yaml
item_sets:
  detective_suit:
    id: "detective_suit"
    name: "Classic Detective's Attire"
    description: "A timeless ensemble that commands respect and attention."
    required_pieces: ["detective_hat", "detective_coat", "detective_slacks", "detective_shoes"]
    set_bonus:
      - attribute: "authority"
        value: 2
        description: "The complete detective's outfit grants an air of unmistakable authority."
```

Key components:
- **id**: Unique identifier for the set
- **name**: Display name
- **description**: Set description
- **required_pieces**: Item IDs needed to complete the set
- **set_bonus**: List of attribute bonuses granted when the set is complete

## Items
The `items` section defines all objects that can be found, used, or equipped in the game:

```yaml
items:
  detective_hat:
    id: "detective_hat"
    name: "Well-Worn Detective's Hat"
    description: "A classic fedora that's seen its share of cases."
    categories: ["WEARABLE"]
    slot: "HEAD"
    weight: 0.5
    style_rating: 7
    effects:
      - attribute: "perception"
        value: 1
        description: "The hat's brim helps focus your attention on details."
    set_id: "detective_suit"
    # Additional optional properties
```

Key components:
- **id**: Unique identifier for the item
- **name**: Display name
- **description**: Item description
- **categories**: Item types (WEARABLE, TOOL, CONSUMABLE, etc.)
- **slot**: Body location for wearable items
- **weight**: Item weight affecting inventory capacity
- **style_rating**: Aesthetic value
- **effects**: Attribute modifications when used or equipped
- **set_id**: Reference to an item set (if applicable)
- **hidden_lore**: Background story revealed with high wisdom
- **hidden_clues**: Details discovered with high perception
- **hidden_usage**: Special uses discovered with skill checks
- **perception_difficulty**: Skill threshold to discover hidden aspects
- **wisdom_difficulty**: Skill threshold to understand hidden aspects

## Locations
The `locations` section defines the physical spaces in the game world:

```yaml
locations:
  warehouse_entrance:
    id: "warehouse_entrance"
    name: "Warehouse Entrance"
    description: "A imposing metal door stands before you..."
    available_actions:
      - name: "inspect_door"
        description: "Examine the warehouse door closely"
        requirements:
          perception: 8
        consequences:
          - event_type: "AddClue"
            data:
              id: "scratch_marks"
              description: "Recent scratch marks around the lock suggest forced entry"
    connected_locations:
      - "warehouse_office"
      - "parking_lot"
```

Key components:
- **id**: Unique identifier for the location
- **name**: Display name
- **description**: Environmental description
- **available_actions**: Special interactions possible at this location
  - **name**: Action identifier
  - **description**: Action description
  - **requirements**: Skill checks needed to perform the action
  - **consequences**: Results of performing the action
- **connected_locations**: Other location IDs that can be accessed from here

## NPCs
The `npcs` section defines the non-player characters that inhabit the game world:

```yaml
npcs:
  guard_martinez:
    id: "guard_martinez"
    name: "Officer Martinez"
    dialogue_entry_point: "martinez_intro"
    disposition: 50
    location: "warehouse_office"
    gender: "male"
```

Key components:
- **id**: Unique identifier for the NPC
- **name**: Display name
- **dialogue_entry_point**: Starting dialogue tree node
- **disposition**: Initial attitude toward player (higher is more friendly)
- **location**: Location ID where the NPC can be found
- **gender**: NPC gender

## Dialogue Trees
The `dialogue_trees` section defines conversation flows with NPCs:

```yaml
dialogue_trees:
  martinez_intro:
    id: "martinez_intro"
    text: "What are you doing here? This is a restricted area."
    speaker: "guard_martinez"
    emotional_state: "Suspicious"
    inner_voice_comments:
      - voice_type: "Empathy"
        text: "His posture is defensive, but there's worry in his eyes."
        skill_requirement: 8
    options:
      - id: "show_badge"
        text: "Show your badge: 'Detective from the 41st precinct...'"
        skill_check:
          base_difficulty: 12
          primary_skill: "authority"
          supporting_skills:
            - ["composure", 0.5]
        emotional_impact:
          Friendly: 2
          Suspicious: -3
        conditions:
          required_items: ["police_badge"]
        next_node: "martinez_cooperative"
```

Key components:
- **id**: Unique identifier for the dialogue node
- **text**: NPC's dialogue
- **speaker**: NPC ID who is speaking
- **emotional_state**: Current mood of the NPC
- **inner_voice_comments**: Player's internal observations (requires skill checks)
- **options**: Possible player responses
  - **id**: Response identifier
  - **text**: Player's dialogue option
  - **skill_check**: Challenge parameters if the response requires a check
  - **emotional_impact**: How the response affects NPC disposition
  - **conditions**: Requirements to see or use this option
  - **next_node**: Next dialogue node ID if selected
  - **success_node/failure_node**: Alternative paths based on skill check

## Quests
The `quests` section defines objectives and storylines for the player to complete:

```yaml
quests:
  main_investigation:
    id: "main_investigation"
    title: "The Warehouse Investigation"
    description: "Investigate the strange occurrences at the warehouse."
    short_description: "Investigate warehouse incidents"
    importance: "Critical"
    is_main_quest: true
    is_hidden: false
    status: "NotStarted"
    stages:
      - id: "initial_investigation"
        title: "Initial Investigation"
        description: "Gather information about the warehouse incident."
        status: "NotStarted"
        objectives:
          - id: "talk_to_guard"
            description: "Talk to Officer Martinez about the incident"
            is_completed: false
            is_optional: false
            completion_events:
              - event_type: "AddClue"
                data:
                  id: "guard_statement"
                  description: "The guard mentioned unusual activity in the warehouse"
```

Key components:
- **id**: Unique identifier for the quest
- **title**: Display name
- **description**: Detailed quest description
- **short_description**: Abbreviated description for quest logs
- **importance**: Priority level (Critical, Optional, etc.)
- **is_main_quest**: Boolean indicating if it's part of the main storyline
- **is_hidden**: Boolean indicating if it should be hidden until discovered
- **status**: Current quest state (NotStarted, InProgress, Completed)
- **stages**: Sequential phases of the quest
  - **id**: Stage identifier
  - **title**: Stage name
  - **description**: Stage description
  - **status**: Current stage state
  - **objectives**: Individual tasks within the stage
    - **id**: Objective identifier
    - **description**: Task description
    - **is_completed**: Boolean completion status
    - **is_optional**: Boolean indicating if required for stage completion
    - **completion_events**: Game events triggered when objective is completed
  - **notification_text**: Message displayed when stage is reached
- **rewards**: Benefits granted upon quest completion 