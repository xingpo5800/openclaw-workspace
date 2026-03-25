"""iFlow SDK Client for interacting with iFlow.

This module provides the main client class for communicating with iFlow
using the ACP (Agent Communication Protocol).
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Union

from ._errors import ConnectionError, ProtocolError
from ._internal.file_handler import FileSystemHandler
from ._internal.process_manager import IFlowNotInstalledError, IFlowProcessManager
from ._internal.protocol import ACPProtocol
from ._internal.transport import WebSocketTransport
from .types import (
    AgentInfo,
    AssistantMessage,
    AssistantMessageChunk,
    ErrorMessage,
    IFlowOptions,
    Message,
    TaskFinishMessage,
    ToolCallConfirmationOutcome,
    ToolCallContent,
    ToolCallMessage,
    ToolCallStatus,
    ToolResultMessage,
    UserMessage,
    UserMessageChunk,
)

logger = logging.getLogger(__name__)


class IFlowClient:
    """Client for bidirectional, interactive conversations with iFlow.

    This client provides full control over the conversation flow with support
    for streaming, interrupts, and dynamic message sending. It implements the
    ACP protocol v0.0.9 for communication with iFlow.

    Key features:
    - **Bidirectional**: Send and receive messages at any time
    - **Stateful**: Maintains conversation context across messages
    - **Interactive**: Send follow-ups based on responses
    - **Tool calls**: Automatic or manual confirmation of tool usage
    - **Streaming**: Real-time streaming of assistant responses
    - **Control flow**: Support for interrupts and session management

    When to use IFlowClient:
    - Building chat interfaces or conversational UIs
    - Interactive debugging or exploration sessions
    - Multi-turn conversations with context
    - When you need to react to iFlow's responses
    - Real-time applications with user input
    - When you need interrupt capabilities

    When to use query() instead:
    - Simple one-off questions
    - Batch processing of prompts
    - Fire-and-forget automation scripts
    - When all inputs are known upfront
    - Stateless operations

    Example - Basic conversation:
        ```python
        async with IFlowClient() as client:
            # Send a message
            await client.send_message("What is 2 + 2?")

            # Receive response
            async for message in client.receive_messages():
                if isinstance(message, AssistantMessage):
                    print(message.chunk.text)
                elif isinstance(message, TaskFinishMessage):
                    break
        ```

    Example - With tool call approval:
        ```python
        options = IFlowOptions(approval_mode=ApprovalMode.DEFAULT)
        async with IFlowClient(options) as client:
            await client.send_message("Create a Python file")

            async for message in client.receive_messages():
                if isinstance(message, ToolConfirmationRequestMessage):
                    # User approval required (DEFAULT mode)
                    approved = await ask_user_confirmation(message)
                    if approved:
                        await client.respond_to_tool_confirmation(
                            message.request_id, "proceed_once"
                        )
                    else:
                        await client.cancel_tool_confirmation(message.request_id)
        ```

    Example - Sandbox mode:
        ```python
        options = IFlowOptions().for_sandbox()
        async with IFlowClient(options) as client:
            await client.send_message("Hello from sandbox!")
            # ...
        ```
    """

    def __init__(self, options: Optional[IFlowOptions] = None):
        """Initialize iFlow client.

        Args:
            options: Configuration options. If None, uses defaults.
            
        Raises:
            ValueError: If configuration options are invalid
        """
        self.options = options or IFlowOptions()
        
        # Validate configuration
        self.options.validate()
        self._transport: Optional[WebSocketTransport] = None
        self._protocol: Optional[ACPProtocol] = None
        self._connected = False
        self._authenticated = False
        self._message_task: Optional[asyncio.Task] = None
        # Use bounded queue to prevent memory leak
        self._message_queue: asyncio.Queue[Message] = asyncio.Queue(
            maxsize=self.options.max_message_queue_size
        )
        # Store tool calls with timestamp for expiration: {tool_id: (message, timestamp)}
        self._pending_tool_calls: Dict[str, tuple[ToolCallMessage, float]] = {}
        self._pending_requests: Dict[int, asyncio.Future] = {}
        self._max_buffered_operations = 100  # Default limit for buffered operations
        self._operation_ttl_seconds = 300  # 5 minutes TTL for operations
        self._session_id: Optional[str] = None
        self._process_manager: Optional[IFlowProcessManager] = None
        self._process_started = False
        self._memory_profiler: Optional["MemoryProfiler"] = None
        
        # Track all background tasks for proper lifecycle management
        self._background_tasks: set[asyncio.Task] = set()
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Event manager with weak references
        from ._internal.event_manager import EventManager
        self._event_manager = EventManager()

        # Start memory profiler if debug mode enabled
        if self.options.debug_memory:
            from ._internal.memory_profiler import MemoryProfiler
            self._memory_profiler = MemoryProfiler()
            self._memory_profiler.start()
            logger.info("Memory profiling enabled (debug mode)")

        # Configure logging
        logging.basicConfig(level=self.options.log_level)
        logger.info(
            "IFlowClient initialized: queue_size=%d, overflow=%s, history=%d",
            self.options.max_message_queue_size,
            self.options.queue_overflow_strategy,
            self.options.max_history_size,
        )

    async def connect(self) -> None:
        """Connect to iFlow and initialize the protocol.

        Performs the following steps:
        1. Establishes WebSocket connection
        2. Initializes ACP protocol
        3. Performs authentication if needed
        4. Starts message handler

        Raises:
            ConnectionError: If connection fails
            ProtocolError: If protocol initialization fails
        """
        if self._connected:
            logger.warning("Already connected")
            return

        try:
            # Check if we need to start iFlow process
            if self.options.auto_start_process:
                # Check if URL is the default localhost URL
                if self.options.url.startswith("ws://localhost:") or self.options.url.startswith(
                    "ws://127.0.0.1:"
                ):
                    # Try to start iFlow process first, let the main connection handle detection
                    should_start_process = True

                    # Quick check if something is listening on the port (without WebSocket handshake)
                    import socket
                    from urllib.parse import urlparse

                    try:
                        parsed_url = urlparse(self.options.url.replace("ws://", "http://"))
                        host = parsed_url.hostname or "localhost"
                        port = parsed_url.port or 8090

                        with socket.create_connection((host, port), timeout=1.0) as sock:
                            should_start_process = False
                            logger.info("iFlow already running at %s", self.options.url)
                    except OSError:
                        # No service listening, need to start iFlow
                        pass

                    if should_start_process:
                        logger.info("iFlow not running, starting process...")
                        self._process_manager = IFlowProcessManager(
                            start_port=self.options.process_start_port,
                            log_file=self.options.process_log_file
                        )
                        try:
                            iflow_url = await self._process_manager.start()
                            self.options.url = iflow_url  # Update URL to the actual port
                            self._process_started = True
                            logger.info("Started iFlow process at %s", iflow_url)
                            # Wait a bit for the process to be ready
                            await asyncio.sleep(3.0)
                        except IFlowNotInstalledError as e:
                            logger.error("iFlow not installed")
                            raise ConnectionError(str(e)) from e
                        except Exception as e:
                            logger.error("Failed to start iFlow process: %s", e)
                            raise ConnectionError(f"Failed to start iFlow process: {e}") from e

            # Create file handler if file access is enabled
            file_handler = None
            if self.options.file_access:
                file_handler = FileSystemHandler(
                    allowed_dirs=self.options.file_allowed_dirs,
                    read_only=self.options.file_read_only,
                    max_file_size=self.options.file_max_size,
                )
                logger.info(
                    "File system access enabled with %s mode",
                    "read-only" if self.options.file_read_only else "read-write",
                )

            # Create transport and protocol
            self._transport = WebSocketTransport(self.options.url, self.options.timeout)
            self._protocol = ACPProtocol(
                self._transport, 
                file_handler, 
                self.options.approval_mode,
                max_pending_requests=self.options.max_pending_requests,
                request_ttl=self.options.request_ttl_seconds,
                debug_memory=self.options.debug_memory
            )

            # Connect transport with retry logic
            max_retries = 3
            retry_delay = 1.0

            for attempt in range(max_retries):
                try:
                    await self._transport.connect()
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        # Last attempt failed, re-raise the exception
                        raise

                    logger.warning(
                        "Connection attempt %d failed: %s. Retrying in %.1fs...",
                        attempt + 1,
                        e,
                        retry_delay,
                    )
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 1.5  # Exponential backoff

            # Prepare protocol configurations
            mcp_servers = []
            if self.options.mcp_servers:
                for server in self.options.mcp_servers:
                    if hasattr(server, "to_dict"):
                        mcp_servers.append(server.to_dict())
                    else:
                        mcp_servers.append(server)

            hooks = None
            if self.options.hooks:
                hooks = {}
                for event_type, configs in self.options.hooks.items():
                    hooks[event_type.value] = [
                        config.to_dict() if hasattr(config, "to_dict") else config
                        for config in configs
                    ]

            commands = None
            if self.options.commands:
                commands = [
                    cmd.to_dict() if hasattr(cmd, "to_dict") else cmd
                    for cmd in self.options.commands
                ]

            agents = None
            if self.options.agents:
                agents = [
                    agent.to_dict() if hasattr(agent, "to_dict") else agent
                    for agent in self.options.agents
                ]

            # Initialize protocol with extended configurations
            init_result = await self._protocol.initialize(
                mcp_servers=mcp_servers, hooks=hooks, commands=commands, agents=agents
            )
            self._authenticated = init_result.get("isAuthenticated", False)

            # Authenticate if needed
            if not self._authenticated:
                method_id = self.options.auth_method_id or "iflow"
                method_info = self.options.auth_method_info

                # Convert AuthMethodInfo to dict if needed
                if method_info is not None:
                    from .types import AuthMethodInfo

                    if isinstance(method_info, AuthMethodInfo):
                        method_info = method_info.to_dict()

                await self._protocol.authenticate(method_id, method_info)
                self._authenticated = True

            # Prepare session settings
            settings = None
            if self.options.session_settings:
                settings = self.options.session_settings.to_dict()
            else:
                # Create default settings if not provided
                settings = {}

            # Always set permission_mode from approval_mode
            if self.options.approval_mode:
                settings["permission_mode"] = self.options.approval_mode.value

            # Create a new session with extended configurations

            if self.options.session_id:
                self._session_id = self.options.session_id
                self._session_id = await self._protocol.load_session(
                    self.options.session_id,
                    self.options.cwd,
                    mcp_servers,
                    hooks,
                    commands,
                    agents,
                    settings,
                )
            else:
                self._session_id = await self._protocol.create_session(
                    self.options.cwd, mcp_servers, hooks, commands, agents, settings
                )
                logger.info("Created session: %s", self._session_id)

            # Start message handler (cancel old one if exists)
            if self._message_task and not self._message_task.done():
                self._message_task.cancel()
                try:
                    await self._message_task
                except asyncio.CancelledError:
                    pass
            
            self._message_task = self._create_background_task(
                self._handle_messages(),
                name="message_handler"
            )
            
            # Start periodic operation cleanup task (every 30 seconds)
            if self._cleanup_task is None or self._cleanup_task.done():
                self._cleanup_task = self._create_background_task(
                    self._periodic_operation_cleanup(),
                    name="operation_cleanup"
                )

            self._connected = True
            logger.info("Connected to iFlow")

        except Exception as e:
            await self._cleanup()
            raise ConnectionError(f"Failed to connect: {e}") from e

    async def load_session(self, session_id: str) -> None:
        """Load an existing session by ID.

        This method attempts to load a previously created session. Note that
        this functionality is not yet supported by iFlow (loadSession capability
        is false), so this will likely fail with current iFlow versions.

        Args:
            session_id: The session ID to load

        Raises:
            ConnectionError: If not connected
            ProtocolError: If session loading fails or is not supported

        Example:
            ```python
            async with IFlowClient() as client:
                try:
                    # Try to load a previous session
                    await client.load_session("session_123")
                except ProtocolError as e:
                    # Fallback to creating a new session
                    print(f"Could not load session: {e}")
            ```
        """
        if not self._connected or not self._protocol:
            raise ConnectionError("Not connected. Call connect() first.")

        try:
            await self._protocol.load_session(
                session_id, self.options.cwd, self.options.mcp_servers
            )
            self._session_id = session_id
            logger.info("Loaded session: %s", session_id)
        except ProtocolError as e:
            if "not supported" in str(e):
                logger.warning(
                    "session/load is not supported by current iFlow version. "
                    "Creating new session instead."
                )
                # Could optionally fallback to create_session here
                raise
            else:
                raise

    def _create_background_task(self, coro, name: str = "background") -> asyncio.Task:
        """Create and track a background task for proper lifecycle management.
        
        Args:
            coro: Coroutine to run as background task
            name: Name for the task (for debugging)
            
        Returns:
            Created task
        """
        task = asyncio.create_task(coro, name=name)
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        logger.debug(f"Created background task: {name} (total: {len(self._background_tasks)})")
        return task
    
    async def _cancel_background_tasks(self) -> None:
        """Cancel all tracked background tasks.
        
        This ensures proper cleanup and prevents task leaks.
        """
        if not self._background_tasks:
            return
            
        logger.debug(f"Cancelling {len(self._background_tasks)} background tasks")
        
        for task in self._background_tasks:
            if not task.done():
                task.cancel()
        
        # Wait for all tasks to complete cancellation
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        self._background_tasks.clear()
        logger.debug("All background tasks cancelled")
    
    def _monitor_task_leaks(self) -> Dict[str, Any]:
        """Monitor for potential task leaks.
        
        Returns:
            Dictionary with task monitoring information
        """
        active_tasks = [t for t in self._background_tasks if not t.done()]
        completed_tasks = [t for t in self._background_tasks if t.done()]
        
        return {
            "total_tasks": len(self._background_tasks),
            "active_tasks": len(active_tasks),
            "completed_tasks": len(completed_tasks),
            "task_names": [t.get_name() for t in active_tasks],
        }
    
    def _cleanup_expired_operations(self) -> int:
        """Clean up expired buffered operations.
        
        Removes tool calls that have exceeded their TTL.
        
        Returns:
            Number of operations cleaned up
        """
        current_time = time.time()
        cutoff_time = current_time - self._operation_ttl_seconds
        
        expired_ids = [
            tool_id
            for tool_id, (_, timestamp) in self._pending_tool_calls.items()
            if timestamp < cutoff_time
        ]
        
        for tool_id in expired_ids:
            msg, timestamp = self._pending_tool_calls.pop(tool_id)
            age_seconds = current_time - timestamp
            logger.warning(
                f"Discarded expired tool call: {tool_id} (age: {age_seconds:.1f}s)"
            )
        
        return len(expired_ids)
    
    def _enforce_operation_limit(self) -> int:
        """Enforce maximum buffered operations limit.
        
        Removes oldest operations if limit is exceeded.
        
        Returns:
            Number of operations removed
        """
        if len(self._pending_tool_calls) <= self._max_buffered_operations:
            return 0
        
        # Sort by timestamp and remove oldest
        sorted_items = sorted(
            self._pending_tool_calls.items(),
            key=lambda x: x[1][1]  # Sort by timestamp
        )
        
        to_remove = len(self._pending_tool_calls) - self._max_buffered_operations
        removed_count = 0
        
        for tool_id, (msg, timestamp) in sorted_items[:to_remove]:
            self._pending_tool_calls.pop(tool_id, None)
            removed_count += 1
            logger.warning(
                f"Removed oldest tool call to enforce limit: {tool_id}"
            )
        
        return removed_count
    
    def get_operation_buffer_stats(self) -> Dict[str, Any]:
        """Get statistics about buffered operations.
        
        Returns:
            Dictionary with buffer statistics
        """
        current_time = time.time()
        
        ages = [
            current_time - timestamp
            for _, timestamp in self._pending_tool_calls.values()
        ]
        
        return {
            "total_operations": len(self._pending_tool_calls),
            "max_operations": self._max_buffered_operations,
            "utilization": len(self._pending_tool_calls) / self._max_buffered_operations,
            "oldest_age_seconds": max(ages) if ages else 0,
            "average_age_seconds": sum(ages) / len(ages) if ages else 0,
            "ttl_seconds": self._operation_ttl_seconds,
        }
    
    async def _periodic_operation_cleanup(self) -> None:
        """Periodically clean up expired buffered operations.
        
        Runs every 30 seconds to check for and remove expired operations.
        """
        try:
            while self._connected:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                if not self._connected:
                    break
                
                # Clean up expired operations
                expired_count = self._cleanup_expired_operations()
                
                # Enforce operation limit
                removed_count = self._enforce_operation_limit()
                
                if expired_count > 0 or removed_count > 0:
                    logger.info(
                        f"Operation cleanup: expired={expired_count}, "
                        f"removed={removed_count}, "
                        f"remaining={len(self._pending_tool_calls)}"
                    )
                
                # Log stats if debug mode enabled
                if self.options.debug_memory and len(self._pending_tool_calls) > 0:
                    stats = self.get_operation_buffer_stats()
                    logger.debug(
                        f"[MemoryDebug] Operation buffer: "
                        f"count={stats['total_operations']}, "
                        f"utilization={stats['utilization']:.1%}, "
                        f"oldest_age={stats['oldest_age_seconds']:.1f}s"
                    )
        
        except asyncio.CancelledError:
            logger.debug("Operation cleanup task cancelled")
        except Exception as e:
            logger.error(f"Error in operation cleanup task: {e}")

    async def disconnect(self) -> None:
        """Disconnect from iFlow gracefully."""
        await self._cleanup()

    async def _cleanup(self) -> None:
        """Clean up resources."""
        self._connected = False

        # Cancel message handler
        if self._message_task:
            self._message_task.cancel()
            try:
                await self._message_task
            except asyncio.CancelledError:
                pass
            self._message_task = None

        # Cancel cleanup task if running
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

        # Cancel all tracked background tasks
        await self._cancel_background_tasks()

        # Stop protocol cleanup task
        if self._protocol:
            self._protocol.cleanup()

        # Clean up event listeners
        if self._event_manager:
            self._event_manager.cleanup_dead_references()
            self._event_manager.clear_all()
            logger.debug("Event listeners cleaned up")

        # Close transport
        if self._transport:
            await self._transport.close()

        # Stop iFlow process if we started it
        if self._process_manager and self._process_started:
            logger.info("Stopping iFlow process...")
            await self._process_manager.stop()
            self._process_manager = None
            self._process_started = False

        self._transport = None
        self._protocol = None
        logger.info("Disconnected from iFlow")

    async def send_message(self, text: str, files: Optional[List[Union[str, Path]]] = None) -> None:
        """Send a message to iFlow.

        Args:
            text: Message text
            files: Optional list of file paths to include

        Raises:
            ConnectionError: If not connected
            ProtocolError: If send fails
        """
        if not self._connected or not self._protocol or not self._session_id:
            raise ConnectionError("Not connected. Call connect() first.")

        # Create prompt content blocks for new protocol
        prompt = [{"type": "text", "text": text}]
        if files:
            for file in files:
                file_path = Path(file)

                # Check if file exists
                if not file_path.exists():
                    logger.warning("File not found, skipping: %s", file_path)
                    continue

                # Determine content type based on file extension
                suffix = file_path.suffix.lower()

                # Image files - use 'image' type with base64 data
                if suffix in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg"]:
                    # For images, we need to read and encode as base64
                    # Note: iFlow expects 'data' field with base64 content and 'mimeType'
                    try:
                        import base64

                        with open(file_path, "rb") as f:
                            image_data = base64.b64encode(f.read()).decode("utf-8")

                        mime_type = {
                            ".png": "image/png",
                            ".jpg": "image/jpeg",
                            ".jpeg": "image/jpeg",
                            ".gif": "image/gif",
                            ".bmp": "image/bmp",
                            ".webp": "image/webp",
                            ".svg": "image/svg+xml",
                        }.get(suffix, "image/unknown")

                        prompt.append({"type": "image", "data": image_data, "mimeType": mime_type})
                        logger.debug("Added image file: %s", file_path.name)
                    except Exception as e:
                        logger.error("Failed to read image file %s: %s", file_path, e)
                        continue

                # Audio files - use 'audio' type with base64 data
                elif suffix in [".mp3", ".wav", ".m4a", ".ogg", ".flac"]:
                    # For audio, we need to read and encode as base64
                    try:
                        import base64

                        with open(file_path, "rb") as f:
                            audio_data = base64.b64encode(f.read()).decode("utf-8")

                        mime_type = {
                            ".mp3": "audio/mpeg",
                            ".wav": "audio/wav",
                            ".m4a": "audio/mp4",
                            ".ogg": "audio/ogg",
                            ".flac": "audio/flac",
                        }.get(suffix, "audio/unknown")

                        prompt.append({"type": "audio", "data": audio_data, "mimeType": mime_type})
                        logger.debug("Added audio file: %s", file_path.name)
                    except Exception as e:
                        logger.error("Failed to read audio file %s: %s", file_path, e)
                        continue

                # All other files - use 'resource_link' type
                else:
                    # For other files, use resource_link which references by URI
                    prompt.append(
                        {
                            "type": "resource_link",
                            "uri": file_path.absolute().as_uri(),
                            "name": file_path.name,
                            "title": file_path.stem,
                            "size": file_path.stat().st_size if file_path.exists() else None,
                        }
                    )
                    logger.debug("Added resource link: %s", file_path.name)

        # Send prompt to session
        await self._protocol.send_prompt(self._session_id, prompt)
        logger.info("Sent prompt with %d content blocks", len(prompt))

    async def interrupt(self) -> None:
        """Interrupt the current message generation.

        Raises:
            ConnectionError: If not connected
        """
        if not self._connected or not self._protocol or not self._session_id:
            raise ConnectionError("Not connected")

        await self._protocol.cancel_session(self._session_id)
        logger.info("Sent interrupt signal")

    async def receive_messages(self) -> AsyncIterator[Message]:
        """Receive messages from iFlow.

        Yields:
            Messages from iFlow (AssistantMessage, ToolCallMessage, etc.)

        Raises:
            ConnectionError: If not connected
        """
        if not self._connected:
            raise ConnectionError("Not connected")

        while self._connected:
            try:
                message = await asyncio.wait_for(self._message_queue.get(), timeout=0.1)
                yield message
            except asyncio.TimeoutError:
                continue

    async def respond_to_tool_confirmation(self, request_id: int, option_id: str) -> None:
        """Respond to a tool confirmation request.

        This method should be called when you receive a ToolConfirmationRequestMessage
        and want to approve the tool call with a specific option.

        Args:
            request_id: The request_id from ToolConfirmationRequestMessage
            option_id: The selected option ID (e.g., "proceed_once", "proceed_always")

        Raises:
            ConnectionError: If not connected
            ProtocolError: If request_id is invalid

        Example:
            ```python
            async for message in client.receive_messages():
                if isinstance(message, ToolConfirmationRequestMessage):
                    # User decides to approve
                    await client.respond_to_tool_confirmation(
                        message.request_id,
                        "proceed_once"
                    )
            ```
        """
        if not self._connected or not self._protocol:
            raise ConnectionError("Not connected")

        await self._protocol.respond_to_permission_request(request_id, option_id, cancelled=False)
        logger.info("Approved tool confirmation request %d with option: %s", request_id, option_id)

    async def cancel_tool_confirmation(self, request_id: int) -> None:
        """Cancel/reject a tool confirmation request.

        This method should be called when you receive a ToolConfirmationRequestMessage
        and want to reject/cancel the tool call.

        Args:
            request_id: The request_id from ToolConfirmationRequestMessage

        Raises:
            ConnectionError: If not connected
            ProtocolError: If request_id is invalid

        Example:
            ```python
            async for message in client.receive_messages():
                if isinstance(message, ToolConfirmationRequestMessage):
                    # User decides to reject
                    await client.cancel_tool_confirmation(message.request_id)
            ```
        """
        if not self._connected or not self._protocol:
            raise ConnectionError("Not connected")

        await self._protocol.respond_to_permission_request(
            request_id, "", cancelled=True  # option_id is ignored when cancelled=True
        )
        logger.info("Cancelled tool confirmation request %d", request_id)

    async def approve_tool_call(
        self,
        tool_id: str,
        outcome: ToolCallConfirmationOutcome = ToolCallConfirmationOutcome.PROCEED_ONCE,
    ) -> None:
        """Approve a tool call that requires confirmation (deprecated).

        DEPRECATED: Use respond_to_tool_confirmation() instead.
        This method is kept for backward compatibility but will be removed in a future version.

        Args:
            tool_id: ID of the tool call to approve
            outcome: Approval outcome (proceed_once, proceed_always, etc.)

        Raises:
            ValueError: If tool call not found
        """
        if tool_id not in self._pending_tool_calls:
            raise ValueError(f"Unknown tool call: {tool_id}")

        logger.warning(
            "approve_tool_call() is deprecated. Use respond_to_tool_confirmation() instead."
        )
        logger.info("Approved tool call %s with outcome %s", tool_id, outcome)
        # Clean up expired operations before removing
        self._cleanup_expired_operations()
        del self._pending_tool_calls[tool_id]

    async def reject_tool_call(self, tool_id: str) -> None:
        """Reject a tool call that requires confirmation (deprecated).

        DEPRECATED: Use cancel_tool_confirmation() instead.
        This method is kept for backward compatibility but will be removed in a future version.

        Args:
            tool_id: ID of the tool call to reject

        Raises:
            ValueError: If tool call not found
        """
        if tool_id not in self._pending_tool_calls:
            raise ValueError(f"Unknown tool call: {tool_id}")

        logger.warning("reject_tool_call() is deprecated. Use cancel_tool_confirmation() instead.")
        logger.info("Rejected tool call %s", tool_id)
        # Clean up expired operations before removing
        self._cleanup_expired_operations()
        del self._pending_tool_calls[tool_id]

    async def _handle_messages(self) -> None:
        """Background task to handle incoming messages."""
        if not self._protocol:
            return

        try:
            async for message_data in self._protocol.handle_messages():
                message = self._process_message(message_data)
                if message:
                    await self._enqueue_message(message)

        except asyncio.CancelledError:
            logger.debug("Message handler cancelled")
        except Exception as e:
            logger.error("Error in message handler: %s", e)
            error_msg = ErrorMessage(-1, str(e))
            try:
                await self._enqueue_message(error_msg)
            except Exception as enqueue_error:
                logger.error("Failed to enqueue error message: %s", enqueue_error)

    async def _enqueue_message(self, message: Message) -> None:
        """Enqueue message with overflow handling.

        Args:
            message: Message to enqueue

        Raises:
            QueueFullError: If queue is full and strategy is 'raise'
            MemoryError: If memory limit is exceeded
        """
        from ._errors import QueueFullError

        # Debug logging if enabled
        if self.options.debug_memory:
            logger.debug(
                "[MemoryDebug] Enqueuing message: type=%s, queue_size=%d/%d",
                type(message).__name__,
                self._message_queue.qsize(),
                self.options.max_message_queue_size
            )

        # Check memory limit before enqueuing (if enabled)
        if self.options.memory_limit_bytes is not None:
            stats = self.get_memory_stats()
            if stats.get("memory_limit_exceeded", False):
                raise MemoryError(
                    f"Memory limit exceeded: {stats['estimated_memory_mb']:.2f} MB > "
                    f"{stats['memory_limit_mb']:.2f} MB. Cannot enqueue new messages."
                )

        try:
            # Try non-blocking put first
            self._message_queue.put_nowait(message)

            # Monitor queue utilization
            queue_size = self._message_queue.qsize()
            max_size = self.options.max_message_queue_size
            utilization = queue_size / max_size if max_size > 0 else 0

            # Warn if utilization is high
            if utilization >= 0.8:
                logger.warning(
                    "High message queue utilization: %d/%d (%.1f%%). "
                    "Consider increasing max_message_queue_size or processing messages faster.",
                    queue_size,
                    max_size,
                    utilization * 100,
                )

        except asyncio.QueueFull:
            # Queue is full, handle according to strategy
            strategy = self.options.queue_overflow_strategy
            queue_size = self._message_queue.qsize()

            # Log warning
            logger.warning(
                "Message queue full (%d/%d), applying strategy: %s",
                queue_size,
                self.options.max_message_queue_size,
                strategy,
            )

            if strategy == "drop_oldest":
                # Remove oldest message and add new one
                try:
                    dropped = self._message_queue.get_nowait()
                    logger.debug("Dropped oldest message: %s", type(dropped).__name__)
                except asyncio.QueueEmpty:
                    pass
                await self._message_queue.put(message)

            elif strategy == "drop_newest":
                # Drop the new message
                logger.debug("Dropped newest message: %s", type(message).__name__)
                return

            elif strategy == "block":
                # Wait for space (with timeout to prevent infinite blocking)
                try:
                    await asyncio.wait_for(self._message_queue.put(message), timeout=30.0)
                except asyncio.TimeoutError:
                    logger.error("Timeout waiting for queue space after 30s")
                    raise QueueFullError(
                        f"Message queue overflow: timeout after 30s (size={queue_size})"
                    )

            else:  # "raise"
                raise QueueFullError(
                    f"Message queue overflow: {queue_size}/{self.options.max_message_queue_size}"
                )

    def _process_message(self, data: Dict[str, Any]) -> Optional[Message]:
        """Process raw message data into Message objects.

        Args:
            data: Raw message data from protocol

        Returns:
            Processed message or None
        """
        msg_type = data.get("type")

        if msg_type == "session_update":
            # Handle session updates from new protocol
            update_type = data.get("update_type")
            update = data.get("update", {})
            agent_id = data.get("agentId")  # Extract agent_id from session_update

            # Create AgentInfo if agent_id is available
            agent_info = None
            if agent_id:
                agent_info = AgentInfo.from_acp_data(data) or AgentInfo.from_agent_id_only(agent_id)

            if update_type == "agent_message_chunk":
                # Agent response chunk
                content = update.get("content", {})
                if content.get("type") == "text":
                    text = content.get("text", "")
                    if text:
                        return AssistantMessage(
                            AssistantMessageChunk(text=text),
                            agent_id=agent_id,
                            agent_info=agent_info,
                        )

            elif update_type == "agent_thought_chunk":
                # Agent thinking process
                content = update.get("content", {})
                if content.get("type") == "text":
                    thought = content.get("text", "")
                    if thought:
                        return AssistantMessage(
                            AssistantMessageChunk(thought=thought),
                            agent_id=agent_id,
                            agent_info=agent_info,
                        )

            elif update_type == "tool_call":
                # Tool call started
                from .types import Icon

                args = update.get("args", {})
                tool_msg = ToolCallMessage(
                    id=update.get("toolCallId", ""),
                    label=update.get("title", "Tool"),
                    icon=Icon("emoji", "🔧"),
                    status=ToolCallStatus(update.get("status", "in_progress")),
                    tool_name=update.get("toolName"),  # New field from protocol
                    agent_id=agent_id,
                    agent_info=agent_info,
                    args=args if args else None,
                )

                return tool_msg

            elif update_type == "tool_call_update":
                # Tool call update
                tool_id = update.get("toolCallId")
                tool_msg = ToolResultMessage(id=tool_id)
                tool_msg.status = ToolCallStatus(update.get("status", "completed"))
                # Update tool_name if provided in update
                if update.get("toolName"):
                    tool_msg.tool_name = update.get("toolName")
                # Update agent_id if not already set
                if not tool_msg.agent_id:
                    tool_msg.agent_id = agent_id
                # Update agent_info if not already set
                if not tool_msg.agent_info and agent_info:
                    tool_msg.agent_info = agent_info

                # Store content in the tool message if available
                if update.get("content") and len(update.get("content")) > 0:
                    content_data = update["content"][0]
                    content_type = content_data.get("type", "markdown")
                    # Ensure type is valid (only "markdown" or "diff")
                    if content_type not in ["markdown", "diff"]:
                        content_type = "markdown"
                    if content_type == "markdown":
                        text_data = content_data.get("content", {})
                        tool_msg.content = ToolCallContent(
                            type=content_type,
                            markdown=text_data.get("text", ""),
                        )
                    elif content_type == "diff":
                        tool_msg.content = ToolCallContent(
                            type=content_type,
                            markdown=content_data.get("content", ""),
                            path=content_data.get("path", ""),
                            old_text=content_data.get("oldText", ""),
                            new_text=content_data.get("newText", ""),
                            fileDiff=content_data.get("fileDiff", ""),
                        )
                    tool_msg.args = content_data.get("args")
                # Always return the tool message to notify about tool call
                return tool_msg

            elif update_type == "plan":
                # Plan update
                from .types import PlanEntry, PlanMessage

                entries_data = update.get("entries", [])
                entries = []
                for entry_data in entries_data:
                    entry = PlanEntry(
                        content=entry_data.get("content", ""),
                        priority=entry_data.get("priority", "medium"),
                        status=entry_data.get("status", "pending"),
                    )
                    entries.append(entry)

                if entries:
                    return PlanMessage(entries)

            elif update_type == "user_message_chunk":
                # User message echo (rarely used but supported in protocol)
                content = update.get("content", {})
                if content.get("type") == "text":
                    text = content.get("text", "")
                    if text:
                        # Return as UserMessage for completeness
                        return UserMessage([UserMessageChunk(text)])

        elif msg_type == "response":
            # Response to our request
            request_id = data.get("id")
            if request_id:
                # Handle pending request responses
                if request_id in self._pending_requests:
                    # This is handled by protocol layer
                    pass

            # Check if this is a prompt response with stopReason
            result = data.get("result", {})
            if "stopReason" in result:
                # Prompt completed with stopReason
                from .types import StopReason

                reason_str = result["stopReason"]
                stop_reason = None

                # Map string value to enum
                if reason_str == "end_turn":
                    stop_reason = StopReason.END_TURN
                elif reason_str == "max_tokens":
                    stop_reason = StopReason.MAX_TOKENS
                elif reason_str == "refusal":
                    stop_reason = StopReason.REFUSAL
                elif reason_str == "cancelled":
                    stop_reason = StopReason.CANCELLED

                return TaskFinishMessage(stop_reason=stop_reason)

        elif msg_type == "permission_request":
            # Tool confirmation request from protocol layer
            from .types import PermissionOption, ToolCall, ToolConfirmationRequestMessage

            tool_call_data = data.get("tool_call", {})
            options_data = data.get("options", [])

            # Convert to our types
            tool_call = ToolCall.from_dict(tool_call_data)
            options = [PermissionOption.from_dict(opt) for opt in options_data]

            return ToolConfirmationRequestMessage(
                session_id=data.get("session_id", ""),
                tool_call=tool_call,
                options=options,
                request_id=data.get("request_id"),
            )

        elif msg_type == "error":
            return ErrorMessage(
                code=data.get("code", -1),
                message=data.get("message", "Unknown error"),
                details=data.get("details"),
            )

        return None

    async def __aenter__(self) -> "IFlowClient":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Async context manager exit."""
        await self.disconnect()
        return False

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get current memory usage statistics.

        Returns:
            Dictionary containing:
            - message_queue_size: Current message queue size
            - message_queue_max: Maximum queue capacity
            - message_queue_utilization: Queue utilization percentage (0-1)
            - pending_tool_calls: Number of pending tool calls
            - pending_requests: Number of pending requests (if protocol available)
            - estimated_memory_bytes: Estimated total memory usage

        Example:
            ```python
            stats = client.get_memory_stats()
            print(f"Queue: {stats['message_queue_size']}/{stats['message_queue_max']}")
            print(f"Utilization: {stats['message_queue_utilization']:.1%}")
            ```
        """
        queue_size = self._message_queue.qsize()
        queue_max = self.options.max_message_queue_size

        # Debug logging if enabled
        if self.options.debug_memory:
            logger.debug(
                "[MemoryDebug] Getting memory stats: queue=%d/%d, pending_requests=%d",
                queue_size,
                queue_max,
                len(self._pending_requests)
            )

        stats = {
            "message_queue_size": queue_size,
            "message_queue_max": queue_max,
            "message_queue_utilization": queue_size / queue_max if queue_max > 0 else 0,
            "pending_tool_calls": len(self._pending_tool_calls),
            "pending_requests": len(self._pending_requests),
        }

        # Add protocol stats if available
        if self._protocol:
            stats["protocol_pending_requests"] = len(self._protocol._pending_requests)
            stats["protocol_pending_permissions"] = len(self._protocol._pending_permission_requests)

        # Estimate memory usage (rough approximation)
        # Average message size ~1KB, tool call ~500 bytes, request ~200 bytes
        estimated_bytes = (
            queue_size * 1024  # Messages in queue
            + len(self._pending_tool_calls) * 512  # Tool calls
            + len(self._pending_requests) * 200  # Pending requests
        )

        if self._protocol:
            estimated_bytes += (
                len(self._protocol._pending_requests) * 200
                + len(self._protocol._pending_permission_requests) * 200
            )

        stats["estimated_memory_bytes"] = estimated_bytes
        stats["estimated_memory_mb"] = estimated_bytes / (1024 * 1024)

        # Check memory limit enforcement
        if self.options.memory_limit_bytes is not None:
            if estimated_bytes > self.options.memory_limit_bytes:
                limit_mb = self.options.memory_limit_bytes / (1024 * 1024)
                logger.error(
                    "🚨 MEMORY LIMIT EXCEEDED: Current usage %.2f MB exceeds limit %.2f MB",
                    stats["estimated_memory_mb"],
                    limit_mb
                )
                stats["memory_limit_exceeded"] = True
                stats["memory_limit_mb"] = limit_mb
            else:
                stats["memory_limit_exceeded"] = False
                stats["memory_limit_mb"] = self.options.memory_limit_bytes / (1024 * 1024)

        # Check memory usage thresholds and log warnings (if monitoring enabled)
        if self.options.enable_memory_monitoring:
            utilization = stats["message_queue_utilization"]
            threshold = self.options.memory_warning_threshold
            
            if utilization >= 0.95:
                logger.error(
                    "🚨 CRITICAL: Memory queue at %.1f%% capacity (%d/%d). "
                    "System may drop messages or become unresponsive. "
                    "Consider increasing max_message_queue_size or processing messages faster.",
                    utilization * 100,
                    queue_size,
                    queue_max
                )
                stats["memory_warning_level"] = "critical"
            elif utilization >= 0.90:
                logger.warning(
                    "⚠️  HIGH: Memory queue at %.1f%% capacity (%d/%d). "
                    "Approaching limits. Monitor closely and consider scaling.",
                    utilization * 100,
                    queue_size,
                    queue_max
                )
                stats["memory_warning_level"] = "high"
            elif utilization >= threshold:
                logger.warning(
                    "⚠️  ELEVATED: Memory queue at %.1f%% capacity (%d/%d). "
                    "Consider reviewing message processing rate.",
                    utilization * 100,
                    queue_size,
                    queue_max
                )
                stats["memory_warning_level"] = "elevated"
            else:
                stats["memory_warning_level"] = "normal"
        else:
            stats["memory_warning_level"] = "monitoring_disabled"

        # Add memory profiler stats if debug mode enabled
        if self._memory_profiler:
            try:
                profiler_summary = self._memory_profiler.get_summary()
                stats["profiler"] = profiler_summary
            except Exception as e:
                logger.error("Failed to get profiler summary: %s", e)

        # Call optional callback if provided
        if self.options.memory_stats_callback is not None:
            try:
                self.options.memory_stats_callback(stats.copy())
            except Exception as e:
                logger.error("Memory stats callback failed: %s", e)

        return stats
    
    def get_memory_profiler(self) -> Optional["MemoryProfiler"]:
        """Get the memory profiler instance.
        
        Returns:
            MemoryProfiler instance if debug_memory is enabled, None otherwise
            
        Example:
            ```python
            options = IFlowOptions(debug_memory=True)
            client = IFlowClient(options)
            
            profiler = client.get_memory_profiler()
            if profiler:
                profiler.take_snapshot()
                allocations = profiler.get_top_allocations(limit=10)
                for alloc in allocations:
                    print(f"{alloc['filename']}: {alloc['size_mb']:.2f} MB")
            ```
        """
        return self._memory_profiler
    
    def add_event_listener(self, event_type: str, callback: Callable) -> None:
        """Add an event listener using weak reference.
        
        The callback is stored as a weak reference, allowing it to be
        garbage collected when no longer used elsewhere. This prevents
        memory leaks from forgotten listeners.
        
        Args:
            event_type: Type of event to listen for (e.g., 'message', 'tool_call')
            callback: Callback function to invoke when event occurs
            
        Example:
            ```python
            def on_message(message):
                print(f"Received: {message}")
            
            client.add_event_listener('message', on_message)
            ```
            
        Note:
            Lambdas and bound methods cannot be weakly referenced.
            Use regular functions or class methods instead.
        """
        self._event_manager.add_listener(event_type, callback)
    
    def remove_event_listener(self, event_type: str, callback: Callable) -> None:
        """Remove an event listener.
        
        Args:
            event_type: Type of event
            callback: Callback function to remove
        """
        self._event_manager.remove_listener(event_type, callback)
    
    def get_event_stats(self) -> Dict[str, Any]:
        """Get event listener statistics.
        
        Returns:
            Dictionary with event statistics including:
            - event_types: Number of event types
            - total_listeners: Total number of active listeners
            - events: Breakdown by event type
        """
        return self._event_manager.get_stats()
