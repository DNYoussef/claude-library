"""
WebSocket Message Types - Base Message Schemas

Provides base message types for WebSocket communication.
Extend these for domain-specific message types.

Zero external dependencies beyond stdlib + pydantic.
"""

from enum import Enum
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field
import json


class BaseMessageType(str, Enum):
    """
    Base WebSocket message types.

    Extend this enum for domain-specific message types:
        class MyMessageType(str, Enum):
            PING = "ping"
            PONG = "pong"
            MY_CUSTOM = "my_custom"
    """
    PING = "ping"
    PONG = "pong"
    ERROR = "error"
    ACK = "ack"


@dataclass
class WSMessage:
    """
    Base WebSocket message.

    Attributes:
        type: Message type (from BaseMessageType or extended enum)
        event_id: Unique event ID for replay/deduplication
        timestamp: Message creation time (UTC)
        data: Message payload (optional)

    Usage:
        msg = WSMessage(
            type=BaseMessageType.ACK,
            event_id="uuid-123",
            data={"status": "ok"}
        )
        json_str = msg.to_json()
    """
    type: str
    event_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type if isinstance(self.type, str) else self.type.value,
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
        }

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WSMessage":
        """Create from dictionary."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        elif timestamp is None:
            timestamp = datetime.now(timezone.utc)

        return cls(
            type=data["type"],
            event_id=data["event_id"],
            timestamp=timestamp,
            data=data.get("data", {}),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "WSMessage":
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class PingMessage:
    """
    Ping message for heartbeat.

    Sent by server to check client liveness.
    Client should respond with PongMessage.
    """
    event_id: str
    type: str = BaseMessageType.PING.value
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


@dataclass
class PongMessage:
    """
    Pong response for heartbeat.

    Sent by client in response to PingMessage.
    """
    event_id: str
    type: str = BaseMessageType.PONG.value
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


@dataclass
class ErrorMessage:
    """
    Error message.

    Used to communicate errors to clients.
    """
    event_id: str
    error: str
    details: Optional[Dict[str, Any]] = None
    type: str = BaseMessageType.ERROR.value
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "type": self.type,
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "error": self.error,
        }
        if not self.details:
            return result
        result["details"] = self.details
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


@dataclass
class AckMessage:
    """
    Acknowledgment message.

    Used to acknowledge receipt of a message.
    """
    event_id: str
    ack_event_id: str  # Event ID being acknowledged
    type: str = BaseMessageType.ACK.value
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "ack_event_id": self.ack_event_id,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())
