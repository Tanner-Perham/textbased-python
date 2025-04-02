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
from game.dialogue_integration import DialogueHandler
from game.engine import GameEngine
from ui.dialogue_ui import DialogueUI


def load_config(config_path: str) -> Optional[GameConfig]:
    """Load game configuration."""
    try:
        return GameConfig.load(config_path)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return None


async def main():
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

    # Initialize dialogue system
    dialogue_manager = DialogueManager()
    dialogue_manager.set_dialogue_tree(convert_dialogue_trees(config))
    dialogue_handler = DialogueHandler(dialogue_manager)
    game_engine.dialogue_handler = dialogue_handler

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

        # Special handling for dialogue commands
        command_parts = user_input.lower().split(maxsplit=1)
        if (
            command_parts
            and command_parts[0] in ["talk", "speak"]
            and len(command_parts) > 1
        ):
            npc_name = command_parts[1]
            # Find NPC in current location
            npc_id = find_npc_by_name(config, game_engine.current_location, npc_name)
            if npc_id:
                # Handle dialogue with async
                try:
                    print(f"\nStarting conversation with {config.npcs[npc_id].name}...")
                    result = await dialogue_handler.handle_dialogue(
                        npc_id, game_engine.game_state
                    )
                    print(result)
                except Exception as e:
                    print(f"Error in dialogue: {e}")
            else:
                print(f"There is no {npc_name} here to talk to.")
        else:
            # Normal command processing
            response = game_engine.process_input(user_input)
            print(response)

        print()  # Empty line for readability


def find_npc_by_name(
    config: GameConfig, current_location: str, npc_name: str
) -> Optional[str]:
    """Find an NPC ID by name in the current location."""
    for npc_id, npc in config.npcs.items():
        # Check if NPC is in current location
        if npc.location != current_location:
            continue

        # Check for name match (case-insensitive partial match)
        if npc_name.lower() in npc.name.lower():
            return npc_id

        # Check for pronoun match
        if matches_pronoun(config, npc, npc_name, current_location):
            return npc_id

    return None


def matches_pronoun(
    config: GameConfig, npc, pronoun: str, current_location: str
) -> bool:
    """Check if NPC matches a pronoun."""
    pronoun = pronoun.lower()

    # Count NPCs of each gender in current location
    males_in_location = sum(
        1
        for n in config.npcs.values()
        if n.location == current_location and n.gender == "male"
    )

    females_in_location = sum(
        1
        for n in config.npcs.values()
        if n.location == current_location and n.gender == "female"
    )

    if (
        pronoun in ["him", "he", "his"]
        and npc.gender == "male"
        and males_in_location == 1
    ):
        return True

    if (
        pronoun in ["her", "she", "hers"]
        and npc.gender == "female"
        and females_in_location == 1
    ):
        return True

    if pronoun in ["them", "they", "their"]:
        return True  # Always matches but might be ambiguous

    return False


def convert_dialogue_trees(config):
    """Convert config dialogue trees to internal format."""
    from dialogue.node import (
        DialogueNode,
        DialogueOption,
        EnhancedSkillCheck,
        InnerVoiceComment,
    )

    internal_trees = {}

    for node_id, config_node in config.dialogue_trees.items():
        # Convert inner voice comments
        inner_voice_comments = []
        for comment in config_node.inner_voice_comments:
            inner_voice_comments.append(
                InnerVoiceComment(
                    voice_type=comment.get("voice_type", ""),
                    text=comment.get("text", ""),
                    skill_requirement=comment.get("skill_requirement"),
                )
            )

        # Convert options
        options = []
        for opt in config_node.options:
            # Convert opt to dictionary if it's not already
            if not isinstance(opt, dict):
                opt = vars(opt)  # Convert object to dictionary

            # Convert skill check if present
            skill_check = None
            if "skill_check" in opt and opt["skill_check"]:
                check_data = opt["skill_check"]
                if not isinstance(check_data, dict):
                    check_data = vars(check_data)

                skill_check = EnhancedSkillCheck(
                    base_difficulty=check_data.get("base_difficulty", 10),
                    primary_skill=check_data.get("primary_skill", ""),
                    supporting_skills=check_data.get("supporting_skills", []),
                    emotional_modifiers=check_data.get("emotional_modifiers", {}),
                    white_check=check_data.get("white_check", False),
                    hidden=check_data.get("hidden", False),
                )

            # Create dialogue option
            option = DialogueOption(
                id=opt.get("id", ""),
                text=opt.get("text", ""),
                next_node=opt.get("next_node", ""),
                skill_check=skill_check,
                emotional_impact=opt.get("emotional_impact", {}),
                conditions=opt.get("conditions", {}),
                consequences=opt.get("consequences", []),
                inner_voice_reactions=[],  # Would need conversion
                success_node=opt.get("success_node", ""),
                failure_node=opt.get("failure_node", ""),
            )
            options.append(option)

        # Create internal node
        internal_node = DialogueNode(
            id=node_id,
            text=config_node.text,
            speaker=config_node.speaker,
            emotional_state=config_node.emotional_state,
            inner_voice_comments=inner_voice_comments,
            options=options,
        )

        internal_trees[node_id] = internal_node

    return internal_trees


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting game. Goodbye!")
        sys.exit(0)
