"""
Dialogue UI module for handling NPC conversations.
"""

from typing import List, Optional, Tuple
import asyncio
import time

from textual import events
from textual.containers import Container, ScrollableContainer
from textual.reactive import reactive
from textual.widgets import Static, Input

from dialogue.response import DialogueResponse
from ui.dialogue_components import DialogueOption, InnerVoice, SkillCheckResult, SpeechBubble


class DialogueMode:
    """Interactive dialogue mode for NPC conversations within the main game UI."""

    def __init__(self, game_ui):
        """Initialize dialogue mode with reference to the main game UI."""
        self.game_ui = game_ui
        self.npc_name = ""
        self.selected_index = 0
        self.options = []
        self.dialogue_history = []
        self.is_active = False
        self.current_dialogue_buffer = []  # Buffer for current dialogue state
        self.stored_game_history = []  # Buffer for storing game history during dialogue
        
        # Typewriter effect properties
        self.typewriter_speed = 0.02  # Seconds per character
        self.is_typing = False
        self.reveal_all_text = False
        self.current_typing_task = None
        self.full_dialogue_buffer = []  # Complete dialogue buffer before typewriter effect
        self.latest_responses = []  # Track the most recent responses for typewriter effect
        self.previously_shown_lines = 0  # Count of lines already shown

    def start_dialogue(self, npc_name: str, responses: List[DialogueResponse]) -> None:
        """Start a dialogue with an NPC."""
        # Store the current game history
        self.stored_game_history = self.game_ui.game_output.lines.copy()
        
        self.npc_name = npc_name
        self.is_active = True
        self.selected_index = 0
        self.dialogue_history = []
        self.current_dialogue_buffer = []  # Clear buffer
        self.full_dialogue_buffer = []  # Clear full dialogue buffer
        self.is_typing = False
        self.reveal_all_text = False
        self.latest_responses = []
        self.previously_shown_lines = 0
        
        # Create and run the async task to process responses
        asyncio.create_task(self._async_process_dialogue(responses))

    async def _async_process_dialogue(self, responses: List[DialogueResponse]) -> None:
        """Process dialogue responses asynchronously."""
        # Process the responses (will wait for any skill checks to complete)
        await self.process_responses(responses)
        # Update the display after all responses are processed
        self.update_display()
        # Set focus to the input box
        self.game_ui.game_input.focus()

    def end_dialogue(self) -> None:
        """End the current dialogue."""
        if self.is_active:
            # Cancel any active typing task
            self.cancel_typing_effect()
            
            # Add conversation end marker to buffer
            self.current_dialogue_buffer.append("\n=== Conversation ended ===\n")
            
            # Clear the game output
            self.game_ui.game_output.clear()
            
            # Restore the game history and append the dialogue
            self.game_ui.game_output.write("\n".join(self.stored_game_history))
            self.game_ui.game_output.write("\n")
            self.game_ui.game_output.write("\n".join(self.current_dialogue_buffer))
            self.game_ui.game_output.write("\n\n")
            
            # Reset dialogue state
            self.is_active = False
            self.npc_name = ""
            self.selected_index = 0
            self.options = []
            self.dialogue_history = []
            self.current_dialogue_buffer = []
            self.full_dialogue_buffer = []
            self.stored_game_history = []
            self.is_typing = False
            self.reveal_all_text = False
            self.game_ui.game_input.placeholder = "Enter your command..."
            # Keep focus on the input box
            self.game_ui.game_input.focus()

    async def process_responses(self, responses: List[DialogueResponse]) -> None:
        """Process a list of dialogue responses."""
        new_options = []
        new_responses = []  # Track new responses for typewriter effect

        for response in responses:
            if isinstance(response, DialogueResponse.Options):
                new_options = response.options
            else:
                await self.add_to_history(response)
                new_responses.append(response)  # Track this as a new response

        # Update options if new ones were provided
        if new_options:
            self.options = new_options
            self.selected_index = 0
        else:
            # No options means conversation should end
            self.end_dialogue()
            
        # Store the latest response for typewriter effect if any
        self.latest_responses = new_responses
        
    async def add_to_history(self, response: DialogueResponse) -> None:
        """Add a dialogue response to the history."""
        if isinstance(response, DialogueResponse.Speech):
            # Use NPC name if speaker matches an NPC ID, otherwise use speaker directly
            speaker_name = self.game_ui.game_engine.config.npcs.get(response.speaker, None)
            display_name = speaker_name.name if speaker_name else response.speaker
            self.dialogue_history.append(f"{display_name}: {response.text}")
        elif isinstance(response, DialogueResponse.InnerVoice):
            # Format inner voice without brackets to avoid markup issues
            self.dialogue_history.append(f"Inner Voice - {response.voice_type}: {response.text}")
        elif isinstance(response, DialogueResponse.SkillCheck):
            # Add a placeholder to history
            result_text = f"Skill Check - {response.skill} - "
            result_text += "Rolling..."
            self.dialogue_history.append(result_text)
            
            # Get the index of the skill check in the history
            history_index = len(self.dialogue_history) - 1
            
            # Create a SkillCheckResult to display and animate
            skill_check = SkillCheckResult(
                skill=response.skill,
                success=response.success,
                roll=response.roll,
                difficulty=response.difficulty,
                dice_values=response.dice_values,
                critical_result=response.critical_result,
                game_output=self.game_ui,
                history_index=history_index
            )
            
            # Animate the dice roll and wait for it to complete
            animation_future = skill_check.animate_dice_roll()
            await animation_future
            
            # Animation is now complete, dialogue can continue

    def select_previous(self) -> None:
        """Select the previous dialogue option."""
        if not self.options:
            return
        self.selected_index = (self.selected_index - 1) % len(self.options)
        self.update_display()
        # Keep focus on the input box
        self.game_ui.game_input.focus()

    def select_next(self) -> None:
        """Select the next dialogue option."""
        if not self.options:
            return
        self.selected_index = (self.selected_index + 1) % len(self.options)
        self.update_display()
        # Keep focus on the input box
        self.game_ui.game_input.focus()

    def select_current(self) -> str:
        """Select the current dialogue option and return its ID."""
        if not self.options:
            return ""
        selected_option = self.options[self.selected_index]
        
        # Create a player speech response
        player_speech = DialogueResponse.Speech(
            speaker="You",
            text=selected_option.text,
            emotion="Neutral"
        )
        
        # Add the selected option to history using create_task since this is called from sync code
        asyncio.create_task(self.add_to_history(player_speech))
        
        return selected_option.id
    
    def reveal_all(self) -> None:
        """Immediately reveal all text, stopping any typewriter effect in progress."""
        if not self.is_active or not self.is_typing:
            return
            
        self.reveal_all_text = True
        # Cancel the current typing task
        self.cancel_typing_effect()
        
        # Show all text at once
        self.game_ui.game_output.clear()
        self.current_dialogue_buffer = []
        for line in self.full_dialogue_buffer:
            self.game_ui.game_output.write(line)
            self.current_dialogue_buffer.append(line)
        
        self.is_typing = False
        
        # Keep focus on the input box
        self.game_ui.game_input.focus()
    
    def cancel_typing_effect(self) -> None:
        """Cancel any ongoing typing effect."""
        if self.current_typing_task and not self.current_typing_task.done():
            self.current_typing_task.cancel()
            self.current_typing_task = None
    
    async def typewriter_effect(self, lines: List[str], start_pos: int = 0) -> None:
        """Apply a typewriter effect to gradually reveal dialogue text.
        
        Args:
            lines: List of new lines to display with typewriter effect
            start_pos: Position in the full buffer where these lines start
        """
        self.is_typing = True
        self.reveal_all_text = False
        
        try:
            for line_index, line in enumerate(lines):
                # Skip empty lines or add them immediately
                if not line.strip():
                    self.game_ui.game_output.write(line)
                    self.current_dialogue_buffer.append(line)
                    continue
                
                # For section headers like "=== Conversation with", display immediately
                if "=== Conversation with" in line:
                    self.game_ui.game_output.write(line)
                    self.current_dialogue_buffer.append(line)
                    continue
                
                # For skill check lines, handle specially to allow dice animation
                if "Skill Check -" in line:
                    # Extract the skill name from the line
                    parts = line.split(" - ")
                    if len(parts) >= 2:
                        skill_name = parts[1]
                        # Find the matching skill check in latest_responses
                        skill_check_response = next(
                            (r for r in self.latest_responses 
                             if isinstance(r, DialogueResponse.SkillCheck) and r.skill == skill_name),
                            None
                        )
                        
                        if skill_check_response:
                            # Write the placeholder text immediately
                            placeholder_text = f"Skill Check - {skill_name} - Rolling..."
                            self.game_ui.game_output.write(placeholder_text)
                            self.current_dialogue_buffer.append(placeholder_text)
                            
                            # Get the history index
                            history_index = line_index + start_pos
                            
                            # Create and animate a SkillCheckResult widget
                            skill_check = SkillCheckResult(
                                skill=skill_check_response.skill,
                                success=skill_check_response.success,
                                roll=skill_check_response.roll,
                                difficulty=skill_check_response.difficulty,
                                dice_values=skill_check_response.dice_values,
                                critical_result=skill_check_response.critical_result,
                                game_output=self.game_ui,
                                history_index=history_index
                            )
                            
                            # Animate the dice roll and wait for the animation to complete
                            animation_future = skill_check.animate_dice_roll()
                            await animation_future
                            
                            # Now continue the loop - we can use continue here because we're in a loop
                            continue
                    
                    # Fall back to immediate display if no matching skill check found
                    self.game_ui.game_output.write(line)
                    self.current_dialogue_buffer.append(line)
                    continue
                
                # For section headers like "Options:", display immediately
                if line == "\nOptions:":
                    self.game_ui.game_output.write(line)
                    self.current_dialogue_buffer.append(line)
                    continue
                
                # For dialogue options (lines starting with ">" or "  "), display immediately
                if line.startswith(">") or (line.startswith("  ") and "\nOptions:" in self.current_dialogue_buffer):
                    self.game_ui.game_output.write(line)
                    self.current_dialogue_buffer.append(line)
                    continue
                
                # Apply typewriter effect to dialogue lines
                current_line = ""
                for char in line:
                    if self.reveal_all_text:
                        # If user requested to reveal all text, break out
                        break
                    
                    current_line += char
                    
                    # Create a temporary buffer with current state
                    temp_buffer = self.current_dialogue_buffer.copy()
                    
                    # Add the current in-progress line
                    if line_index + start_pos < len(temp_buffer):
                        temp_buffer[line_index + start_pos] = current_line
                    else:
                        temp_buffer.append(current_line)
                    
                    # Clear and redisplay with updated line
                    self.game_ui.game_output.clear()
                    for buffer_line in temp_buffer:
                        self.game_ui.game_output.write(buffer_line)
                    
                    # Adding a delay between characters for the typewriter effect
                    await asyncio.sleep(self.typewriter_speed)
                
                # If we broke out of the loop, we still need to ensure the full line is displayed
                if self.reveal_all_text:
                    break
                
                # Update the current buffer with the complete line
                if line_index + start_pos < len(self.current_dialogue_buffer):
                    self.current_dialogue_buffer[line_index + start_pos] = line
                else:
                    self.current_dialogue_buffer.append(line)
            
            # If reveal_all_text was triggered, show all text at once
            if self.reveal_all_text:
                self.game_ui.game_output.clear()
                self.current_dialogue_buffer = []
                for full_line in self.full_dialogue_buffer:
                    self.game_ui.game_output.write(full_line)
                    self.current_dialogue_buffer.append(full_line)
            
        except asyncio.CancelledError:
            # Task was cancelled, likely by reveal_all()
            pass
        finally:
            self.is_typing = False
            # Make sure the input has focus
            self.game_ui.game_input.focus()

    def update_display(self) -> None:
        """Update the game UI to show current dialogue state."""
        if not self.is_active:
            return

        # Cancel any ongoing typing effect
        self.cancel_typing_effect()

        # Update input placeholder to show current selection
        if self.options:
            selected_text = self.options[self.selected_index].text
            self.game_ui.game_input.placeholder = f"Selected: {selected_text} (↑/↓ to change, Enter to select, Space to skip)"
        else:
            self.game_ui.game_input.placeholder = "No options available (Space to skip text)"

        # Build the current dialogue state
        output = []
        
        # Add a header for the conversation
        output.append(f"\n=== Conversation with {self.npc_name} ===\n")
        
        # Add dialogue history with proper spacing
        for item in self.dialogue_history:
            # Add extra spacing between dialogue entries
            output.append("")
            # Split long lines into multiple lines
            wrapped_lines = []
            for line in item.split('\n'):
                # Wrap long lines at 80 characters
                while len(line) > 80:
                    # Find the last space before 80 characters
                    split_pos = line[:80].rfind(' ')
                    if split_pos == -1:
                        split_pos = 80
                    wrapped_lines.append(line[:split_pos])
                    line = line[split_pos:].lstrip()
                wrapped_lines.append(line)
            output.extend(wrapped_lines)
        
        # Add options if available
        if self.options:
            output.append("\nOptions:")
            for i, option in enumerate(self.options):
                prefix = "> " if i == self.selected_index else "  "
                # Wrap long option text
                wrapped_option = []
                line = option.text
                while len(line) > 80:
                    split_pos = line[:80].rfind(' ')
                    if split_pos == -1:
                        split_pos = 80
                    wrapped_option.append(f"{prefix}{line[:split_pos]}")
                    line = line[split_pos:].lstrip()
                    prefix = "  "  # Indent wrapped lines
                wrapped_option.append(f"{prefix}{line}")
                output.extend(wrapped_option)
        
        # Store the full buffer before typewriter effect
        self.full_dialogue_buffer = output.copy()
        
        # Clear the game output and the current buffer
        self.game_ui.game_output.clear()
        self.current_dialogue_buffer = []
        
        # Check if we have new responses to apply the typewriter effect to
        if self.latest_responses and any(isinstance(r, DialogueResponse.Speech) and r.speaker != "You" for r in self.latest_responses):
            # Display all previously shown content instantly
            prev_content = output[:self.previously_shown_lines] if self.previously_shown_lines < len(output) else output[:]
            for line in prev_content:
                self.game_ui.game_output.write(line)
                self.current_dialogue_buffer.append(line)
            
            # Only apply typewriter effect to new content
            new_content = output[self.previously_shown_lines:] if self.previously_shown_lines < len(output) else []
            if new_content:
                self.current_typing_task = asyncio.create_task(self.typewriter_effect(new_content, len(self.current_dialogue_buffer)))
        else:
            # No new NPC responses, just display everything immediately
            for line in output:
                self.game_ui.game_output.write(line)
                self.current_dialogue_buffer.append(line)
        
        # Update the count of shown lines for next time
        self.previously_shown_lines = len(output)
        
        # Clear latest responses after processing
        self.latest_responses = []

    def handle_key(self, event) -> bool:
        """Handle key events specific to dialogue mode.
        
        Returns True if the key was handled, False otherwise.
        """
        if not self.is_active:
            return False
            
        # Space to reveal all text or skip typing effect
        if event.key == " ":
            if self.is_typing:
                self.reveal_all()
                return True
                
        return False
