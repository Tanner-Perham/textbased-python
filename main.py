"""
Main module for the Tequila Sunrise text adventure game.
"""
import os
import sys
import time
from typing import Optional, Tuple

from config.config_loader import GameConfig
from game.engine import GameEngine


def load_config(config_path: str) -> Optional[GameConfig]:
    """Load game configuration."""
    try:
        return GameConfig.load(config_path)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return None


def main():
    """Main function."""
    # Set up
    config_path = "game_config.yaml"
    
    print("Loading game configuration...")
    config = load_config(config_path)
    if not config:
        print("Failed to load game configuration. Exiting.")
        sys.exit(1)
    
    print(f"Welcome to {config.game_settings.title}!")
    print("Type 'help' for a list of commands.")
    
    # Initialize the game engine with the configuration
    game_engine = GameEngine(config)
    
    print(f"Current Location: {game_engine.current_location}")
    print("Enter a command (or type 'help' for a list of commands):")
    
    last_update_time = time.time()
    notification_check_time = time.time()
    
    # Main game loop
    while True:
        # Get user input
        try:
            prompt = "> "
            user_input = input(prompt)
        except KeyboardInterrupt:
            print("\nExiting game. Goodbye!")
            break
        except EOFError:
            print("\nExiting game. Goodbye!")
            break
        
        # Exit command
        if user_input.lower() == "quit":
            # Ask about saving
            print("Would you like to save before exiting? (yes/no)")
            save_response = input("> ").strip().lower()
            
            if save_response in ["yes", "y"]:
                print(game_engine.process_input("quicksave"))
            
            print("Exiting game. Goodbye!")
            break
        
        # Check if it's time to update quests (every 2 seconds)
        current_time = time.time()
        if current_time - last_update_time >= 2:
            game_engine.check_quest_updates()
            last_update_time = current_time
        
        # Check for notifications (every 100ms in a real implementation)
        if current_time - notification_check_time >= 0.1:
            # In a real implementation with a UI, you'd display notifications here
            notification_check_time = current_time
        
        # Process the command and display the response
        response = game_engine.process_input(user_input)
        print(response)
        print()  # Empty line for readability


if __name__ == "__main__":
    main()
