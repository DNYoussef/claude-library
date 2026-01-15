"""
WebSocket Heartbeat Manager

Implements ping/pong heartbeat with automatic connection cleanup.
Default: Ping every 30s, disconnect if no pong after 60s.

Zero external dependencies beyond stdlib.
"""

import asyncio
import logging
import uuid
from typing import Dict, Optional, Callable, Any, Protocol
from datetime import datetime, timezone

from .message_types import PingMessage

logger = logging.getLogger(__name__)


class WebSocketProtocol(Protocol):
    """Protocol for WebSocket-like objects."""
    async def send_json(self, data: Dict[str, Any]) -> None: ...


class HeartbeatManager:
    """
    Manages WebSocket heartbeat (ping/pong) for connection health monitoring.

    Features:
    - Send ping every N seconds (configurable)
    - Expect pong within timeout seconds
    - Auto-disconnect stale connections via callback
    - Track last activity per connection

    Usage:
        manager = HeartbeatManager(ping_interval=30, pong_timeout=60)

        # Start heartbeat for a connection
        manager.start_heartbeat(
            connection_id="conn-123",
            websocket=ws,
            on_disconnect_callback=my_disconnect_handler
        )

        # When pong received from client
        manager.record_pong("conn-123")

        # When connection closes
        manager.stop_heartbeat("conn-123")
    """

    def __init__(
        self,
        ping_interval: int = 30,
        pong_timeout: int = 60
    ):
        """
        Initialize heartbeat manager.

        Args:
            ping_interval: Seconds between ping messages (default 30)
            pong_timeout: Seconds to wait for pong before disconnecting (default 60)
        """
        if ping_interval <= 0:
            raise ValueError("ping_interval must be positive")
        if pong_timeout <= 0:
            raise ValueError("pong_timeout must be positive")
        if pong_timeout <= ping_interval:
            raise ValueError("pong_timeout must be greater than ping_interval")

        self.ping_interval = ping_interval
        self.pong_timeout = pong_timeout

        # Track last pong time for each connection
        self._last_pong: Dict[str, datetime] = {}

        # Track heartbeat tasks
        self._heartbeat_tasks: Dict[str, asyncio.Task] = {}

    def start_heartbeat(
        self,
        connection_id: str,
        websocket: WebSocketProtocol,
        on_disconnect_callback: Optional[Callable[[str], Any]] = None
    ) -> None:
        """
        Start heartbeat for a connection.

        Args:
            connection_id: Unique connection identifier
            websocket: WebSocket instance with send_json method
            on_disconnect_callback: Optional async callback when connection fails heartbeat
        """
        # Initialize last pong time
        self._last_pong[connection_id] = datetime.now(timezone.utc)

        # Create heartbeat task
        task = asyncio.create_task(
            self._heartbeat_loop(
                connection_id,
                websocket,
                on_disconnect_callback
            )
        )
        self._heartbeat_tasks[connection_id] = task

        logger.info(f"Started heartbeat for connection {connection_id}")

    def stop_heartbeat(self, connection_id: str) -> None:
        """
        Stop heartbeat for a connection.

        Args:
            connection_id: Connection identifier
        """
        # Cancel heartbeat task
        task = self._heartbeat_tasks.pop(connection_id, None)
        if task and not task.done():
            task.cancel()

        # Remove last pong tracking
        self._last_pong.pop(connection_id, None)

        logger.info(f"Stopped heartbeat for connection {connection_id}")

    def record_pong(self, connection_id: str) -> None:
        """
        Record pong received from client.

        Args:
            connection_id: Connection identifier
        """
        if connection_id not in self._last_pong:
            return
        self._last_pong[connection_id] = datetime.now(timezone.utc)
        logger.debug(f"Pong received from {connection_id}")

    def is_connection_alive(self, connection_id: str) -> bool:
        """
        Check if connection is alive based on last pong.

        Args:
            connection_id: Connection identifier

        Returns:
            True if connection is alive, False otherwise
        """
        last_pong_time = self._last_pong.get(connection_id)
        if not last_pong_time:
            return False

        time_since_pong = (datetime.now(timezone.utc) - last_pong_time).total_seconds()
        return time_since_pong < self.pong_timeout

    async def _heartbeat_loop(
        self,
        connection_id: str,
        websocket: WebSocketProtocol,
        on_disconnect_callback: Optional[Callable[[str], Any]] = None
    ) -> None:
        """
        Heartbeat loop that sends pings and monitors pongs.

        Args:
            connection_id: Connection identifier
            websocket: WebSocket instance
            on_disconnect_callback: Callback when connection dies
        """
        try:
            while True:
                # Wait for ping interval
                await asyncio.sleep(self.ping_interval)

                # Check if last pong is too old
                if not self.is_connection_alive(connection_id):
                    logger.warning(
                        f"Connection {connection_id} failed heartbeat "
                        f"(no pong for {self.pong_timeout}s)"
                    )

                    # Trigger disconnect callback
                    if on_disconnect_callback:
                        result = on_disconnect_callback(connection_id)
                        if asyncio.iscoroutine(result):
                            await result

                    break

                # Send ping
                try:
                    ping_message = PingMessage(event_id=str(uuid.uuid4()))
                    await websocket.send_json(ping_message.to_dict())
                    logger.debug(f"Sent ping to {connection_id}")
                except Exception as e:
                    logger.error(f"Error sending ping to {connection_id}: {e}")

                    # Trigger disconnect callback
                    if on_disconnect_callback:
                        result = on_disconnect_callback(connection_id)
                        if asyncio.iscoroutine(result):
                            await result

                    break

        except asyncio.CancelledError:
            logger.info(f"Heartbeat cancelled for {connection_id}")
            raise
        except Exception as e:
            logger.error(f"Heartbeat error for {connection_id}: {e}", exc_info=True)

    def get_connection_health(self, connection_id: str) -> Dict[str, Any]:
        """
        Get health metrics for a connection.

        Args:
            connection_id: Connection identifier

        Returns:
            Dictionary with health metrics
        """
        last_pong_time = self._last_pong.get(connection_id)

        if not last_pong_time:
            return {
                "connection_id": connection_id,
                "status": "unknown",
                "last_pong": None,
                "seconds_since_pong": None
            }

        seconds_since_pong = (datetime.now(timezone.utc) - last_pong_time).total_seconds()

        return {
            "connection_id": connection_id,
            "status": "alive" if self.is_connection_alive(connection_id) else "dead",
            "last_pong": last_pong_time.isoformat(),
            "seconds_since_pong": seconds_since_pong
        }

    def get_all_health_metrics(self) -> Dict[str, Any]:
        """
        Get health metrics for all connections.

        Returns:
            Dictionary with all connection health metrics
        """
        alive_count = sum(
            1 for conn_id in self._last_pong
            if self.is_connection_alive(conn_id)
        )
        dead_count = len(self._last_pong) - alive_count

        return {
            "total_connections": len(self._last_pong),
            "alive_connections": alive_count,
            "dead_connections": dead_count,
            "connections": [
                self.get_connection_health(conn_id)
                for conn_id in self._last_pong.keys()
            ]
        }

    @property
    def active_connection_count(self) -> int:
        """Get count of connections with active heartbeats."""
        return len(self._heartbeat_tasks)
