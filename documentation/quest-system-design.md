# Quest System Design for YAML-Driven Text Adventure Game

## Overview
This document details a quest system architecture for a text adventure game that reads game content from YAML files. The system integrates with an existing game state object and engine to provide comprehensive quest management capabilities.

## Core Architecture Components

### 1. YAMLParser
Responsible for loading and parsing quest definitions from YAML files into the game state.

**Key Functions:**
- `parse_quest_data(yaml_file)`: Loads quest definitions, triggers, and consequences
- `validate_quest_structure(quest_data)`: Ensures quest data follows required format

### 2. GameState
Maintains the state of all game elements including quests.

**Quest-Related Properties:**
- `quests`: Dictionary of all quest objects with their states
- `active_quests`: Currently active quests
- `completed_quests`: History of finished quests
- `quest_flags`: Markers tracking quest-related events

**Functions:**
- `get_quest_data(quest_id)`: Retrieves quest information
- `set_quest_status(quest_id, status)`: Updates quest status
- `set_stage_status(quest_id, stage_id, status)`: Updates stage status
- `get_quest_flag(flag_name)` / `set_quest_flag(flag_name, value)`: Manages flags

### 3. QuestManager
Central coordinator of all quest-related operations and logic.

**Query Functions:**
- `get_all_quests()`: Returns all quests defined in the game
- `get_active_quests()`: Returns currently active quests
- `get_available_quests()`: Returns quests that can be started
- `get_completed_quests()`: Returns finished quests
- `get_failed_quests()`: Returns quests that were failed
- `get_quest_by_id(quest_id)`: Retrieves a specific quest

**Status Functions:**
- `start_quest(quest_id)`: Activates a quest if prerequisites are met
- `complete_quest(quest_id)`: Marks quest as completed, gives rewards
- `fail_quest(quest_id)`: Marks quest as failed, implements consequences
- `is_quest_available(quest_id)`: Checks if a quest can be started
- `is_quest_complete(quest_id)`: Checks if a quest is finished
- `get_quest_status(quest_id)`: Returns current status of a quest

**Stage Functions:**
- `get_current_stage(quest_id)`: Gets active stage for a quest
- `get_next_stage(quest_id)`: Determines next stage in progression
- `complete_stage(quest_id, stage_id)`: Marks stage as completed
- `is_stage_complete(quest_id, stage_id)`: Checks if stage is done
- `get_stage_requirements(quest_id, stage_id)`: Lists requirements
- `update_quest_progress(quest_id)`: Updates status based on stages

**Trigger System:**
- `check_quest_triggers(action, context)`: Evaluates if actions trigger events
- `process_world_event(event_type, event_data)`: Handles game world events
- `evaluate_condition(condition, context)`: Interprets trigger conditions
- `execute_consequence(consequence_type, data)`: Implements quest effects

### 4. GameEngine
Coordinates all systems and processes player actions.

**Quest-Related Functions:**
- `process_player_action(action)`: Routes to QuestManager
- `render_quest_information()`: Displays info to player
- `apply_quest_consequences(quest_id)`: Implements world changes
- `check_location_triggers(location)`: Checks for location-based triggers
- `check_item_triggers(item_id, action)`: Checks for item-based triggers
- `check_dialogue_triggers(npc_id, dialogue_node, option)`: Checks dialogue triggers

## YAML Structure

### Quest Definition
```yaml
quests:
  quest_id:
    title: "Quest Title"
    description: "Quest description"
    giver: "npc_id"
    initial_status: "not_started"  # not_started, active, completed, failed
    
    stages:
      - id: "stage_id"
        description: "Stage description"
        initial: true  # Whether this is the first stage
        requires:
          - "prerequisite_stage_id"  # Optional dependencies on other stages
          
    completion_triggers:
      all_stages_complete: true
      # or specific conditions
      
    consequences:
      on_complete:
        - type: "consequence_type"
          data: consequence_specific_data
      on_fail:
        - type: "consequence_type"
          data: consequence_specific_data
```

### Trigger Definitions

**Dialogue Triggers:**
```yaml
npcs:
  npc_id:
    dialogue:
      node_id:
        options:
          - text: "Option text"
            triggers:
              quest_start: "quest_id"
              quest_stage_complete: 
                quest_id: "quest_id"
                stage_id: "stage_id"
              condition: "expression"  # Optional condition
```

**Item Triggers:**
```yaml
items:
  item_id:
    triggers:
      on_pickup:
        quest_stage_complete:
          quest_id: "quest_id"
          stage_id: "stage_id"
      on_use:
        location: "location_id"  # Optional context requirement
        quest_update:
          quest_id: "quest_id"
          update: "update_type"
```

**Location Triggers:**
```yaml
locations:
  location_id:
    triggers:
      on_enter:
        quest_stage_complete:
          quest_id: "quest_id"
          stage_id: "stage_id"
          condition: "expression"
```

## Workflow Integration

### Game Initialization
1. YAMLParser loads quest definitions into GameState
2. QuestManager initializes with GameState
3. GameEngine orchestrates all components

### Player Action Handling
1. GameEngine receives player action (movement, item use, dialogue)
2. Updates game world state
3. Checks for relevant triggers via QuestManager
4. QuestManager processes triggers and updates quest states
5. GameEngine applies consequences and renders results

### Quest Progression Flow
1. Player performs action triggering quest event
2. QuestManager.check_quest_triggers() identifies relevant triggers
3. If conditions are met, QuestManager updates quest/stage status
4. QuestManager.update_quest_progress() checks if quest state should change
5. If quest completes/fails, consequences are executed
6. GameState is updated with new quest information
7. GameEngine renders results to player

## Supported Trigger Types
- Dialogue selection
- Item acquisition/use
- World Object Examining
- Location entry/exit
- Combat outcomes
- Inventory state
- Game time events
- Player stat changes

## Supported Consequence Types
- Item rewards/removals
- Currency changes
- NPC state changes
- Location accessibility changes
- New quest availability
- Stat/skill changes
- World state alterations

## Condition Expression System
Support for expressions like:
- `quest_active(quest_id)`
- `quest_stage_complete(quest_id, stage_id)`
- `has_item(item_id, [quantity])`
- `player.stat > value`
- Compound expressions with `&&` (AND) and `||` (OR)

## Implementation Notes
1. Maintain clear separation between data (GameState) and logic (QuestManager)
2. Process triggers after state changes to ensure correct context
3. Design quest stages to be independent enough to handle out-of-order completion
4. Cache quest availability to avoid recalculating frequently
5. Consider save/load serialization of quest state early in development

This architecture provides a flexible, data-driven system where quest behavior can be defined entirely in YAML configuration, allowing for rapid quest development without code changes.
