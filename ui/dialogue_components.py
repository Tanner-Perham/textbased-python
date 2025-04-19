"""
Custom components for the dialogue UI.
"""

from typing import ClassVar, Dict, Optional, List

from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Button, Static

# Emotional state colors
EMOTION_COLORS: Dict[str, str] = {
    "Neutral": "white",
    "Friendly": "green",
    "Nervous": "yellow",
    "Angry": "red",
    "Suspicious": "orange",
    "Desperate": "magenta",
}

# Inner voice colors
VOICE_COLORS: Dict[str, str] = {
    "Logic": "cyan",
    "Intuition": "purple",
    "Empathy": "pink",
    "Authority": "gold",
    "Electrochemistry": "red",
    "Encyclopedia": "teal",
    "Drama": "magenta",
    "Suggestion": "orange",
}


class SpeechBubble(Static):
    """A speech bubble for dialogue."""

    DEFAULT_CSS = """
    SpeechBubble {
        margin: 1 0;
        padding: 1;
        width: 100%;
        border-radius: 1;
    }
    
    .npc-bubble {
        border: tall $primary;
        background: $surface;
    }
    
    .player-bubble {
        border: tall $secondary;
        background: $surface-darken-1;
        color: $text;
    }
    
    .speaker-name {
        color: $text-muted;
        text-style: italic;
    }
    """

    def __init__(self, speaker: str, text: str, emotion: str = "Neutral", **kwargs):
        """Initialize the speech bubble."""
        super().__init__(**kwargs)
        self.speaker = speaker
        self.text = text
        self.emotion = emotion

        # Determine if this is player or NPC speech
        self.is_player = speaker == "PLAYER"

        # Set bubble classes
        self.add_class("player-bubble" if self.is_player else "npc-bubble")

        # Set emotion-specific color if applicable
        if emotion in EMOTION_COLORS and not self.is_player:
            self.styles.color = EMOTION_COLORS[emotion]

    def render(self) -> str:
        """Render the speech bubble content."""
        if self.is_player:
            return f"You: {self.text}"
        else:
            emotion_text = f" ({self.emotion})" if self.emotion != "Neutral" else ""
            return f"[b]{self.speaker}{emotion_text}:[/b]\n{self.text}"


class InnerVoice(Static):
    """An inner voice comment."""

    DEFAULT_CSS = """
    InnerVoice {
        margin: 1 2;
        padding: 0 1;
        border-left: heavy $accent;
        color: $text-muted;
        text-style: italic;
    }
    """

    def __init__(self, voice_type: str, text: str, **kwargs):
        """Initialize the inner voice comment."""
        super().__init__(**kwargs)
        self.voice_type = voice_type
        self.text = text

        # Set voice-specific color if applicable
        if voice_type in VOICE_COLORS:
            self.styles.border_left_color = VOICE_COLORS[voice_type]
            self.styles.color = VOICE_COLORS[voice_type]

    def render(self) -> str:
        """Render the inner voice content."""
        return f"[{self.voice_type}] {self.text}"


class SkillCheckResult(Static):
    """A skill check result display."""

    DEFAULT_CSS = """
    SkillCheckResult {
        margin: 1;
        padding: 1;
        border: round;
        width: auto;
    }
    
    .success {
        border: tall $success;
        color: $success;
    }
    
    .failure {
        border: tall $error;
        color: $error;
    }
    
    .critical-success {
        border: double $success;
        color: $success;
        background: $success 10%;
    }
    
    .critical-failure {
        border: double $error;
        color: $error;
        background: $error 10%;
    }
    
    .dice {
        margin-right: 1;
    }
    """

    def __init__(self, skill: str, success: bool, roll: int, difficulty: int, 
                 dice_values: List[int] = None, critical_result: str = None, **kwargs):
        """Initialize the skill check result."""
        super().__init__(**kwargs)
        self.skill = skill
        self.success = success
        self.roll = roll
        self.difficulty = difficulty
        self.dice_values = dice_values or []
        self.critical_result = critical_result
        
        # Set appropriate styling class
        if critical_result == "success":
            self.add_class("critical-success")
        elif critical_result == "failure":
            self.add_class("critical-failure")
        else:
            self.add_class("success" if success else "failure")
        
        # For animation we'd set up a timer and update the dice values
        # but for now we'll just display the final result
        self.animate_dice = False

    def render(self) -> str:
        """Render the skill check content."""
        # Create dice display
        dice_display = ""
        if self.dice_values:
            dice_faces = {
                1: "⚀",
                2: "⚁",
                3: "⚂",
                4: "⚃",
                5: "⚄",
                6: "⚅"
            }
            dice_str = " ".join([dice_faces.get(d, str(d)) for d in self.dice_values])
            dice_display = f"[bold white on black]{dice_str}[/] "
        
        # Determine result text
        if self.critical_result == "success":
            result = "CRITICAL SUCCESS"
        elif self.critical_result == "failure":
            result = "CRITICAL FAILURE"
        else:
            result = "SUCCESS" if self.success else "FAILURE"
            
        return f"[b]Skill Check:[/b] {self.skill} - {dice_display}{result} (Total: {self.roll}/{self.difficulty})"

    def animate_dice_roll(self) -> None:
        """Animate the dice roll over time before revealing the final result."""
        # This would be implemented in a real application using the Textual Timer
        # and updating the display with random dice values before showing the final result
        
        # Example pseudocode for dice animation:
        # 1. Start with random dice values
        # 2. Set a timer to update dice values every 100ms for ~2 seconds
        # 3. Finally reveal the actual dice values
        
        # For now, we'll just set a flag that we want to animate
        self.animate_dice = True
        
        # If this were fully implemented:
        # timer = self.set_timer(0.1, self._update_dice_animation, repeat=20)
        # Where _update_dice_animation would update dice_values with random values
        # and the last call would set the real dice values


class DialogueOption(Button):
    """A selectable dialogue option."""

    DEFAULT_CSS = """
    DialogueOption {
        width: 100%;
        height: auto;
        padding: 1;
        margin: 0 0 1 0;
        background: $surface;
        color: $text;
        border: none;
    }
    
    DialogueOption:hover {
        background: $surface-lighten-1;
    }
    
    DialogueOption.selected {
        background: $primary-background;
        color: $text;
        border-left: heavy $accent;
    }
    """

    def __init__(self, option_id: str, text: str, selected: bool = False, **kwargs):
        """Initialize the dialogue option."""
        super().__init__(text, **kwargs)
        self.option_id = option_id

        if selected:
            self.add_class("selected")
            # Add a '>' indicator to selected option
            self.label = f"> {text}"
        else:
            self.label = f"  {text}"
