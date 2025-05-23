"""
Dialogue manager for handling NPC conversations.
"""

import random
import logging
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
from game.game_state import GameState, QuestStatus
from quest.quest import Quest

logger = logging.getLogger(__name__)

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
        self.game_engine = None

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
        """
        Determine the appropriate dialogue entry point based on game state.
        
        This checks conditions such as:
        - Whether specific quests are in progress or completed
        - Whether the player has certain items
        - Whether specific clues have been discovered
        - The current relationship value with the NPC
        - Time of day or other game state flags
        
        Returns the node ID to start the dialogue from.
        """
        # Get all dialogue nodes for this NPC
        npc_nodes = {
            key: node for key, node in self.dialogue_tree.items() 
            if node.speaker == npc_id and key.startswith(f"{npc_id}_")
        }
        
        # Filter for entry point nodes (those with conditions)
        entry_nodes = []
        
        for node_id, node in npc_nodes.items():
            # Check if this is a potential entry node (has conditions and is not part of an ongoing conversation)
            if hasattr(node, 'conditions') and node.conditions:
                entry_nodes.append((node_id, node))
        
        # Sort entry nodes by specificity (more conditions = more specific)
        def count_conditions(node):
            conditions = node.conditions
            count = 0
            count += len(conditions.required_items)
            count += len(conditions.required_clues)
            count += len(conditions.required_quests)
            count += len(conditions.required_skills)
            count += len(conditions.required_thoughts)
            count += 1 if conditions.required_emotional_state else 0
            count += 1 if conditions.time_of_day else 0
            count += 1 if conditions.quest_stage_active else 0
            count += 1 if conditions.quest_objective_completed else 0
            count += 1 if conditions.quest_branch_taken else 0
            return count
        
        # Sort nodes by condition count (highest first)
        entry_nodes.sort(key=lambda x: count_conditions(x[1]), reverse=True)
        
        # Check each entry node in order of specificity
        for node_id, node in entry_nodes:
            if self._check_dialogue_conditions(node.conditions, game_state):
                return node_id
        
        # If no conditional entry points match or none exist, fall back to default
        default_node_id = f"{npc_id}_default"
        
        # If there's no default node, use the first available node for this NPC
        if default_node_id not in self.dialogue_tree and npc_nodes:
            return next(iter(npc_nodes.keys()))
            
        return default_node_id
        
    def _check_dialogue_conditions(self, conditions: DialogueConditions, game_state: GameState) -> bool:
        """Check if dialogue conditions are met based on game state."""
        # Check required items
        if conditions.required_items:
            has_items = all(
                any(item.id == item_id for item in game_state.inventory_manager.items)
                for item_id in conditions.required_items
            )
            if not has_items:
                return False

        # Check required clues
        if conditions.required_clues:
            has_clues = all(
                any(clue.id == clue_id for clue in game_state.discovered_clues)
                for clue_id in conditions.required_clues
            )
            if not has_clues:
                return False

        # Check required quests
        if conditions.required_quests:
            quest_status_ok = all(
                game_state.quest_log.get(quest_id) == status
                for quest_id, status in conditions.required_quests.items()
            )
            if not quest_status_ok:
                return False
                
        # Check required skills
        if conditions.required_skills:
            skills_ok = all(
                getattr(game_state.player.skills, skill_name, 0) >= value
                for skill_name, value in conditions.required_skills.items()
            )
            if not skills_ok:
                return False
                
        # Check quest stage active
        if conditions.quest_stage_active:
            quest_id, stage_id = conditions.quest_stage_active
            quest = game_state.get_quest(quest_id)
            if not quest or not game_state.is_quest_stage_active(quest_id, stage_id):
                return False
                
        # Check quest objective completed
        if conditions.quest_objective_completed:
            quest_id, objective_id = conditions.quest_objective_completed
            if not game_state.is_objective_completed(quest_id, objective_id):
                return False
                
        # Check quest branch taken
        if conditions.quest_branch_taken:
            quest_id, branch_id = conditions.quest_branch_taken
            if quest_id not in game_state.taken_quest_branches or branch_id not in game_state.taken_quest_branches.get(quest_id, set()):
                return False
                
        # Check time of day
        if conditions.time_of_day and game_state.time_of_day not in conditions.time_of_day:
            return False
            
        # Check emotional state if required
        if conditions.required_emotional_state:
            # For now, we'll use the emotional state in the relationship data
            # This could be expanded to a more complex emotion system
            if npc_id := conditions.required_emotional_state.split(':')[0]:
                emotional_state = conditions.required_emotional_state.split(':')[1]
                current_state = game_state.get_npc_emotional_state(npc_id)
                if current_state != emotional_state:
                    return False
        
        # Check NPC relationship value if specified
        if hasattr(conditions, 'npc_relationship_value') and conditions.npc_relationship_value:
            relationship_data = conditions.npc_relationship_value
            if isinstance(relationship_data, dict):
                npc_id = relationship_data.get('npc_id')
                min_value = relationship_data.get('min_value')
                if npc_id and min_value is not None:
                    current_value = game_state.get_relationship_value(npc_id)
                    if current_value < min_value:
                        return False
        
        # All conditions passed
        return True

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
        if comment.skill_requirement:
            skill_name = comment.voice_type.lower()
            player_skill = 0

            if hasattr(game_state.player.skills, skill_name):
                player_skill = getattr(game_state.player.skills, skill_name)

            return player_skill >= comment.skill_requirement

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

        if not conditions:
            return True

        if "required_items" in conditions:
            has_items = all(
                any(item.id == item_id for item in game_state.inventory_manager.items)
                for item_id in conditions["required_items"]
            )
            if not has_items:
                return False

        if "required_clues" in conditions:
            has_clues = all(
                any(clue.id == clue_id for clue in game_state.discovered_clues)
                for clue_id in conditions["required_clues"]
            )
            if not has_clues:
                return False

        if "required_quests" in conditions:
            quest_status_ok = all(
                game_state.quest_log.get(quest_id) == status
                for quest_id, status in conditions["required_quests"].items()
            )
            if not quest_status_ok:
                return False

        return True

    def select_option(
        self, option_id: str, game_state: GameState
    ) -> List[DialogueResponse]:
        """Process option selection and return responses."""
        responses = []
        option = self._find_option(option_id)

        if not option:
            return responses

        default_next_node = option.next_node
        success_node = option.success_node
        failure_node = option.failure_node
        critical_success_node = option.critical_success_node
        critical_failure_node = option.critical_failure_node
        skill_check_success = False
        critical_result = None

        if option.skill_check:
            skill_check_response = self._process_skill_check(
                option.skill_check, game_state
            )
            responses.append(skill_check_response)

            if isinstance(skill_check_response, DialogueResponse.SkillCheck):
                skill_check_success = skill_check_response.success
                critical_result = skill_check_response.critical_result
        print(f"DialogueManager: Option {option}")
        print(f"DialogueManager: Skill check success {skill_check_success}, Critical result {critical_result}")
        self._apply_emotional_changes(option.emotional_impact)

        print(f"DialogueManager: Processing effects {option.consequences}")
        self._process_effects(option.consequences, game_state)

        for reaction in option.inner_voice_reactions:
            if self._should_trigger_inner_voice(reaction, game_state):
                responses.append(
                    DialogueResponse.InnerVoice(
                        voice_type=reaction.voice_type, text=reaction.text
                    )
                )

        self.dialogue_history.append(option_id)

        next_node = ""
        if option.skill_check:
            if critical_result == "success" and critical_success_node:
                next_node = critical_success_node
            elif critical_result == "failure" and critical_failure_node:
                next_node = critical_failure_node
            elif skill_check_success and success_node:
                next_node = success_node
            elif not skill_check_success and failure_node:
                next_node = failure_node
            else:
                next_node = default_next_node
        else:
            next_node = default_next_node

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
        difficulty = check.base_difficulty

        current_emotion = self.emotional_states.get(self.current_node)
        if current_emotion and current_emotion in check.emotional_modifiers:
            difficulty += check.emotional_modifiers[current_emotion]

        player_skill = 0
        if check.primary_skill in game_state.player.skills:
            player_skill = game_state.player.skills[check.primary_skill]

        for skill_name, factor in check.supporting_skills:
            if skill_name in game_state.player.skills:
                supporting_value = int(
                    game_state.player.skills[skill_name] * factor
                )
                player_skill += supporting_value

        # Roll 2d6 instead of 1d20
        dice_values = [random.randint(1, 6), random.randint(1, 6)]
        roll = sum(dice_values)
        
        # Check for critical success or failure
        critical_result = None
        if dice_values[0] == 6 and dice_values[1] == 6:
            critical_result = "success"
            success = True  # Critical success always succeeds
        elif dice_values[0] == 1 and dice_values[1] == 1:
            critical_result = "failure"
            success = False  # Critical failure always fails
        else:
            success = (roll + player_skill) >= difficulty

        return DialogueResponse.SkillCheck(
            success=success,
            skill=check.primary_skill,
            player_skill=player_skill,
            roll=roll,
            difficulty=difficulty,
            dice_values=dice_values,
            critical_result=critical_result
        )

    def _apply_emotional_changes(self, changes: Dict[str, int]) -> None:
        """Apply emotional changes from dialogue."""
        if not changes:
            return

        for emotion, value in changes.items():
            self.emotional_states[self.current_node] = emotion

    def _process_effects(self, effects: List[DialogueEffect], game_state: GameState) -> None:
        """Process a list of dialogue effects."""
        for effect in effects:
            effect_type = effect.effect_type
            data = effect.data

            if effect_type == "quest":
                self._handle_quest_effect(data, game_state)
            elif effect_type == "relationship":
                self._handle_relationship_effect(data, game_state)
            elif effect_type == "item":
                self._handle_item_effect(data, game_state)
            elif effect_type == "skill":
                self._handle_skill_effect(data, game_state)
            elif effect_type == "stat":
                self._handle_stat_effect(data, game_state)
            elif effect_type == "flag":
                self._handle_flag_effect(data, game_state)
            elif effect_type == "notification":
                self._handle_notification_effect(data, game_state)
            elif effect_type == "scene":
                self._handle_scene_effect(data, game_state)
            elif effect_type == "combat":
                self._handle_combat_effect(data, game_state)
            elif effect_type == "custom":
                self._handle_custom_effect(data, game_state)
            else:
                logger.warning(f"Unknown effect type: {effect_type}")

    def _handle_quest_effect(self, data: Any, game_state: GameState) -> None:
        """Handle quest-related effects."""
        print(f"DialogueManager: Handling quest effect {data}")
        if data.get("action") == "add":
            print(f"DialogueManager: Adding quest {data['quest_id']}")
            # Get the quest from the game config
            quest_config = self.game_engine.config.get_quest(data["quest_id"])
            if quest_config:
                # Convert config quest to Quest object
                quest = Quest(
                    id=quest_config.id,
                    title=quest_config.title,
                    description=quest_config.description,
                    short_description=quest_config.short_description,
                    objectives=[],
                    status=QuestStatus.NotStarted
                )
                # Add the quest to the game state
                game_state.add_quest(quest)
        elif data.get("action") == "start":
            print(f"DialogueManager: Starting quest {data['quest_id']}")
            # First ensure the quest exists
            quest = game_state.get_quest(data["quest_id"])
            if not quest:
                # Try to get the quest from the game config
                quest_config = self.game_engine.config.get_quest(data["quest_id"])
                if quest_config:
                    # Convert config quest to Quest object
                    quest = Quest(
                        id=quest_config.id,
                        title=quest_config.title,
                        description=quest_config.description,
                        short_description=quest_config.short_description,
                        objectives=[],
                        status=QuestStatus.NotStarted
                    )
                    # Add the quest to the game state
                    self.game_engine.quest_manager.game_state.add_quest(quest)
            # Now update the quest status
            self.game_engine.quest_manager.game_state.update_quest_status(data["quest_id"], QuestStatus.InProgress)
        elif data.get("action") == "advance":
            self.game_engine.quest_manager.game_state.set_active_stage(data["quest_id"], data["stage_id"])
        elif data.get("action") == "complete_objective":
            self.game_engine.quest_manager.game_state.add_completed_objective(data["quest_id"], data["objective_id"])
        elif data.get("action") == "fail":
            self.game_engine.quest_manager.game_state.update_quest_status(data["quest_id"], QuestStatus.Failed)
        elif data.get("action") == "unlock_branch":
            if data["quest_id"] not in self.game_engine.quest_manager.game_state.taken_quest_branches:
                self.game_engine.quest_manager.game_state.taken_quest_branches[data["quest_id"]] = set()
            game_state.taken_quest_branches[data["quest_id"]].add(data["branch_id"])
            
        # Update quest state after any quest-related changes
        game_state.check_all_quest_updates()

    def _handle_relationship_effect(self, data: Any, game_state: GameState) -> None:
        """Handle relationship-related effects."""
        npc_id = data.get("npc_id")
        value = data.get("value")
        if npc_id and value is not None:
            game_state.modify_relationship(npc_id, value)

    def _handle_item_effect(self, data: Any, game_state: GameState) -> None:
        """Handle item-related effects."""
        if data.get("action") == "add":
            game_state.add_item(data["item_id"])
        elif data.get("action") == "remove":
            game_state.remove_item(data["item_id"])

    def _handle_skill_effect(self, data: Any, game_state: GameState) -> None:
        """Handle skill-related effects."""
        skill_name = data.get("skill_name")
        amount = data.get("amount")
        if skill_name and amount is not None:
            game_state.modify_skill(skill_name, amount)

    def _handle_stat_effect(self, data: Any, game_state: GameState) -> None:
        """Handle stat-related effects."""
        stat_name = data.get("stat_name")
        amount = data.get("amount")
        if stat_name and amount is not None:
            game_state.modify_stat(stat_name, amount)

    def _handle_flag_effect(self, data: Any, game_state: GameState) -> None:
        """Handle flag-related effects."""
        flag_name = data.get("flag_name")
        value = data.get("value")
        if flag_name and value is not None:
            game_state.set_flag(flag_name, value)

    def _handle_notification_effect(self, data: Any, game_state: GameState) -> None:
        """Handle notification-related effects."""
        if self.game_engine and hasattr(self.game_engine, 'notification_manager'):
            self.game_engine.notification_manager.add_notification(
                data.get("text", ""),
                data.get("type", "info")
            )

    def _handle_scene_effect(self, data: Any, game_state: GameState) -> None:
        """Handle scene-related effects."""
        if data.get("action") == "change_location":
            game_state.change_location(data["location_id"])
        elif data.get("action") == "change_scene":
            game_state.change_scene(data["scene_id"])

    def _handle_combat_effect(self, data: Any, game_state: GameState) -> None:
        """Handle combat-related effects."""
        if self.game_engine and hasattr(self.game_engine, 'combat_manager'):
            if data.get("action") == "start":
                self.game_engine.combat_manager.start_combat(data["enemy_id"])
            elif data.get("action") == "end":
                self.game_engine.combat_manager.end_combat()

    def _handle_custom_effect(self, data: Any, game_state: GameState) -> None:
        """Handle custom-related effects."""
        if self.game_engine and hasattr(self.game_engine, 'handle_custom_effect'):
            self.game_engine.handle_custom_effect(data)


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
