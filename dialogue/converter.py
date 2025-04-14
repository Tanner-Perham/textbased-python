"""Module for converting dialogue trees from config format to internal format."""

from dialogue.node import (
    DialogueConditions,
    DialogueEffect,
    DialogueNode,
    DialogueOption,
    EnhancedSkillCheck,
    InnerVoiceComment,
)

def convert_dialogue_trees(config):
    """Convert config dialogue trees to internal format."""
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