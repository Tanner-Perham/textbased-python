"""
Custom components for the dialogue UI.
"""

from typing import ClassVar, Dict, Optional

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
    """

    def __init__(self, skill: str, success: bool, roll: int, difficulty: int, **kwargs):
        """Initialize the skill check result."""
        super().__init__(**kwargs)
        self.skill = skill
        self.success = success
        self.roll = roll
        self.difficulty = difficulty

        # Set success/failure styling
        self.add_class("success" if success else "failure")

    def render(self) -> str:
        """Render the skill check content."""
        result = "SUCCESS" if self.success else "FAILURE"
        return f"[b]Skill Check:[/b] {self.skill} - {result} (Roll: {self.roll}/{self.difficulty})"


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
