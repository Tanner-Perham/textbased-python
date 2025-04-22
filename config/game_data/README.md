# Game Configuration Structure

This directory contains the game's configuration files split into modular components for better maintainability.

## Configuration Files

The game configuration is split into the following files:

- `main.yaml` - Main configuration file that includes all the component files
- `game_settings.yaml` - Basic game settings like title, starting location, etc.
- `character_archetypes.yaml` - Character archetypes for player selection
- `item_sets.yaml` - Sets of items that provide bonuses when worn together
- `items.yaml` - All game items, including wearables, tools, and consumables
- `locations.yaml` - All game locations with their descriptions and connections
- `npcs.yaml` - Non-player characters in the game
- `dialogue_trees.yaml` - Dialogue trees for conversations with NPCs
- `quests.yaml` - Game quests and their stages
- `inner_voices.yaml` - Configuration for the character's inner voices (currently empty)
- `thoughts.yaml` - Configuration for the character's thoughts (currently empty)

## How it Works

The game loads configuration in the following way:

1. The `main.py` script checks if the `config/game_data` directory exists
   - If it does, it uses this directory as the config source
   - If not, it falls back to using the single `game_config.yaml` file

2. When loading from the directory:
   - The loader first checks for a `main.yaml` file
   - If found, it reads the `include` section to determine which files to load
   - If not found, it loads all YAML files in the directory

## Adding New Content

To add new content to the game:

1. Identify the appropriate configuration file for your content
2. Add your content using the existing format as a guide
3. Make sure your YAML is properly formatted

## Converting from Single File to Split Configuration

If you have custom changes in a single `game_config.yaml` file and want to convert to the split structure:

1. Copy the relevant sections from your file to the corresponding component files
2. Keep the same YAML structure within each section
3. Use the `main.yaml` file to include all the component files 