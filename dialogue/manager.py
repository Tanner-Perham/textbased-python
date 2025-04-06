"""
Dialogue manager for handling NPC conversations.
"""

import random
from typing import Any, Dict, List, Optional, Set

from dialogue.node import (
    DialogueConditions,
    DialogueEffect,
    DialogueNode,
    DialogueOption,
    EnhancedSkillCheck,
    InnerVoiceComment,
)
from dialogue.response import DialogueResponse
from game.game_state import GameState


class DialogueManager:
    """Manages dialogue trees and interactions."""

    def __init__(self):
        """Initialize the dialogue manager."""
        self.current_node = ""
        self.dialogue_history = []
        self.active_nodes = set()
        self.locked_nodes = set()
        self.emotional_states = {}
        self.relationship_values = {}
        self.dialogue_tree = {}

    def set_dialogue_tree(self, dialogue_tree: Dict[str, DialogueNode]) -> None:
        """Set the dialogue tree."""
        self.dialogue_tree = dialogue_tree

    def debug_state(self) -> str:
        """Return debug information about the manager's state."""
        return (
            f"Current node: {self.current_node}, "
            f"Available nodes: {len(self.dialogue_tree)}, "
            f"Active nodes: {len(self.active_nodes)}, "
            f"Locked nodes: {len(self.locked_nodes)}"
        )

    def start_dialogue(
        self, npc_id: str, game_state: GameState
    ) -> List[DialogueResponse]:
        """Start a dialogue with an NPC."""
        responses = []

        # Filter dialogue tree for nodes belonging to this NPC
        npc_dialogue_tree = {
            key: value for key, value in self.dialogue_tree.items() 
            if value.speaker == npc_id
        }

        if not npc_dialogue_tree:
            responses.append(
                DialogueResponse.Speech(
                    speaker="System",
                    text=f"No dialogue found for NPC: {npc_id}",
                    emotion="Neutral",
                )
            )
            return responses

        # Determine entry point based on NPC ID
        entry_node = self._determine_entry_point(npc_id, game_state)

        # Check if entry node exists
        if entry_node in npc_dialogue_tree:
            self.current_node = entry_node
        else:
            # Use first available node for this NPC
            self.current_node = next(iter(npc_dialogue_tree))

        # Process current node
        responses.extend(self.process_node(self.current_node, game_state))

        return responses

    def _determine_entry_point(self, npc_id: str, game_state: GameState) -> str:
        """Determine the appropriate dialogue entry point."""
        # This could be expanded based on relationship, time of day, quests, etc.
        return f"{npc_id}_default"

    def process_node(
        self, node_id: str, game_state: GameState
    ) -> List[DialogueResponse]:
        """Process a dialogue node and return responses."""
        responses = []

        if node := self.dialogue_tree.get(node_id):
            # Add main dialogue text
            responses.append(
                DialogueResponse.Speech(
                    speaker=node.speaker, text=node.text, emotion=node.emotional_state
                )
            )

            # Process inner voice comments
            for comment in node.inner_voice_comments:
                if self._should_trigger_inner_voice(comment, game_state):
                    responses.append(
                        DialogueResponse.InnerVoice(
                            voice_type=comment.voice_type, text=comment.text
                        )
                    )

            # Add available dialogue options
            available_options = self.get_available_options(node, game_state)
            if available_options:
                responses.append(DialogueResponse.Options(options=available_options))

        return responses

    def _should_trigger_inner_voice(
        self, comment: InnerVoiceComment, game_state: GameState
    ) -> bool:
        """Determine if an inner voice comment should trigger."""
        # Check skill requirement
        if comment.skill_requirement:
            skill_name = comment.voice_type.lower()
            player_skill = 0

            # Get corresponding player skill value
            if hasattr(game_state.player.skills, skill_name):
                player_skill = getattr(game_state.player.skills, skill_name)

            # Return true if player skill meets requirement
            return player_skill >= comment.skill_requirement

        # Default to true if no requirements
        return True

    def get_available_options(
        self, node: DialogueNode, game_state: GameState
    ) -> List[DialogueOption]:
        """Get available dialogue options based on conditions."""
        return [
            option
            for option in node.options
            if self._check_option_conditions(option, game_state)
        ]

    def _check_option_conditions(
        self, option: DialogueOption, game_state: GameState
    ) -> bool:
        """Check if conditions for a dialogue option are met."""
        conditions = option.conditions

        # If no conditions, always available
        if not conditions:
            return True

        # Check required items
        if "required_items" in conditions:
            has_items = all(
                any(item.id == item_id for item in game_state.inventory)
                for item_id in conditions["required_items"]
            )
            if not has_items:
                return False

        # Check required clues
        if "required_clues" in conditions:
            has_clues = all(
                any(clue.id == clue_id for clue in game_state.discovered_clues)
                for clue_id in conditions["required_clues"]
            )
            if not has_clues:
                return False

        # Check quest status
        if "required_quests" in conditions:
            quest_status_ok = all(
                game_state.quest_log.get(quest_id) == status
                for quest_id, status in conditions["required_quests"].items()
            )
            if not quest_status_ok:
                return False

        # More conditions could be added as needed

        return True

    def select_option(
        self, option_id: str, game_state: GameState
    ) -> List[DialogueResponse]:
        """Process option selection and return responses."""
        responses = []
        option = self._find_option(option_id)

        if not option:
            return responses

        # Save data before processing
        default_next_node = option.next_node
        success_node = option.success_node
        failure_node = option.failure_node
        skill_check_success = False

        # Process skill check if present
        if option.skill_check:
            skill_check_response = self._process_skill_check(
                option.skill_check, game_state
            )
            responses.append(skill_check_response)

            # Store result for node selection
            if isinstance(skill_check_response, DialogueResponse.SkillCheck):
                skill_check_success = skill_check_response.success

        # Apply emotional changes
        self._apply_emotional_changes(option.emotional_impact)

        # Process effects
        self._process_effects(option.consequences, game_state)

        # Process inner voice reactions
        for reaction in option.inner_voice_reactions:
            if self._should_trigger_inner_voice(reaction, game_state):
                responses.append(
                    DialogueResponse.InnerVoice(
                        voice_type=reaction.voice_type, text=reaction.text
                    )
                )

        # Update dialogue history
        self.dialogue_history.append(option_id)

        # Determine next node
        next_node = ""
        if option.skill_check:
            if skill_check_success and success_node:
                next_node = success_node
            elif not skill_check_success and failure_node:
                next_node = failure_node
            else:
                next_node = default_next_node
        else:
            next_node = default_next_node

        # Process next node if specified
        if next_node:
            self.current_node = next_node
            responses.extend(self.process_node(next_node, game_state))

        return responses

    def _find_option(self, option_id: str) -> Optional[DialogueOption]:
        """Find a dialogue option by ID."""
        node = self.dialogue_tree.get(self.current_node)
        if node:
            for option in node.options:
                if option.id == option_id:
                    return option
        return None

    def _process_skill_check(
        self, check: EnhancedSkillCheck, game_state: GameState
    ) -> DialogueResponse.SkillCheck:
        """Process a skill check and return the result."""
        # Get base difficulty
        difficulty = check.base_difficulty

        # Apply emotional modifiers
        current_emotion = self.emotional_states.get(self.current_node)
        if current_emotion and current_emotion in check.emotional_modifiers:
            difficulty += check.emotional_modifiers[current_emotion]

        # Get player's skill value
        player_skill = 0
        if hasattr(game_state.player.skills, check.primary_skill):
            player_skill = getattr(game_state.player.skills, check.primary_skill)

        # Add supporting skills
        for skill_name, factor in check.supporting_skills:
            if hasattr(game_state.player.skills, skill_name):
                supporting_value = int(
                    getattr(game_state.player.skills, skill_name) * factor
                )
                player_skill += supporting_value

        # Roll for skill check
        roll = random.randint(1, 20)

        # Determine success
        success = (roll + player_skill) >= difficulty

        return DialogueResponse.SkillCheck(
            success=success, skill=check.primary_skill, roll=roll, difficulty=difficulty
        )

    def _apply_emotional_changes(self, changes: Dict[str, int]) -> None:
        """Apply emotional changes from dialogue."""
        # This would update NPC emotional states
        if not changes:
            return

        # Implementation depends on how emotions are tracked
        for emotion, value in changes.items():
            self.emotional_states[self.current_node] = emotion

    def _process_effects(
        self, effects: List[Dict[str, Any]], game_state: GameState
    ) -> None:
        """Process dialogue effects."""
        for effect in effects:
            effect_type = effect.get("effect_type")
            data = effect.get("data")

            if effect_type == "ModifyRelationship":
                npc_id, value = data
                game_state.modify_relationship(npc_id, value)

            elif effect_type == "AddItem":
                game_state.add_item(data)

            elif effect_type == "RemoveItem":
                game_state.remove_item(data)

            elif effect_type == "StartQuest":
                game_state.start_quest(data)

            elif effect_type == "AdvanceQuest":
                quest_id, stage_id = data
                game_state.advance_quest(quest_id, stage_id)

            # Additional effect types can be handled here

            elif effect_type == "CompleteQuestObjective":
                quest_id, objective_id = data
                game_state.complete_objective(quest_id, objective_id)

            elif effect_type == "FailQuest":
                game_state.fail_quest(data)

            elif effect_type == "UnlockQuestBranch":
                quest_id, branch_id = data
                game_state.unlock_quest_branch(quest_id, branch_id)

            elif effect_type == "ModifySkill":
                skill_name, amount = data
                game_state.modify_skill(skill_name, amount)

            elif effect_type == "ChangeLocation":
                game_state.change_location(data)


def create_dialogue_node(
    id: str, text: str, speaker: str, emotion: str, options: List[DialogueOption] = None
) -> DialogueNode:
    """Create a simple dialogue node."""
    if options is None:
        options = []

    return DialogueNode(
        id=id,
        text=text,
        speaker=speaker,
        emotional_state=emotion,
        inner_voice_comments=[],
        options=options,
        conditions=DialogueConditions(),
        effects=[],
    )
