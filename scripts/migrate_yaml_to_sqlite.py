#!/usr/bin/env python3
"""
Script to migrate YAML game data to SQLite database.
"""

import os
import sys
import argparse
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from core.database import YamlToSqliteMigrator

def main():
    """Main function to run the migration."""
    parser = argparse.ArgumentParser(description="Migrate YAML game data to SQLite database")
    parser.add_argument(
        "--yaml-dir",
        type=str,
        default="config/game_data/content",
        help="Directory containing YAML game data"
    )
    parser.add_argument(
        "--db",
        type=str,
        default="game_data.db",
        help="Path to SQLite database file"
    )
    
    args = parser.parse_args()
    
    # Check if YAML directory exists
    if not os.path.exists(args.yaml_dir):
        print(f"Error: YAML directory '{args.yaml_dir}' does not exist")
        sys.exit(1)
        
    # Create database directory if it doesn't exist
    db_dir = os.path.dirname(args.db)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
        
    # Run the migration
    print(f"Migrating YAML data from '{args.yaml_dir}' to '{args.db}'...")
    migrator = YamlToSqliteMigrator(args.yaml_dir, args.db)
    migrator.migrate()
    print("Migration complete!")
    
if __name__ == "__main__":
    main() 