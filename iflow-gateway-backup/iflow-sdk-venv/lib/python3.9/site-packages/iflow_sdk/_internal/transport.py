"""WebSocket transport implementation for iFlow SDK.

This module provides the low-level WebSocket communication layer.
It handles connection management, message sending/receiving, and
basic error handling.
"""

import asyncio
import json
import logging
import time
from collections import deque
from typing import Any, AsyncIterator, Dict, Optional, Union

try:
    import websockets
    from websockets.client import WebSocketClientProtocol
    from websockets.exceptions import ConnectionClosed, WebSocketException
except ImportError:
    raise ImportError(
        "websockets is required for iFlow SDK. " "Install it with: pip install websockets>=11.0"
    )

from .._errors import ConnectionError, JSONDecodeError, TimeoutError, TransportError

logger = logging.getLogger(__name__)


class WebSocketTransport:
    """WebSocket transport for iFlow communication.

    This class provides a low-level WebSocket interface for communicating
    with iFlow. It handles connection management, message serialization,
    and error recovery.

    Attributes:
        url: WebSocket URL to connect to
        websocket: Active WebSocket connection (if connected)
        connected: Whether the transport is currently connected
    """

    def __init__(self, url: str, timeout: float = 300.0):
        """Initialize WebSocket transport.

        Args:
            url: WebSocket URL (e.g., ws://localhost:8090/acp?peer=iflow)
            timeout: Connection timeout in seconds
        """
        self.url = url
        self.timeout = timeout
        self.websocket: Optional[WebSocketClientProtocol] = None
        self.connected = False
        self._receive_task: Optional[asyncio.Task] = None
        
        # Circuit breaker state for memory-safe failure tracking
        self._failure_history: deque = deque(maxlen=100)  # Bounded failure history
        self._retry_attempts: deque = deque(maxlen=1000)  # Limited retry records
        self._failure_expiration_seconds = 3600  # 1 hour TTL for failures

    async def connect(self) -> None:
        """Establish WebSocket connection.

        Raises:
            ConnectionError: If connection fails
            TimeoutError: If connection times out
        """
        if self.connected:
            logger.warning("Already connected to %s", self.url)
            return

        # Clean up expired failures before attempting connection
        self._cleanup_expired_failures()
        self._record_retry_attempt()

        try:
            logger.info("Connecting to %s", self.url)
            self.websocket = await asyncio.wait_for(
                websockets.connect(
                    self.url,
                    ping_interval=None,  # We'll handle ping/pong if needed
                    ping_timeout=None,
                    max_size=10 * 1024 * 1024,  # 10MB limit for large messages
                ),
                timeout=self.timeout,
            )
            self.connected = True
            logger.info("Connected to %s", self.url)

        except asyncio.TimeoutError as e:
            self._record_failure(e)
            raise TimeoutError(f"Connection timeout after {self.timeout}s") from e
        except WebSocketException as e:
            self._record_failure(e)
            raise ConnectionError(f"WebSocket connection failed: {e}") from e
        except Exception as e:
            self._record_failure(e)
            raise ConnectionError(f"Failed to connect to {self.url}: {e}") from e

    async def send(self, message: Union[str, Dict[str, Any]]) -> None:
        """Send a message through WebSocket.

        Args:
            message: Message to send (string or dictionary)

        Raises:
            ConnectionError: If not connected
            TransportError: If send fails
        """
        if not self.connected or not self.websocket:
            raise ConnectionError("Not connected")

        try:
            # Serialize message if it's a dictionary
            if isinstance(message, dict):
                data = json.dumps(message)
            else:
                data = message

            await self.websocket.send(data)
            logger.debug("Sent message: %s", data[:200] + "..." if len(data) > 200 else data)

        except ConnectionClosed as e:
            self.connected = False
            raise ConnectionError(f"Connection lost: {e}") from e
        except Exception as e:
            raise TransportError(f"Failed to send message: {e}") from e

    async def receive(self) -> AsyncIterator[Union[str, Dict[str, Any]]]:
        """Receive messages from WebSocket.

        Yields:
            Received messages (raw strings or parsed JSON)

        Raises:
            ConnectionError: If not connected
            JSONDecodeError: If JSON parsing fails
        """
        if not self.connected or not self.websocket:
            raise ConnectionError("Not connected")

        while self.connected:
            try:
                message = await self.websocket.recv()

                # Return raw message - let protocol layer decide how to handle it
                # Control messages (starting with //) are returned as strings
                # JSON messages are returned as strings to be parsed by protocol
                logger.debug(
                    "Received message: %s", message[:200] + "..." if len(message) > 200 else message
                )
                yield message

            except ConnectionClosed as e:
                logger.info("Connection closed: %s", e)
                self.connected = False
                break
            except Exception as e:
                logger.error("Error receiving message: %s", e)
                raise TransportError(f"Failed to receive message: {e}") from e

    def _record_failure(self, error: Exception) -> None:
        """Record a connection failure with timestamp for circuit breaker.
        
        Uses bounded deque to prevent unbounded memory growth.
        
        Args:
            error: The exception that caused the failure
        """
        timestamp = time.time()
        self._failure_history.append((timestamp, str(error)))
        logger.debug(f"Recorded failure: {error} (history size: {len(self._failure_history)})")
    
    def _record_retry_attempt(self) -> None:
        """Record a retry attempt with timestamp.
        
        Uses bounded deque limited to last 1000 attempts.
        """
        timestamp = time.time()
        self._retry_attempts.append(timestamp)
        logger.debug(f"Recorded retry attempt (total: {len(self._retry_attempts)})")
    
    def _cleanup_expired_failures(self) -> int:
        """Remove failures older than expiration time.
        
        Returns:
            Number of failures cleaned up
        """
        current_time = time.time()
        cutoff_time = current_time - self._failure_expiration_seconds
        
        # Count failures to remove
        expired_count = sum(1 for ts, _ in self._failure_history if ts < cutoff_time)
        
        if expired_count > 0:
            # Create new deque with only non-expired failures
            self._failure_history = deque(
                ((ts, err) for ts, err in self._failure_history if ts >= cutoff_time),
                maxlen=100
            )
            logger.debug(f"Cleaned up {expired_count} expired failures")
        
        return expired_count
    
    def get_failure_stats(self) -> Dict[str, Any]:
        """Get circuit breaker failure statistics.
        
        Returns:
            Dictionary with failure counts and recent errors
        """
        self._cleanup_expired_failures()
        
        return {
            "total_failures": len(self._failure_history),
            "total_retries": len(self._retry_attempts),
            "recent_failures": [
                {"timestamp": ts, "error": err}
                for ts, err in list(self._failure_history)[-10:]  # Last 10 failures
            ],
            "failure_history_capacity": self._failure_history.maxlen,
            "retry_history_capacity": self._retry_attempts.maxlen,
        }

    async def close(self) -> None:
        """Close WebSocket connection gracefully."""
        if self.websocket and self.connected:
            try:
                await self.websocket.close()
                logger.info("WebSocket connection closed")
            except Exception as e:
                logger.warning("Error closing WebSocket: %s", e)
            finally:
                self.connected = False
                self.websocket = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        return False

    @property
    def is_connected(self) -> bool:
        """Check if transport is connected.

        Returns:
            True if connected, False otherwise
        """
        return self.connected and self.websocket is not None
