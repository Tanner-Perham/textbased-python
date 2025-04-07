from textual.widgets import Static
from textual.message import Message

class Notification(Static):
    """Popup notification widget."""
    
    class Dismissed(Message):
        """Sent when notification is dismissed."""

    def __init__(self, text: str, timeout: float = 5.0):
        super().__init__(text)
        self.timeout = timeout

    async def on_mount(self) -> None:
        """Called when notification is mounted."""
        await self.sleep(self.timeout)
        self.remove()
        self.post_message(self.Dismissed())