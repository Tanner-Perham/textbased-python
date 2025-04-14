"""
Main module for the Tequila Sunrise text adventure game.
"""

import asyncio
import os
import sys
import time
from typing import Optional, Tuple

from config.config_loader import GameConfig
from dialogue.manager import DialogueManager
from dialogue.response import DialogueResponse
from dialogue.converter import convert_dialogue_trees
from game.engine import GameEngine
from ui.dialogue_ui import DialogueMode
from ui.game_ui import GameUI
from textual.app import App


def main():
    """Main function."""
    # Set up
    config_path = "game_config.yaml"

    print("Loading game configuration...")
    try:
        config = GameConfig.load(config_path)
    except Exception as e:
        print(f"Failed to load game configuration: {e}")
        sys.exit(1)

    # Initialize the game engine
    game_engine = GameEngine(config)

    # Initialize dialogue system
    dialogue_manager = DialogueManager()
    dialogue_manager.game_engine = game_engine  # Set the game_engine reference
    dialogue_manager.set_dialogue_tree(convert_dialogue_trees(config))
    game_engine.dialogue_handler = dialogue_manager

    # Create and run the UI
    app = GameUI()
    app.game_engine = game_engine  # Attach game engine to UI
    game_engine.ui = app  # Attach UI to game engine
    app.title = config.game_settings.title
    
    return app


if __name__ == "__main__":
    app = main()
    app.run()
