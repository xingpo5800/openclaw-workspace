"""iFlow process management.

This module handles automatic startup and management of iFlow CLI processes.
Each IFlowClient instance gets its own iFlow process.
"""

import asyncio
import logging
import platform
import shutil
import socket
from collections import deque
from pathlib import Path
from typing import Deque, List, Optional

logger = logging.getLogger(__name__)


class IFlowNotInstalledError(Exception):
    """Raised when iFlow CLI is not installed."""

    pass


class IFlowProcessManager:
    """Manages the lifecycle of an iFlow CLI process.

    This class handles:
    - Detecting if iFlow is installed
    - Finding available ports
    - Starting iFlow with the ACP protocol
    - Cleanly shutting down the process
    """

    def __init__(self, start_port: int = 8090, max_log_lines: int = 10000, log_file: Optional[str] = None):
        """Initialize the process manager.

        Args:
            start_port: The port to start checking from (default: 8090)
            max_log_lines: Maximum log lines to keep in memory (default: 10000)
            log_file: Optional file path to write logs (None = memory only)
        """
        self._process: Optional[asyncio.subprocess.Process] = None
        self._port: Optional[int] = None
        self._start_port = start_port
        self._iflow_path: Optional[str] = None
        self._max_log_lines = max_log_lines
        self._log_file = log_file
        self._log_file_handle = None

        # Output draining
        self._stdout_buffer: Deque[str] = deque(maxlen=max_log_lines)
        self._stderr_buffer: Deque[str] = deque(maxlen=max_log_lines)
        self._stdout_task: Optional[asyncio.Task] = None
        self._stderr_task: Optional[asyncio.Task] = None

    @property
    def port(self) -> Optional[int]:
        """Get the port the iFlow process is running on."""
        return self._port

    @property
    def url(self) -> str:
        """Get the WebSocket URL for connecting to iFlow."""
        if not self._port:
            raise RuntimeError("iFlow process not started")
        return f"ws://localhost:{self._port}/acp"

    def _find_iflow(self) -> str:
        """Find the iFlow CLI executable.

        Returns:
            Path to the iFlow executable

        Raises:
            IFlowNotInstalledError: If iFlow is not found
        """
        # First check if it's in PATH
        if iflow_path := shutil.which("iflow"):
            logger.debug(f"Found iFlow at: {iflow_path}")
            return iflow_path

        # Check common installation locations
        locations = [
            Path.home() / ".npm-global/bin/iflow",
            Path("/usr/local/bin/iflow"),
            Path.home() / ".local/bin/iflow",
            Path.home() / "node_modules/.bin/iflow",
            Path.home() / ".yarn/bin/iflow",
            # Windows locations
            Path.home() / "AppData/Roaming/npm/iflow.cmd",
            Path("C:/Program Files/nodejs/iflow.cmd"),
        ]

        for path in locations:
            if path.exists() and path.is_file():
                logger.debug(f"Found iFlow at: {path}")
                return str(path)

        # Check if npm is installed
        npm_installed = shutil.which("npm") is not None
        node_installed = shutil.which("node") is not None

        system = platform.system().lower()

        # Build installation instructions based on platform
        if system == "windows":
            if not npm_installed and not node_installed:
                error_msg = "iFlow 需要 Node.js，但系统中未安装。\n\n"
                error_msg += "请先安装 Node.js: https://nodejs.org/\n"
                error_msg += "\n安装 Node.js 后，使用以下命令安装 iFlow:\n"
                error_msg += "  npm install -g @iflow-ai/iflow-cli@latest"
            else:
                error_msg = "未找到 iFlow CLI。请使用以下命令安装:\n"
                error_msg += "  npm install -g @iflow-ai/iflow-cli@latest"
        else:
            # Mac/Linux/Ubuntu
            error_msg = "未找到 iFlow CLI。请使用以下命令安装:\n\n"
            error_msg += "🍎 Mac/Linux/Ubuntu 用户:\n"
            error_msg += '  bash -c "$(curl -fsSL https://gitee.com/iflow-ai/iflow-cli/raw/main/install.sh)"\n\n'
            error_msg += "🪟 Windows 用户:\n"
            error_msg += "  npm install -g @iflow-ai/iflow-cli@latest"

        raise IFlowNotInstalledError(error_msg)

    def _is_port_available(self, port: int) -> bool:
        """Check if a port is available for use.

        Args:
            port: Port number to check

        Returns:
            True if the port is available, False otherwise
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("localhost", port))
                return True
            except OSError:
                return False

    def _find_available_port(self, start_port: int = 8090, max_attempts: int = 100) -> int:
        """Find an available port starting from the given port.

        Args:
            start_port: Port to start searching from
            max_attempts: Maximum number of ports to try

        Returns:
            An available port number

        Raises:
            RuntimeError: If no available port is found
        """
        for i in range(max_attempts):
            port = start_port + i
            if self._is_port_available(port):
                logger.debug(f"Found available port: {port}")
                return port

        raise RuntimeError(
            f"No available port found in range {start_port}-{start_port + max_attempts}"
        )

    async def start(self) -> str:
        """Start the iFlow process.

        Returns:
            The WebSocket URL to connect to

        Raises:
            IFlowNotInstalledError: If iFlow is not installed
            RuntimeError: If the process fails to start
        """
        if self._process and self._process.returncode is None:
            # Process already running
            return self.url

        # Find iFlow executable
        self._iflow_path = self._find_iflow()

        # Find an available port
        self._port = self._find_available_port(self._start_port)

        # Build command
        cmd = [self._iflow_path, "--experimental-acp", "--port", str(self._port)]

        logger.info(f"Starting iFlow process: {' '.join(cmd)}")

        try:
            # Start the process
            self._process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.DEVNULL,  # No stdin needed
            )

            # Open log file if configured
            if self._log_file:
                try:
                    self._log_file_handle = open(self._log_file, "a", encoding="utf-8")
                    logger.info(f"Opened log file: {self._log_file}")
                except Exception as e:
                    logger.error(f"Failed to open log file {self._log_file}: {e}")
                    self._log_file_handle = None

            # Start output draining tasks immediately to prevent buffer overflow
            self._stdout_task = asyncio.create_task(self._drain_output("stdout"))
            self._stderr_task = asyncio.create_task(self._drain_output("stderr"))
            logger.debug("Started output draining tasks")

            # Wait a bit to ensure the process starts successfully
            await asyncio.sleep(0.5)

            # Check if process is still running
            if self._process.returncode is not None:
                # Process exited, read any remaining output from buffers
                error_lines = list(self._stderr_buffer)
                error_msg = "\n".join(error_lines) if error_lines else "No error output"
                raise RuntimeError(f"iFlow process exited immediately: {error_msg}")

            logger.info(f"iFlow process started on port {self._port} (PID: {self._process.pid})")
            return self.url

        except Exception as e:
            self._process = None
            self._port = None
            raise RuntimeError(f"Failed to start iFlow process: {e}") from e

    async def stop(self) -> None:
        """Stop the iFlow process gracefully."""
        if not self._process:
            return

        if self._process.returncode is not None:
            # Process already stopped
            self._process = None
            self._port = None
            return

        logger.info(f"Stopping iFlow process (PID: {self._process.pid})")

        try:
            # Cancel output draining tasks first
            if self._stdout_task:
                self._stdout_task.cancel()
                try:
                    await self._stdout_task
                except asyncio.CancelledError:
                    pass
                self._stdout_task = None

            if self._stderr_task:
                self._stderr_task.cancel()
                try:
                    await self._stderr_task
                except asyncio.CancelledError:
                    pass
                self._stderr_task = None

            # Close log file if open
            if self._log_file_handle:
                try:
                    self._log_file_handle.close()
                    logger.info(f"Closed log file: {self._log_file}")
                except Exception as e:
                    logger.error(f"Failed to close log file: {e}")
                finally:
                    self._log_file_handle = None

            # Try graceful termination first
            self._process.terminate()

            # Wait up to 5 seconds for graceful shutdown
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
                logger.info("iFlow process terminated gracefully")
            except asyncio.TimeoutError:
                # Force kill if graceful shutdown fails
                logger.warning("iFlow process did not terminate gracefully, forcing kill")
                self._process.kill()
                await self._process.wait()

            # Note: StreamReader objects (stdout/stderr) don't have close() method
            # They are automatically cleaned up when the process terminates
            # Only stdin (StreamWriter) needs explicit closing
            if self._process.stdin:
                try:
                    self._process.stdin.close()
                    await self._process.stdin.wait_closed()
                except Exception:
                    pass  # Ignore errors during stdin cleanup

        except ProcessLookupError:
            # Process already gone
            pass
        except Exception as e:
            logger.error(f"Error stopping iFlow process: {e}")
        finally:
            # Clear process reference to prevent __del__ issues
            self._process = None
            self._port = None

    async def __aenter__(self) -> "IFlowProcessManager":
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.stop()

    async def _drain_output(self, stream_name: str) -> None:
        """Continuously drain process output to prevent buffer overflow.

        This task runs in the background for the lifetime of the process,
        reading stdout/stderr and storing in bounded circular buffers.

        Args:
            stream_name: 'stdout' or 'stderr'
        """
        if not self._process:
            return

        stream = self._process.stdout if stream_name == "stdout" else self._process.stderr
        if not stream:
            logger.warning(f"No {stream_name} stream available")
            return

        buffer = self._stdout_buffer if stream_name == "stdout" else self._stderr_buffer

        try:
            while True:
                # Read line from stream
                line = await stream.readline()

                # EOF reached
                if not line:
                    logger.debug(f"EOF on {stream_name}")
                    break

                # Decode and store in buffer
                decoded = line.decode("utf-8", errors="ignore").rstrip()
                buffer.append(decoded)

                # Write to log file if configured
                if self._log_file_handle:
                    try:
                        self._log_file_handle.write(f"[{stream_name}] {decoded}\n")
                        self._log_file_handle.flush()
                    except Exception as e:
                        logger.error(f"Failed to write to log file: {e}")

                # Log at appropriate level
                if stream_name == "stderr":
                    logger.debug(f"iFlow stderr: {decoded}")
                else:
                    logger.debug(f"iFlow stdout: {decoded}")

        except asyncio.CancelledError:
            logger.debug(f"Output draining cancelled for {stream_name}")
        except Exception as e:
            logger.error(f"Error draining {stream_name}: {e}")

    def get_process_logs(self, last_n: int = 100, stream: str = "both") -> List[str]:
        """Get recent process output lines.

        Args:
            last_n: Number of recent lines to return (default: 100)
            stream: Which stream to return ('stdout', 'stderr', or 'both')

        Returns:
            List of log lines (most recent last)
        """
        if stream == "stdout":
            return list(self._stdout_buffer)[-last_n:]
        elif stream == "stderr":
            return list(self._stderr_buffer)[-last_n:]
        else:  # 'both'
            # Interleave stdout and stderr (approximate chronological order)
            stdout_lines = [f"[stdout] {line}" for line in self._stdout_buffer]
            stderr_lines = [f"[stderr] {line}" for line in self._stderr_buffer]
            all_lines = stdout_lines + stderr_lines
            return all_lines[-last_n:]
