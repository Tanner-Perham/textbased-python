# Tequila Sunrise Text Adventure Game Engine

A powerful and flexible text-based adventure game engine that allows you to create rich, interactive narrative experiences through YAML configuration.

## Overview

Tequila Sunrise is a Python-based game engine that enables game designers and writers to build complex text adventures without extensive programming knowledge. By defining your game world, characters, quests, and dialogues in YAML files, you can create engaging interactive fiction with:

- **Rich dialogue systems** with NPC interactions and branching conversations
- **Complex quest systems** with triggers, conditions, and consequences
- **Dynamic inventory management** with containers, wearable items, and item sets
- **Character creation and progression** with skills, attributes and equipment
- **Save/load functionality** for game persistence
- **Modern TUI** powered by Textual for a visually appealing interface

## Getting Started

### Prerequisites

- Python 3.13 or higher
- pip (Python package manager)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/textbased-python.git
   cd textbased-python
   ```

2. Set up a virtual environment (recommended):
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run the game:
   ```
   python main.py
   ```

## Game Configuration

The entire game is defined through YAML configuration files, primarily `game_config.yaml`. This file defines:

- Game settings (title, starting location, etc.)
- Character archetypes and skills
- Items and equipment
- Locations and their connections
- NPCs and dialogue trees
- Quests and objectives
- Game world interactions

See the [Game Configuration Documentation](documentation/game_config_documentation.md) for detailed information on how to define your game world.

## Documentation

Comprehensive documentation is available to help you create your own games:

- [Game Configuration Guide](documentation/game_config_documentation.md) - How to structure your game's YAML config
- [Quest System Design](documentation/quest-system-design.md) - Details on the quest management system
- [UI-Engine Integration](documentation/ui-engine-integration.md) - How the UI interacts with the game engine
- [Condition Types](documentation/condition_types.md) - Available condition types for triggers and requirements

## Features

### Game Engine

- **State Management**: Tracks player progress, inventory, location, and game world state
- **Command Processing**: Handles player input with natural language understanding
- **Quest Management**: Tracks quest progress and triggers events
- **Save/Load System**: Allows players to save and resume their games

### Character System

- **Character Creation**: Choose from different character archetypes
- **Skills & Attributes**: Character stats that affect gameplay options
- **Inventory Management**: Item collection, equipment, and container handling
- **Progression**: Experience points, level-ups, and skill improvements

### World Interaction

- **Location Navigation**: Move between connected areas in the game world
- **Object Interaction**: Examine, use, take, and drop items
- **NPC Dialogue**: Conversation system with branching dialogue trees
- **Environmental Descriptions**: Rich text descriptions of locations and objects

### UI System

- **Textual TUI**: Modern terminal user interface with styled text
- **Dialogue Mode**: Specialized interface for conversations
- **Inventory Display**: Visual representation of player inventory
- **Quest Tracking**: Interface for monitoring quest progress

## Extending the Engine

The engine is designed to be modular and extensible. You can:

1. Add new command handlers in `game/engine.py`
2. Create custom dialogue response types in `dialogue/response.py`
3. Implement new item categories or effects in `game/inventory.py`
4. Add quest trigger types in `quest/quest_manager.py`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 