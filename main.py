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
    game_engine.dialogue_handler = dialogue_manager  # Use dialogue_manager directly

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

        # Normal command processing
        response = game_engine.process_input(user_input)
        print(response)

        print()  # Empty line for readability

def convert_dialogue_trees(config):
    """Convert config dialogue trees to internal format."""
    from dialogue.node import (
        DialogueConditions,
        DialogueEffect,
        DialogueNode,
        DialogueOption,
        EnhancedSkillCheck,
        InnerVoiceComment,
    )

    # If the dialogue trees are already in the internal format, return them as-is
    if all(isinstance(node, DialogueNode) for node in config.dialogue_trees.values()):
        return config.dialogue_trees

    internal_trees = {}

    for node_id, config_node in config.dialogue_trees.items():
        # Convert inner voice comments
        inner_voice_comments = []
        for comment in getattr(config_node, "inner_voice_comments", []) or []:
            # Ensure comment is a dictionary or has the necessary attributes
            if isinstance(comment, dict):
                inner_voice_comments.append(
                    InnerVoiceComment(
                        voice_type=comment.get("voice_type", ""),
                        text=comment.get("text", ""),
                        skill_requirement=comment.get("skill_requirement"),
                        trigger_condition=(
                            DialogueConditions()
                            if comment.get("trigger_condition")
                            else None
                        ),
                    )
                )
            else:
                # If it's already an InnerVoiceComment or similar object
                inner_voice_comments.append(comment)

        # Convert options
        options = []
        for opt in getattr(config_node, "options", []) or []:
            # Skip None or invalid options
            if opt is None:
                continue

            # Handle both dictionary and object options
            if isinstance(opt, dict):
                # Convert skill check if present
                skill_check = None
                skill_check_data = opt.get("skill_check", {}) or {}
                if skill_check_data:
                    skill_check = EnhancedSkillCheck(
                        base_difficulty=skill_check_data.get("base_difficulty", 10),
                        primary_skill=skill_check_data.get("primary_skill", ""),
                        supporting_skills=skill_check_data.get("supporting_skills", []),
                        emotional_modifiers=skill_check_data.get(
                            "emotional_modifiers", {}
                        ),
                        white_check=skill_check_data.get("white_check", False),
                        hidden=skill_check_data.get("hidden", False),
                    )

                # Convert inner voice reactions
                inner_voice_reactions = []
                for reaction in opt.get("inner_voice_reactions", []) or []:
                    inner_voice_reactions.append(
                        InnerVoiceComment(
                            voice_type=reaction.get("voice_type", ""),
                            text=reaction.get("text", ""),
                            skill_requirement=reaction.get("skill_requirement"),
                            trigger_condition=(
                                DialogueConditions()
                                if reaction.get("trigger_condition")
                                else None
                            ),
                        )
                    )

                # Convert consequences to DialogueEffect
                consequences = []
                for cons in opt.get("consequences", []) or []:
                    if isinstance(cons, dict):
                        consequences.append(
                            DialogueEffect(
                                effect_type=cons.get("event_type", ""),
                                data=cons.get("data"),
                            )
                        )

                # Create dialogue option
                option = DialogueOption(
                    id=opt.get("id", ""),
                    text=opt.get("text", ""),
                    next_node=opt.get("next_node", ""),
                    skill_check=skill_check,
                    emotional_impact=opt.get("emotional_impact", {}),
                    conditions=opt.get("conditions", {}),
                    consequences=consequences,
                    inner_voice_reactions=inner_voice_reactions,
                    success_node=opt.get("success_node", ""),
                    failure_node=opt.get("failure_node", ""),
                )
            else:
                # If it's already a DialogueOption object
                option = opt

            options.append(option)

        # Create internal node with full conversion
        internal_node = DialogueNode(
            id=node_id,
            text=getattr(config_node, "text", ""),
            speaker=getattr(config_node, "speaker", ""),
            emotional_state=getattr(config_node, "emotional_state", "Neutral"),
            inner_voice_comments=inner_voice_comments,
            options=options,
            conditions=DialogueConditions(),
            effects=[],  # Add effects conversion if needed
        )

        internal_trees[node_id] = internal_node

    return internal_trees


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting game. Goodbye!")
        sys.exit(0)
