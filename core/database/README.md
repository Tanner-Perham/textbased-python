# Database Migration

This directory contains the code for migrating game data from YAML files to SQLite database.

## Overview

The migration process consists of three main components:

1. `database_manager.py`: Handles all database operations
2. `config_loader.py`: Loads game configuration from SQLite database
3. `migrate_yaml_to_sqlite.py`: Migrates YAML data to SQLite database

## Usage

### Migration

To migrate YAML data to SQLite, run:

```bash
./scripts/migrate_yaml_to_sqlite.py [--yaml-dir PATH] [--db PATH]
```

Arguments:
- `--yaml-dir`: Directory containing YAML game data (default: `config/game_data/content`)
- `--db`: Path to SQLite database file (default: `game_data.db`)

### Loading Configuration

To load game configuration from SQLite, use the `SqliteConfigLoader` class:

```python
from core.database import SqliteConfigLoader

loader = SqliteConfigLoader("game_data.db")
config = loader.load_game_config()
```

## Database Schema

The database schema is defined in `schema.py`. It includes tables for:

- Game settings
- Locations
- NPCs
- Dialogues
- Quests
- Items
- Item sets
- Character archetypes

## Notes

- The migration process preserves all data from the YAML files
- Complex data structures (lists, dictionaries) are stored as JSON strings
- Boolean values are stored as integers (0 or 1)
- Foreign key relationships are maintained
- The database is created if it doesn't exist
- Existing data in the database is not automatically cleared before migration 